import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sConfigMap 

class DiscConfigMaps(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the configmaps of each namespace
        """
        if not self.reload_api():
            return
        
        # Filter namespaces based on a matching cluster ID.
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(
            f'_.name =~ "{str(self.cluster_id)}-.*"'
        )
        self._disc_loop(namespaces, self._disc_configmaps, __name__.split(".")[-1])
    
    def _disc_configmaps(self, ns_obj: K8sNamespace, **kwargs):
        """
        Discover all configmaps in a namespace using the Kubernetes API
        """
        client_cred = client.CoreV1Api(self.cred)
        configmaps = self.call_k8s_api(
            f=client_cred.list_namespaced_config_map,
            namespace=ns_obj.ns_name
        )
        
        if not configmaps or not configmaps.items:
            return

        self._disc_loop(
            configmaps.items,
            self._save_configmap,
            __name__.split(".")[-1] + f"-{ns_obj.ns_name}",
            **{"ns_obj": ns_obj}
        )
    
    def _save_configmap(self, configmap, **kwargs):
        """
        Save the retrieved configmap information to purplepanda
        
        This function assumes that there is a K8sConfigMap model (or similar)
        that handles the persistence of configmap information.
        """
        ns_obj = kwargs["ns_obj"]
        ns_name = ns_obj.name
        
        # Here, we serialize the data dictionary to a JSON string,
        # but you can adjust the serialization as needed.
        configmap_obj = K8sConfigMap(
            name=f"{ns_name}:{configmap.metadata.name}",
            self_link=configmap.metadata.self_link,
            uid=configmap.metadata.uid,
            labels=json.dumps(configmap.metadata.labels) if configmap.metadata.labels else '{}',
            data=json.dumps(configmap.data) if configmap.data else '{}'
        ).save()
        
        # Associate the configmap with its namespace in purplepanda.
        configmap_obj.namespaces.update(ns_obj)
        configmap_obj.save()
