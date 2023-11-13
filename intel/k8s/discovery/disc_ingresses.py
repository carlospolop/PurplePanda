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

        if not self.reload_api(): return
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_ingresses, __name__.split(".")[-1])

    def _disc_ingresses(self, ns_obj: K8sNamespace, **kwargs):
        """Discover all the ingresses of a namespace"""

        client_cred = client.NetworkingV1Api(self.cred)
        ingresses = self.call_k8s_api(f=client_cred.list_namespaced_ingress, namespace=ns_obj.ns_name)
        if not ingresses or not ingresses.items:
            return

        self._disc_loop(ingresses.items, self._save_ingress, __name__.split(".")[-1] + f"-{ns_obj.ns_name}",
                        **{"ns_obj": ns_obj})

    def _save_ingress(self, ingress, **kwargs):
        """Given K8s ingress information, save it"""

        ns_obj = kwargs["ns_obj"]
        ns_name = ns_obj.name
        ingress_obj = K8sIngress(
            name=f"{ns_name}:{ingress.metadata.name}",
            self_link=ingress.metadata.self_link,
            uid=ingress.metadata.uid,
            labels=json.dumps(ingress.metadata.labels),
        ).save()
        ingress_obj.namespaces.update(ns_obj)
        ingress_obj.save()

        # Check Rules
        if ingress.spec.rules:
            for rule in ingress.spec.rules:
                host = rule.host
                if host:
                    dom_obj = PublicDomain(name=host).save()
                    ingress_obj.public_domains.update(dom_obj)

                for path in ingress.spec.rules[0].http.paths:
                    url_path = path.path
                    path_type = path.path_type if hasattr(path, "path_type") else ""
                    port = path.backend.service.port.number
                    service_name = path.backend.service.name
                    if service_name:
                        service_obj = K8sService(name=f"{ns_name}:{service_name}", ).save()
                        ingress_obj.services.update(service_obj, url_path=url_path, path_type=path_type, port=port)

        # Specify tls data
        if ingress.spec.tls:
            for info in ingress.spec.tls:
                for host in info.hosts:
                    dom_obj = PublicDomain(name=host).save()
                    ingress_obj.public_domains.update(dom_obj)

                secret_obj = K8sSecret(name=info.secret_name).save()
                ingress_obj.secrets.update(secret_obj, hosts=info.hosts)

        if ingress.status and ingress.status.load_balancer and ingress.status.load_balancer.ingress:
            for info in ingress.status.load_balancer.ingress:
                ip = info.ip
                if ip:
                    ip_obj = PublicIP(name=ip).save()
                    ingress_obj.public_ips.update(ip_obj)

                hostname = info.hostname
                if hostname:
                    dom_obj = PublicDomain(name=hostname).save()
                    ingress_obj.public_domains.update(dom_obj)

        ingress_obj.save()
