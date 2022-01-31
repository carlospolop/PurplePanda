from py2neo.ogm import Property, Label, RelatedFrom, RelatedTo

from intel.google.models.google_workspace import GoogleWorkspace
from intel.google.models.gcp_perm_models import GcpPrincipal


class GoogleGroup(GcpPrincipal):
    __primarylabel__ = "GoogleGroup"
    __primarykey__ = "email"

    name = Property()
    displayName = Property()
    description = Property()
    email = Property()

    groups = RelatedTo("GoogleGroup", "MEMBER_OF")
    users = RelatedFrom("GcpUser", "MEMBER_OF")
    workspaces = RelatedTo(GoogleWorkspace, "PART_OF")
    service_accounts = RelatedFrom("GcpServiceAccount", "MEMBER_OF")

    gcp = Label(name="Gcp")
    principal = Label(name="GcpPrincipal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
