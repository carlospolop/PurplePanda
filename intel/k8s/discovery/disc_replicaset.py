import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sReplicaSet, K8sDeployment

class DiscReplicaSets(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the deployments of each namespace, relate it with the namespaces and the running containers.
        """

        client_cred = client.AppsV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_replicasets, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_replicasets(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the replica sets of a namespace"""

        client_cred = kwargs["client_cred"]
        replica_sets = self.call_k8s_api(f=client_cred.list_namespaced_replica_set, namespace=ns_obj.ns_name)
        if not replica_sets or not replica_sets.items:
            return

        for rs in replica_sets.items:
            self._save_replica_set(rs, ns_obj)    

    def _save_replica_set(self, rs, orig, **kwargs):
        """Given K8s replica set information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = rs.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name
        
        rs_obj = K8sReplicaSet(
            name = f"{ns_name}:{rs.metadata.name}",
            generate_name = rs.metadata.generate_name,
            self_link = rs.metadata.self_link,
            uid = rs.metadata.uid,
            labels = json.dumps(rs.metadata.labels),
            annotations = json.dumps(rs.metadata.annotations) if rs.metadata.annotations else "",

            status_ready_replicas = rs.status.ready_replicas,
        ).save()
        rs_obj.namespaces.update(ns_obj)
        rs_obj.save()

        if rs.metadata.owner_references:
            for own_r in rs.metadata.owner_references:
                if own_r.kind.lower() == "deployment":
                    dp_obj = K8sDeployment(name=f"{ns_name}:{own_r.name}").save()
                    rs_obj.deployments.update(dp_obj)
                
                else:
                    self.logger.warning(f"Uknown type of parent: {own_r.kind}")
        
        rs_obj.save()

        self._save_pod(rs.spec.template, rs_obj, ns_name=ns_obj.ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if rs.spec.selector:
            self._pod_selector(rs_obj, rs.spec.selector.match_labels)