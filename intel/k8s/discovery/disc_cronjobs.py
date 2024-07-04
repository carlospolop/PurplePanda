import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sCronJob

class DiscCronjobs(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the cronjobs of each namespace, relate it with the namespaces and the running containers.
        """

        if not self.reload_api(): return
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_cronjobs, __name__.split(".")[-1])

    
    def _disc_cronjobs(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the cronjobs of a namespace"""

        client_cred = client.BatchV1Api(self.cred)
        cronjobs = self.call_k8s_api(f=client_cred.list_namespaced_cron_job, namespace=ns_obj.ns_name)
        if not cronjobs or not cronjobs.items:
            return

        self._disc_loop(cronjobs.items, self._save_cronjob, __name__.split(".")[-1]+f"-{ns_obj.ns_name}", **{"orig": ns_obj})


    def _save_cronjob(self, cj, **kwargs):
        """Given K8s cronjobs information, save it"""
        
        orig = kwargs["orig"]
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = cj.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        
        ns_name = ns_obj.name
        
        cj_obj = K8sCronJob(
            name = f"{ns_name}:{cj.metadata.name}",
            generate_name = cj.metadata.generate_name,
            self_link = cj.metadata.self_link,
            uid = cj.metadata.uid,
            labels = json.dumps(cj.metadata.labels),
            annotations = json.dumps(cj.metadata.annotations) if cj.metadata.annotations else "",

            concurrency_policy = cj.spec.concurrency_policy,
            schedule = cj.spec.schedule,
            suspend = cj.spec.suspend
        ).save()
        cj_obj.namespaces.update(ns_obj)
        cj_obj.save()

        self._save_pod(cj.spec.job_template.spec.template, orig=cj_obj, ns_name=ns_obj.ns_name)
