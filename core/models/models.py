from py2neo.ogm import Property, RelatedTo, RelatedFrom, Label

from core.db.customogm import CustomOGM
from intel.github.models.github_model import GithubPrincipal, GithubRepo, GithubWebhook
from intel.bitbucket.models.bitbucket_model import BitbucketRepo


########################
#### PUBLIC ASSETS #####
########################

class PublicIP(CustomOGM):
    __primarylabel__ = "PublicIP"
    __primarykey__ = "name"

    name = Property()
    is_private = Property()

    ports = RelatedTo("PublicPort", "HAS_PORT")
    gcp_compute_instances = RelatedFrom("GcpComputeInstance", "HAS_IP")
    gcp_clusters = RelatedFrom("GcpCluster", "HAS_IP")
    gcp_composerenvs = RelatedFrom("GcpComposerEnv", "HAS_IP")
    gcp_resourcerecords = RelatedFrom("GcpResourceRecord", "HAS_IP")
    gcp_sqlinstances = RelatedFrom("GcpSqlInstance", "HAS_IP")
    k8s_service = RelatedFrom("K8sService", "HAS_IP")
    public_domains = RelatedFrom("PublicDomain", "HAS_IP")
    k8s_mutatingwebhookconfigs = RelatedFrom("K8sMutatingWebhookConfig", "HAS_IP")
    concourse_workers = RelatedFrom("ConcurseWorker", "HAS_IP")
    gh_webhooks = RelatedFrom(GithubWebhook, "HAS_IP")


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
    gcp_managedzones = RelatedFrom("GcpManagedZone", "HAS_DOMAIN")
    gcp_resourcerecords = RelatedFrom("GcpResourceRecord", "HAS_DOMAIN")
    k8s_service = RelatedFrom("K8sService", "HAS_DOMAIN")
    k8s_ingress = RelatedFrom("K8sIngress", "HAS_DOMAIN")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    k8s_mutatingwebhookconfigs = RelatedFrom("K8sMutatingWebhookConfig", "HAS_DOMAIN")
    concourse_workers = RelatedFrom("ConcourseWorker", "HAS_DOMAIN")
    gh_webhooks = RelatedFrom(GithubWebhook, "HAS_DOMAIN")


class RepoPpalPrivesc(CustomOGM):
    __primarylabel__ = "RepoPpalPrivesc"

    repo_privesc = RelatedFrom(GithubPrincipal, "PRIVESC")


########################
####### CLUSTERS #######
########################

class CloudCluster(CustomOGM):
    __primarylabel__ = "CloudCluster"

    k8s_namespaces = RelatedFrom("K8sNamespace", "HAS_NAMESPACE")
    k8s_nodes = RelatedFrom("K8sNode", "HAS_NODE")
    k8s_mutatingwebhookconfigurations = RelatedFrom("K8sMutatingWebhookConfig", "HAS_MUTATINGWEBHOOKCONFIG")


########################
### CONTAINER IMAGES ###
########################

class ContainerImage(CustomOGM):
    __primarylabel__ = "ContainerImage"
    __primarykey__ = "name"

    name = Property()

    image_containers = RelatedFrom("StoresContainerImage", "STORES_IMAGE")
    image_runners = RelatedFrom("RunsContainerImage", "RUN_IMAGE")

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)

        if (
            "gcr.io/" in self.name
            and "k8s.gcr.io/" not in self.name
            and "gke.gcr.io/" not in self.name
        ):
            from intel.google.models import GcpStorage
            zone_subdomain = self.name.split(".gcr.io/")[
                                 0] + "." if ".gcr.io/" in self.name else ""  # Get "eu." in "eu.gcr.io/..."
            project_name = self.name.split("gcr.io/")[1].split("/")[0]
            bucket_name = f"{zone_subdomain}artifacts.{project_name}.appspot.com"
            storage_obj = GcpStorage(name=bucket_name, contains_images=True).save()
            self.image_containers.update(storage_obj)
            return super().save(*args, **kwargs)

        return ret


class StoresContainerImage(CustomOGM):
    __primarylabel__ = "StoresContainerImage"

    container_images = RelatedTo(ContainerImage, "STORES_IMAGE")

    label = Label(name="StoresContainerImage")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = True


class RunsContainerImage(CustomOGM):
    __primarylabel__ = "RunsContainerImage"

    run_images = RelatedTo(ContainerImage, "RUN_IMAGE")

    label = Label(name="RunsContainerImage")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = True


########################
###### CODE REPOS ######
########################

class CodeMirror(CustomOGM):
    __primarylabel__ = "CodeMirror"

    github_repos = RelatedTo(GithubRepo, "IS_MIRROR")
    bitbucket_repos = RelatedTo(BitbucketRepo, "IS_MIRROR")

    label = Label(name="CodeMirror")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = True
