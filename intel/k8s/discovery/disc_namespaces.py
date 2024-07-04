import logging
import json
from kubernetes import client
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace

class DiscNamespaces(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the namespaces of the cluster
        """

        if not self.reload_api(): return
        client_cred = client.CoreV1Api(self.cred)
        namespaces = self.call_k8s_api(f=client_cred.list_namespace)
        if not namespaces or not namespaces.items:
            return
        
        self._disc_loop(namespaces.items, self._disc_nss, __name__.split(".")[-1])
        
    
    def _disc_nss(self, ns):
        ns_obj = K8sNamespace(
            name = f"{self.cluster_id}-{ns.metadata.name}",
            ns_name = ns.metadata.name,
            cluster_name = getattr(ns.metadata, 'cluster_name', ""),
            generate_name = ns.metadata.generate_name,
            self_link = ns.metadata.self_link,
            labels = json.dumps(ns.metadata.labels),
            resource_version = ns.metadata.resource_version,
            uid = ns.metadata.uid,
            status = ns.status.phase,
            iam_amazonaws_com_permitted = ns.metadata.annotations.get("iam.amazonaws.com/permitted", "") if ns.metadata.annotations else "",
            iam_amazonaws_com_allowed_roles = ns.metadata.annotations.get("iam.amazonaws.com/allowed-roles", "") if ns.metadata.annotations else "",
        ).save()
        self.rel_to_cloud_cluster(ns_obj)


