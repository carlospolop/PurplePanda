import logging
import json
import validators
from urllib.parse import urlparse

from kubernetes import client
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sMutatingWebhookConfig
from core.models import PublicDomain, PublicIP


class DiscMutatingWebhookConfigurations(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the MutationWebHook Configurations.
        """

        if not self.reload_api(): return
        client_cred = client.AdmissionregistrationV1Api(self.cred)
        mwcs = self.call_k8s_api(f=client_cred.list_mutating_webhook_configuration)
        if not mwcs or not mwcs.items:
            return
        
        self._disc_loop(mwcs.items, self._save_mutationwebhookconfig, __name__.split(".")[-1])


    def _save_mutationwebhookconfig(self, mwc, **kwargs):
        """Given K8s replicationcontroller information, save it"""

        namespace_selector_expresions = []
        for w in mwc.webhooks:
            if w.namespace_selector.match_expressions:
                for e in w.namespace_selector.match_expressions:
                    match_expr_str = f"Key: {e.key}, Operator: {e.operator}, Values:{e.values}"
                    namespace_selector_expresions.append(match_expr_str)
        
        namespace_selector_labels = []
        for w in mwc.webhooks:
            if w.namespace_selector.match_expressions:
                namespace_selector_labels += json.dumps(w.namespace_selector.match_labels)
        
        mwc_obj = K8sMutatingWebhookConfig(
            name = mwc.metadata.name,
            self_link = mwc.metadata.self_link,
            uid = mwc.metadata.uid,
            labels = json.dumps(mwc.metadata.labels),
            annotations = json.dumps(mwc.metadata.annotations) if mwc.metadata.annotations else "",

            namespace_selector_expresions = namespace_selector_expresions,
            namespace_selector_labels = namespace_selector_labels,
            #client_config = [json.dumps(w.client_config) for w in mwc.webhooks] if mwc.webhooks else [],
            reinvocation_policy = [w.reinvocation_policy for w in mwc.webhooks] if mwc.webhooks else [],
            failure_policy = [json.dumps(w.failure_policy) for w in mwc.webhooks] if mwc.webhooks else [],
            rules_operations = [json.dumps(r.operations) for w in mwc.webhooks for r in w.rules] if mwc.webhooks else [],
            rules_resources = [json.dumps(r.resources) for w in mwc.webhooks for r in w.rules] if mwc.webhooks else [],
        ).save()

        #dom_obj = PublicDomain(name=mwc.metadata.name).save() #They aren't domains always
        #mwc_obj.public_domains.update(dom_obj)

        for w in mwc.webhooks:
            if w.client_config.url:
                uparsed = urlparse(w.client_config.url)
                hostname = uparsed.hostname
                if validators.domain(hostname) is True or hostname == "localhost":
                    dom_obj = PublicDomain(name=hostname).save()
                    mwc_obj.public_domains.update(dom_obj)
                
                else:
                    ip_obj = PublicIP(name=hostname).save()
                    mwc_obj.public_ips.update(ip_obj)
        
        mwc_obj.save()
        self.rel_to_cloud_cluster(mwc_obj)