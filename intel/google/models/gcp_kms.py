from py2neo.ogm import Property, RelatedTo, RelatedFrom, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource


class GcpKMSKey(GcpResource):
    __primarylabel__ = "GcpKMSKey"
    __primarykey__ = "name"

    name = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    clusters = RelatedFrom("GcpCluster", "USES")
    kmskeys = RelatedFrom("GcpComposerEnv", "USES")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
