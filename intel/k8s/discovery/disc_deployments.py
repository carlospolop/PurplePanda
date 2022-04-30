import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sDeployment

class DiscDeployments(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the deployments of each namespace, relate it with the namespaces and the running containers.
        """

        if not self.reload_api(): return
        client_cred = client.AppsV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_deployments, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_deployments(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the deployments of a namespace"""

        client_cred = kwargs["client_cred"]
        deployments = self.call_k8s_api(f=client_cred.list_namespaced_deployment, namespace=ns_obj.ns_name)
        if not deployments or not deployments.items:
            return

        for ds in deployments.items:
            self._save_deployment(ds, ns_obj)    

    def _save_deployment(self, dp, orig, **kwargs):
        """Given K8s deployment information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = dp.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name
        
        dp_obj = K8sDeployment(
            name = f"{ns_name}:{dp.metadata.name}",
            generate_name = dp.metadata.generate_name,
            self_link = dp.metadata.self_link,
            uid = dp.metadata.uid,
            labels = json.dumps(dp.metadata.labels),
            annotations = json.dumps(dp.metadata.annotations) if dp.metadata.annotations else "",

            status_ready_replicas = dp.status.ready_replicas,
        ).save()
        dp_obj.namespaces.update(ns_obj)
        dp_obj.save()

        self._save_pod(dp.spec.template, dp_obj, ns_name=ns_obj.ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if dp.spec.selector:
            self._pod_selector(dp_obj, dp.spec.selector.match_labels)