from pycircleci.api import Api, CIRCLE_API_URL
import yaml
import os
import json
import logging
import requests
import re

from base64 import b64decode
from core.utils.purplepanda_config import PurplePandaConfig
from core.utils.purplepanda import PurplePanda
from intel.circleci.models import CircleCIProject, CircleCISecret, CircleCIVar, CircleCIOrganization
from intel.github.models import GithubRepo
from intel.bitbucket.models import BitbucketRepo

"""
Example yaml:

circleci:
- url: "string"
  token: "https://ci.example.com"
  org_slug: "github/org_name"
  projects: ["repo1", "repo2"]

The url and org_slug is optional, the token isn't
"""

KNOWN_PROJECTS = set()

class CircleCIDiscClient(PurplePanda):
    logger = logging.getLogger(__name__)

    def __init__(self, get_creds=True):
        super().__init__()
        panop = PurplePandaConfig()
        
        self.env_var = panop.get_env_var("circleci")
        self.env_var_content = os.getenv(self.env_var)
        assert bool(self.env_var_content), "CircleCI env variable not configured"
        
        self.circleci_config : dict = yaml.safe_load(b64decode(self.env_var_content))
        assert bool(self.circleci_config.get("circleci", None)), "CircleCI env variable isn't a correct yaml"

        if get_creds:
            self.creds : dict = self._circleci_creds()
    
    def _circleci_creds(self) -> dict:
        """
        Parse circleci env variable and extract all the circleci credentials
        """

        creds : dict = []

        for entry in self.circleci_config["circleci"]:
            
            if entry.get("token"):
                token = entry["token"]
            else:
                assert False, f"CircleCI entry doesn't contain a token: {entry}"
            
            if entry.get("url"):
                url = entry["url"]
            else:
                url = CIRCLE_API_URL
            
            org_slug = entry.get("org_slug", "")
            if org_slug and not "/" in org_slug:
                self.logger.error(f"Org slug is incorrect: {org_slug}. Add 'github/' or 'bitbucket/' at the begginig")
                continue
            
            if org_slug and not org_slug.startswith("github/") and not org_slug.startswith("bitbucket/"):
                self.logger.error(f"Org slug is incorrect: {org_slug}. Must start with 'github/' or 'bitbucket/'")
                continue

            projects = entry.get("projects", [])
            
            cred = Api(token=token, url=CIRCLE_API_URL)
            
            try:
                slugs = set(org_slug) if org_slug else set()
                for p in cred.get_projects():
                    slugs.add(p["vcs_type"] + "/" + p["username"]) #This would be something like "github/org_name"

                creds.append({
                    "cred": cred,
                    "slugs": slugs,
                    "projects": projects
                })
            
            except:
                self.logger.error(f"The token {token} in url {url} isn't valid. If you are sure this is a CircleCI token, it might be a project token (which isn't supported).")

        return creds


