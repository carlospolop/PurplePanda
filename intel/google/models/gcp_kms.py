from py2neo.ogm import Property, RelatedTo, RelatedFrom, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource


class GcpKMSKeyRing(GcpResource):
    __primarylabel__ = "GcpKMSKeyRing"
    __primarykey__ = "name"

    name = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    kmskeys = RelatedFrom("GcpKMSKey", "PART_OF")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpKMSKey(GcpResource):
    __primarylabel__ = "GcpKMSKey"
    __primarykey__ = "name"

    name = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    keyrings = RelatedTo(GcpKMSKeyRing, "PART_OF")
    keyversions = RelatedFrom("GcpKMSKey", "PART_OF")
    clusters = RelatedFrom("GcpCluster", "USES")
    composers = RelatedFrom("GcpComposerEnv", "USES")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpKMSKeyVersion(GcpResource):
    __primarylabel__ = "GcpKMSKeyVersion"
    __primarykey__ = "name"

    name = Property()
    purpose = Property()
    createTime = Property()
    nextRotationTime = Property()
    labels = Property()
    importOnly = Property()
    destroyScheduledDuration = Property()
    cryptoKeyBackend = Property()
    rotationPeriod = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    keys = RelatedTo(GcpKMSKey, "PART_OF")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

