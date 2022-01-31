from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_project import GcpProject
from core.db.customogm import CustomOGM


class GcpBqDataset(CustomOGM):
    __primarylabel__ = "GcpBqDataset"
    __primarykey__ = "name"

    name = Property() # project-name:datasetname
    datasetId = Property() # datasetname
    displayName = Property()
    resource_name = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    bgtables = RelatedFrom("GcpBqTable", "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpBqTable(GcpResource):
    __primarylabel__ = "GcpBqTable"
    __primarykey__ = "name"

    name = Property() # project-name:datasetname.table name
    tableId = Property() # table name
    type = Property() # 'TABLE'
    resource_name = Property()

    bgdatasets = RelatedTo(GcpBqDataset, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True