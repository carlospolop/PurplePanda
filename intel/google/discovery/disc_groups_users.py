import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_group import GcpGroup
from intel.google.models.gcp_user_account import GcpUserAccount
from intel.google.models.gcp_workspace import GcpWorkspace


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

        workspaces: List[GcpWorkspace] = GcpWorkspace.get_all()

        for w_obj in workspaces:
            customer_id: str = w_obj.name

            http_prep = self.service.groups()  # .list(pageSize=page_size, parent=customer_id, view=view)

            groups: list = self.execute_http_req(http_prep, "groups",
                                                 list_kwargs={"pageSize": page_size, "parent": customer_id,
                                                              "view": view})
            self._disc_loop(groups, self._disc_group, __name__.split(".")[-1], **{"w_obj": w_obj})

    def _disc_group(self, g, **kwargs):
        """Discover each group of the workspace"""

        w_obj: GcpWorkspace = kwargs["w_obj"]
        g_obj: GcpGroup = GcpGroup(
            name=g["name"],
            displayName=g.get("displayName", ""),
            email=g["groupKey"]["id"],
            description=g.get("description", "")
        ).save()
        self._proc_group(g_obj, w_obj)

    def _proc_group(self, g_obj: GcpGroup, w_obj: GcpWorkspace):
        # groups_to_ignore = ['abuse@', 'postmaster@'] # these are hidden groups on all Google Workspaces that you can't edit
        # if any(g_obj.email.startswith(ignore) for ignore in groups_to_ignore):
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

    def _proc_member(self, member: dict, g_obj: GcpGroup, w_obj: GcpWorkspace):
        name: str = member["member"]
        try:
            email: str = member["preferredMemberKey"][0]["id"]
        except Exception:
            email: str = member["member"].split("/")[1] + "@" + "".join(g_obj.email.split("@")[1:])

        roles: List[str] = [r["role"] for r in member["roles"]]

        if name.startswith("users/"):
            u_obj: GcpUserAccount = GcpUserAccount(
                name=name,
                email=email
            ).save()

            self._extracted_from__proc_member_16(u_obj, g_obj, roles, w_obj)
        elif name.startswith("groups/"):
            g2_obj: GcpGroup = GcpGroup(
                name=name,
                email=email
            ).save()

            self._extracted_from__proc_member_16(g2_obj, g_obj, roles, w_obj)
        else:
            self.logger.error(f"Group member {email} using unexpected type {name} with roles {roles}")

    # TODO Rename this here and in `_proc_member`
    def _extracted_from__proc_member_16(self, arg0, g_obj, roles, w_obj):
        arg0.groups.update(g_obj, roles=roles)
        arg0.workspaces.update(w_obj)
        arg0.save()
