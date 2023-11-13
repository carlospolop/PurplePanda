import logging
from intel.circleci.discovery.circleci_disc_client import CircleCIDisc
from intel.github.models import GithubOrganization, GithubRepo
from intel.bitbucket.models import BitbucketOrganization, BitbucketRepo


class DiscProjects(CircleCIDisc):
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Try to discover all the projects of each organization
        """

        user_projects = [
            {
                "vcs_type": org_name.split("/")[0],
                "username": org_name,
                "reponame": project_name,
            }
            for project_name in self.projects
        ]
        # Check in the database if any github org with the same name org name
        gh_projects = []
        for o in self.orgs:
            org_name = o.split("/")[-1]
            if gh_org := GithubOrganization.get_by_name(org_name):
                part_of_org = gh_org.get_by_relation("PART_OF")
                gh_projects.extend(
                    {
                        "vcs_type": "github",
                        "username": org_name,
                        "reponame": repo_obj.name,
                    }
                    for repo_obj in part_of_org
                    if type(repo_obj) == GithubRepo
                )
        self._disc_loop(gh_projects, self._disc_projects, __name__.split(".")[-1] + ".github", paginate=True)

        # Check in the database if any bitbucket org with the same name org name
        bk_projects = []
        for o in self.orgs:
            org_name = o.split("/")[-1]
            if bk_org := BitbucketOrganization.get_by_name(org_name):
                part_of_org = bk_org.get_all_with_relation("PART_OF")
                bk_projects.extend(
                    {
                        "vcs_type": "bitbucket",
                        "username": org_name,
                        "reponame": repo_obj.name,
                    }
                    for repo_obj in part_of_org
                    if type(repo_obj) == BitbucketRepo
                )
        self._disc_loop(bk_projects, self._disc_projects, __name__.split(".")[-1] + ".bitbucket", paginate=True)

    def _disc_projects(self, project, **kwargs):
        """Discover each project"""

        if project["vcs_type"].lower() == "github":
            org = "gh/" + project["username"]
            project_slug = f"{org}/" + project["reponame"]

        elif project["vcs_type"].lower() == "bitbucket":
            org = "bk/" + project["username"]
            project_slug = f"{org}/" + project["reponame"]

        else:
            self.logger.error(
                f"I don't know if {project['vcs_type']} is github or bitbucket, please create an issue in purplepana's github with this info")

        self._disc_project(project_slug, org)
