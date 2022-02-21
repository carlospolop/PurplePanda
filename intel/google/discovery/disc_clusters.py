import logging
import json
import subprocess
import tempfile
import os
from typing import List
from urllib.parse import urlparse
from base64 import b64encode
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_cluster import GcpCluster, GcpNodePool
from intel.google.models.gcp_compute import GcpSubnetwork
from core.models.models import PublicIP
from intel.google.models.gcp_kms import GcpKMSKey
from intel.k8s.purplepanda_k8s import PurplePandaK8s


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
            self.save_cluster(cluster, p_obj)
    
    
    def save_cluster(self, cluster, p_obj:GcpProject):
        """Save the Given GCP cluster"""

        cluster_masterauth = cluster.get("masterAuth", {})
        cluster_nodeConfig = cluster.get("nodeConfig", {})
        cluster_privateClusterConfig = cluster.get("privateClusterConfig", {})
        cluster_databaseEncryption = cluster["databaseEncryption"]

        cluster_nodeConfig_metadata = cluster_nodeConfig.get("metadata", {})
        cluster_nodeConfig_shiled = cluster_nodeConfig.get("shieldedInstanceConfig", {})

        cluster_obj: GcpCluster = GcpCluster(
            name = cluster["name"],
            id = cluster["id"],
            description = cluster.get("description", ""),
            initialNodeCount = cluster.get("initialNodeCount", ""),
            loggingService = cluster.get("loggingService", ""),
            monitoringService = cluster.get("monitoringService", ""),
            locations = cluster.get("locations", ""),
            enableKubernetesAlpha = cluster.get("enableKubernetesAlpha", False),
            resourceLabels = json.dumps(cluster.get("resourceLabels", {})),
            labelFingerprint = cluster.get("labelFingerprint", ""),
            selfLink = cluster.get("selfLink", ""),
            endpoint = cluster.get("endpoint", ""),
            initialClusterVersion = cluster.get("initialClusterVersion", ""),
            currentMasterVersion = cluster.get("currentMasterVersion", ""),
            currentNodeCount = cluster.get("currentNodeCount", ""),
            status = cluster.get("status", ""),
            nodeIpv4CidrSize = cluster.get("nodeIpv4CidrSize", ""),
            servicesIpv4Cidr = cluster.get("servicesIpv4Cidr", ""),
            expireTime = cluster.get("expireTime", ""),
            location = cluster.get("location", ""),
            enableTpu = cluster.get("enableTpu", False),
            tpuIpv4CidrBlock = cluster.get("tpuIpv4CidrBlock", ""),
            autopilot = cluster.get("autopilot", {}).get("enabled", False),

            master_username = cluster_masterauth.get("username", ""),
            master_password = cluster_masterauth.get("password", ""),
            clusterCaCertificate = cluster_masterauth.get("clusterCaCertificate", ""),
            clientCertificate = cluster_masterauth.get("clientCertificate", ""),
            clientKey = cluster_masterauth.get("clientKey", ""),

            addonsConfig = json.dumps(cluster.get("addonsConfig", {})),

            masterAuthorizedNetworksConfig = cluster.get("masterAuthorizedNetworksConfig", {}).get("enabled", False),

            binaryAuthorization = cluster.get("binaryAuthorization", {}).get("enabled", False),

            databaseEncryption = cluster_databaseEncryption.get("state", ""),

            enablePrivateNodes = cluster_privateClusterConfig.get("cluster_privateClusterConfig", False), # If True, it's a private cluster
            enablePrivateEndpoint = cluster_privateClusterConfig.get("enablePrivateEndpoint", False),
            masterIpv4CidrBlock = cluster_privateClusterConfig.get("masterIpv4CidrBlock", ""),
            privateEndpoint = cluster_privateClusterConfig.get("privateEndpoint", ""),
            publicEndpoint = cluster_privateClusterConfig.get("publicEndpoint", ""),
            peeringName = cluster_privateClusterConfig.get("peeringName", ""),
            masterGlobalAccessConfig = cluster_privateClusterConfig.get("masterGlobalAccessConfig", {}).get("enabled", False),

            node_machineTye = cluster_nodeConfig.get("machineType", ""),
            node_diskSizeGb = cluster_nodeConfig.get("diskSizeGb", ""),
            node_serialPortLoggingEnable = cluster_nodeConfig_metadata.get("serial-port-logging-enable", False),
            node_disableLegacyEndpoints = cluster_nodeConfig_metadata.get("disable-legacy-endpoints", False),
            node_VmDnsSetting = cluster_nodeConfig_metadata.get("VmDnsSetting", ""),
            node_imageType = cluster_nodeConfig.get("imageType", ""),
            node_diskType = cluster_nodeConfig.get("diskType", ""),
            node_enableSecureBoot = cluster_nodeConfig_shiled.get("enableSecureBoot", ""),
            node_enableIntegrityMonitoring = cluster_nodeConfig_shiled.get("enableIntegrityMonitoring", ""),
                        
            maxPodsPerNode = cluster["defaultMaxPodsConstraint"].get("maxPodsPerNode", False) if "defaultMaxPodsConstraint" in cluster else "",
            
            shieldedNodes = cluster["shieldedNodes"].get("enabled", False) if "shieldedNodes" in cluster else "",
            releaseChannel = cluster["releaseChannel"].get("channel", "") if "releaseChannel" in cluster else "",
        ).save()
        cluster_obj.projects.update(p_obj, zone=cluster.get("location", cluster.get("zone", "")))
        cluster_obj.save()

        # Relate with subnetwork
        if cluster.get("subnetwork"):
            subnet_obj: GcpSubnetwork = GcpSubnetwork.get_by_name(name=cluster["subnetwork"]).save()
            subnet_obj.clusters.update(cluster_obj)
            subnet_obj.save()
        else:
            self.logger.warning(f"Cluster {cluster['name']} found without subnetwork")
        
        # Potential public IP
        if cluster.get("endpoint"):
            uparsed = urlparse(cluster.get("endpoint"))
            hostname = uparsed.hostname if uparsed.hostname else cluster.get("endpoint")
            ip_obj = PublicIP(ip=hostname).save()
            cluster_obj.public_ips.update(ip_obj)
        else:
            self.logger.warning(f"Cluster {cluster['name']} found without endpoint")
        
        # Public IP
        if cluster_privateClusterConfig.get("publicEndpoint"):
            ip_obj = PublicIP(ip=cluster_privateClusterConfig.get("publicEndpoint")).save()
            cluster_obj.public_ips.update(ip_obj)
        
        # Potential KMS to encrypt K8s secrets (ETCD)
        kms_key_name = cluster_databaseEncryption.get("keyName")
        if kms_key_name:
            kmskey_obj: GcpKMSKey = GcpKMSKey(name=kms_key_name).save()
            cluster_obj.kmskeys.update(kmskey_obj)
            cluster_obj.save()
        
        sa_email = cluster_nodeConfig.get("serviceAccount", f"{p_obj.projectNumber}-compute@developer.gserviceaccount.com")
        cluster_obj.relate_sa(sa_email, cluster_nodeConfig["oauthScopes"])

        # Relate with running nodepools
        if cluster.get("nodePools"):
            for nodepool in cluster.get("nodePools"):
                self.save_node_pool(cluster_obj, nodepool, sa_email, cluster_nodeConfig["oauthScopes"])
        
        # Try to analize the cluster
        self.analyze_cluster(cluster_obj, p_obj)

    
    def save_node_pool(self, cluster_obj: GcpCluster, nodepool: dict, sa_email: str, oauthScopes: list):
        """Given the nodepool of a cluster, save it"""
        
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

        cluster_obj.relate_sa(sa_email, oauthScopes)
    
    def analyze_cluster(self, cluster_obj: GcpCluster, p_obj:GcpProject):
        """Having found a cluster, try to analyze it"""

        if not self.tool_exists("gcloud"):
            self.logger.error("Tool gcloud doesn't exist, I cannot analize internal K8s env")
            return
        
        with tempfile.NamedTemporaryFile() as tmp:
            env={"KUBECONFIG": tmp.name, "PATH": os.getenv("PATH")}
            try:
                out = subprocess.check_output(["gcloud", "container", "clusters", "get-credentials", "--project", p_obj.name.split("/")[1], "--zone", cluster_obj.location, cluster_obj.name], env=env, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Couldn't get K8s credentials from cluster {cluster_obj.name} in project {p_obj.name.split('/')[1]} and zone {cluster_obj.location}. Error: {e}")
                return

            tmp.read() # Need to read first
            if tmp.tell() <= 0:
                self.logger.info(f"Looks like you didn't have enough permissions to get the kubeconfig: {out}")
                return
            
            k8s_config = b64encode(f'k8s:\n- file_path: "{tmp.name}"'.encode())
            functions = []
            functions.append((PurplePandaK8s().discover, "kubernetes",
                {
                    "k8s_get_secret_values": self.gcp_get_secret_values,
                    "config": k8s_config,
                    "belongs_to": cluster_obj,
                    "cluster_id": cluster_obj.name
                }
            ))
            self.start_discovery(functions)
