from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from intel.google.models.gcp_perm_models import GcpResource, GcpPrincipal
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_folder import GcpFolder
from intel.google.models.gcp_org_policy import GcpOrgPolicy
from core.models.models import PublicDomain


class GcpOrganization(GcpPrincipal, GcpResource):
    __primarylabel__ = "GcpOrganization"
    __primarykey__ = "domain"

    name = Property()
    domain = Property()
    lifecycleState = Property()

    folders = RelatedFrom(GcpFolder, "PART_OF")
    projects = RelatedFrom(GcpProject, "PART_OF")
    workspaces = RelatedTo("GcpWorkspace", "PART_OF")
    roles = RelatedFrom("GcpRole", "PART_OF")
    service_accounts = RelatedFrom("GcpServiceAccount", "PART_OF")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    policies = RelatedTo(GcpOrgPolicy, "HAS_POLICY")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
