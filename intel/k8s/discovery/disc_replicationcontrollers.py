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

        client_cred = client.CoreV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._disc_replicationcontroller, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_replicationcontroller(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the replicationcontrollers of a namespace"""

        client_cred = kwargs["client_cred"]
        ns_name = ns_obj.name
        replicationcontroller = client_cred.list_namespaced_replication_controller(namespace=ns_name)
        if not replicationcontroller or not replicationcontroller.items:
            return

        for rc in replicationcontroller.items:
            self._save_replicationcontroller(rc, ns_obj)    

    def _save_replicationcontroller(self, rc, orig, **kwargs):
        """Given K8s replicationcontroller information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
            ns_name = ns_obj.name
        else:
            ns_name = rc.metadata.namespace
            ns_obj = K8sNamespace(name = ns_name).save()
        
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

        self._save_pod(rc.spec.template, rc_obj, ns_name=ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if rc.spec.selector:
            self._pod_selector(rc_obj, rc.spec.selector.match_labels)