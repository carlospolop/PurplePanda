import logging
import json
from typing import List

from intel.google.models.gcp_cluster import GcpCluster
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_compute import GcpComputeInstance, GcpComputeDisk, GcpSubnetwork
from core.models.models import PublicIP

class DiscComputeInstances(GcpDisc):
    resource = 'compute'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the compute instance from each project discovered.

        This module will create the compute objects and relate them with the parent project, subnetworks, iams, and disks.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_instances, __name__.split(".")[-1])


    def _disc_instances(self, p_obj:GcpProject):
        """Discover all the compute instances of a project"""

        project_id: str = p_obj.name.split("/")[1]
        http_prep = self.service.zones()#.list(project=project_id)
        locations: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_id})
        for loc in locations:
            location: str = loc["name"]
            http_prep = self.service.instances().list(project=project_id, zone=location)
            instances: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_id})
            
            for inst in instances:
                inst_obj = GcpComputeInstance(
                    name = inst["selfLink"],
                    displayName = inst["name"],
                    machineType = inst.get("machineType", ""),
                    status = inst.get("status", ""),
                    cpuPlatform = inst.get("cpuPlatform", ""),
                    startRestricted = inst.get("startRestricted", False),
                    deletionProtection = inst.get("deletionProtection", False),
                    enableSecureBoot = inst["shieldedInstanceConfig"].get("enableSecureBoot", False) if "shieldedInstanceConfig" in inst else False,
                    enableVtpm = inst["shieldedInstanceConfig"].get("enableVtpm", False) if "enableVtpm" in inst else "",
                    enableIntegrityMonitoring = inst["shieldedInstanceConfig"].get("enableIntegrityMonitoring", False) if "enableIntegrityMonitoring" in inst else False,
                    updateAutoLearnPolicy = inst["shieldedInstanceIntegrityPolicy"].get("updateAutoLearnPolicy", False) if "shieldedInstanceIntegrityPolicy" in inst else False,
                    metadata = json.dumps(inst.get("metadata", {}).get("items"))
                ).save()
                inst_obj.projects.update(p_obj, zone=location)
                inst_obj.save()

                if inst.get("metadata", {}).get("items"):
                    cluster_name = ""
                    inst_obj.metadata = str(inst["metadata"]["items"])

                    if "'cluster-name'" in str(inst["metadata"]["items"]):
                        cluster_name = str(inst["metadata"]["items"]).split("'cluster-name'")[1].split("'")[3]
                    
                    if "CLUSTER_NAME" in str(inst["metadata"]["items"]):
                        cluster_name = str(inst["metadata"]["items"]).split("CLUSTER_NAME: ")[1].split("\\n")[0]

                    if cluster_name:
                        cl_obj = GcpCluster(name=cluster_name).save()
                        inst_obj.clusters.update(cl_obj)
                        inst_obj.save()

                if inst.get("serviceAccounts"):
                    for sa in inst.get("serviceAccounts"):
                        inst_obj.relate_sa(sa["email"], sa["scopes"])

                self.get_iam_policy(inst_obj, self.service.instances(), inst_obj.name, project=project_id, zone=location)

                if inst.get("disks"):
                    for disk in inst.get("disks"):
                        disk_obj: GcpComputeDisk = GcpComputeDisk(
                            name = disk["source"].split("/")[-1],
                            source = disk["source"],
                            type = disk.get("type", ""),
                            mode = disk.get("mode", ""),
                            index = disk.get("index", ""),
                            boot = disk.get("boot", False),
                            autoDelete = disk.get("autoDelete", False),
                            interface = disk.get("interface", ""),
                            diskSizeGb = disk.get("diskSizeGb", ""),
                            guestOsFeatures = [g.get("type", "") for g in disk.get("guestOsFeatures", {})],
                        )
                        disk_obj.compute_instances.update(inst_obj)
                        disk_obj.save()

                        self.get_iam_policy(disk_obj, self.service.disks(), disk_obj.name, project=project_id, zone=location)

                if inst.get("networkInterfaces"):
                    for nic in inst.get("networkInterfaces"):
                        accessConfigs = nic.get("accessConfigs", [])
                        natIps = [elem["natIP"] for elem in accessConfigs if "natIP" in elem]
                        natIps += [elem["externalIpv6"] for elem in accessConfigs if "externalIpv6" in elem and not elem["externalIpv6"] in natIps]

                        subnet_obj: GcpSubnetwork = GcpSubnetwork(source=nic["subnetwork"]).save()

                        accessConfigsv6 = nic.get("accessConfigs", [])
                        natIpsv6 = [elem["natIP"] for elem in accessConfigsv6 if "natIP" in elem]
                        natIpsv6 += [elem["externalIpv6"] for elem in accessConfigs if "externalIpv6" in elem and not elem["externalIpv6"] in natIpsv6]
                        
                        subnet_obj.instances.update(inst_obj,
                            name = nic["name"], 
                            networkIP = nic.get("networkIP", ""),
                            stackType = nic.get("stackType", ""),
                            accessConfigs_types = [elem["type"] for elem in accessConfigs],
                            accessConfigs_names = [elem["name"] for elem in accessConfigs],
                            accessConfigs_natIPs = natIps,
                            accessConfigsv6_types = [elem["type"] for elem in accessConfigsv6],
                            accessConfigsv6_names = [elem["name"] for elem in accessConfigsv6],
                            accessConfigsv6_natIPs = natIpsv6,
                        )
                        subnet_obj.save()

                        for natIP in natIps:
                            ip_obj = PublicIP(name=natIP).save()
                            inst_obj.public_ips.update(ip_obj)
                        
                        for natIP in natIpsv6:
                            ip_obj = PublicIP(name=natIP).save()
                            inst_obj.public_ips.update(ip_obj)
                        
                        inst_obj.save()
