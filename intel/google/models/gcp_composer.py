from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from core.db.customogm import CustomOGM
from intel.google.models.gcp_project import GcpProject


class GcpComposerEnv(CustomOGM):
    __primarylabel__ = "GcpComposerEnv"
    __primarykey__ = "name"

    name = Property()
    state = Property()
    dagGcsPrefix = Property()
    nodeCount = Property()
    imageVersion = Property()
    pypiPackages = Property()
    envVariables = Property()
    pythonVersion = Property()
    airflowUri = Property()
    enablePrivateEnvironment = Property()
    enablePrivateEndpoint = Property()
    masterIpv4CidrBlock = Property()
    masterIpv4ReservedRange = Property()
    webServerIpv4CidrBlock = Property()
    cloudSqlIpv4CidrBlock = Property()
    webServerIpv4ReservedRange = Property()
    allowedIpRanges = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    clusters = RelatedFrom(GcpProject, "PART_OF")
    composer_environments = RelatedFrom("GcpCluster", "PART_OF")
    opeerations = RelatedFrom("GcpOperation", "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpOperation(CustomOGM):
    __primarylabel__ = "GcpOperation"
    __primarykey__ = "name"

    name = Property()
    state = Property()
    operationType = Property()
    done = Property()

    composer_environmetns = RelatedTo(GcpComposerEnv, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True