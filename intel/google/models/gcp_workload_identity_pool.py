from py2neo.ogm import Property, Label

from intel.google.models.gcp_perm_models import GcpPrincipal

class GcpWorkloadIdentityPool(GcpPrincipal):
    __primarylabel__ = "GcpWorkloadIdentityPool"
    __primarykey__ = "name"

    name = Property()
    project_number = Property()
    pool_id = Property()
    final_part = Property()

    gcp = Label(name="Gcp")

    def __init__(self, name, *args, **kwargs):
        kwargs["name"] = name

        if "/projects/" in name:
            name_part = name.split("/projects/")[1]
            kwargs["project_number"] = name_part.split("/")[0]
        
        if "/workloadIdentityPools/" in name:
            name_part = name.split("/workloadIdentityPools/")[1]
            kwargs["pool_id"] = name_part.split("/")[0]
            kwargs["final_part"] = name.split(f"/workloadIdentityPools/{kwargs['pool_id']}/")[1]
        
        elif "/workforcePools/" in name:
            name_part = name.split("/workforcePools/")[1]
            kwargs["pool_id"] = name_part.split("/")[0]
            kwargs["final_part"] = name.split(f"/workforcePools/{kwargs['pool_id']}/")[1]

        super().__init__(*args, **kwargs)
        self.gcp = True