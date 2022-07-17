from py2neo.ogm import Property, Label, RelatedTo

from intel.google.models.gcp_workspace import GcpWorkspace
from intel.google.models.gcp_perm_models import GcpPrincipal
from intel.google.models.gcp_group import GcpGroup


class GcpUserAccount(GcpPrincipal):
    __primarylabel__ = "GcpUserAccount"
    __primarykey__ = "email"

    name = Property()
    email = Property()

    groups = RelatedTo(GcpGroup, "MEMBER_OF")
    workspaces = RelatedTo(GcpWorkspace, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
