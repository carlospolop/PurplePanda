import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_cloud_run import GcpCloudRunSvc
from intel.google.models.gcp_service_account import GcpServiceAccount


class DiscCloudRun(GcpDisc):
    resource = 'run'
    version = 'v1'
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the cloud run from each project discovered.

        This module will create the cloud run and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_cloudrun, __name__.split(".")[-1])

    def _disc_cloudrun(self, p_obj: GcpProject):
        """Discover al the cloudruns of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().locations()  # .list(name=project_name)
        locations: List[str] = self.execute_http_req(http_prep, "locations", disable_warn=True,
                                                     list_kwargs={"name": project_name})
        for loc in locations:
            parent_cf_fullname: str = "projects/" + loc["name"]
            loc_name: str = loc["locationId"]
            http_prep = self.service.projects().locations().services()  # .list(parent=parent_cf_fullname)
            run_services: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True,
                                                            list_kwargs={"parent": parent_cf_fullname})

            for run_svc in run_services:
                metadata = run_svc["metadata"]
                annotations = metadata["annotations"]
                spec = run_svc["spec"]["template"]["spec"]
                containers_info = spec.get("containers", [])
                containers = [c["image"] for c in containers_info]
                ports = [p["containerPort"] for c in containers_info if c.get("ports") for p in c["ports"] if
                         p.get("containerPort")]
                status = run_svc["status"]

                run_obj = GcpCloudRunSvc(
                    name=f"{parent_cf_fullname}/services/{metadata['name']}",
                    displayName=metadata["name"],
                    namespace=metadata["namespace"],
                    selfLink=metadata["selfLink"],
                    uid=metadata["uid"],
                    creator=annotations.get("serving.knative.dev/creator", ""),
                    lastModifier=annotations.get(
                        "serving.knative.dev/lastModifier", ""
                    ),
                    user_image=annotations.get(
                        "client.knative.dev/user-image", ""
                    ),
                    containers=containers,
                    ports=ports,
                    url=status.get("url", ""),
                    latestReadyRevisionName=status.get(
                        "latestReadyRevisionName", ""
                    ),
                    latestCreatedRevisionName=status.get(
                        "latestCreatedRevisionName", ""
                    ),
                ).save()
                run_obj.projects.update(p_obj, zone=loc_name)
                run_obj.save()

                sa_email = spec.get("serviceAccountName",
                                    f"{p_obj.projectNumber}-compute@developer.gserviceaccount.com")
                run_obj.relate_sa(sa_email, [])

                self.get_iam_policy(run_obj, self.service.projects().locations().services(), run_obj.name)
