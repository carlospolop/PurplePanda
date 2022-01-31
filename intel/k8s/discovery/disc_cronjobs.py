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

        client_cred = client.BatchV1beta1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._disc_cronjobs, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_cronjobs(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the cronjobs of a namespace"""

        client_cred = kwargs["client_cred"]
        ns_name = ns_obj.name
        cronjobs = client_cred.list_namespaced_cron_job(namespace=ns_name)
        if not cronjobs or not cronjobs.items:
            return

        for cj in cronjobs.items:
            self._save_cronjob(cj, ns_obj)    

    def _save_cronjob(self, cj, orig, **kwargs):
        """Given K8s cronjobs information, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
            ns_name = ns_obj.name
        else:
            ns_name = cj.metadata.namespace
            ns_obj = K8sNamespace(name = ns_name).save()
        
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

        self._save_pod(cj.spec.job_template.spec.template, cj_obj, ns_name=ns_name)
