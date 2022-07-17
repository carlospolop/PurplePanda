from py2neo.ogm import Property, Label, RelatedFrom

from core.db.customogm import CustomOGM
from intel.google.models.gcp_organization import GcpOrganization


class GcpWorkspace(CustomOGM):
    __primarylabel__ = "GcpWorkspace"
    __primarykey__ = "name"

    name = Property()

    organisations = RelatedFrom(GcpOrganization, "PART_OF")
    groups = RelatedFrom("GcpGroup", "PART_OF")
    users = RelatedFrom("GcpUser", "PART_OF")

    gcp = Label(name="Gcp")

    def __init__(self, name, *args, **kwargs):
        if not name.startswith("customers/"):
            kwargs["name"] = f"customers/{name}"
        else:
            kwargs["name"] = name

        super().__init__(*args, **kwargs)

        self.gcp = True
