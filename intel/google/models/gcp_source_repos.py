from py2neo.ogm import Property, RelatedTo, Label, RelatedFrom
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpRunningSA
from intel.google.models.gcp_pubsub import GcpPubSubTopic
from intel.google.models.gcp_service_account import GcpServiceAccount
from core.models import CodeMirror

class GcpSourceRepo(CodeMirror, GcpRunningSA):
    __primarylabel__ = "GcpSourceRepo"
    __primarykey__ = "name"

    name = Property()
    url = Property()
    mirrorUrl = Property()
    mirrorWebhookId = Property()
    mirrorDeployKeyId = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    pubsubTopics = RelatedTo(GcpPubSubTopic, "TOPIC_PUBLISHER")
    cloudbuildBuild = RelatedFrom("GcpCloudbuildBuild", "HAS_SOURCE")
    cloud_functions = RelatedFrom("GcpCloudFunction", "USING_CODE")

    gcp = Label(name="Gcp")

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
