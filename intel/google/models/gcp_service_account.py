from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from intel.google.models.gcp_perm_models import GcpPrincipal, GcpResource
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.google_group import GoogleGroup

class GcpServiceAccount(GcpPrincipal, GcpResource):
    __primarylabel__ = "GcpServiceAccount"
    __primarykey__ = "email"

    name = Property()
    email = Property()
    description = Property()
    displayName = Property()
    uniqueId = Property()

    groups = RelatedTo(GoogleGroup, "MEMBER_OF")
    projects = RelatedTo(GcpProject, "PART_OF")
    organizations = RelatedTo(GcpOrganization, "PART_OF")
    cloud_functions = RelatedTo("GcpCloudFunction", "RUN_IN")
    compute_instances = RelatedTo("GcpComputeInstance", "RUN_IN")
    api_keys = RelatedTo("GcpApiKey", "HAS_KEY")
    privesc_from_k8s = RelatedFrom("K8sPrincipal", "PRIVESC")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
