from py2neo.ogm import Property, RelatedTo, RelatedFrom

from core.db.customogm import CustomOGM
from intel.github.models.github_model import GithubPrincipal

class PublicIP(CustomOGM):
    __primarylabel__ = "PublicIP"
    __primarykey__ = "ip"

    ip = Property()
    is_private = Property()

    ports = RelatedTo("PublicPort", "HAS_PORT")
    gcp_compute_instances = RelatedFrom("GcpComputeInstance", "HAS_IP")
    gcp_clusters = RelatedFrom("GcpCluster", "HAS_IP")
    gcp_composerenvs = RelatedFrom("GcpComposerEnv", "HAS_IP")
    k8s_service = RelatedFrom("K8sService", "HAS_IP")
    public_domains = RelatedFrom("PublicDomain", "HAS_IP")
    k8s_mutatingwebhookconfigs = RelatedFrom("K8sMutatingWebhookConfig", "HAS_IP")

class PublicPort(CustomOGM):
    __primarylabel__ = "PublicPort"
    __primarykey__ = "port"

    port = Property()

    public_ips = RelatedFrom(PublicIP, "HAS_PORT")

class PublicDomain(CustomOGM):
    __primarylabel__ = "PublicDomain"
    __primarykey__ = "name"

    name = Property()
    is_real = Property()
    is_external = Property()

    gcp_orgs = RelatedFrom("GcpOrganization", "HAS_DOMAIN")
    gcp_composerenvs = RelatedFrom("GcpComposerEnv", "HAS_IP")
    k8s_service = RelatedFrom("K8sService", "HAS_DOMAIN")
    k8s_ingress = RelatedFrom("K8sIngress", "HAS_DOMAIN")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    k8s_mutatingwebhookconfigs = RelatedFrom("K8sMutatingWebhookConfig", "HAS_DOMAIN")


class RepoPpalPrivesc(CustomOGM):
    __primarylabel__ = "RepoPpalPrivesc"

    repo_privesc = RelatedFrom(GithubPrincipal, "PRIVESC")

class CloudCluster(CustomOGM):
    __primarylabel__ = "CloudCluster"

    k8s_namespaces = RelatedFrom("K8sNamespace", "HAS_NAMESPACE")
    k8s_nodes = RelatedFrom("K8sNode", "HAS_NODE")
    k8s_mutatingwebhookconfigurations = RelatedFrom("K8sMutatingWebhookConfig", "HAS_MUTATINGWEBHOOKCONFIG")