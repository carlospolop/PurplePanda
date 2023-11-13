import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_compute import GcpNetwork, GcpSubnetwork, GcpFirewallRule


class DiscComputeNetworks(GcpDisc):
    resource = 'compute'
    version = 'v1'
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the networks from each project discovered.

        This module will create the network objects and relate them with the parent project, subnetworks, peers and fw rules.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_networks, __name__.split(".")[-1])

    def _disc_networks(self, p_obj: GcpProject):
        """Discover all the networks of a project"""

        project_id: str = p_obj.name.split("/")[1]
        http_prep = self.service.networks()  # .list(project=project_id)
        networks: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True,
                                                    list_kwargs={"project": project_id})

        for network in networks:
            network_obj = GcpNetwork(
                name=f'{p_obj.name}/global/networks/{network["name"]}',
                description=network.get("description", ""),
                selfLink=network["selfLink"],
                autoCreateSubnetworks=network.get("autoCreateSubnetworks", False),
                routingMode=network["routingConfig"].get("routingMode", "") if "routingConfig" in network else ""
            ).save()
            network_obj.projects.update(p_obj)
            network_obj.save()

            self._get_firewall(network_obj, project_id)

            if network.get("peerings"):
                for peering in network.get("peerings"):
                    network2_obj: GcpNetwork = GcpNetwork(
                        name="projects/" + peering["network"].split("projects/")[-1],
                        selfLink=peering["network"]
                    ).save()

                    network2_obj.networks.update(network_obj,
                                                 name=peering["name"],
                                                 state=peering.get("state", ""),
                                                 stateDetails=peering.get("stateDetails", ""),
                                                 autoCreateRoutes=peering.get("autoCreateRoutes", False),
                                                 exportCustomRoutes=peering.get("exportCustomRoutes", False),
                                                 importCustomRoutes=peering.get("importCustomRoutes", False),
                                                 exchangeSubnetRoutes=peering.get("exchangeSubnetRoutes", False),
                                                 exportSubnetRoutesWithPublicIp=peering.get(
                                                     "exportSubnetRoutesWithPublicIp", False),
                                                 importSubnetRoutesWithPublicIp=peering.get(
                                                     "importSubnetRoutesWithPublicIp", False),
                                                 )
                    network2_obj.save()

            if network.get("subnetworks"):
                for subnet in network.get("subnetworks"):
                    subnet_obj: GcpSubnetwork = GcpSubnetwork(
                        name="projects/" + subnet.split("projects/")[-1],
                        selfLink=subnet
                    ).save()
                    subnet_obj.parent_network.update(network_obj)
                    subnet_obj.save()

    def _get_firewall(self, network_obj, project_id):
        http_prep = self.service.networks().getEffectiveFirewalls(network=network_obj.name.split("/")[-1],
                                                                  project=project_id)
        firewalls: List[str] = self.execute_http_req(http_prep, "firewalls", disable_warn=True)

        for fw in firewalls:
            fw_obj: GcpFirewallRule = GcpFirewallRule(
                name="projects/" + fw["selfLink"].split("projects/")[-1],
                description=fw.get("description", ""),
                direction=fw.get("direction", ""),
                disabled=fw.get("disabled", False),
                logEnabled=fw["logConfig"].get("enabled", False) if "logConfig" in fw else False,
                priority=fw.get("priority", ""),
                selfLink=fw.get("selfLink", ""),
                sourceRanges=fw.get("sourceRanges", []),
                targetTags=fw.get("targetTags", []),
                allowed=[f"{proto['IPProtocol']}:" + (",".join(proto['ports']) if 'ports' in proto else "*") for proto
                         in fw.get("allowed", [])],
                denied=[f"{proto['IPProtocol']}:" + (",".join(proto['ports']) if 'ports' in proto else "*") for proto in
                        fw.get("denied", [])],
            ).save()
            fw_obj.networks.update(network_obj)
            fw_obj.save()
