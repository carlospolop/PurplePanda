from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_project import GcpProject
from core.models import PublicIP, PublicDomain


class GcpManagedZone(GcpResource):
    __primarylabel__ = "GcpManagedZone"
    __primarykey__ = "name"

    name = Property()
    dnsName = Property()
    displayName = Property()
    description = Property()
    id = Property()
    nameServers = Property()
    creationTime = Property()
    visibility = Property()
    networks = Property()

    projects = RelatedFrom(GcpProject, "PART_OF")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpResourceRecord(GcpResource):
    __primarylabel__ = "GcpResourceRecord"
    __primarykey__ = "name"

    name = Property()
    type = Property()
    ttl = Property()
    rrdatas = Property()
    signatureRrdatas = Property()

    projects = RelatedFrom(GcpProject, "PART_OF")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True