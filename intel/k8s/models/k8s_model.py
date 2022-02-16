from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from core.db.customogm import CustomOGM
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.google.models.gcp_perm_models import GcpRunningSA
from core.models.models import PublicIP, PublicDomain, CloudCluster

# In K8s objects primary keys must be "name"

class K8sBasicModel(CustomOGM):
    name = Property()
    self_link = Property()
    resource_version = Property()
    uid = Property()
    labels = Property()
    status = Property()
    annotations = Property()
    
    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sBasicModelNS(K8sBasicModel):

    namespaces = RelatedTo("K8sNamespace", "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sContainsContainer(K8sBasicModelNS):
    __primarylabel__ = "K8sContainsContainer"

    containers = RelatedFrom("K8sContainer", "PART_OF")

    k8sContainsContainer = Label(name="K8sContainsContainer")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8sContainsContainer = True


class K8sPodTemplate(K8sContainsContainer):
    __primarylabel__ = "K8sPodTemplate"

    pods = RelatedFrom("K8sPod", "PART_OF")

    K8sPodTemplate = Label(name="K8sPodTemplate")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.K8sPodTemplate = True


class K8sNamespace(K8sPodTemplate):
    __primarylabel__ = "K8sNamespace"
    __primarykey__ = "name"

    ns_name = Property() # Namespace name without identifier
    iam_amazonaws_com_permitted = Property()
    iam_amazonaws_com_allowed_roles = Property()
    cluster_name = Property()
    generate_name = Property()

    pods = RelatedFrom("K8sPod", "PART_OF")
    volumes = RelatedFrom("K8sVol", "CLAIMED")
    secrets = RelatedFrom("K8sSecret", "PART_OF")
    roles = RelatedFrom("K8sRole", "PART_OF")
    serviceaccounts = RelatedFrom("K8sServiceAccount", "PART_OF")
    services = RelatedFrom("K8sService", "PART_OF")
    ingresses = RelatedFrom("K8sIngress", "PART_OF")
    cloudclusters = RelatedTo(CloudCluster, "HAS_NAMESPACE")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sNode(K8sBasicModel):
    __primarylabel__ = "K8sNode"
    __primarykey__ = "name"

    role = Property()
    instance_type = Property()
    zone = Property()
    
    addresses = Property()
    addresses_type = Property()

    kubelet_port = Property()

    arch = Property()
    kernelVersion = Property()
    kubeProxyVersion = Property()
    kubeletVersion = Property()
    os = Property()
    osImage = Property()

    pods = RelatedFrom("K8sPod", "PART_OF")
    volumes = RelatedFrom("K8sVol", "MOUNTED")
    cloudclusters = RelatedTo(CloudCluster, "HAS_NODE")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sContainer(K8sBasicModel):
    __primarylabel__ = "K8sContainer"
    __primarykey__ = "name"

    command = Property()
    args = Property()
    args = Property()
    working_dir = Property()
    image_pull_policy = Property()
    lifecycle_post_start = Property()
    lifecycle_pre_stop = Property()
    exist_limit_resources = Property()
    potential_escape_to_node = Property()
    
    sc_allowPrivilegeEscalation = Property()
    sc_capabilities_drop = Property()
    sc_capabilities_add = Property()
    sc_privileged = Property()
    sc_procMount = Property()
    sc_readOnlyRootFilesystem = Property()
    sc_runAsGroup = Property()
    sc_runAsNonRoot = Property()
    sc_runAsUser = Property()
    sc_seLinuxOptions = Property()
    sc_seccompProfile = Property()
    sc_windowsOptions = Property()

    volumes = RelatedFrom("K8sVol", "MOUNTED")
    secrets = RelatedTo("K8sSecret", "USE_SECRET")
    envvars = RelatedTo("K8sEnvVar", "USE_ENV_VAR")
    containscnotainer = RelatedTo("K8sContainsContainer", "PART_OF")
    container_ports = RelatedTo("K8sContainerPort", "LISTEN")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sContainerPort(CustomOGM):
    __primarylabel__ = "K8sContainerPort"
    __primarykey__ = "name"

    name = Property()
    port = Property()
    protocol = Property()

    containers = RelatedFrom(K8sContainer, "LISTEN")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sPod(K8sContainsContainer, GcpRunningSA):
    __primarylabel__ = "K8sPod"
    __primarykey__ = "name"

    iam_amazonaws_com_role = Property()
    iam_amazonaws_external_id = Property()

    dnsPolicy = Property()
    enableServiceLinks = Property()
    imagePullSecrets = Property()
    priority = Property()
    priorityClassName = Property()
    restartPolicy = Property()
    schedulerName = Property()
    no_automount_service_account_token = Property()

    host_ipc = Property()
    host_network = Property()
    host_pid = Property()
    host_path = Property()
    potential_escape_to_node = Property()

    # Security Context
    sc_fsGroup = Property()
    sc_fsGroupChangePolicy = Property()
    sc_runAsGroup = Property()
    sc_runAsNonRoot = Property()
    sc_runAsUser = Property()
    sc_seLinuxOptions = Property()
    sc_seccompProfile_type = Property()
    sc_seccompProfile_localhost_profile = Property()
    sc_supplemental_groups = Property()
    sc_sysctls = Property()
    sc_windowsOptions = Property()

    phase = Property()
    pod_ips = Property()

    nodes = RelatedTo("K8sNode", "PART_OF")
    volumes = RelatedFrom("K8sVol", "MOUNTED")
    secrets = RelatedTo("K8sSecret", "USE_SECRET")
    serviceaccounts = RelatedFrom("K8sServiceAccount", "RUN_IN")
    services_attached = RelatedTo("K8sPod", "HAS_SERVICE")
    containspodtemplate = RelatedTo("K8sPodTemplate", "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sVol(K8sBasicModelNS):
    __primarylabel__ = "K8sVol"
    __primarykey__ = "name"

    is_hostpath = Property()

    pods = RelatedTo(K8sPod, "MOUNTED")
    containers = RelatedTo(K8sContainer, "MOUNTED")
    secrets = RelatedTo("K8sSecret", "USE_SECRET")
    nodes = RelatedTo(K8sNode, "MOUNTED")
    statefulset = RelatedTo("K8sStatefulSet", "MOUNTED")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sSecret(K8sBasicModelNS):
    __primarylabel__ = "K8sSecret"
    __primarykey__ = "name"

    immutable = Property()
    keys = Property()
    values = Property()
    values_cleartext = Property()
    type = Property()

    volumes = RelatedFrom(K8sVol, "USE_SECRET")
    envvars = RelatedFrom("K8sEnvVar", "USE_SECRET")
    pods = RelatedFrom(K8sPod, "USE_SECRET")
    containers = RelatedFrom(K8sContainer, "USE_SECRET")
    serviceaccounts = RelatedFrom("K8sServiceAccount", "CONTAINS_TOKEN")
    ingresses = RelatedFrom("K8sIngress", "USE_SECRET")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sEnvVar(CustomOGM):
    __primarylabel__ = "K8sEnvVar"
    __primarykey__ = "name"

    name = Property()

    containers = RelatedFrom(K8sContainer, "USE_ENV_VAR")
    secrets = RelatedTo("K8sSecret", "USE_SECRET")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sDeployment(K8sPodTemplate):
    __primarylabel__ = "K8sDeployment"
    __primarykey__ = "name"

    status_ready_replicas = Property()

    replicasets = RelatedFrom("K8sReplicaSet", "PART_OF")
    statefulsets = RelatedFrom("K8sStatefulSet", "PART_OF")
    daemonsets = RelatedFrom("K8sDaemonSet", "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sCronJob(K8sPodTemplate):
    __primarylabel__ = "K8sCronJob"
    __primarykey__ = "name"

    concurrency_policy = Property()
    schedule = Property()
    suspend = Property()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sJob(K8sPodTemplate):
    __primarylabel__ = "K8sJob"
    __primarykey__ = "name"

    parallelism = Property()
    suspend = Property()
    completions = Property()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sDaemonSet(K8sPodTemplate):
    __primarylabel__ = "K8sDaemonSet"
    __primarykey__ = "name"

    status_number_ready = Property()

    deployments = RelatedTo(K8sDeployment, "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sStatefulSet(K8sPodTemplate):
    __primarylabel__ = "K8sStatefulSet"
    __primarykey__ = "name"

    status_ready_replicas = Property()

    volumes = RelatedFrom(K8sVol, "PART_OF")
    deployments = RelatedTo(K8sDeployment, "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sReplicaSet(K8sPodTemplate):
    __primarylabel__ = "K8sReplicaSet"
    __primarykey__ = "name"

    status_ready_replicas = Property()
    deployments = RelatedTo(K8sDeployment, "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sReplicationController(K8sPodTemplate):
    __primarylabel__ = "K8sReplicationController"
    __primarykey__ = "name"

    status_ready_replicas = Property()
    deployments = RelatedTo(K8sDeployment, "PART_OF")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sPrincipal(CustomOGM):
    __primarylabel__ = "K8sPrincipal"
    __primarykey__ = "name"

    name = Property()
    interesting_permissions = Property()

    resources = RelatedTo("K8sResource", "HAS_PERMS")
    privesc = RelatedTo("K8sPrincipal", "PRIVESC")
    privesc_from = RelatedFrom("K8sPrincipal", "PRIVESC")
    potential_privesc_to = RelatedTo("K8sPrincipal", "POTENTIAL_PRIVESC")
    potential_privesc_from = RelatedFrom("K8sPrincipal", "POTENTIAL_PRIVESC")
    privesc_to_gcp = RelatedTo(GcpServiceAccount, "PRIVESC")

    principal = Label(name="K8sPrincipal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.principal = True


class K8sServiceAccount(K8sPrincipal):
    __primarylabel__ = "K8sServiceAccount"
    __primarykey__ = "name"

    name = Property()
    self_link = Property()
    uid = Property()
    labels = Property()
    potential_escape_to_node = Property()
    annotations = Property()
    iam_amazonaws_role_arn = Property()

    pods = RelatedTo(K8sPod, "RUN_IN")
    namespaces = RelatedTo(K8sNamespace, "PART_OF")
    secrets = RelatedTo("K8sSecret", "CONTAINS_TOKEN")
    groups = RelatedTo("K8sGroup", "MEMBER_OF")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sUser(K8sPrincipal):
    __primarylabel__ = "K8sUser"
    __primarykey__ = "name"

    name = Property()
    potential_escape_to_node = Property()

    groups = RelatedTo("K8sGroup", "MEMBER_OF")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sGroup(K8sPrincipal):
    __primarylabel__ = "K8sGroup"
    __primarykey__ = "name"

    name = Property()
    potential_escape_to_node = Property()

    serviceaccounts = RelatedFrom("K8sGroup", "MEMBER_OF")
    users = RelatedFrom("K8sUser", "MEMBER_OF")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sResource(CustomOGM):
    __primarylabel__ = "K8sSResource"
    __primarykey__ = "name"

    name = Property()

    clusterroles = RelatedFrom("K8sClusterRole", "HAS_ROLE")
    roles = RelatedFrom("K8sRole", "HAS_ROLE")
    serviceaccounts = RelatedFrom(K8sServiceAccount, "HAS_PERMS")
    users = RelatedFrom(K8sUser, "HAS_PERMS")
    groups = RelatedFrom(K8sGroup, "HAS_PERMS")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sClusterRole(CustomOGM):
    __primarylabel__ = "K8sClusterRole"
    __primarykey__ = "name"

    name = Property()
    self_link = Property()
    uid = Property()
    labels = Property()

    resources = RelatedTo(K8sResource, "HAS_ROLE")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sRole(CustomOGM):
    __primarylabel__ = "K8sRole"
    __primarykey__ = "name"

    name = Property()
    self_link = Property()
    uid = Property()
    labels = Property()

    resources = RelatedTo(K8sResource, "HAS_ROLE")
    namespaces = RelatedTo(K8sNamespace, "PART_OF")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k8s = True


class K8sService(K8sBasicModelNS):
    __primarylabel__ = "K8sService"
    __primarykey__ = "name"

    type = Property()
    ports = Property()
    cluster_ips = Property()

    external_traffic_policy = Property()
    health_check_node_port = Property()
    internal_traffic_policy = Property()
    ip_families = Property()
    ip_family_policy = Property()
    load_balancer_class = Property()
    load_balancer_ip = Property()
    load_balancer_source_ranges = Property()

    public_ips = RelatedTo(PublicIP, "HAS_IP")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    pods = RelatedFrom(K8sPod, "HAS_SERVICE")
    ingresses = RelatedFrom("K8sIngress", "TO_SERVICE")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sIngress(K8sBasicModelNS):
    __primarylabel__ = "K8sIngress"
    __primarykey__ = "name"

    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    services = RelatedTo(K8sService, "TO_SERVICE")
    secrets = RelatedTo("K8sSecret", "USE_SECRET")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class K8sMutatingWebhookConfig(K8sBasicModelNS):
    __primarylabel__ = "K8sMutatingWebhookConfig"
    __primarykey__ = "name"
    
    name = Property()
    self_link = Property()
    uid = Property()
    labels = Property()
    annotations = Property()

    namespace_selector_expresions = Property()
    namespace_selector_labels = Property()
    #client_config = Property()
    reinvocation_policy = Property()
    failure_policy = Property()
    rules_operations = Property()
    rules_resources = Property()

    public_ips = RelatedTo(PublicIP, "HAS_IP")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    cloudclusters = RelatedTo(CloudCluster, "HAS_MUTATINGWEBHOOKCONFIG")

    k8s = Label(name="K8s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)