from py2neo.ogm import Property, Label, RelatedFrom

from core.db.customogm import CustomOGM
from intel.google.models.gcp_service_account import GcpServiceAccount

class GcpApiKey(CustomOGM):
    __primarylabel__ = "GcpApiKey"
    __primarykey__ = "name"

    name = Property()
    validAfterTime = Property()
    validBeforeTime = Property()
    keyAlgorithm = Property()
    keyOrigin = Property()
    keyType = Property()

    service_accounts = RelatedFrom(GcpServiceAccount, "HAS_KEY")

    gcp = Label(name="Gcp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True
