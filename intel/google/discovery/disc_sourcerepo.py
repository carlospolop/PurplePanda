import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_source_repos import GcpSourceRepo
from intel.google.models.gcp_pubsub import GcpPubSubTopic
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.github.models import GithubRepo
from intel.bitbucket.models import BitbucketRepo

class DiscSourceRepos(GcpDisc):
    resource = 'sourcerepo'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the repos from each project discovered.

        This module will create the repos and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_sourcerepos, __name__.split(".")[-1])


    def _disc_sourcerepos(self, p_obj:GcpProject):
        """Discover all the sourcerepos of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().repos()#.list(name=project_name)
        repos: List[str] = self.execute_http_req(http_prep, "repos", list_kwargs={"name": project_name})
            
        for repo in repos:
            mirror_url = repo.get("mirrorConfig", {}).get("url", "")
            repo_obj = GcpSourceRepo(
                name = repo["name"],
                url = repo.get("url", ""),
                mirrorUrl = mirror_url,
                mirrorWebhookId= repo.get("mirrorConfig", {}).get("webhookId", ""),
                mirrorDeployKeyId = repo.get("mirrorConfig", {}).get("deployKeyId", ""),
            ).save()
            repo_obj.projects.update(p_obj)

            if mirror_url:
                if GithubRepo.is_github_repo_url(mirror_url):
                    gh_repo_obj = GithubRepo(full_name=GithubRepo.get_full_name_from_url(mirror_url)).save()
                    repo_obj.github_repos.update(gh_repo_obj)
                
                if BitbucketRepo.is_bitbucket_repo_url(mirror_url):
                    gh_repo_obj = BitbucketRepo(full_name=BitbucketRepo.get_full_name_from_url(mirror_url)).save()
                    repo_obj.bitbucket_repos.update(gh_repo_obj)

            pubsubinfo = repo.get("pubsubConfig", {})
            if pubsubinfo.get("topic"):
                topic_obj: GcpPubSubTopic = GcpPubSubTopic(name=pubsubinfo.get("topic")).save()
                repo_obj.pubsubTopics.update(topic_obj)
            
            repo_obj.save()

            self.get_iam_policy(repo_obj, self.service.projects().repos(), repo_obj.name)

            # It's just a SA for the pubsub, you cannot abuse it: https://cloud.google.com/source-repositories/docs/reference/rpc/google.devtools.sourcerepo.v1#pubsubconfig
            #sa_email = pubsubinfo.get("serviceAccountEmail", f"{p_obj.projectNumber}-compute@developer.gserviceaccount.com")
            #repo_obj.relate_sa(sa_email, [])
