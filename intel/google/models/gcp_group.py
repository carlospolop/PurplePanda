from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.gcp_workspace import GcpWorkspace
from intel.google.models.gcp_perm_models import GcpPrincipal


class GcpGroup(GcpPrincipal):
    __primarylabel__ = "GcpGroup"
    __primarykey__ = "email"

    name = Property()
    displayName = Property()
    description = Property()
    email = Property()

    groups = RelatedTo("GcpGroup", "MEMBER_OF")
    users = RelatedFrom("GcpUser", "MEMBER_OF")
    workspaces = RelatedTo(GcpWorkspace, "PART_OF")
    service_accounts = RelatedFrom("GcpServiceAccount", "MEMBER_OF")

    gcp = Label(name="Gcp")
    principal = Label(name="GcpPrincipal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
