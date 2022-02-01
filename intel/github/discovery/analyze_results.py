import logging
import time
from typing import List, Union
from .github_disc import GithubDisc

from intel.github.models.github_model import GithubBranch, GithubOrganization, GithubRepo, GithubSecret, GithubUser, GithubTeam

class AnalyzeResults(GithubDisc):
    logger = logging.getLogger(__name__)
    known_ppals_with_role = {}
    
    def discover(self) -> None:
        start = time.time()
        self.logger.info(f"Running analysis module: {self.__class__.__name__}")
        self._disc()
        self.logger.info(f"Analysis module {self.__class__.__name__} run in {time.time() - start}s")
    

    def _disc(self) -> None:
        """
        Process the found information to be able to find privilege escalation paths easily in the database.
        """

        # Set as repos admin all the org admin
        self._disc_loop(GithubOrganization.get_all(), self._set_repo_admins, __name__.split(".")[-1]+"._set_repo_admins")

        # Roles write, maintain and admin --> steal repo secrets and org secrets
        self._disc_loop(GithubOrganization.get_all(), self._steal_repo_secrets, __name__.split(".")[-1]+"._steal_repo_secrets")

        # orgs.members_can_create_repositories --> Any user can steal org secrets
        self._disc_loop(GithubOrganization.get_all(), self._steal_org_secrets_with_generic_write_permission, __name__.split(".")[-1]+"._steal_org_secrets_with_generic_write_permission")

        # Find users that can write in repos with self-hosted runners
        self._disc_loop(GithubOrganization.get_all(), self._run_selfhosted_runner, __name__.split(".")[-1]+"._run_selfhosted_runner")

        # Find users that can write to the default branch
        self._disc_loop(GithubOrganization.get_all(), self._write_to_default_branch, __name__.split(".")[-1]+"._write_to_default_branch")


    def _set_repo_admins(self, org_obj:GithubOrganization):
        """
        Find all the organization admins and make them admins in all the organization repos
        """

        # Get all the admin users of organization
        admin_ppals: List[GithubUser] = []
        for user_obj, role in org_obj.users._related_objects:
            if role["membership"] == "admin":
                admin_ppals.append(user_obj)
        
        org_partof = org_obj.get_by_relation("PART_OF")
        for user_obj in admin_ppals:
            for repo_obj in org_partof:
                if type(repo_obj) == GithubRepo:
                    user_obj.perms_repos.update(repo_obj, admin=True,
                                            maintain=True,
                                            pull=True,
                                            push=True,
                                            triage=True)
            user_obj.save()

    
    def _steal_repo_secrets(self, org_obj:GithubOrganization):
        """
        If org.members_can_create_repositories --> Any user can steal org secrets
        """

        part_of_org = org_obj.get_by_relation("PART_OF")
        for repo_obj in part_of_org:
            if type(repo_obj) == GithubRepo:
                for secret_obj, _ in repo_obj.secrets._related_objects:
                    for user_obj, roles in repo_obj.users._related_objects:
                        if roles["admin"] or roles["maintain"] or roles["push"]:
                            secret_obj.users.update(user_obj, reason=f"Can write in repo {repo_obj.full_name}")
                    
                    for team_obj, roles in repo_obj.teams._related_objects:
                        if roles["admin"] or roles["maintain"] or roles["push"]:
                            secret_obj.teams.update(team_obj, reason=f"Can write in repo {repo_obj.full_name}")

                    secret_obj.save()
    
    def _steal_org_secrets_with_generic_write_permission(self, org_obj:GithubOrganization):
        """
        Roles write, maintain and admin --> steal repo secrets and org secrets
        """

        if org_obj.members_can_create_repositories:
            part_of_org = org_obj.get_by_relation("PART_OF")
            for secret_obj in part_of_org:
                if type(secret_obj) == GithubSecret:
                    for user_obj in part_of_org:
                        if type(user_obj) == GithubUser:
                            secret_obj.users.update(user_obj, reason="Can create new repos")
            
                secret_obj.save()

    def _run_selfhosted_runner(self, org_obj:GithubOrganization):
        """
        If the repo has a self hosted runner and you have write permissions, you can run it
        """

        for repo_obj in org_obj.get_by_relation("PART_OF"):
            if type(repo_obj) == GithubRepo:
                for selfhosted_runner, _ in repo_obj.self_hosted_runners._related_objects:
                    for user_obj, roles in repo_obj.users._related_objects:
                        if roles["admin"] or roles["maintain"] or roles["push"]:
                            selfhosted_runner.users.update(user_obj, reason=f"Can write in repo {repo_obj.full_name}")
                    
                    for team_obj, roles in repo_obj.teams._related_objects:
                        if roles["admin"] or roles["maintain"] or roles["push"]:
                            selfhosted_runner.teams.update(team_obj, reason=f"Can write in repo {repo_obj.full_name}")
                    
                    selfhosted_runner.save()


    def _write_to_default_branch(self, org_obj:GithubOrganization):
        """
        Bypass branch protections
            - If no branch protection
            - If allow_force_pushes allows everyone or at least your user
            - If admin and not included administrators
            - If admin, remove branch protections, merge code, reenable branch protections
            - If write equivalent and 1 review and no codeowners
            - If write equivalent and 1 review and codeowners but user in code owners
            - If write equivalent and 1 review and codeowners but missconfgured codeowners
            - If write equivalent and "Dismiss approvals when new commits are pushed" is not set (this requiere other people approving a legit PR created by a different user)
        """

        for repo_obj in org_obj.get_by_relation("PART_OF"):
            if type(repo_obj) == GithubRepo:
                write_ppals = []
                admin_ppals = []
                for ppal_obj, roles in repo_obj.users._related_objects + repo_obj.teams._related_objects:
                    if roles["admin"] or roles["maintain"] or roles["push"]:
                        write_ppals.append(ppal_obj)
                    
                    if roles["admin"]:
                        admin_ppals.append(ppal_obj)
                
                default_branch_name = repo_obj.default_branch
                for branch_obj, _ in repo_obj.branches._related_objects: 
                    if branch_obj.name == default_branch_name:
                        #- If no branch protection
                        if not branch_obj.protected:
                            self._relate_to_merge(branch_obj, write_ppals, reason="Not protected")
                        
                        # - If allow_force_pushes allows everyone or at least your user
                        #TODO: We are only getting if everyone is allowed. Get if specific people/groups are allowed
                        elif branch_obj.allow_force_pushes:
                            self._relate_to_merge(branch_obj, write_ppals, reason="All can force pushes")
                        
                        else:
                            # Get codeowners with write permissions
                            writers_codeowners = []
                            already_writers_codeowners = set()
                            codeowners = []
                            if branch_obj.require_code_owner_reviews:
                                # Get users and users from teams codeowners
                                for codeowner in repo_obj.get_by_relation("CODE_OWNER"):
                                    if type(codeowner) is GithubUser:
                                        codeowners.append(codeowner)
                                    
                                    elif type(codeowner) is GithubTeam:
                                        for user_co, _ in codeowner.users._related_objects:
                                            if not type(user_co) is GithubUser:
                                                self.logger.error("Something that isn't a GithubUser is related to a GithubTeam")
                                            else:
                                                codeowners.append(user_co)
                                    
                                    else:
                                        self.logger.error("Something that isn't a GithubUser or GithubTeam is a codeowner")
                                
                                for codeowner in codeowners:
                                    for write_user in write_ppals:
                                        # Do not accept repetitions
                                        if write_user.__primaryvalue__ == codeowner.__primaryvalue__ and not codeowner.__primaryvalue__ in already_writers_codeowners:
                                            writers_codeowners.append(codeowner)
                                            already_writers_codeowners.add(codeowner.__primaryvalue__)
                                            break
                            
                            if str(branch_obj.required_approving_review_count) == "1":
                                # - If write equivalent and 1 review and codeowners but codeowners is missconfigured
                                if branch_obj.require_code_owner_reviews and (repo_obj.unkown_codeowners or repo_obj.no_codeowners):
                                    self._relate_to_merge(branch_obj, write_ppals, reason="Can use GitBot token to create the PR and approve it himself as codeowners are missconfigured")
                                
                                # - If write equivalent and 1 review and codeowners but user in code owners
                                if branch_obj.require_code_owner_reviews:
                                    self._relate_to_merge(branch_obj, writers_codeowners, reason="Can use GitBot token to create the PR and approve it himself (as codeowner)")
                                
                                # - If write equivalent and 1 review and no codeowners
                                else:
                                    self._relate_to_merge(branch_obj, write_ppals, reason="Use the GitBot token to create the PR and you approve it, or crete the PR yourself and make the GitBot approve it")

                            elif branch_obj.required_approving_review_count and branch_obj.required_approving_review_count > 1 and not branch_obj.dismiss_stale_reviews:
                                self._relate_to_merge(branch_obj, write_ppals, reason="Hijack a PR adding malicious code when it has 1 (or less) approval required")


                            # If admin and not included administrators
                            if not branch_obj.enforce_admins:
                                self._relate_to_merge(branch_obj, admin_ppals, reason="Admins not enforced")

                            # - If admin, remove branch protections, merge code, reenable branch protections
                            else:
                                self._relate_to_merge(branch_obj, admin_ppals, reason="Admins can remove the protection, merge, and set it again")
                                

    def _relate_to_merge(self, branch_obj: GithubBranch, ppal_objs: List[Union[GithubUser, GithubTeam]], **kwargs):
        """
        Relate all the users to the branch as "CAN_MERGE"
        """

        if ppal_objs:
            for ppal_obj in ppal_objs:
                if type(ppal_obj) is GithubUser:
                    branch_obj.users_merge.update(ppal_obj, **kwargs)
                
                elif type(ppal_obj) is GithubTeam:
                    branch_obj.teams_merge.update(ppal_obj, **kwargs)
                
                else:
                    self.logger.warning(f"Something of type {type(ppal_obj)} arrived in _relate_to_merge. Primary value: {ppal_obj.__primarykey__}")
                    continue
            
            branch_obj.save()
