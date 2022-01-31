from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource, GcpRunningSA
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_composer import GcpComposerEnv
from intel.google.models.gcp_service_account import GcpServiceAccount


class GcpCluster(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpCluster"
    __primarykey__ = "name"

    name = Property()
    node_machineTye = Property()
    node_diskSizeGb = Property()
    node_serialPortLoggingEnable = Property()
    node_disableLegacyEndpoints = Property()
    node_VmDnsSetting = Property()
    node_imageType = Property()
    node_diskType = Property()
    node_enableSecureBoot = Property()
    node_enableIntegrityMonitoring = Property()
    locations = Property()
    masterAuthorizedNetworksConfig = Property()
    maxPodsPerNode = Property()
    enablePrivateNodes = Property()
    enablePrivateEndpoint = Property()
    masterIpv4CidrBlock = Property()
    privateEndpoint = Property()
    publicEndpoint = Property()
    peeringName = Property()
    databaseEncryption = Property()
    shieldedNodes = Property()
    releaseChannel = Property()
    source = Property()
    status = Property()
    currentMasterVersion = Property()
    currentNodeCount = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    subnets = RelatedTo("GcpSubnetwork", "CONNECTED")
    nodepools = RelatedFrom("GcpNodePool", "PART_OF")
    composer_environments = RelatedTo(GcpComposerEnv, "PART_OF")
    compute_instances = RelatedFrom("GcpComputeInstance", "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpNodePool(GcpResource):
    __primarylabel__ = "GcpNodePool"
    __primarykey__ = "name"

    name = Property()
    node_machineTye = Property()
    node_diskSizeGb = Property()
    node_serialPortLoggingEnable = Property()
    node_disableLegacyEndpoints = Property()
    node_VmDnsSetting = Property()
    node_imageType = Property()
    node_diskType = Property()
    node_enableSecureBoot = Property()
    node_enableIntegrityMonitoring = Property()
    initialNodeCount = Property()
    autoUpgrade = Property()
    autoRepair = Property()
    maxPodsPerNode = Property()
    podIpv4CidrSize = Property()
    locations = Property()
    source = Property()
    version = Property()
    status = Property()

    clusters = RelatedTo(GcpCluster, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True