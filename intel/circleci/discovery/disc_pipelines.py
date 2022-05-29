import logging

from intel.circleci.discovery.circleci_disc_client import CircleCIDisc
from intel.circleci.models import CircleCIProject


class DiscPipelines(CircleCIDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover some pipelines of the followed projects
        """

        self._disc_loop(self.orgs, self._disc_pipelines, __name__.split(".")[-1])

    
    def _disc_pipelines(self, org, **kwargs):
        """Discover latest 20 pipelines of the followed projects"""
        
        pipelines = self.call_circleci_api(self.cred.get_pipelines, [], show_404=True, username=org.split("/")[-1], paginate=True, limit=20)

        if not pipelines:
            return
        
        for pipeline in pipelines:
            proj_obj = CircleCIProject(name=pipeline["project_slug"]).save()
            self._disc_vars_in_pipe(pipeline["id"], proj_obj)
