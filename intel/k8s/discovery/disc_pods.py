import logging
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace

class DiscPods(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the pods of each namespace, relate it with the namespaces and the running containers.
        """

        client_cred = client.CoreV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_pods, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_pods(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the pods of a namespace"""

        client_cred = kwargs["client_cred"]
        pods = self.call_k8s_api(f=client_cred.list_namespaced_pod, namespace=ns_obj.ns_name)
        if not pods or not pods.items:
            return

        for pod in pods.items:
            self._save_pod(pod, ns_obj, ns_obj.ns_name)
