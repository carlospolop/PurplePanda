import logging
import json
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_compute import GcpSubnetwork, GcpNetwork
from intel.google.models.gcp_service_account import GcpServiceAccount

class DiscComputeSubnetworks(GcpDisc):
    resource = 'compute'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the subnetworks from each project discovered.

        This module will create the subnetwork objects and relate them with the parent project, iams and parent networks.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_subnetworks, __name__.split(".")[-1])


    def _disc_subnetworks(self, p_obj:GcpProject):
        """Discover all the subnetworks of a project"""
        
        project_id: str = p_obj.name.split("/")[1]
        http_prep = self.service.zones()#.list(project=project_id)
        locations: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_id})
        loc_names = set(["-".join(l["name"].split("-")[:-1]) for l in locations])

        for location in loc_names:
            http_prep = self.service.subnetworks()#.list(project=project_id, region=location)
            subnetworks: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_id, "region": location})
            
            for subnet in subnetworks:
                subnet_obj = GcpSubnetwork(
                    name = subnet["name"],
                    source = subnet["selfLink"],
                    ipCidrRange = subnet.get("ipCidrRange", ""),
                    gatewayAddress = subnet.get("gatewayAddress", ""),
                    privateIpGoogleAccess = subnet.get("privateIpGoogleAccess", False),
                    privateIpv6GoogleAccess = subnet.get("privateIpv6GoogleAccess", False),
                    purpose = subnet.get("purpose", ""),
                    stackType = subnet.get("stackType", ""),
                    logEnabled = subnet["logConfig"].get("enable", False) if "logConfig" in subnet else False,
                    secondaryIpRanges = [r.get("ipCidrRange", "") for r in subnet.get("secondaryIpRanges", [])]
                ).save()
                subnet_obj.projects.update(p_obj, zone=location)
                subnet_obj.save()

                self.get_iam_policy(subnet_obj, self.service.subnetworks(), subnet_obj.name, project=project_id, region=location)

                if subnet.get("network"):
                    network_obj: GcpNetwork = GcpNetwork(source=subnet["network"]).save()
                    network_obj.subnetworks.update(subnet_obj)
                    network_obj.save()
