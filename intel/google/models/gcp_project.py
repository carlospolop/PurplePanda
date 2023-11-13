from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_org_policy import GcpOrgPolicy


class GcpProject(GcpResource):
    __primarylabel__ = "GcpProject"
    __primarykey__ = "name"

    name = Property()
    projectNumber = Property()
    displayName = Property()
    lifecycleState = Property()

    organizations = RelatedTo("GcpOrganization", "PART_OF")
    folders = RelatedTo("GcpFolder", "PART_OF")
    roles = RelatedFrom("GcpRole", "PART_OF")
    cloud_functions = RelatedFrom("GcpCloudFunction", "PART_OF")
    basic_roles = RelatedTo(GcpResource, "HAS_BASIC_ROLES")
    networks = RelatedFrom("GcpNetwork", "PART_OF")
    subnetworks = RelatedFrom("GcpNetwork", "PART_OF")
    composer_environments = RelatedFrom("GcpComposerEnv", "PART_OF")
    clusters = RelatedFrom("GcpCluster", "PART_OF")
    bqdatasets = RelatedFrom("GcpBqDataset", "PART_OF")
    kmskeyrings = RelatedFrom("GcpKMSKeyRing", "PART_OF")
    kmskeys = RelatedFrom("GcpKMSKey", "PART_OF")
    policies = RelatedTo(GcpOrgPolicy, "HAS_POLICY")

    gcp = Label(name="Gcp")

    def __init__(self, name, *args, **kwargs):
        kwargs["name"] = name if name.startswith("projects/") else f"projects/{name}"
        super().__init__(*args, **kwargs)

        self.gcp = True
