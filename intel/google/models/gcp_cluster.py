from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource, GcpRunningSA
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_composer import GcpComposerEnv
from intel.google.models.gcp_service_account import GcpServiceAccount #Needed
from core.models.models import PublicIP, CloudCluster
from intel.google.models.gcp_kms import GcpKMSKey
from intel.k8s.models.k8s_model import K8sNamespace, K8sNode, K8sMutatingWebhookConfig #Needed


class GcpCluster(GcpResource, GcpRunningSA, CloudCluster):
    __primarylabel__ = "GcpCluster"
    __primarykey__ = "name"

    name = Property()
    id = Property()
    description = Property()
    initialNodeCount = Property()
    loggingService = Property()
    monitoringService = Property()
    locations = Property()
    enableKubernetesAlpha = Property()
    resourceLabels = Property()
    labelFingerprint = Property()
    selfLink = Property()
    endpoint = Property()
    initialClusterVersion = Property()
    currentMasterVersion = Property()
    currentNodeCount = Property()
    status = Property()
    nodeIpv4CidrSize = Property()
    servicesIpv4Cidr = Property()
    expireTime = Property()
    location = Property()
    enableTpu = Property()
    tpuIpv4CidrBlock = Property()
    autopilot = Property()

    master_username = Property()
    master_password = Property()
    clusterCaCertificate = Property()
    clientCertificate = Property()
    clientKey = Property()

    addonsConfig = Property()

    masterAuthorizedNetworksConfig = Property()

    binaryAuthorization = Property()

    databaseEncryption = Property()

    enablePrivateNodes = Property()
    enablePrivateEndpoint = Property()
    masterIpv4CidrBlock = Property()
    privateEndpoint = Property()
    publicEndpoint = Property()
    peeringName = Property()
    masterGlobalAccessConfig = Property()

    node_machineTye = Property()
    node_diskSizeGb = Property()
    node_serialPortLoggingEnable = Property()
    node_disableLegacyEndpoints = Property()
    node_VmDnsSetting = Property()
    node_imageType = Property()
    node_diskType = Property()
    node_enableSecureBoot = Property()
    node_enableIntegrityMonitoring = Property()

    maxPodsPerNode = Property()

    shieldedNodes = Property()
    releaseChannel = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    subnets = RelatedTo("GcpSubnetwork", "CONNECTED")
    nodepools = RelatedFrom("GcpNodePool", "PART_OF")
    composer_environments = RelatedTo(GcpComposerEnv, "PART_OF")
    compute_instances = RelatedFrom("GcpComputeInstance", "PART_OF")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    kmskeys = RelatedTo(GcpKMSKey, "USES")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpNodePool(GcpResource, GcpRunningSA):
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