from py2neo.ogm import Property, RelatedFrom, RelatedTo, Related, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource, GcpRunningSA
from intel.google.models.gcp_cluster import GcpCluster
from intel.google.models.gcp_service_account import GcpServiceAccount  # This needs to be imported!
from core.db.customogm import CustomOGM
from core.models.models import PublicIP


class GcpComputeInstance(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpComputeInstance"
    __primarykey__ = "name"

    name = Property()
    displayName = Property()
    machineType = Property()
    status = Property()
    cpuPlatform = Property()
    startRestricted = Property()
    deletionProtection = Property()
    enableSecureBoot = Property()
    enableVtpm = Property()
    enableIntegrityMonitoring = Property()
    updateAutoLearnPolicy = Property()
    metadata = Property()
    tags = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    subnetworks = RelatedTo("GcpSubnetwork", "CONNECTED")
    disks = RelatedFrom("GcpComputeDisk", "PART_OF")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    clusters = RelatedTo(GcpCluster,
                         "PART_OF")  # Relate to cluster and not to nodepool because the name of the nodepools are less prone to be different

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpComputeDisk(GcpResource):
    __primarylabel__ = "GcpComputeDisk"
    __primarykey__ = "name"

    name = Property()
    type = Property()
    mode = Property()
    source = Property()
    index = Property()
    boot = Property()
    autoDelete = Property()
    interface = Property()
    diskSizeGb = Property()
    guestOsFeatures = Property()

    compute_instances = RelatedTo(GcpComputeInstance, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpNetwork(CustomOGM):
    __primarylabel__ = "GcpNetwork"
    __primarykey__ = "name"

    name = Property()
    description = Property()
    selfLink = Property()
    autoCreateSubnetworks = Property()
    routingMode = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    networks = Related("GcpNetwork", "PEERING")
    subnetworks = RelatedFrom("GcpSubnetwork", "PART_OF")
    firewall_rules = RelatedFrom("GcpFirewallRule", "PROTECT")
    sqlinstances = RelatedFrom("GcpSqlInstance", "CONNECTED")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpSubnetwork(GcpResource):
    __primarylabel__ = "GcpSubnetwork"
    __primarykey__ = "name"

    name = Property()
    selfLink = Property()
    ipCidrRange = Property()
    gatewayAddress = Property()
    privateIpGoogleAccess = Property()
    privateIpv6GoogleAccess = Property()
    purpose = Property()
    stackType = Property()
    logEnabled = Property()
    secondaryIpRanges = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    parent_network = RelatedTo(GcpNetwork, "PART_OF")
    instances = RelatedFrom(GcpComputeInstance, "CONNECTED")
    clusters = RelatedFrom(GcpCluster, "CONNECTED")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True


class GcpFirewallRule(CustomOGM):
    __primarylabel__ = "GcpFirewallRule"
    __primarykey__ = "name"

    name = Property()
    description = Property()
    direction = Property()
    disabled = Property()
    logEnabled = Property()
    priority = Property()
    selfLink = Property()
    sourceRanges = Property()
    targetTags = Property()
    allowed = Property()
    denied = Property()

    networks = RelatedTo(GcpNetwork, "PROTECT")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
