from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from intel.google.models.gcp_perm_models import GcpRunningSA
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_storage import GcpStorage
from intel.google.models.gcp_pubsub import GcpPubSubTopic, GcpPubSubSubscription
from intel.google.models.gcp_secrets import GcpSecretVersion
from intel.google.models.gcp_source_repos import GcpSourceRepo
from intel.google.models.gcp_service_account import GcpServiceAccount
from core.db.customogm import CustomOGM
from intel.github.models.github_model import GithubRepo


class GcpCloudbuildBuild(CustomOGM, GcpRunningSA):
    __primarylabel__ = "GcpCloudbuildBuild"
    __primarykey__ = "id"

    name = Property()
    id = Property()
    images = Property()
    logsBucket = Property() # gs://541234567077.cloudbuild-logs.googleusercontent.com
    tags = Property()
    
    #bucket source
    bucket = Property() #Bucket name
    bucketObject = Property() #Path to object inside the bucket

    #reposource
    repoName = Property()
    repoDir = Property()
    branchName = Property()
    tagName = Property()
    commitSha = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    buckets = RelatedTo(GcpStorage, "HAS_SOURCE")
    sourceRepos = RelatedTo(GcpSourceRepo, "HAS_SOURCE")
    cloudbuildTriggers = RelatedFrom("GcpCloudbuildTrigger", "BUILDS")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpCloudbuildTrigger(CustomOGM, GcpRunningSA):
    __primarylabel__ = "GcpCloudbuildTrigger"
    __primarykey__ = "id"

    name = Property()
    id = Property()
    resourceName = Property()
    description = Property()
    tags = Property()

    # If the trigger is a change in a GCP Source Repo, here is defined the specific change
    triggerRepoProjectId =Property()
    triggerRepoName = Property()
    triggerRepoDir = Property()
    triggerBranchName = Property()
    triggerTagName = Property()
    triggerCommitSha = Property()

    # If the trigger is a change in a Github Repo, here is defined the specific change
    triggerGhOwner = Property()
    triggerGhName = Property()
    triggerGhEnterpriseConfigResourceName = Property()
    triggerGhPRBranch = Property()
    triggerGhInvertRegex = Property()
    triggerGhPSBranch = Property()
    triggerGhPSTag = Property()

    # If the trigger listen in a webhook, here you can find the secret with it
    triggerWebhook = Property()

    # If the trigger listen ina pub/sub, here is the subscription and topic
    triggerPubSubSubscription = Property()
    triggerPubSubTopic = Property()

    disabled = Property()
    ignoredFiles = Property()
    includedFiles = Property()
    approvalRequired = Property()
    filter = Property()
    autodetect = Property()
    filename = Property()

    # These fields defines where is the file indicating how to build
    gitFilePath = Property()
    gitFileUri = Property()
    gitFileRevision = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    pubsubSubscriptions_trigger = RelatedTo(GcpPubSubSubscription, "TRIGGER")
    pubsubTopics_trigger = RelatedTo(GcpPubSubTopic, "TRIGGER")
    secrets_trigger = RelatedTo(GcpSecretVersion, "WEBHOOK")
    sourcerepos_trigger = RelatedTo(GcpSourceRepo, "TRIGGER")
    cloudbuildBuilds = RelatedTo(GcpCloudbuildBuild, "BUILDS")    
    github_repos = RelatedTo(GithubRepo, "IS_MIRROR")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
