import logging
import json
import validators
from urllib.parse import urlparse
from typing import List, Union
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_composer import GcpComposerEnv, GcpOperation
from intel.google.models.gcp_cluster import GcpCluster
from intel.google.models.gcp_kms import GcpKMSKey
from intel.google.models.gcp_storage import GcpStorage
from intel.google.info.regions import gcp_regions
from core.models import PublicIP, PublicDomain

class DiscComposer(GcpDisc):
    resource = 'composer'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the composer resources from each project discovered.

        This module will create the composer resources objects and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_composer, __name__.split(".")[-1])


    def _disc_composer(self, p_obj:GcpProject):
        """Discover all the composer resources from a given project"""

        for location in gcp_regions:
            http_prep = self.service.projects().locations().environments()#.list(parent=f"{p_obj.name}/locations/{location}")
            environments: Union[list, str] = self.execute_http_req(http_prep, "environments", disable_warn=True, ret_err=True, list_kwargs={"parent": f"{p_obj.name}/locations/{location}"})

            if type(environments) is str:
                # If this error, we cannot see anythin in this project
                if "Cloud Composer API has not been used" in environments:
                    break

                # If other error, continue checking zones
                continue

            for compose_env in environments:
                config = compose_env.get("config", {})
                softwareConfig = config.get("softwareConfig", {})
                privateEnvironmentConfig = config.get("privateEnvironmentConfig", {})
                privateClusterConfig = privateEnvironmentConfig.get("privateClusterConfig", {})
                webServerNetworkAccessControl = config.get("webServerNetworkAccessControl", {})
                databaseConfig = config.get("databaseConfig", {})
                webServerConfig = config.get("webServerConfig", {})
                encryptionConfig = config.get("encryptionConfig", {})

                composerenv_obj: GcpComposerEnv = GcpComposerEnv(
                    name = compose_env["name"],
                    state = compose_env.get("state", ""),
                    labels = json.dumps(compose_env.get("labels", {})),

                    gkeCluster = config.get("gkeCluster", ""),
                    dagGcsPrefix = config.get("dagGcsPrefix", ""),
                    nodeCount = config.get("nodeCount", ""),
                    airflowUri = config.get("airflowUri", ""),
                    environmentSize = config.get("environmentSize", ""),

                    imageVersion = softwareConfig.get("imageVersion", ""),
                    airflowConfigOverrides = json.dumps(softwareConfig.get("airflowConfigOverrides", {})),
                    pypiPackages = json.dumps(softwareConfig.get("pypiPackages", {})),
                    envVariables = json.dumps(softwareConfig.get("envVariables", {})),
                    pythonVersion = softwareConfig.get("pythonVersion", ""),
                    schedulerCount = softwareConfig.get("schedulerCount", ""),

                    enablePrivateEnvironment = privateEnvironmentConfig.get("enablePrivateEnvironment", False),
                    enablePrivateEndpoint = privateClusterConfig.get("enablePrivateEndpoint", False),
                    masterIpv4CidrBlock = privateClusterConfig.get("masterIpv4CidrBlock", ""),
                    masterIpv4ReservedRange = privateClusterConfig.get("masterIpv4ReservedRange", ""),
                    webServerIpv4CidrBlock = privateEnvironmentConfig.get("webServerIpv4CidrBlock", ""),
                    cloudSqlIpv4CidrBlock = privateEnvironmentConfig.get("cloudSqlIpv4CidrBlock", ""),
                    webServerIpv4ReservedRange = privateEnvironmentConfig.get("webServerIpv4ReservedRange", ""),
                    cloudComposerNetworkIpv4CidrBlock = privateEnvironmentConfig.get("cloudComposerNetworkIpv4CidrBlock", ""),
                    cloudComposerNetworkIpv4ReservedRange = privateEnvironmentConfig.get("cloudComposerNetworkIpv4ReservedRange", ""),
                    enablePrivatelyUsedPublicIps = privateEnvironmentConfig.get("enablePrivatelyUsedPublicIps", False),
                    
                    allowedIpRanges = [net["value"] for net in webServerNetworkAccessControl.get("allowedIpRanges", [])],

                    databaseMachineType = databaseConfig.get("machineType", ""),

                    webServerType = webServerConfig.get("machineType", ""),
                ).save()

                composerenv_obj.projects.update(p_obj, zone=location)
                composerenv_obj.save()

                if config.get("dagGcsPrefix"):
                    bucket_name = config.get("dagGcsPrefix").split("gs://")[-1].split("/")[0] #Format: gs://folder/folder/folder... to just the first folder
                    storage_obj = GcpStorage(name=bucket_name).save() 
                    composerenv_obj.storages.update(storage_obj, link=config.get("dagGcsPrefix"))
                    composerenv_obj.save()
                
                # Potential Public Exposure
                if config.get("airflowUri"):
                    uparsed = urlparse(config.get("airflowUri"))
                    hostname = uparsed.hostname
                    if validators.domain(hostname) is True:
                        dom_obj = PublicDomain(name=hostname).save()
                        composerenv_obj.public_domains.update(dom_obj)
                    
                    else:
                        ip_obj = PublicIP(name=hostname).save()
                        composerenv_obj.public_ips.update(ip_obj)
                    
                    composerenv_obj.save()

                if encryptionConfig.get("kmsKeyName"):
                    kmskey_obj: GcpKMSKey = GcpKMSKey(name=encryptionConfig.get("kmsKeyName")).save()
                    composerenv_obj.kmskeys.update(kmskey_obj)
                    composerenv_obj.save()

                cluster_complete_name = config.get("gkeCluster", "")
                if cluster_complete_name:
                    cluster_name = cluster_complete_name.split("/")[-1]
                    cluster_obj: GcpCluster = GcpCluster(name=cluster_name).save()
                    cluster_obj.composer_environments.update(composerenv_obj)
                    cluster_obj.save()
                
                # Useless data to privesc?
                #self._get_operations(p_obj, location, composerenv_obj)


    def _get_operations(self, p_obj, location, composerenv_obj):
        '''
        Get each possible airflow operation from each airflow environment
        '''
        
        http_prep = self.service.projects().locations().operations()#.list(name=f"{p_obj.name}/locations/{location}")
        operations: List[dict] = self.execute_http_req(http_prep, "operations", list_kwargs={"name": f"{p_obj.name}/locations/{location}"})

        for op in operations:
            metadata = op.get("metadata", {})

            op_obj: GcpOperation = GcpOperation(
                name = op["name"],
                state = metadata.get("state", ""),
                operationType = metadata.get("operationType", ""),
                done = op.get("done", False),
            ).save()
            op_obj.composer_environments.update(composerenv_obj)
            op_obj.save()
