import logging
from intel.circleci.discovery.circleci_disc_client import CircleCIDisc
from intel.circleci.models import CircleCIOrganization
from intel.github.models import GithubOrganization
from intel.bitbucket.models import BitbucketOrganization

class DiscOrgs(CircleCIDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the orgs
        """

        self._disc_loop(self.orgs, self._disc_orgs, __name__.split(".")[-1])

    
    def _disc_orgs(self, org, **kwargs):
        """Discover each org"""

        ciorg_obj = CircleCIOrganization(name=org).save()
        
        if org.lower().startswith("bitbucket"):
            bkorg_obj = BitbucketOrganization(name=org.split("/")[-1]).save()
            ciorg_obj.bk_orgs.update(bkorg_obj)
            ciorg_obj.save()

        elif org.lower().startswith("gh/") or org.lower().startswith("github/"):
            ghorg_obj = GithubOrganization(name=org.split("/")[-1]).save()
            ciorg_obj.gh_orgs.update(ghorg_obj)
            ciorg_obj.save()
        
        else:
            self.logger.error(f"I don't know if {org} is github or bitbucket, please create an issue in purplepana's github with this info")
        
        
