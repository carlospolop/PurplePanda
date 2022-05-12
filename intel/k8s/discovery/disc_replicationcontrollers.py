import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sReplicationController, K8sDeployment

class DiscReplicationControllers(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the replicationcontrollers of each namespace, relate it with the namespaces and the running containerc.
        """

        if not self.reload_api(): return
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_replicationcontroller, __name__.split(".")[-1])

    
    def _disc_replicationcontroller(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the replicationcontrollers of a namespace"""

        client_cred = client.CoreV1Api(self.cred)
        replicationcontroller = self.call_k8s_api(f=client_cred.list_namespaced_replication_controller, namespace=ns_obj.ns_name)
        if not replicationcontroller or not replicationcontroller.items:
            return

        self._disc_loop(replicationcontroller.items, self._save_replicationcontroller, __name__.split(".")[-1]+f"-{ns_obj.ns_name}", **{"orig": ns_obj})
 

    def _save_replicationcontroller(self, rc, **kwargs):
        """Given K8s replicationcontroller information, save it"""
        
        orig = kwargs["orig"]
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = rc.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name
        
        rc_obj = K8sReplicationController(
            name = f"{ns_name}:{rc.metadata.name}",
            generate_name = rc.metadata.generate_name,
            self_link = rc.metadata.self_link,
            uid = rc.metadata.uid,
            labels = json.dumps(rc.metadata.labels),
            annotations = json.dumps(rc.metadata.annotations) if rc.metadata.annotations else "",

            status_ready_replicas = rc.status.ready_replicas,
        ).save()
        rc_obj.namespaces.update(ns_obj)
        rc_obj.save()

        if rc.metadata.owner_references:
            for own_r in rc.metadata.owner_references:
                if own_r.kind.lower() == "deployment":
                    dp_obj = K8sDeployment(name=f"{ns_name}:{own_r.name}").save()
                    rc_obj.deployments.update(dp_obj)
                
                else:
                    self.logger.warning(f"Uknown type of parent: {own_r.kind}")
        
        rc_obj.save()

        self._save_pod(rc.spec.template, orig=rc_obj, ns_name=ns_obj.ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if rc.spec.selector:
            self._pod_selector(rc_obj, rc.spec.selector.match_labels)