class CircleCIDisc(CircleCIDiscClient):
    logger = logging.getLogger(__name__)

    def __init__(self, cred, orgs, projects) -> None:
        super().__init__(get_creds=False)
        self.cred = cred
        self.orgs = orgs
        self.projects = projects
        self.task_name = "circleci"
    

    def call_circleci_api(self, f, ret_val=[], *args, **kwargs):
        """Call the circleci api from one site to manage errors"""
        
        try:
            return f(*args, **kwargs)
        
        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                self.logger.warning(f"CircleCI not found: {e}")
        
        except Exception as e:
            self.logger.error(f"Councourse error: {e}")
        
        return ret_val


    def _disc_project(self, project_slug: str, org: str) -> CircleCIProject:
        """Given a project slug get the project info"""

        proj_info = None
        if project_slug not in KNOWN_PROJECTS:
            # Only request proj info to the api for the same project 1 time
            proj_info = self.call_circleci_api(self.cred.get_project_settings, [], username=org.split("/")[-1], project=project_slug.split("/")[-1])
            KNOWN_PROJECTS.add(project_slug)

        if not proj_info:
            proj_obj = CircleCIProject(name=project_slug).save()
        
        else:
            proj_obj = CircleCIProject(
                name = project_slug,
                irc_server = proj_info.get("irc_server", ""),
                irc_keyword = proj_info.get("irc_keyword", ""),
                irc_password = proj_info.get("irc_password", ""),
                irc_username = proj_info.get("irc_username", ""),
                irc_notify_prefs = proj_info.get("irc_notify_prefs", ""),

                slack_integration_channel = proj_info.get("slack_integration_channel", ""),
                slack_integration_team_id = proj_info.get("slack_integration_team_id", ""),
                slack_integration_team = proj_info.get("slack_integration_team", ""),
                slack_integration_notify_prefs = proj_info.get("slack_integration_notify_prefs", ""),
                slack_integration_webhook_url = proj_info.get("slack_integration_webhook_url", ""),
                slack_subdomain = proj_info.get("slack_subdomain", ""),
                slack_notify_prefs = proj_info.get("slack_notify_prefs", ""),
                slack_channel_override = proj_info.get("slack_channel_override", ""),
                slack_api_token = proj_info.get("slack_api_token", ""),
                slack_channel = proj_info.get("slack_channel", ""),
                slack_integration_channel_id = proj_info.get("slack_integration_channel_id", ""),
                slack_integration_access_token = proj_info.get("slack_integration_access_token", ""),

                vcs_type = proj_info.get("vcs-type", ""),
                vcs_url = proj_info.get("vcs_url", ""),
                
                aws = json.dumps(proj_info.get("aws", "")),
                default_branch = proj_info.get("default_branch", ""),
                flowdock_api_token = proj_info.get("flowdock_api_token", ""),
                has_usable_key = proj_info.get("has_usable_key", False),
                oss = proj_info.get("oss", False),
                jira = json.dumps(proj_info.get("jira", "")),
                ssh_keys = json.dumps(proj_info.get("ssh_keys", "")),
                feature_flags = json.dumps(proj_info.get("feature_flags", ""))
            ).save()
            org_obj = CircleCIOrganization(name=org).save()
            proj_obj.orgs.update(org_obj)

            if proj_info["vcs-type"].lower() == "github":
                repo_full_name = "/".join(project_slug.split("/")[1:])
                ghrepo_obj = GithubRepo(
                    full_name=repo_full_name,
                    name = repo_full_name.split("/")[-1]
                    ).save()
                proj_obj.gh_repos.update(ghrepo_obj)
                proj_obj.save()
            
            elif proj_info["vcs-type"].lower() == "bitbucket":
                repo_full_name = "/".join(project_slug.split("/")[1:])
                bkrepo_obj = BitbucketRepo(
                    full_name=repo_full_name,
                    name = repo_full_name.split("/")[-1]
                    ).save()
                proj_obj.bk_repos.update(bkrepo_obj)
                proj_obj.save()
            
            else:
                self.logger.error(f"I don't know if {proj_info.get('vcs-type')} is github or bitbucket, please create an issue in purplepana's github with this info")
            
            self._disc_proj_secrets(proj_obj, org)

            # Get some pipelines vars related to the project
            branches = set(list(proj_info["branches"].keys())[:5])
            branches.add(proj_info["default_branch"])
            for branch in branches:
                if branch in  proj_info["branches"] and proj_info["branches"][branch]["latest_workflows"]:
                    for workflow in list(proj_info["branches"][branch]["latest_workflows"].keys())[:2]:
                        workflow_info = self.call_circleci_api(self.cred.get_workflow, workflow_id=proj_info["branches"][branch]["latest_workflows"][workflow]["id"])
                        self._disc_vars(workflow_info["pipeline_id"], proj_obj)

        return proj_obj


    def _disc_proj_secrets(self, proj_obj: CircleCIProject, org: str) -> CircleCIProject:
        """Given a project get the project secrets"""

        proj_env_vars = self.call_circleci_api(self.cred.list_envvars, [], username=org.split("/")[-1], project=proj_obj.name.split("/")[-1])

        for env_var in proj_env_vars:
            secret_obj = CircleCISecret(
                name = env_var["name"],
                value = env_var["value"],
            ).save()
            proj_obj.secrets.update(secret_obj)
        
        proj_obj.save()

        
    def _disc_vars_in_pipe(self, pipe_id, proj_obj: CircleCIProject):
        """Given a pipeline discover the variables in the configuration"""

        config = self.call_circleci_api(self.cred.get_pipeline_config, [], pipeline_id=pipe_id)

        if not config:
            return
        
        disc_vars_in_txt(proj_obj, config["source"], pipe_id)


def disc_vars_in_txt(proj_obj: CircleCIProject, text_yaml: str, pipe_id=".circleci/config.yml"):
    """Given a text, dicover vars"""

    env_vars = {}
    shell_declared_vars = re.findall(r'\w+=[^=].*', text_yaml)
    for env_var in shell_declared_vars:
        name = env_var.split("=")[0]
        val = "=".join(env_var.split("=")[1:])
        env_vars[name] = val
    
    try:
        env_declared_vars = _search_environment(yaml.safe_load(text_yaml))
        env_vars.update(_search_environment(env_declared_vars))
    except yaml.parser.ParserError:
        pass
    except yaml.scanner.ScannerError:
        pass
    
    for k,v in env_vars.items():
        var_obj = CircleCIVar(
            name = k,
            value = v
        ).save()
        proj_obj.vars.update(var_obj, pipeline_id=pipe_id)
    
    proj_obj.save()
    

def _search_environment(config_dic) -> dict:
    if type(config_dic) is not dict:
        return {}
    
    envs = dict()
    if "environment" in config_dic:
        envs = config_dic["environment"]

    for v in config_dic.values():
        if type(v) is dict:
            envs.update(_search_environment(v))
    
    return envs
