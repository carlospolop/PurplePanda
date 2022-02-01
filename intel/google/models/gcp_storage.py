from py2neo.ogm import Property, RelatedFrom, RelatedTo, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_service_account import GcpServiceAccount


class GcpStorage(GcpResource):
    __primarylabel__ = "GcpStorage"
    __primarykey__ = "name"

    name = Property()
    selflink = Property()
    storageClass = Property()
    rpo = Property()
    location = Property()
    publicAccessPrevention = Property()
    bucketPolicyOnly = Property()
    uniformBucketLevelAccess = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    cloudbuils = RelatedFrom("GcpCloudbuild", "HAS_SOURCE")

    gcp = Label(name="Gcp")

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
