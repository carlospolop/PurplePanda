import json
import time
import subprocess
import os
import validators
import re
from urllib.parse import urlparse
from shutil import which
from typing import List, Tuple
from github import NamedUser, Team, Repository, Organization, Branch, Membership, GithubException

from .github_disc_client import GithubDiscClient
from intel.circleci.discovery.circleci_disc_client import disc_vars_in_txt
from intel.github.models.github_model import GithubAction, GithubUser, GithubTeam, GithubRepo, GithubBranch, \
    GithubOrganization, GithubSecret, GithubLeak, GithubEnvironment, GithubSelfHostedRunner, GithubWebhook
from intel.circleci.models import CircleCIProject, CircleCIOrganization, CircleCIVar
from core.models import PublicIP, PublicDomain

USERS = dict()
TEAMS = dict()
REPOS = dict()
ORGS = dict()
INV_USERS = set()
INV_TEAMS = set()
INV_REPOS = set()
INV_ORGS = set()


class GithubDisc(GithubDiscClient):
    def __init__(self, cred, org_name, str_cred, *args, **kwargs):
        super().__init__(get_creds=False)
        self.cred = cred
        self.org_name = org_name
        self.str_cred = str_cred
        self.github_only_org = kwargs.get("github_only_org", False)
        self.github_only_org_and_org_users = kwargs.get("github_only_org_and_org_users", False)
        self.all_branches = kwargs.get("all_branches", False)
        self.github_no_leaks = kwargs.get("github_no_leaks", False)
        self.github_get_redundant_info = kwargs.get("github_get_redundant_info", False)
        self.github_get_archived = kwargs.get("github_get_archived", False)
        self.github_write_as_merge = kwargs.get("github_write_as_merge", False)

        if not self.github_no_leaks and which("gitleaks") is None:
            self.gitleaks_installed = False
            self.logger.error(
                "Gitleaks isn't installed. If you want to search for leaks install https://github.com/zricethezav/gitleaks/releases/latest")
            exit()
        else:
            self.gitleaks_installed = True

        if not self.github_no_leaks and which("timeout") is None:
            self.logger.error(
                "timeout isn't installed. You need it to search for leaks, if you are in MacOS you can install it with: brew install coreutils")
            exit()

        self.task_name = "Github"

    def _disc(self) -> None:
        """
        This module starts discovering all the organizations the user has access to.
        For each org, all the info is disocvered,

        Then, the module discovers information about the user of the current token.
        """

        # Start discovreing org info
        if self.github_only_org or self.github_only_org_and_org_users:
            orgs = set()
        else:
            orgs = set(self.call_github(self.cred.get_user().get_orgs, ret_val=None))

        if self.org_name:
            orgs.add(self.cred.get_organization(self.org_name))

        for org in orgs:
            self.org = org
            self.save_org(org)

        # Get current token user info
        if not self.github_only_org and not self.github_only_org_and_org_users:
            self.save_user(self.call_github(self.cred.get_user, ret_val=None))

    def get_members(self, github_obj, n4j_obj):
        """
        Given a github object (org or team), get all the members 
        """

        members = self.call_github(github_obj.get_members, ret_val=[])
        self._disc_loop(members, self._get_member, __name__.split(".")[-1] + f".get_members({n4j_obj.name})",
                        **{"n4j_obj": n4j_obj, "github_obj": github_obj})
        n4j_obj.save()

    def _get_member(self, github_user, **kwargs):

        n4j_obj = kwargs["n4j_obj"]
        github_obj = kwargs["github_obj"]
        user_obj: GithubUser = self.save_user(github_user)
        if type(n4j_obj) is GithubOrganization:
            try:
                membership: Membership.Membership = github_user.get_organization_membership(n4j_obj.name)
                role = membership.role
            except GithubException as e:
                if "You must be a member" in str(e):
                    role = "unknown"
                else:
                    raise e

            n4j_obj.users.update(user_obj, membership=role)

        elif type(n4j_obj) is GithubTeam:
            membership: Membership.Membership = github_obj.get_team_membership(user_obj.name)
            n4j_obj.users.update(user_obj, membership=membership.role)

        else:
            n4j_obj.users.update(user_obj)

    def get_teams(self, github_obj, n4j_obj):
        """
        Given a github object (org), get all the teams 
        """

        teams = self.call_github(github_obj.get_teams, ret_val=[])
        self._disc_loop(teams, self._get_team, __name__.split(".")[-1] + f".get_teams({n4j_obj.name})",
                        **{"n4j_obj": n4j_obj, "github_obj": github_obj})
        n4j_obj.save()

    def _get_team(self, team, **kwargs):
        n4j_obj = kwargs["n4j_obj"]
        github_obj = kwargs["github_obj"]
        team_obj: GithubTeam = self.save_team(team)
        n4j_obj.teams.update(team_obj)

    def get_repos(self, github_obj, n4j_obj):
        """
        Given a github object (org, user), get all the repos 
        """

        repos = self.call_github(github_obj.get_repos, ret_val=[])
        self._disc_loop(repos, self._get_repo, __name__.split(".")[-1] + f".get_repos({n4j_obj.name})",
                        **{"n4j_obj": n4j_obj, "github_obj": github_obj})
        n4j_obj.save()

    def _get_repo(self, repo, **kwargs):
        n4j_obj = kwargs["n4j_obj"]
        github_obj = kwargs["github_obj"]
        repo_obj: GithubRepo = self.save_repo(repo)
        n4j_obj.repos.update(repo_obj)

    def get_branches(self, github_obj, n4j_obj):
        """
        Given a github object (repo), get all the branches 
        """

        branches = []
        if not self.all_branches:
            try:
                # This should never be [None]
                branches = [self.call_github(github_obj.get_branch, ret_val=None, branch=github_obj.default_branch)]
            except:
                pass

        else:
            branches = self.call_github(github_obj.get_branches, ret_val=[])

        for branch in branches:
            if branch:
                branch_obj: GithubBranch = self.save_branch(branch, github_obj.full_name)
                n4j_obj.branches.update(branch_obj)

        n4j_obj.save()

    def get_orgs(self, github_obj, n4j_obj):
        """
        Given a github object (user), get all the orgs the user belongs to 
        """

        for org in self.call_github(github_obj.get_orgs, ret_val=[]):
            org_obj: GithubOrganization = self.save_org(org, investigate=False)  # Do not investigate new organizations
            org_obj.users.update(n4j_obj)

        org_obj.save()

    @GithubDiscClient.call_github_decorator
    def save_user(self, github_user: NamedUser.NamedUser, investigate=True) -> GithubUser:
        """
        Save the given user.
        Get also repos of the user. 
        """

        global USERS, INV_USERS

        gid = github_user.id
        if gid in USERS:
            user_obj = USERS[gid]

        else:
            user_obj: GithubUser = GithubUser(
                name=github_user.login,
                person_name=github_user.name,
                avatar_url=github_user.avatar_url,
                bio=github_user.bio,
                blog=github_user.blog,
                disk_usage=github_user.disk_usage,
                email=github_user.email,
                followers=github_user.followers,
                followers_url=github_user.followers_url,
                following=github_user.following,
                following_url=github_user.following_url,
                gists_url=github_user.gists_url,
                gravatar_id=github_user.gravatar_id,
                hireable=github_user.hireable,
                id=github_user.id,
                last_modified=github_user.last_modified,
                location=github_user.location,
                public_gists=github_user.public_gists,
                public_repos=github_user.public_repos,
                site_admin=github_user.site_admin,
                role=github_user.role,
                twitter_username=github_user.twitter_username,
            ).save()

        if investigate and not gid in INV_USERS:
            INV_USERS.add(gid)

            if not self.github_only_org:
                for repo in self.call_github(github_user.get_repos, ret_val=[]):
                    repo_obj: GithubRepo = self.save_repo(repo, investigate=True)
                    perms = repo.permissions
                    user_obj.perms_repos.update(repo_obj,
                                                admin=perms.admin,
                                                maintain=perms.maintain,
                                                pull=perms.pull,
                                                push=perms.push,
                                                triage=perms.triage)

            for org in self.call_github(github_user.get_orgs, ret_val=[]):
                org_obj: GithubOrganization = self.save_org(org, investigate=False)
                user_obj.orgnaizations.update(org_obj)

            user_obj.save()

        USERS[gid] = user_obj
        return USERS[gid]

    @GithubDiscClient.call_github_decorator
    def save_team(self, github_team: Team.Team, investigate=True) -> GithubTeam:
        """
        Save the given team.
        Get also members of the team.
        """
        global TEAMS, INV_TEAMS

        gid = github_team.id
        if gid in TEAMS:
            team_obj = TEAMS[gid]

        else:
            team_obj: GithubTeam = GithubTeam(
                name=github_team.name,
                description=github_team.description,
                id=github_team.id,
                last_modified=github_team.last_modified,
                members_count=github_team.members_count,
                permission=github_team.permission,
                repos_count=github_team.repos_count,
                slug=github_team.slug,
            ).save()

        if investigate and not gid in INV_TEAMS:
            INV_TEAMS.add(gid)

            if github_team.parent:
                team_obj_parent: GithubTeam = GithubTeam(id=github_team.parent.id).save()
                team_obj.teams.update(team_obj_parent)

            for repo in self.call_github(github_team.get_repos, ret_val=[]):
                repo_obj: GithubRepo = self.save_repo(repo, investigate=False)
                perms = repo.permissions
                team_obj.perms_repos.update(repo_obj,
                                            admin=perms.admin,
                                            maintain=perms.maintain,
                                            pull=perms.pull,
                                            push=perms.push,
                                            triage=perms.triage)

            team_obj.save()
            self.get_members(github_team, team_obj)

        TEAMS[gid] = team_obj
        return TEAMS[gid]

    @GithubDiscClient.call_github_decorator
    def save_repo(self, github_repo: Repository.Repository, investigate=True) -> GithubRepo:
        """
        Save the given repo.
        Get also secrets of the repo.
        Get also permissions over the repo. 
        Get also the codeowners of the repo.
        """

        global REPOS, INV_REPOS

        gid = github_repo.id
        if gid in REPOS:
            repo_obj = REPOS[gid]

        else:
            allow_merge_commit = None
            allow_rebase_merge = None
            allow_squash_merge = None
            delete_branch_on_merge = None
            subscribers_count = None
            try:
                allow_merge_commit = github_repo.allow_merge_commit
                allow_rebase_merge = github_repo.allow_rebase_merge
                allow_squash_merge = github_repo.allow_squash_merge
                delete_branch_on_merge = github_repo.delete_branch_on_merge
                subscribers_count = github_repo.subscribers_count
            except Exception:
                self.logger.warning("Failed to get repo settings for repo %s (potentially because it doesn't exist)",
                                    github_repo.full_name)

            repo_obj: GithubRepo = GithubRepo(
                id=github_repo.id,
                allow_merge_commit=allow_merge_commit,
                allow_rebase_merge=allow_rebase_merge,
                allow_squash_merge=allow_squash_merge,
                archived=github_repo.archived,
                created_at=github_repo.created_at.strftime("%m-%d-%Y %H:%M:%S") if github_repo.created_at else "",
                default_branch=github_repo.default_branch,
                delete_branch_on_merge=delete_branch_on_merge,
                description=github_repo.description,
                fork=github_repo.fork,
                forks_count=github_repo.forks_count,
                full_name=github_repo.full_name,
                has_downloads=github_repo.has_downloads,
                has_issues=github_repo.has_issues,
                has_pages=github_repo.has_pages,
                has_projects=github_repo.has_projects,
                has_wiki=github_repo.has_wiki,
                homepage=github_repo.homepage,
                language=github_repo.language,
                last_modified=github_repo.last_modified,
                name=github_repo.name,
                pushed_at=github_repo.pushed_at.strftime("%m-%d-%Y %H:%M:%S") if github_repo.pushed_at else "",
                size=github_repo.size,
                stargazers_count=github_repo.stargazers_count,
                subscribers_count=subscribers_count,
                unkown_codeowners=[],
                no_codeowners=False,
                updated_at=github_repo.updated_at.strftime("%m-%d-%Y %H:%M:%S") if github_repo.updated_at else "",
                watchers_count=github_repo.watchers_count,
            ).save()

        if investigate and not gid in INV_REPOS and \
                (not github_repo.archived or self.github_get_archived):

            INV_REPOS.add(gid)

            self.logger.info("Checking repo %s", github_repo.full_name)
            github_secrets = self._get_repo_secrets(github_repo.full_name)
            if github_secrets and github_secrets.get("secrets"):
                for s in github_secrets.get("secrets"):
                    secret_obj: GithubSecret = GithubSecret(name=s["name"]).save()
                    repo_obj.secrets.update(secret_obj, reason="Declared")

            repo_obj = self.save_workflows(github_repo, repo_obj)

            if github_repo.owner:
                owner_obj: GithubUser = self.save_user(github_repo.owner, investigate=False)
                repo_obj.owner.update(owner_obj)

            if github_repo.source:
                repo_obj_src: GithubRepo = self.save_repo(github_repo.source, investigate=False)
                repo_obj.source.update(repo_obj_src)

            if github_repo.organization:
                org_obj: GithubOrganization = self.save_org(github_repo.organization, investigate=False)
                repo_obj.orgnaizations.update(org_obj)

            if self.github_get_redundant_info:
                for team in self.call_github(github_repo.get_teams, ret_val=[]):
                    team_obj: GithubTeam = self.save_team(team, investigate=False)
                    perms = team.get_repo_permission(github_repo.full_name)
                    repo_obj.teams.update(team_obj,
                                          admin=perms.admin,
                                          maintain=perms.maintain,
                                          pull=perms.pull,
                                          push=perms.push,
                                          triage=perms.triage)

            for user in self.call_github(github_repo.get_collaborators, ret_val=[]):
                user_obj: GithubUser = self.save_user(user, investigate=False)
                perms = user.permissions
                repo_obj.users.update(user_obj,
                                      admin=perms.admin,
                                      maintain=perms.maintain,
                                      pull=perms.pull,
                                      push=perms.push,
                                      triage=perms.triage)

            for shrunner in self.call_github(github_repo.get_self_hosted_runners, ret_val=[]):
                shrunner_obj: GithubSelfHostedRunner = GithubSelfHostedRunner(
                    id=shrunner["id"],
                    name=shrunner["name"],
                    os=shrunner["os"],
                    status=shrunner["status"]).save()

                repo_obj.self_hosted_runners.update(shrunner_obj)

            codeowners = self.get_codeowners(github_repo)
            if not codeowners:
                repo_obj.no_codeowners = True

            for co in codeowners:
                try:
                    identity_name = co
                    identity_name = identity_name.split("/")[1] if "/" in co else identity_name
                    identity_name = identity_name[1:] if identity_name.startswith("@") else identity_name
                    github_team = self.call_github(self.org.get_team_by_slug, ret_val=None, slug=identity_name)

                    if github_team:
                        team_obj: GithubTeam = self.save_team(github_team, investigate=False)
                        repo_obj.teams_cos.update(team_obj)

                    else:
                        github_user = self.call_github(self.cred.get_user, ret_val=None, login=identity_name)
                        if github_user:
                            user_obj: GithubUser = self.save_user(github_user, investigate=False)
                            repo_obj.users_cos.update(user_obj)

                        else:
                            self.logger.warning(f"Codeowner not found {co} as team or user in {github_repo.full_name}.")
                            repo_obj.unkown_codeowners.append(co)

                except Exception as e:
                    self.logger.warning(f"Codeowner not found {co} in {github_repo.full_name}. Error: {e}")
                    repo_obj.unkown_codeowners.append(co)

            leaks = self.get_leaks(github_repo)
            for leak in leaks:
                gh_leak: GithubLeak = GithubLeak(name=leak["name"], description=leak["description"]).save()
                repo_obj.leaks.update(gh_leak, commit=leak["commit"], file=leak["file"], match=leak["match"])

            webhooks = self._get_webhooks(github_repo)
            for webhook in webhooks:
                url = webhook["url"]
                wh_obj = GithubWebhook(
                    name=url,
                    insecure_ssl=webhook["insecure_ssl"],
                ).save()

                uparsed = urlparse(url)
                hostname = uparsed.hostname
                if validators.domain(hostname) is True or hostname == "localhost":
                    dom_obj = PublicDomain(name=hostname).save()
                    dom_obj.gh_webhooks.update(wh_obj)
                    dom_obj.save()

                else:
                    ip_obj = PublicIP(name=hostname).save()
                    ip_obj.gh_webhooks.update(wh_obj)
                    ip_obj.save()

                repo_obj.webhooks.update(wh_obj)

            self.get_circleci(github_repo, repo_obj)

            repo_obj.save()
            self.get_branches(github_repo, repo_obj)

        REPOS[gid] = repo_obj
        return REPOS[gid]

    def _get_repo_secrets(self, repo_full_name):
        """
        Get secrets of a repo
        """

        status, headers, data = self.cred._Github__requester.requestJson(
            "GET", f"{self.cred._Github__requester._Requester__base_url}/repos/{repo_full_name}/actions/secrets"
        )

        data = json.loads(data)
        if data.get("message"):
        if data.get("message") and "API rate limit exceeded" in data.get("message"):
            self.logger.error(f"Sleeping 15 mins for rate limit and trying again.")
            time.sleep(15*60)
            return self._get_repo_secrets(repo_full_name)
        return data

    def _get_org_secrets(self, org_name):
        """
        Get secrets of an org
        """

        status, headers, data = self.cred._Github__requester.requestJson(
            "GET", f"{self.cred._Github__requester._Requester__base_url}/orgs/{org_name}/actions/secrets"
        )

        data = json.loads(data)
        if data.get("message"):
            if "API rate limit exceeded" in data.get("message"):
                self.logger.error(f"time.sleeping 5mins for rate limit and trying again.")
                time.sleep(5 * 60)
                return self._get_org_secrets(org_name)

        return data

    def _get_webhooks(self, github_repo):
        """Get all the WebHooks of the repo"""

        webhooks = list()
        hooks = self.call_github(github_repo.get_hooks, ret_val=[])
        for hook in hooks:
            hook_obj = self.call_github(github_repo.get_hook, ret_val=[], id=hook.id)

            if hook_obj and hasattr(hook_obj, "config"):
                webhooks.append(hook_obj.config)

            else:
                self.logger.error(f"No config found in repo {github_repo.full_name} with id {hook.id}")

        return webhooks

    @GithubDiscClient.call_github_decorator
    def save_branch(self, github_branch: Branch.Branch, repo_name: str) -> GithubBranch:
        """
        Save the given branch.
        Get also protections of the branch.
        """

        # Branches are supposed to be saved only once per branch. In any other case we need to cimplement the cache

        full_name = repo_name + "/" + github_branch.name
        enforce_admins = False
        required_signatures = False
        required_status_checks = False
        require_code_owner_reviews = False
        required_approving_review_count = 0
        dismiss_stale_reviews = False

        branch_obj: GithubBranch = GithubBranch(
            last_modified=github_branch.last_modified,
            name=github_branch.name,
            protected=github_branch.protected,
            full_name=full_name,

            known_protections=False,
            enforce_admins=enforce_admins,
            required_signatures=required_signatures,
            required_status_checks=required_status_checks,
            require_code_owner_reviews=require_code_owner_reviews,
            required_approving_review_count=required_approving_review_count,
            dismiss_stale_reviews=dismiss_stale_reviews
        ).save()

        # Get branch protection
        if github_branch.protected:
            protections = self.call_github(github_branch.get_protection, ret_val={})
            if protections:
                allow_force_pushes = protections.raw_data.get("allow_force_pushes", {}).get("enabled", False)
                allow_deletions = protections.raw_data.get("allow_deletions", {}).get("enabled", False)
                enforce_admins = protections.enforce_admins
                required_signatures = protections.raw_data["required_signatures"].get("enabled",
                                                                                      False) if protections.raw_data.get(
                    "required_signatures") else False
                required_status_checks = protections.required_status_checks.strict if protections.required_status_checks else None

                prr = protections.required_pull_request_reviews
                if prr:
                    require_code_owner_reviews = prr.require_code_owner_reviews
                    required_approving_review_count = prr.required_approving_review_count
                    dismiss_stale_reviews = prr.dismiss_stale_reviews

                # TODO: We are only getting if everyone is allowed to force push. Get if specific people/groups are allowed
                branch_obj.allow_force_pushes = allow_force_pushes
                branch_obj.allow_deletions = allow_deletions
                branch_obj.enforce_admins = enforce_admins
                branch_obj.required_signatures = required_signatures
                branch_obj.required_status_checks = required_status_checks
                branch_obj.require_code_owner_reviews = require_code_owner_reviews
                branch_obj.required_approving_review_count = required_approving_review_count
                branch_obj.dismiss_stale_reviews = dismiss_stale_reviews
                branch_obj.known_protections = True
                branch_obj.save()

                if prr and prr.dismissal_users:
                    for user in prr.dismissal_users:
                        user_obj: GithubUser = self.save_user(user, investigate=False)
                        branch_obj.users_dimiss.update(user_obj)

                if prr and prr.dismissal_teams:
                    for team in prr.dismissal_teams:
                        team_obj: GithubTeam = self.save_team(team, investigate=False)
                        branch_obj.teams_dimisss.update(team_obj)

            for user in self.call_github(github_branch.get_user_push_restrictions, ret_val=[]):
                user_obj: GithubUser = self.save_user(user, investigate=False)
                branch_obj.users_push.update(user_obj)

            for team in self.call_github(github_branch.get_team_push_restrictions, ret_val=[]):
                team_obj: GithubTeam = self.save_team(team, investigate=False)
                branch_obj.teams_push.update(branch_obj)

            branch_obj.save()

        return branch_obj

    def get_codeowners(self, github_repo) -> List[str]:
        """
        Get entities of the codeowners file of a repo
        """

        try:
            github_content = self.call_github(github_repo.get_dir_contents, ret_val=[], path="/CODEOWNERS")
        except:
            pass

        if not github_content:
            try:
                github_content = self.call_github(github_repo.get_dir_contents, ret_val=[], path="/docs/CODEOWNERS")
            except:
                pass

        if not github_content:
            try:
                github_content = self.call_github(github_repo.get_dir_contents, ret_val=[], path="/.github/CODEOWNERS")
            except:
                pass

        if github_content:
            content = github_content.decoded_content.decode("utf-8")

            entities = set()
            for line in content.splitlines():
                # If not "@" in line then the line is probably to remove access from previous given access and there is no entity specified
                if line and " " in line and "@" in line:
                    for entity in line.split(" ")[
                                  1:]:  # Remove first element as it's the path and in this moment we don't care about that
                        if entity.strip():
                            entities.add(entity.strip())

            return list(entities)

        return []

    def get_circleci(self, github_repo, repo_obj: GithubRepo) -> None:
        """
        Get vars of the circleci file of a repo
        """

        try:
            github_content = self.call_github(github_repo.get_dir_contents, ret_val=[], path="/.circleci/config.yml")
        except:
            return

        if github_content:
            corg_obj = CircleCIOrganization(name="github/" + github_repo.full_name.split("/")[0]).save()
            ghorg_obj = GithubOrganization(name=github_repo.full_name.split("/")[0]).save()
            corg_obj.gh_orgs.update(ghorg_obj)
            corg_obj.save()

            cproj_obj = CircleCIProject(name="gh/" + github_repo.full_name).save()
            cproj_obj.gh_repos.update(repo_obj)
            cproj_obj.orgs.update(corg_obj)
            cproj_obj.save()

            content = github_content.decoded_content.decode("utf-8")

            disc_vars_in_txt(cproj_obj, content)

    def save_workflows(self, github_repo, repo_obj: GithubRepo) -> Tuple[str, List[str]]:
        """
        Get the secrets from github actions workflows
        """

        try:
            github_contents = self.call_github(github_repo.get_contents, ret_val=[], path=".github/workflows")
        except:
            return repo_obj

        # From https://cloud.hacktricks.xyz/pentesting-ci-cd/github-security#understanding-the-risk-of-script-injections
        potential_injections_regexes = [
            r"github\.event\.comment\.body",
            r"github\.event\.issue\.body",
            r"github\.event\.issue\.title",
            r"github\.head_ref",
            r"github\.pull_request\.",
            r"github\..*\.authors\.name",
            r"github\..*\.authors\.email",
        ]

        if github_contents:
            for gh_content in github_contents:
                potential_injections = set()
                secrets = set()
                github_envs = set()
                self_hosted_runner = False
                has_pull_request_target = False
                env_vars = set()
                in_env_vars = False

                content = gh_content.decoded_content.decode("utf-8")
                name = gh_content.path
                full_name = github_repo.full_name + "/" + name

                # Analyze each action workflow
                for line in content.splitlines():
                    if line and "secrets." in line:
                        secret = line.split("secrets.")[1]
                        secret = secret.split('}}')[0].strip()
                        secrets.add(secret)

                    # Check if github environment for secrets is used
                    if line and "environment:" in line:
                        env_name = line.split("environment:")[1].strip()
                        if env_name:
                            github_envs.add(env_name)

                    # Check if pull_request_target supported
                    if line and "pull_request_target" in line:
                        has_pull_request_target = True

                    # Get env vars from the workflow supposing that they have more trailing spaces than "env:"
                    if line and in_env_vars:
                        if len(line) - len(line.lstrip(' ')) <= in_env_vars:
                            in_env_vars = False
                        else:
                            env_vars.add(line.strip())

                    if line and "env:" in line:
                        in_env_vars = len(line) - len(line.lstrip(' '))

                    # Check self hosts runners
                    if line and "self-hosted" in line and "runs-on" in line and line.index("self-hosted") > line.index(
                            "runs-on"):
                        self_hosted_runner = True

                    # Check potential command injections
                    for regex in potential_injections_regexes:
                        if re.search(regex, line):
                            potential_injections.add(line)

                # Generate the action object
                action_obj = GithubAction(
                    name=name,
                    full_name=full_name,
                    injection_points=list(potential_injections),
                    env_vars=list(env_vars),
                    has_pull_request_target=has_pull_request_target
                ).save()
                repo_obj.actions.update(action_obj)

                # Relate each enrionment with the action and the repo
                for g_env in github_envs:
                    env_obj: GithubEnvironment = GithubEnvironment(name=g_env).save()
                    repo_obj.environments.update(env_obj)
                    action_obj.environments.update(env_obj)

                # Relate each secret with the action, the repo, and the potential environ
                for s in secrets:
                    secret_obj: GithubSecret = GithubSecret(name=s).save()
                    repo_obj.secrets.update(secret_obj, reason="Used")
                    action_obj.secrets.update(secret_obj)
                    if github_envs:
                        env_obj.secrets.update(secret_obj)

                if self_hosted_runner:
                    shrunner_obj: GithubSelfHostedRunner = GithubSelfHostedRunner(
                        id="Generic",
                        name="Generic",
                        os="",
                        status="Active").save()

                    repo_obj.self_hosted_runners.update(shrunner_obj)
                    action_obj.self_hosted_runners.update(shrunner_obj)

        return repo_obj

    def get_leaks(self, github_repo) -> dict:
        """
        Get gitleaks from a repo
        """

        leaks = []
        if self.github_no_leaks or not self.gitleaks_installed:
            return []

        subprocess.call(
            ["git", "clone", f'https://{self.str_cred}@github.com/{github_repo.full_name}', "/tmp/purplepanda_github"],
            stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
        # Max 5mins, if not finish stop it and continue
        subprocess.call(
            ["timeout", str(5 * 60), "gitleaks", "detect", "-s", "/tmp/purplepanda_github", "--report-format", "json",
             "--report-path", "/tmp/gitleaks.json"], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
        subprocess.call(["rm", "-rf", "/tmp/purplepanda_github"], stdout=open(os.devnull, 'wb'),
                        stderr=open(os.devnull, 'wb'))

        results = []
        try:
            with open("/tmp/gitleaks.json", "r") as f:
                results = json.load(f)

            subprocess.call(["rm", "-rf", "/tmp/gitleaks.json"], stdout=open(os.devnull, 'wb'),
                            stderr=open(os.devnull, 'wb'))

            already_known = set()
            for result in results:
                # Save each secret only 1 time (only 1 relation would be created anyway)
                if not result["Secret"] in already_known:
                    already_known.add(result["Secret"])
                    leaks.append({
                        "name": result["Secret"],
                        "match": result["Match"],
                        "description": result["Description"],
                        "commit": result["Commit"],
                        "file": result["File"],
                    })

        except FileNotFoundError:
            pass

        return leaks

    @GithubDiscClient.call_github_decorator
    def save_org(self, github_org: Organization.Organization, investigate=True) -> GithubOrganization:
        """
        Save the given branch.
        Get also secrets of the org.
        Get also members and teams of the org. These operations are threaded to improve the speed
        """

        global ORGS

        gid = github_org.id
        if gid in ORGS:
            org_obj = ORGS[gid]

        else:
            org_obj: GithubOrganization = GithubOrganization(
                id=github_org.id,
                name=github_org.login,
                avatar_url=github_org.avatar_url,
                billing_email=github_org.billing_email,
                blog=github_org.blog,
                collaborators=github_org.collaborators,
                company=github_org.company,
                created_at=github_org.created_at.strftime("%m-%d-%Y %H:%M:%S") if github_org.created_at else "",
                description=github_org.description,
                disk_usage=github_org.disk_usage,
                email=github_org.email,
                followers=github_org.followers,
                following=github_org.following,
                gravatar_id=github_org.gravatar_id,
                has_organization_projects=github_org.has_organization_projects,
                has_repository_projects=github_org.has_repository_projects,
                last_modified=github_org.last_modified,
                location=github_org.location,
                members_can_create_repositories=github_org.members_can_create_repositories,
                owned_private_repos=github_org.owned_private_repos,
                plan=github_org.plan.name if github_org.plan else "",
                private_gists=github_org.private_gists,
                public_gists=github_org.public_gists,
                public_repos=github_org.public_repos,
                private_repos=github_org.total_private_repos,

                members_default_repository_permission=github_org.default_repository_permission,
                members_can_create_public_repositories=github_org.__dict__["_rawData"].get(
                    "members_can_create_public_repositories"),
                members_can_create_private_repositories=github_org.__dict__["_rawData"].get(
                    "members_can_create_private_repositories"),
                members_can_create_internal_repositories=github_org.__dict__["_rawData"].get(
                    "members_can_create_internal_repositories"),
                members_can_create_pages=github_org.__dict__["_rawData"].get("members_can_create_pages"),
                members_can_create_public_pages=github_org.__dict__["_rawData"].get("members_can_create_public_pages"),
                members_can_create_private_pages=github_org.__dict__["_rawData"].get(
                    "members_can_create_private_pages"),
                members_can_fork_private_repositories=github_org.__dict__["_rawData"].get(
                    "members_can_fork_private_repositories"),
                two_factor_requirement_enabled=github_org.two_factor_requirement_enabled,
            ).save()
            ORGS[gid] = org_obj

        if investigate and not gid in INV_ORGS:
            INV_ORGS.add(gid)

            github_secrets = self._get_org_secrets(github_org.login)
            if github_secrets and github_secrets.get("secrets"):
                for s in github_secrets.get("secrets"):
                    secret_obj: GithubSecret = GithubSecret(name=s["name"]).save()
                    org_obj.secrets.update(secret_obj, reason="Declared")
                org_obj.save()

            self.get_members(github_org, org_obj)
            self.get_teams(github_org, org_obj)
            self.get_repos(github_org, org_obj)

            for user in self.call_github(github_org.get_outside_collaborators, ret_val=[]):
                user_obj: GithubUser = self.save_user(user)
                org_obj.users.update(user_obj, membership="Outside Collaborator")

            for user in self.call_github(github_org.get_public_members, ret_val=[]):
                user_obj: GithubUser = self.save_user(user)
                org_obj.users.update(user_obj, is_public=True)

            org_obj.save()

        ORGS[gid] = org_obj
        return ORGS[gid]
