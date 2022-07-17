import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_storage import GcpStorage, GcpFile

class DiscStorage(GcpDisc):
    resource = 'storage'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the storage buckets from each project discovered.

        This module will create the storage objects and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_storages, __name__.split(".")[-1])


    def _disc_storages(self, p_obj:GcpProject):
        """Discover all the buckets of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.buckets()#.list(project=project_name.split("/")[1])
        storages: List[dict] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_name.split("/")[1]})
        for storage in storages:
            storage_obj: GcpStorage = GcpStorage(
                name = storage["name"],
                selfLink = storage.get("selfLink", ""),
                storageClass = storage.get("storageClass", ""),
                rpo = storage.get("rpo", ""),
                location = storage.get("location", ""),
                publicAccessPrevention = storage["iamConfiguration"].get("publicAccessPrevention","") if "iamConfiguration" in storage else "",
                bucketPolicyOnly = storage["iamConfiguration"]["bucketPolicyOnly"].get("enabled",False) if "iamConfiguration" in storage and "bucketPolicyOnly" in storage["iamConfiguration"] else False,
                uniformBucketLevelAccess = storage["iamConfiguration"]["uniformBucketLevelAccess"].get("enabled",False) if "iamConfiguration" in storage and "uniformBucketLevelAccess" in storage["iamConfiguration"] else False,
            ).save()
            storage_obj.projects.update(p_obj)
            storage_obj.save()

            self.get_iam_policy(storage_obj, self.service.buckets(), storage_obj.name)

            self._disc_files(p_obj, storage_obj)

    def _disc_files(self, p_obj:GcpProject, storage_obj:GcpStorage):
        """Discover all the files of a storage bucket"""

        updated_contains_images = False
        updated_contains_tfstates = False

        http_prep = self.service.objects()
        files: List[dict] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"bucket": storage_obj.name})
        for file in files:
            file_obj = GcpFile(
                name = file["id"],
                selfLink = file.get("selfLink", ""),
                contentType = file.get("contentType", ""),
                storageClass = file.get("storageClass", ""),
                size = file.get("size", ""),
                md5Hash = file.get("md5Hash", ""),
                timeCreated = file.get("timeCreated", ""),
                updated = file.get("updated", ""),
            ).save()
            file_obj.storages.update(p_obj)
            file_obj.save()

            if file["name"].startswith("containers/images/") and not updated_contains_images:
                storage_obj.contains_images = True
                storage_obj.save()
                updated_contains_images = True
            
            if ".tfstate" in file["name"] and not updated_contains_tfstates:
                storage_obj.contains_tfstates = True
                storage_obj.save()
                updated_contains_tfstates = True
            

