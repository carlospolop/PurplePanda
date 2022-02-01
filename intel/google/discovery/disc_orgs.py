import logging
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.google_workspace import GoogleWorkspace
from core.models.models import PublicDomain


class DiscOrgs(GcpDisc):
    resource = 'cloudresourcemanager'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover each organization the account has access to.
        
        This module will create the organizations and relate them with the workspaces acounts.
        It will also get the IAM policies of the organization, relate the user/sa/groups with the orgs
        and also create the roles and relate each role with the permissions it has.
        """

        prep_http = self.service.organizations().search(body={})
        organizations = self.execute_http_req(prep_http, "organizations")
        self._disc_loop(organizations, self._disc_orgs, __name__.split(".")[-1])


    def _disc_orgs(self, o):
        """Discover each organization and its related workspace"""
        
        domain = o.get("displayName", "")
        o_obj: GcpOrganization = GcpOrganization(
            name=o["name"],
            domain=domain,
            lifecycleState=o.get("lifecycleState", "")
        ).save()

        if domain:
            dom_obj = PublicDomain(name=domain).save()
            o_obj.public_domains.update(dom_obj)
            o_obj.save()

        directoryCustomerId: str = o["owner"]["directoryCustomerId"]
        w_obj: GoogleWorkspace = GoogleWorkspace(name=directoryCustomerId).save()
        w_obj.organisations.update(o_obj)
        w_obj.save()

        self.get_iam_policy(o_obj, self.service.organizations(), o_obj.name)
