import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.google_group import GoogleGroup
from intel.google.models.gcp_user_account import GcpUserAccount
from intel.google.models.google_workspace import GoogleWorkspace

class DiscGroupsUsers(GcpDisc):
    resource = 'cloudidentity'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the groups from each Workspace account discovered.
        
        This module will create the groups and relate them with the parent workspace.
        It will also get the members of each group (groups and users) and relate them
        and also relate the new users/groups with the parent workspace.
        """

        page_size: int = 500
        view: str = "FULL"

        workspaces: List[GoogleWorkspace] = GoogleWorkspace.get_all()

        for w_obj in workspaces:
            customer_id: str = w_obj.name

            http_prep = self.service.groups()#.list(pageSize=page_size, parent=customer_id, view=view)

            groups: list = self.execute_http_req(http_prep, "groups", list_kwargs={"pageSize": page_size, "parent": customer_id, "view": view})
            self._disc_loop(groups, self._disc_group, __name__.split(".")[-1], **{"w_obj": w_obj})


    def _disc_group(self, g, **kwargs):
        """Discover each group of the workspace"""
        
        w_obj: GoogleWorkspace = kwargs["w_obj"]
        g_obj: GoogleGroup = GoogleGroup(
            name = g["name"],
            displayName = g.get("displayName", ""),
            email = g["groupKey"]["id"],
            description = g.get("description", "")
        ).save()
        self._proc_group(g_obj, w_obj)
                
    
    def _proc_group(self, g_obj: GoogleGroup, w_obj: GoogleWorkspace):
        #groups_to_ignore = ['abuse@', 'postmaster@'] # these are hidden groups on all Google Workspaces that you can't edit
        #if any(g_obj.email.startswith(ignore) for ignore in groups_to_ignore):
        #    return

        g_obj.workspaces.update(w_obj)
        g_obj.save()

        page_size: int = 500
        http_prep = self.service.groups().memberships().searchTransitiveMemberships(
                                                                            parent=g_obj.name,
                                                                            pageSize=page_size,
                                                                            )
        memberships: list = self.execute_http_req(http_prep, "memberships", disable_warn=True)
        for m in memberships:
            self._proc_member(m, g_obj, w_obj)
            
    
    def _proc_member(self, member: dict, g_obj: GoogleGroup, w_obj: GoogleWorkspace):
        name: str = member["member"]
        email: str = member["preferredMemberKey"][0]["id"]
        roles: List[str] = [r["role"] for r in member["roles"]]

        if name.startswith("users/"):
            u_obj: GcpUserAccount = GcpUserAccount(
                name = name,
                email = email
            ).save()
            
            u_obj.groups.update(g_obj, roles=roles)
            u_obj.workspaces.update(w_obj)
            u_obj.save()
        
        elif name.startswith("groups/"):
            g2_obj: GoogleGroup = GoogleGroup(
                name = name,
                email = email
            ).save()
            
            g2_obj.groups.update(g_obj, roles=roles)
            g2_obj.workspaces.update(w_obj)
            g2_obj.save()
        
        else:
            self.logger.error(f"Group member {email} using unexpected type {name} with roles {roles}")
