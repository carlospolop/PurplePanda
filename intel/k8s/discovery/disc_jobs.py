import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sJob


class DiscJobs(K8sDisc):
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the jobs of each namespace, relate it with the namespaces and the running containers.
        """

        if not self.reload_api(): return
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_jobs, __name__.split(".")[-1])

    def _disc_jobs(self, ns_obj: K8sNamespace, **kwargs):
        """Discover all the jobs of a namespace"""

        client_cred = client.BatchV1Api(self.cred)
        jobs = self.call_k8s_api(f=client_cred.list_namespaced_job, namespace=ns_obj.ns_name)
        if not jobs or not jobs.items:
            return

        self._disc_loop(jobs.items, self._save_job, __name__.split(".")[-1] + f"-{ns_obj.ns_name}", **{"orig": ns_obj})

    def _save_job(self, jb, **kwargs):
        """Given K8s job information, save it"""

        orig = kwargs["orig"]
        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_name = jb.metadata.namespace
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name

        jb_obj = K8sJob(
            name=f"{ns_name}:{jb.metadata.name}",
            generate_name=jb.metadata.generate_name,
            self_link=jb.metadata.self_link,
            uid=jb.metadata.uid,
            labels=json.dumps(jb.metadata.labels),
            annotations=json.dumps(jb.metadata.annotations) if jb.metadata.annotations else "",

            parallelism=jb.spec.parallelism,
            suspend=jb.spec.suspend if hasattr(jb.spec, "suspend") else False,
            completions=jb.spec.completions
        ).save()
        jb_obj.namespaces.update(ns_obj)
        jb_obj.save()

        self._save_pod(jb.spec.template, orig=jb_obj, ns_name=ns_obj.ns_name)

        # TODO: Consider ds.spec.selector.match_expressions
        if jb.spec.selector:
            self._pod_selector(jb_obj, jb.spec.selector.match_labels)
