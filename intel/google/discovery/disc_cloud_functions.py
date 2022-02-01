import logging
import json
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models import GcpCloudFunction, GcpServiceAccount, GcpSourceRepo


class DiscCloudFunctions(GcpDisc):
    resource = 'cloudfunctions'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the cloud functions from each project discovered.

        This module will create the cloud functions and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_cloudfunction, __name__.split(".")[-1])
    

    def _disc_cloudfunction(self, p_obj:GcpProject):
        """Discover all the cloudfunctions of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().locations()#.list(name=project_name)
        locations: List[str] = self.execute_http_req(http_prep, "locations", disable_warn=True, list_kwargs={"name": project_name})
        for loc in locations:
            parent_cf_fullname: str = loc["name"]
            loc_name: str = loc["locationId"]
            http_prep = self.service.projects().locations().functions()#.list(parent=parent_cf_fullname)
            functions: List[str] = self.execute_http_req(http_prep, "functions", disable_warn=True, list_kwargs={"parent": parent_cf_fullname})
            
            for func in functions:
                cf_obj = GcpCloudFunction(
                    name = func["name"],
                    description = func.get("description", ""),
                    sourceArchiveUrl = func.get("sourceArchiveUrl", ""),
                    sourceUploadUrl = func.get("sourceUploadUrl", ""),
                    httpsTrigger = func["httpsTrigger"].get("url", "") if "httpsTrigger" in func else "",
                    eventTrigger = json.dumps(func["eventTrigger"]) if "eventTrigger" in func else "",
                    environmentVariables = json.dumps(func["environmentVariables"]) if "environmentVariables" in func else "",
                    entryPoint = func.get("entryPoint", ""),
                    runtime = func.get("runtime", ""),
                    ingressSettings = func.get("ingressSettings", ""),
                    buildName = func.get("buildName", "")
                ).save()
                cf_obj.projects.update(p_obj, zone=loc_name)
                cf_obj.save()

                project_id: str = p_obj.name.split("/")[1]
                sa_email = func.get("serviceAccountEmail", f"{project_id}@appspot.gserviceaccount.com")
                cf_obj.relate_sa(sa_email, [])

                source_repo = func.get("sourceRepository")
                if source_repo:
                    source_repo_name = "projects/" + "/".join(source_repo["url"].split("/projects/")[1].split("/")[:3])
                    sr_obj = GcpSourceRepo(name=source_repo_name).save()
                    cf_obj.source_repo.update(sr_obj)
                    cf_obj.save()

                self.get_iam_policy(cf_obj, self.service.projects().locations().functions(), cf_obj.name)
