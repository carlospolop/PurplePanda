import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_cluster import GcpCluster, GcpNodePool
from intel.google.models.gcp_compute import GcpSubnetwork


class DiscClusters(GcpDisc):
    resource = 'container'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the composer resources from each project discovered.

        This module will create the composer resources objects and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_clusters, __name__.split(".")[-1])


    def _disc_clusters(self, p_obj:GcpProject):
        """Discover all the clusters from the given project"""
                
        http_prep = self.service.projects().locations().clusters()#.list(parent=p_obj.name+"/locations/-")
        clusters: List[str] = self.execute_http_req(http_prep, "clusters", list_kwargs={"parent": p_obj.name+"/locations/-"})

        for cluster in clusters:
            cluster_nodeConfig = cluster.get("nodeConfig", {})
            cluster_nodeConfig_metadata = cluster_nodeConfig.get("metadata", {})
            cluster_nodeConfig_shiled = cluster_nodeConfig.get("shieldedInstanceConfig", {})
            privateClusterConfig = cluster.get("privateClusterConfig", {})

            cluster_obj: GcpCluster = GcpCluster(
                name = cluster["name"],
                id = cluster["id"],
                node_machineTye = cluster_nodeConfig.get("machineType", ""),
                node_diskSizeGb = cluster_nodeConfig.get("diskSizeGb", ""),
                node_serialPortLoggingEnable = cluster_nodeConfig_metadata.get("serial-port-logging-enable", False),
                node_disableLegacyEndpoints = cluster_nodeConfig_metadata.get("disable-legacy-endpoints", False),
                node_VmDnsSetting = cluster_nodeConfig_metadata.get("VmDnsSetting", ""),
                node_imageType = cluster_nodeConfig.get("imageType", ""),
                node_diskType = cluster_nodeConfig.get("diskType", ""),
                node_enableSecureBoot = cluster_nodeConfig_shiled.get("enableSecureBoot", ""),
                node_enableIntegrityMonitoring = cluster_nodeConfig_shiled.get("enableIntegrityMonitoring", ""),
                locations = cluster.get("locations", ""),
                masterAuthorizedNetworksConfig = cluster["masterAuthorizedNetworksConfig"].get("enabled", False) if "masterAuthorizedNetworksConfig" in cluster else False,
                maxPodsPerNode = cluster["defaultMaxPodsConstraint"].get("maxPodsPerNode", False) if "defaultMaxPodsConstraint" in cluster else "",
                enablePrivateNodes = privateClusterConfig.get("enablePrivateNodes", False),
                enablePrivateEndpoint = privateClusterConfig.get("enablePrivateEndpoint", False),
                masterIpv4CidrBlock = privateClusterConfig.get("masterIpv4CidrBlock", ""),
                privateEndpoint = privateClusterConfig.get("privateEndpoint", ""),
                publicEndpoint = privateClusterConfig.get("publicEndpoint", ""),
                peeringName = privateClusterConfig.get("peeringName", ""),
                databaseEncryption = cluster["databaseEncryption"].get("state", "") if "databaseEncryption" in cluster else "",
                shieldedNodes = cluster["shieldedNodes"].get("enabled", False) if "shieldedNodes" in cluster else "",
                releaseChannel = cluster["releaseChannel"].get("channel", "") if "releaseChannel" in cluster else "",
                source = cluster.get("selfLink", ""),
                status = cluster.get("status", ""),
                currentMasterVersion = cluster.get("currentMasterVersion", ""),
                currentNodeCount = cluster.get("currentNodeCount", ""),
            ).save()
            cluster_obj.projects.update(p_obj, zone=cluster.get("location", cluster.get("zone", "")))
            cluster_obj.save()

            # Relate with subnetwork
            if cluster.get("subnetwork"):
                subnet_obj: GcpSubnetwork = GcpSubnetwork.get_by_name(name=cluster["subnetwork"]).save()
                subnet_obj.clusters.update(cluster_obj)
                subnet_obj.save()

            # Realate with running SA
            sa_email = cluster_nodeConfig.get("serviceAccount", f"{p_obj.projectNumber}-compute@developer.gserviceaccount.com")
            cluster_obj.relate_sa(sa_email, cluster_nodeConfig["oauthScopes"])

            # Relate with running nodepools
            if cluster.get("nodePools"):
                for nodepool in cluster.get("nodePools"):
                    nodeconfig = nodepool.get("config", {})
                    npool_obj = GcpNodePool(
                        name = nodepool["name"],
                        node_machineTye = nodeconfig.get("machineType", "") if "config" in nodepool else "",
                        node_diskSizeGb = nodeconfig.get("diskSizeGb", "") if "config" in nodepool else "",
                        node_serialPortLoggingEnable = nodeconfig["metadata"].get("serial-port-logging-enable", False) if "metadata" in nodeconfig else "",
                        node_disableLegacyEndpoints = nodeconfig["metadata"].get("disable-legacy-endpoints", False) if "metadata" in nodeconfig else False,
                        node_VmDnsSetting = nodeconfig["metadata"].get("VmDnsSetting", "") if "metadata" in nodeconfig else "",
                        node_imageType = nodeconfig.get("imageType", "") if "config" in nodepool else "",
                        node_diskType = nodeconfig.get("diskType", "") if "config" in nodepool else "",
                        node_enableSecureBoot = nodeconfig["shieldedInstanceConfig"].get("enableSecureBoot", False) if "shieldedInstanceConfig" in nodeconfig else False,
                        node_enableIntegrityMonitoring = nodeconfig["shieldedInstanceConfig"].get("enableIntegrityMonitoring", False) if "shieldedInstanceConfig" in nodeconfig else False,
                        initialNodeCount = nodepool.get("initialNodeCount", ""),
                        autoUpgrade = nodepool["management"].get("autoUpgrade", "") if "management" in nodepool else "",
                        autoRepair = nodepool["management"].get("autoRepair", "") if "management" in nodepool else "",
                        maxPodsPerNode = nodepool["maxPodsConstraint"].get("maxPodsPerNode", "") if "maxPodsConstraint" in nodepool else "",
                        podIpv4CidrSize = nodepool.get("podIpv4CidrSize", ""),
                        locations = nodepool.get("locations", ""),
                        source = nodepool.get("selfLink", ""),
                        version = nodepool.get("version", ""),
                        status = nodepool.get("status", ""),
                    ).save()
                    npool_obj.clusters.update(cluster_obj)
                    npool_obj.save()
