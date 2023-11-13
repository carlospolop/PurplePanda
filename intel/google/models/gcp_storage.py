from py2neo.ogm import Property, RelatedFrom, RelatedTo, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_service_account import GcpServiceAccount
from core.models.models import StoresContainerImage


class GcpStorage(StoresContainerImage, GcpResource):
    __primarylabel__ = "GcpStorage"
    __primarykey__ = "name"

    name = Property()
    selfLink = Property()
    storageClass = Property()
    rpo = Property()
    location = Property()
    publicAccessPrevention = Property()
    bucketPolicyOnly = Property()
    uniformBucketLevelAccess = Property()
    contains_images = Property()
    contains_tfstates = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    cloudbuils = RelatedFrom("GcpCloudbuild", "HAS_SOURCE")
    composerenvs = RelatedFrom("GcpComposerEnv", "HAS_CODE")
    files = RelatedFrom("GcpFile", "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpFile(StoresContainerImage, GcpResource):
    __primarylabel__ = "GcpFile"
    __primarykey__ = "name"

    name = Property()
    selfLink = Property()
    contentType = Property()
    storageClass = Property()
    size = Property()
    md5Hash = Property()
    timeCreated = Property()
    updated = Property()

    storages = RelatedTo(GcpStorage, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
