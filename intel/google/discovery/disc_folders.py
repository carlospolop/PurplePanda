import logging
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_folder import GcpFolder
from intel.google.models.gcp_organization import GcpOrganization


class DiscFolders(GcpDisc):
    resource = 'cloudresourcemanager'
    version = 'v2'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the folders accesible by the active account.

        This module will relate folders with parent folder/organization.
        """

        prep_http = self.service.folders().search(body={})
        folders: List[str] = self.execute_http_req(prep_http, "folders")
        self._disc_loop(folders, self._disc_subnetworks, __name__.split(".")[-1])


    def _disc_subnetworks(self, f):
        """Discover each folder of the organization"""
        
        f_obj: GcpFolder = GcpFolder(
            name=f["name"],
            displayName=f.get("displayName", ""),
            lifecycleState=f.get("lifecycleState", "")
        ).save()
    
        parent: str = f["parent"]
        if parent.startswith("folders/"):
            f2: GcpFolder = GcpFolder(name=parent).save()
            f2.folders.update(f_obj)
            f2.save()
        
        elif parent.startswith("organizations/"):
            o: GcpOrganization = GcpOrganization.get_by_name(name=parent)
            
            # In case we couldn't initially enumerate the organization name and we found it now
            if not o:
                o: GcpOrganization = GcpOrganization(
                    name=parent,
                    domain="unknown",
                    lifecycleState=o.get("lifecycleState", "")
                ).save()
            
            o.folders.update(f_obj)
            o.save()
        
        else:
            self.logger.error(f"Folder {f['name']} with unexpected parent type {f['parent']}")
        
        self.get_iam_policy(f_obj, self.service.folders(), f_obj.name)
