from py2neo.ogm import Property, RelatedTo, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource, GcpRunningSA
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.google.models.gcp_source_repos import GcpSourceRepo


class GcpCloudFunction(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpCloudFunction"
    __primarykey__ = "name"

    name = Property()
    description = Property()
    sourceArchiveUrl = Property()
    sourceUploadUrl = Property()
    httpsTrigger = Property()
    eventTrigger = Property()
    environmentVariables = Property()
    entryPoint = Property()
    runtime = Property()
    ingressSettings = Property()
    buildName = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    source_repo = RelatedTo(GcpSourceRepo, "USING_CODE")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
