from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from core.db.customogm import CustomOGM
from intel.google.models.gcp_project import GcpProject
from core.models import PublicDomain, PublicIP
from intel.google.models.gcp_kms import GcpKMSKey


class GcpComposerEnv(CustomOGM):
    __primarylabel__ = "GcpComposerEnv"
    __primarykey__ = "name"

    name = Property()
    state = Property()
    labels = Property()

    gkeCluster = Property()
    dagGcsPrefix = Property()
    nodeCount = Property()
    airflowUri = Property()
    environmentSize = Property()

    imageVersion = Property()
    airflowConfigOverrides = Property()
    pypiPackages = Property()
    envVariables = Property()
    pythonVersion = Property()
    schedulerCount = Property()

    enablePrivateEnvironment = Property()
    enablePrivateEndpoint = Property()
    masterIpv4CidrBlock = Property()
    masterIpv4ReservedRange = Property()
    webServerIpv4CidrBlock = Property()
    cloudSqlIpv4CidrBlock = Property()
    webServerIpv4ReservedRange = Property()
    cloudComposerNetworkIpv4CidrBlock = Property()
    cloudComposerNetworkIpv4ReservedRange = Property()
    enablePrivatelyUsedPublicIps = Property()

    allowedIpRanges = Property()

    databaseMachineType = Property()

    webServerType = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    clusters = RelatedFrom(GcpProject, "PART_OF")
    composer_environments = RelatedFrom("GcpCluster", "PART_OF")
    operations = RelatedFrom("GcpOperation", "PART_OF")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    kmskeys = RelatedTo(GcpKMSKey, "USES")

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

    composer_environments = RelatedTo(GcpComposerEnv, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True