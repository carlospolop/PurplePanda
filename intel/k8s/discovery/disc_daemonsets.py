import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sDaemonSet, K8sDeployment

class DiscDaemonsets(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the daemonsets of each namespace, relate it with the namespaces and the running containers.
        """

        client_cred = client.AppsV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._disc_daemonsets, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_daemonsets(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the daemonsets of a namespace"""

        client_cred = kwargs["client_cred"]
        ns_name = ns_obj.name
        daemons_sets = client_cred.list_namespaced_daemon_set(namespace=ns_name)
        if not daemons_sets or not daemons_sets.items:
            return

        for ds in daemons_sets.items:
            self._save_daemonset(ds, ns_obj)    

    def _save_daemonset(self, ds, orig, **kwargs):
        """Given K8s daemonset information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
            ns_name = ns_obj.name
        else:
            ns_name = ds.metadata.namespace
            ns_obj = K8sNamespace(name = ns_name).save()
        
        ds_obj = K8sDaemonSet(
            name = f"{ns_name}:{ds.metadata.name}",
            generate_name = ds.metadata.generate_name,
            self_link = ds.metadata.self_link,
            uid = ds.metadata.uid,
            labels = json.dumps(ds.metadata.labels),
            annotations = json.dumps(ds.metadata.annotations) if ds.metadata.annotations else "",

            status_number_ready = ds.status.number_ready,
        ).save()
        ds_obj.namespaces.update(ns_obj)
        ds_obj.save()

        if ds.metadata.owner_references:
            for own_r in ds.metadata.owner_references:
                if own_r.kind.lower() == "deployment":
                    dp_obj = K8sDeployment(name=f"{ns_name}:{own_r.name}").save()
                    ds_obj.deployments.update(dp_obj)
                
                else:
                    self.logger.warning(f"Uknown type of parent: {own_r.kind}")

        self._save_pod(ds.spec.template, ds_obj, ns_name=ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if ds.spec.selector:
            self._pod_selector(ds_obj, ds.spec.selector.match_labels)