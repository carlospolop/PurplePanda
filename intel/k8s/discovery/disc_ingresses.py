import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sService, K8sIngress, K8sSecret
from core.models.models import PublicIP, PublicDomain
from core.db.customogm import CustomOGM

class DiscIngresses(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the services of each namespace
        """

        client_cred = client.NetworkingV1beta1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_ingresses, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_ingresses(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the ingresses of a namespace"""

        client_cred = kwargs["client_cred"]
        ingresses = self.call_k8s_api(f=client_cred.list_namespaced_ingress, namespace=ns_obj.ns_name)
        if not ingresses or not ingresses.items:
            return
        
        ns_name = ns_obj.name
        for ingress in ingresses.items:
            ingress_obj = K8sIngress(
                name = f"{ns_name}:{ingress.metadata.name}",
                self_link = ingress.metadata.self_link,
                uid = ingress.metadata.uid,
                labels = json.dumps(ingress.metadata.labels),
            ).save()
            ingress_obj.namespaces.update(ns_obj)
            ingress_obj.save()
            
            # Check Rules
            if ingress.spec.rules:
                for rule in ingress.spec.rules:
                    host = rule.host
                    dom_obj = PublicDomain(name=host).save()
                    ingress_obj.public_domains.update(dom_obj)

                    for path in ingress.spec.rules[0].http.paths:
                        url_path = path.path
                        path_type = path.path_type
                        port = path.backend.service_port
                        service_name = path.backend.service_name
                        if service_name:
                            service_obj = K8sService(name=f"{ns_name}:{service_name}",).save()
                            ingress_obj.services.update(service_obj, url_path=url_path, path_type=path_type, port=port)

            # Specify tls data
            if ingress.spec.tls:
                for info in ingress.spec.tls:
                    for host in info.hosts:
                        dom_obj = PublicDomain(name=host).save()
                        ingress_obj.public_domains.update(dom_obj)
                    
                    secret_obj = K8sSecret(name=info.secret_name).save()
                    ingress_obj.secrets.update(secret_obj, hosts=info.hosts)
            
            ingress_obj.save()
