from py2neo.ogm import Property, Label, RelatedFrom

from core.db.customogm import CustomOGM
from intel.google.models.gcp_project import GcpProject


class GcpService(CustomOGM):
    __primarylabel__ = "GcpService"
    __primarykey__ = "name"

    name = Property()
    title = Property()

    projects = RelatedFrom(GcpProject, "HAS_ENABLED")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
