import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sService
from core.models.models import PublicIP, PublicDomain


class DiscServices(K8sDisc):
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the services of each namespace
        """

        if not self.reload_api(): return
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_services, __name__.split(".")[-1])

    def _disc_services(self, ns_obj: K8sNamespace, **kwargs):
        """Discover all the services of a namespace"""

        client_cred = client.CoreV1Api(self.cred)
        services = self.call_k8s_api(f=client_cred.list_namespaced_service, namespace=ns_obj.ns_name)
        if not services or not services.items:
            return

        self._disc_loop(services.items, self._save_service, __name__.split(".")[-1] + f"-{ns_obj.ns_name}",
                        **{"ns_obj": ns_obj})

    def _save_service(self, service, **kwargs):
        """Given K8s secret information, save it"""

        ns_obj = kwargs["ns_obj"]
        ns_name = ns_obj.name
        cluster_ips = [service.spec.cluster_ip] if service.spec.cluster_ip else []
        if hasattr(service.spec, "cluster_i_ps") and service.spec.cluster_i_ps:
            # Create array of non-repeated IPs
            for ip in service.spec.cluster_i_ps:
                if ip not in cluster_ips:
                    cluster_ips.add(ip)

        ports = []
        if hasattr(service.spec, "ports") and service.spec.ports:
            for p in service.spec.ports:
                port = str(p.port)
                port += f":{p.protocol}" if hasattr(p, "protocol") else ""
                port += f":{p.target_port}" if hasattr(p, "target_port") else ""
                port += f":{p.name}" if hasattr(p, "name") else ""
                port += f":{p.node_port}" if hasattr(p, "node_port") else ""
                port += f":{p.app_protocol}" if hasattr(p, "app_protocol") else ""
                ports.append(port)

        service_obj = K8sService(
            name=f"{ns_name}:{service.metadata.name}",
            self_link=service.metadata.self_link,
            uid=service.metadata.uid,
            labels=json.dumps(service.metadata.labels),

            external_traffic_policy=service.spec.external_traffic_policy if hasattr(service.spec,
                                                                                    "external_traffic_policy") and service.spec.external_traffic_policy else "",
            health_check_node_port=service.spec.health_check_node_port if hasattr(service.spec,
                                                                                  "health_check_node_port") and service.spec.health_check_node_port else "",
            internal_traffic_policy=service.spec.internal_traffic_policy if hasattr(service.spec,
                                                                                    "internal_traffic_policy") and service.spec.internal_traffic_policy else "",
            ip_families=service.spec.ip_families if hasattr(service.spec,
                                                            "ip_families") and service.spec.ip_families else [],
            ip_family_policy=service.spec.ip_family_policy if hasattr(service.spec,
                                                                      "ip_family_policy") and service.spec.ip_family_policy else "",
            load_balancer_class=service.spec.load_balancer_class if hasattr(service.spec,
                                                                            "load_balancer_class") and service.spec.load_balancer_class else "",
            load_balancer_ip=service.spec.load_balancer_ip if hasattr(service.spec,
                                                                      "load_balancer_ip") and service.spec.load_balancer_ip else "",
            load_balancer_source_ranges=service.spec.load_balancer_source_ranges if hasattr(service.spec,
                                                                                            "load_balancer_source_ranges") and service.spec.load_balancer_source_ranges else [],

            type=service.spec.type,
            ports=ports,
            cluster_ips=cluster_ips
        ).save()
        service_obj.namespaces.update(ns_obj)
        service_obj.save()

        # Get external ips
        if service.spec.external_i_ps:
            for ip in service.spec.external_i_ps:
                pip_obj = PublicIP(name=ip).save()
                service_obj.public_ips.update(pip_obj)

            service_obj.save()

        # Get external domain
        if service.spec.external_name:
            dom_obj = PublicDomain(name=service.spec.external_name).save()
            service_obj.public_domains.update(dom_obj)
            service_obj.save()

        if service.status and service.status.load_balancer:
            if service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        pip_obj = PublicIP(name=ingress.ip).save()
                        service_obj.public_ips.update(pip_obj)
                    if ingress.hostname:
                        dom_obj = PublicDomain(name=ingress.hostname).save()
                        service_obj.public_domains.update(dom_obj)
        
            service_obj.save()

        # Get resources using the service
        self._pod_selector(service_obj, service.spec.selector)
