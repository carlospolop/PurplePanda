from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_compute import GcpNetwork
from intel.google.models.gcp_perm_models import GcpRunningSA
from intel.google.models.gcp_service_account import GcpServiceAccount # This needs to be imported!

from core.models import PublicIP


class GcpSqlInstance(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpSqlInstance"
    __primarykey__ = "name"

    name = Property()
    state = Property()
    databaseVersion = Property()
    backendType = Property()
    selfLink = Property()
    connectionName = Property()
    region = Property()
    databaseInstalledVersion = Property()
    createTime = Property()
    ipAddresses = Property()

    projects = RelatedFrom(GcpProject, "PART_OF")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    networks = RelatedTo(GcpNetwork, "CONNECTED")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpSqlDB(GcpResource, GcpRunningSA):
    __primarylabel__ = "GcpSqlDB"
    __primarykey__ = "name"

    name = Property()
    selfLink = Property()

    projects = RelatedFrom(GcpProject, "PART_OF")
    instances = RelatedTo(GcpSqlInstance, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True