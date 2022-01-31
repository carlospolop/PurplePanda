from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_perm_models import GcpResource
from intel.google.models.gcp_project import GcpProject


class GcpSecret(GcpResource):
    __primarylabel__ = "GcpSecret"
    __primarykey__ = "name"

    name = Property()
    createTime = Property()

    projects = RelatedFrom(GcpProject, "PART_OF")
    versions = RelatedTo("GcpSecretVersion", "HAS_VERSION")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpSecretVersion(GcpResource):
    __primarylabel__ = "GcpSecretVersion"
    __primarykey__ = "name"

    name = Property()
    value = Property()

    secrets = RelatedFrom(GcpSecret, "HAS_VERSION")
    cloudbuildTriggers = RelatedFrom("GcpCloudbuildTrigger", "TRIGGER")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
