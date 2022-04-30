import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sReplicaSet, K8sDeployment, K8sVol

class DiscStatefulSet(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the statefulsets of each namespace, relate it with the namespaces and the running containers.
        """

        if not self.reload_api(): return
        client_cred = client.AppsV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_replicasets, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_statefulsets(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the statefulsets of a namespace"""

        client_cred = kwargs["client_cred"]
        statefulsets = self.call_k8s_api(f=client_cred.list_namespaced_stateful_set, namespace=ns_obj.ns_name)
        if not statefulsets or not statefulsets.items:
            return

        for ss in statefulsets.items:
            self._save_deployment(ss, ns_obj)    

    def _save_statefulset(self, ss, orig, **kwargs):
        """Given K8s statefulset information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = ss.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name
        
        ss_obj = K8sReplicaSet(
            name = f"{ns_name}:{ss.metadata.name}",
            generate_name = ss.metadata.generate_name,
            self_link = ss.metadata.self_link,
            uid = ss.metadata.uid,
            labels = json.dumps(ss.metadata.labels),
            annotations = json.dumps(ss.metadata.annotations) if ss.metadata.annotations else "",

            status_ready_replicas = ss.status.ready_replicas,
        ).save()
        ss_obj.namespaces.update(ns_obj)
        ss_obj.save()

        if ss.metadata.owner_references:
            for own_r in ss.metadata.owner_references:
                if own_r.kind.lower() == "deployment":
                    dp_obj = K8sDeployment(name=f"{ns_name}:{own_r.name}").save()
                    ss_obj.deployments.update(dp_obj)
                
                else:
                    self.logger.warning(f"Uknown type of parent: {own_r.kind}")
        
        ss_obj.save()

        if ss.spec.volume_claim_templates:
            for vol in ss.spec.volume_claim_templates:
                vol_obj = K8sVol(
                    name=vol.metadata.name,
                    annotations = json.dumps(ss.metadata.annotations) if ss.metadata.annotations else "",
                    accessModes = vol.spec.accessModes if vol.spec.accessModes else []
                ).save()
                ss_obj.volumes.update(vol_obj)
            ss_obj.save()

        self._save_pod(ss.spec.template, ss_obj, ns_name=ns_obj.ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if ss.spec.selector:
            self._pod_selector(ss_obj, ss.spec.selector.match_labels)