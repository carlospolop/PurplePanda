from py2neo.ogm import Property, Label, RelatedFrom

from intel.google.models.gcp_perm_models import GcpResource


class GcpOrgPolicy(GcpResource):
    __primarylabel__ = "GcpOrgPolicy"
    __primarykey__ = "name"

    name = Property()
    enforced = Property()
    updateTime = Property()
    version = Property()
    allowedValues = Property()
    deniedValues = Property()
    allValues = Property()
    suggestedValues = Property()
    inheritFromParent = Property()

    organizations = RelatedFrom("GcpOrganization", "HAS_POLICY")
    folders = RelatedFrom("GcpFolder", "HAS_POLICY")
    projects = RelatedFrom("GcpProject", "HAS_POLICY")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
