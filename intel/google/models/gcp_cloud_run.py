from py2neo.ogm import Property, RelatedTo, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource, GcpRunningSA
from intel.google.models.gcp_service_account import GcpServiceAccount


class GcpCloudRunSvc(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpCloudRunSvc"
    __primarykey__ = "name"

    name = Property()
    displayName = Property()
    namespace = Property()
    selfLink = Property()
    uid = Property()
    creator = Property()
    lastModifier = Property()
    user_image = Property()
    containers = Property()
    ports = Property()
    url = Property()
    latestReadyRevisionName = Property()
    latestCreatedRevisionName = Property()

    projects = RelatedTo(GcpProject, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
