from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource


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

    gcp = Label(name="Gcp")

    def __init__(self, name, *args, **kwargs):
        if not name.startswith("projects/"):
            kwargs["name"] = f"projects/{name}"
        else:
            kwargs["name"] = name

        super().__init__(*args, **kwargs)

        self.gcp = True

