import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sNode, K8sPod, K8sVol, K8sSecret, K8sContainer, K8sEnvVar, K8sServiceAccount

class DiscPods(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the pods of each namespace, relate it with the namespaces and the running containers.
        """

        client_cred = client.CoreV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._disc_pods, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_pods(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the pods of a namespace"""

        client_cred = kwargs["client_cred"]
        ns_name = ns_obj.name
        pods = client_cred.list_namespaced_pod(namespace=ns_name)
        if not pods or not pods.items:
            return

        for pod in pods.items:
            self._save_pod(pod, ns_obj, ns_obj.name)
