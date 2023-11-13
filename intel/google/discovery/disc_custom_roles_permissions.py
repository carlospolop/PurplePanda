import logging
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.gcp_project import GcpProject


class DiscCustomRolesPermissions(GcpDisc):
    resource = "iam"
    version = "v1"
    logger = logging.getLogger(__name__)

    def _disc(self):
        """
        Discover all the custom roles in every project and organization.
        At this point all the used ones will have been already discovered
        so this will be useful to discover unused ones and save them in the DB

        This module will relate orgs/projects with roles and roles with permissions
        """

        organisations: List[GcpOrganization] = GcpOrganization.get_all()
        projects: List[GcpProject] = GcpProject.get_all()
        loop_list = organisations + projects
        self._disc_loop(loop_list, self._disc_roles, __name__.split(".")[-1])

    def _disc_roles(self, o_obj):
        # You could use null ([""]) to get default roles and their permissions
        # But you should have already discover the defalt roles the environment is using
        # and if you discover all of them, the graph size increase in 4000 nodes+relations
        http_prep = self.service.roles()  # .list(parent=o_obj.name)
        roles = self.execute_http_req(http_prep, "roles", disable_warn=True, list_kwargs={"parent": o_obj.name})

        for role in roles:
            self._get_role_perms(role["name"], o_obj, create_parent_rel=True)
