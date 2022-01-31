from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_project import GcpProject


class GcpFolder(GcpResource):
    __primarylabel__ = "GcpFolder"
    __primarykey__ = "name"

    name = Property()
    displayName = Property()
    lifecycleState = Property()

    organizations = RelatedTo("GcpOrganization", "PART_OF")
    folders = RelatedFrom("GcpFolder", "PART_OF")
    projects = RelatedFrom(GcpProject, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
