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

        client_cred = client.CoreV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._disc_services, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_services(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the services of a namespace"""

        client_cred = kwargs["client_cred"]
        services = client_cred.list_namespaced_service(namespace=ns_obj.name)
        if not services or not services.items:
            return
        
        ns_name = ns_obj.name
        for service in services.items:
            cluster_ips = [service.spec.cluster_ip] if service.spec.cluster_ip else []
            if service.spec.cluster_i_ps:
                # Create array of non-repeated IPs
                for ip in service.spec.cluster_i_ps:
                    if not ip in cluster_ips:
                        cluster_ips.add(ip)
            
            service_obj = K8sService(
                name = f"{ns_name}:{service.metadata.name}",
                self_link = service.metadata.self_link,
                uid = service.metadata.uid,
                labels = json.dumps(service.metadata.labels),

                external_traffic_policy = service.spec.external_traffic_policy if service.spec.external_traffic_policy else "",
                health_check_node_port = service.spec.health_check_node_port if service.spec.health_check_node_port else "",
                internal_traffic_policy = service.spec.internal_traffic_policy if service.spec.internal_traffic_policy else "",
                ip_families = service.spec.ip_families if service.spec.ip_families else [],
                ip_family_policy = service.spec.ip_family_policy if service.spec.ip_family_policy else "",
                load_balancer_class = service.spec.load_balancer_class if service.spec.load_balancer_class else "",
                load_balancer_ip = service.spec.load_balancer_ip if service.spec.load_balancer_ip else "",
                load_balancer_source_ranges = service.spec.load_balancer_source_ranges if service.spec.load_balancer_source_ranges else [],

                type = service.spec.type,
                ports = [f"{p.port}:{p.protocol}:{p.target_port}:{p.name}:{p.node_port}:{p.app_protocol}" for p in service.spec.ports] if service.spec.ports else [],
                cluster_ips = cluster_ips
            ).save()
            service_obj.namespaces.update(ns_obj)
            service_obj.save()
            
            # Get external ips
            if service.spec.external_i_ps:
                for ip in service.spec.external_i_ps:
                    pip_obj = PublicIP(ip=ip).save()
                    service_obj.public_ips.update(pip_obj)
                
                service_obj.save()
            
            # Get external domain
            if service.spec.external_name:
                dom_obj = PublicDomain(name=service.spec.external_name).save()
                service_obj.public_domains.update(dom_obj)
                service_obj.save()
            
            # Get resources using the service
            self._pod_selector(service_obj, service.spec.selector)
