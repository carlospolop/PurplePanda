from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from core.db.customogm import CustomOGM
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_organization import GcpOrganization


class GcpPermission(CustomOGM):
    __primarylabel__ = "GcpPermission"
    __primarykey__ = "name"

    name = Property()

    roles = RelatedFrom("GcpRole", "CONTAINS")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpRole(CustomOGM):
    __primarylabel__ = "GcpRole"
    __primarykey__ = "name"

    name = Property()
    displayName = Property()
    description = Property()
    stage = Property()
    etag = Property()

    permissions = RelatedTo(GcpPermission, "CONTAINS")
    projects = RelatedTo(GcpProject, "PART_OF")
    organization = RelatedTo(GcpOrganization, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
