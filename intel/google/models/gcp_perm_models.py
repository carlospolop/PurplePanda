from typing import List
from py2neo.ogm import RelatedTo, RelatedFrom, Label, Property

from core.db.customogm import CustomOGM
from core.models.models import RepoPpalPrivesc


class GcpResource(RepoPpalPrivesc):
    __primarylabel__ = "GcpResource"

    perms = RelatedFrom("GcpPrincipal", "HAS_ROLE")
    basic_roles = RelatedFrom("GcpProject", "HAS_BASIC_ROLES")
    privesc = RelatedFrom("GcpPrincipal", "PRIVESC")
    potential_privesc = RelatedFrom("GcpPrincipal", "POTENTIAL_PRIVESC")

    resource = Label(name="GcpResource")

    def get_basic_viewers(self):
        return self.get_by_role("roles/viewer")

    def get_basic_editors(self):
        return self.get_by_role("roles/editor")
    
    def get_basic_owners(self):
        return self.get_by_role("roles/owner")

    def get_by_role(self, role):
        from intel.google.models.gcp_user_account import GcpUserAccount
        from intel.google.models.gcp_organization import GcpOrganization
        from intel.google.models.gcp_group import GcpGroup
        from intel.google.models.gcp_service_account import GcpServiceAccount
        objs = self.get_by_relation("HAS_ROLE", where=f'"{role}" in _.roles')
        return objs
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = True


class GcpPrincipal(CustomOGM):
    __primarylabel__ = "GcpPrincipal"

    interesting_permissions = Property()

    has_perm = RelatedTo(GcpResource, "HAS_ROLE")
    privesc = RelatedTo(GcpResource, "PRIVESC")
    privesc_helper = RelatedTo(GcpResource, "PRIVESC_HELPER")

    principal = Label(name="GcpPrincipal")

    @classmethod
    def get_all_principals_with_role(cls, role):
        from intel.google.models.gcp_user_account import GcpUserAccount
        from intel.google.models.gcp_organization import GcpOrganization
        from intel.google.models.gcp_group import GcpGroup
        from intel.google.models.gcp_service_account import GcpServiceAccount
        objs = cls.get_all_with_relation("HAS_ROLE", where=f'"{role}" in _.roles', get_only_start=True)
        return objs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.principal = True

class GcpRunningSA():

    running_gcp_service_accounts = RelatedFrom("GcpServiceAccount", "RUN_IN")

    def relate_sa(self, sa_email: str, scopes: List[str]):
        from intel.google.models.gcp_service_account import GcpServiceAccount
        sa_obj: GcpServiceAccount = GcpServiceAccount(email=sa_email).save()
        
        self.running_gcp_service_accounts.update(sa_obj, scopes=scopes)
        self.save()