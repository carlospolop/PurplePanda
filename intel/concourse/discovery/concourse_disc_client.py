import concoursepy
import yaml
import os
import logging
import requests
import json

from base64 import b64decode
from core.utils.purplepanda_config import PurplePandaConfig
from core.utils.purplepanda import PurplePanda
from core.models import ContainerImage
from intel.concourse.models import ConcourseResource
from intel.github.models import GithubRepo

"""
Example yaml:

concourse:
- url: "string"
  username: "string"
  password: "string"
  token: "https://ci.example.com"

At least URL and token or username+password need to be filled
"""


class ConcourseDiscClient(PurplePanda):
    logger = logging.getLogger(__name__)

    def __init__(self, get_creds=True):
        super().__init__()
        panop = PurplePandaConfig()

        self.env_var = panop.get_env_var("concourse")
        self.env_var_content = os.getenv(self.env_var)
        assert bool(self.env_var_content), "Concourse env variable not configured"

        self.concurse_config: dict = yaml.safe_load(b64decode(self.env_var_content))
        assert bool(self.concurse_config.get("concourse", None)), "Concourse env variable isn't a correct yaml"

        if get_creds:
            self.creds: dict = self._concourse_creds()

    def _concourse_creds(self) -> dict:
        """
        Parse concourse env variable and extract all the concourse credentials
        """

        creds: dict = []

        for entry in self.concurse_config["concourse"]:
            url = entry["url"]
            if entry.get("token"):
                kwargs = {"token": entry.get("token")}

            elif entry.get("username") and entry.get("password"):
                kwargs = {"username": entry.get("username"), "password": entry.get("password")}

            else:
                assert False, f"Concourse entry doesn't contain token or username+password: {entry}"

            cred = concoursepy.api(url, **kwargs)

            if not cred.auth():
                self.logger.error(f"The crendetials '{kwargs}' aren't valid.")

            else:
                creds.append({
                    "cred": cred,
                })

        return creds


class ConcourseDisc(ConcourseDiscClient):
    logger = logging.getLogger(__name__)

    def __init__(self, cred) -> None:
        super().__init__(get_creds=False)
        self.cred = cred
        self.task_name = "concourse"

    def call_concourse_api(self, f, ret_val=None, **kwargs):
        """Call the concourse api from one site to manage errors"""

        if ret_val is None:
            ret_val = []
        try:
            return f(**kwargs)

        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                self.logger.warning(f"Councourse not found: {e}")

        except Exception as e:
            self.logger.error(f"Councourse error: {e}")

        return ret_val

    def get_resource_obj(self, resource: dict):
        """Given the dict of a resource get the resource object"""

        name = resource.get("name") or resource.get("identifier") or resource.get("image")

        if not name:
            self.logger.critical(f"Coulden't find resource name of {resource}")

        res_obj = ConcourseResource(
            name=name,
            type=resource.get("type"),
            image=resource.get("image"),
            version=resource.get("version"),
            privileged=resource.get("privileged", False),
            unique_version_history=resource.get("unique_version_history"),
            source=json.dumps(resource.get("source")),
        ).save()

        # Might be using a docker container
        if resource.get("type") == "docker-image":
            if repo := resource.get("source", {}).get("repository"):
                conimg_obj = ContainerImage(name=repo).save()
                res_obj.run_images.update(conimg_obj)
                res_obj.save()

        # Might be using a github repo
        if resource.get("type") == "git":
            if uri := resource.get("source", {}).get("uri"):
                grepo_obj = GithubRepo(full_name=uri.split(":")[-1].replace(".git", "")).save()
                res_obj.github_repos.update(grepo_obj)
                res_obj.save()

        return res_obj
