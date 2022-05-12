import logging
import json
import base64
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sSecret


class DiscSecrets(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the secrets of each namespace
        """

        if not self.reload_api(): return
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_secrets, __name__.split(".")[-1])

    
    def _disc_secrets(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the secrets of a namespace"""

        client_cred = client.CoreV1Api(self.cred)
        secrets = self.call_k8s_api(f=client_cred.list_namespaced_secret, namespace=ns_obj.ns_name)
        if not secrets or not secrets.items:
            return
        
        self._disc_loop(secrets.items, self._save_secret, __name__.split(".")[-1]+f"-{ns_obj.ns_name}", **{"ns_obj": ns_obj})
    
    def _save_secret(self, secret, **kwargs):
        """Given K8s secret information, save it"""

        ns_obj = kwargs["ns_obj"]
        ns_name = ns_obj.name
        values_cleartext = []
        if self.k8s_get_secret_values and secret.data:
            for val in secret.data.values():
                try:
                    values_cleartext.append(base64.b64decode(val))
                except:
                    values_cleartext.append(val)
                
        secret_obj = K8sSecret(
            name = f"{ns_name}:{secret.metadata.name}",
            self_link = secret.metadata.self_link,
            uid = secret.metadata.uid,
            labels = json.dumps(secret.metadata.labels),
            immutable = secret.immutable,
            keys = list(secret.data.keys()) if secret.data else [],
            values = list(secret.data.values()) if self.k8s_get_secret_values and secret.data else [],
            values_cleartext =values_cleartext,
            type = secret.type
        ).save()
        secret_obj.namespaces.update(ns_obj)
        secret_obj.save()



