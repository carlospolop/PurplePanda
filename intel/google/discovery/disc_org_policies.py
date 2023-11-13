import logging
from typing import List, Union

from .gcp_disc_client import GcpDisc
from intel.google.models import GcpOrganization, GcpFolder, GcpProject, GcpOrgPolicy


class DiscOrgPolicies(GcpDisc):
    resource = 'cloudresourcemanager'
    version = 'v1'
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the Org policies accesible by the active account.

        This module will relate org policies with parent organization/folder/project.
        """

        orgs: List[GcpOrganization] = GcpOrganization.get_all()
        folders: List[GcpFolder] = GcpFolder.get_all()
        projects: List[GcpProject] = GcpProject.get_all()

        self._disc_loop(orgs, self._disc_org_policies, __name__.split(".")[-1] + ".orgs")
        self._disc_loop(folders, self._disc_folder_policies, __name__.split(".")[-1] + ".folders")
        self._disc_loop(projects, self._disc_project_policies, __name__.split(".")[-1] + ".projects")

    def _disc_org_policies(self, org_obj: GcpOrganization):
        """Discover each policy of the organization"""

        prep_http = self.service.organizations().listOrgPolicies(resource=org_obj.name)
        policies: List[str] = self.execute_http_req(prep_http, "policies")
        for policy in policies:
            self._save_policy(policy, org_obj)

    def _disc_folder_policies(self, folder_obj: GcpFolder):
        """Discover each policy of the folder"""

        prep_http = self.service.folders().listOrgPolicies(resource=folder_obj.name)
        policies: List[str] = self.execute_http_req(prep_http, "policies")
        for policy in policies:
            self._save_policy(policy, folder_obj)

    def _disc_project_policies(self, project_obj: GcpProject):
        """Discover each policy of the project"""

        prep_http = self.service.projects().listOrgPolicies(resource=project_obj.name)
        policies: List[str] = self.execute_http_req(prep_http, "policies")
        for policy in policies:
            self._save_policy(policy, project_obj)

    def _save_policy(self, policy, obj: Union[GcpOrganization, GcpFolder, GcpProject]):
        """Given a policy save it related to the affected object"""

        op_obj = GcpOrgPolicy(
            name=policy["constraint"],
            enforced=policy.get("booleanPolicy", {}).get("enforced", False),
            updateTime=policy["updateTime"],
            version=policy.get("version", 0),
            allowedValues=policy.get("listPolicy", {}).get("allowedValues", []),
            deniedValues=policy.get("listPolicy", {}).get("deniedValues", []),
            allValues=policy.get("listPolicy", {}).get("allValues", ""),
            suggestedValues=policy.get("listPolicy", {}).get("suggestedValues", ""),
            inheritFromParent=policy.get("listPolicy", {}).get("inheritFromParent", ""),
        ).save()
        obj.policies.update(op_obj)
        obj.save()
