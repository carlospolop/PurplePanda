from py2neo.ogm import Property, Label, RelatedTo

from intel.google.models.google_workspace import GoogleWorkspace
from intel.google.models.gcp_perm_models import GcpPrincipal
from intel.google.models.google_group import GoogleGroup


class GcpUserAccount(GcpPrincipal):
    __primarylabel__ = "GcpUserAccount"
    __primarykey__ = "email"

    name = Property()
    email = Property()

    groups = RelatedTo(GoogleGroup, "MEMBER_OF")
    workspaces = RelatedTo(GoogleWorkspace, "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
