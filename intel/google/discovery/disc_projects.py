import logging
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_folder import GcpFolder
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.gcp_service import GcpService
from core.db.customogm import graph


class DiscProjects(GcpDisc):
    resource = 'cloudresourcemanager'
    version = 'v1'
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover each project the account has access to.
        
        This module will create the projects and relate them with the parent folder/organization.
        It will also get the IAM policies of the project, relate the user/sa/groups with the project
        and also create the roles and relate each role with the permissions it has.
        """

        prep_http = self.service.projects()  # .list()
        projects: List[str] = self.execute_http_req(prep_http, "projects")
        self._disc_loop(projects, self._disc_projects, __name__.split(".")[-1])
        self._extend_basic_roles_to_projects()  # Extend the basic roles to the projects

    def _disc_projects(self, p):
        """Discover each project"""

        if p.get("lifecycleState", "").upper() in ["DELETE_REQUESTED"]:
            return

        p_obj: GcpProject = GcpProject(
            name=p["projectId"],
            projectNumber=p["projectNumber"],
            displayName=p.get("name", ""),
            lifecycleState=p.get("lifecycleState", "")
        ).save()

        if parent := p.get("parent", {}):
            if parent["type"] == "folder":
                f: GcpFolder = GcpFolder(name=f"folders/{parent['id']}").save()
                f.projects.update(p_obj)
                f.save()

            elif parent["type"] == "organization":
                name = f"organizations/{parent['id']}"
                o: GcpOrganization = GcpOrganization.get_by_name(name=name)
                o.projects.update(p_obj)
                o.save()

            else:
                self.logger.error(f"Project {p['name']} with unexpected parent type {p['parent']}")

        self._list_enabled_svcs(p_obj)

        self.get_iam_policy(p_obj, self.service.projects(), p_obj.name.split("/")[1])

    def _list_enabled_svcs(self, proj_obj):
        svcs_service = self.get_other_svc("serviceusage", "v1")

        http_prep = svcs_service.services()  # .list(parent=proj_obj.name, filter="state:ENABLED")
        gcp_services: list = self.execute_http_req(http_prep, "services", disable_warn=True,
                                                   list_kwargs={"parent": proj_obj.name, "filter": "state:ENABLED"})

        for svc in gcp_services:
            if svc["state"].upper() == "ENABLED":
                svc_obj: GcpService = GcpService(
                    name=svc["config"]["name"],
                    title=svc["config"]["title"]
                ).save()
                svc_obj.projects.update(proj_obj)
                svc_obj.save()

    def _extend_basic_roles_to_projects(self):
        """
        Extend org and folders owners, editors and viewers to projects
        """

        def _extend_role(role, parent_type):
            """Given the role and parent type extend the role to the project level"""

            query = f""" MATCH(ppal:GcpPrincipal)-[r:HAS_ROLE]->(o:{parent_type}) where "roles/{role}" in r.roles
                        MATCH(p:GcpProject)-[:PART_OF*..]->(o)
                        MERGE (ppal)-[rl:HAS_ROLE]->(p)
                        ON CREATE SET rl.roles = ["roles/{role}"]
                        ON MATCH SET 
                            rl.roles = CASE WHEN "roles/{role}" IN rl.roles
                                THEN rl.roles
                                ELSE rl.roles + "roles/{role}"
                                END"""

            graph.evaluate(query)

        _extend_role("owner", "GcpOrganization")
        _extend_role("editor", "GcpOrganization")
        _extend_role("viewer", "GcpOrganization")
        _extend_role("owner", "GcpFolder")
        _extend_role("editor", "GcpFolder")
        _extend_role("viewer", "GcpFolder")
