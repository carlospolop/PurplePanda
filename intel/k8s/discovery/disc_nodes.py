import logging
import json
from kubernetes import client
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNode

class DiscNodes(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the namespaces of the cluster
        """

        client_cred = client.CoreV1Api(self.cred)
        nodes = self.call_k8s_api(f=client_cred.list_node)
        if not nodes or not nodes.items:
            return
        
        self._disc_loop(nodes.items, self._disc_nodes, __name__.split(".")[-1])


    def _disc_nodes(self, node):
        node_obj = K8sNode(
            name = node.metadata.name,
            generate_name = node.metadata.generate_name,
            self_link = node.metadata.self_link,
            uid = node.metadata.uid,
            labels = json.dumps(node.metadata.labels),

            role = node.metadata.labels.get("node.kubernetes.io/role", ""),
            instance_type = node.metadata.labels.get("node.kubernetes.io/instance-type", ""),
            zone = node.metadata.labels.get("topology.kubernetes.io/zone", ""),
            
            addresses = [a.address for a in node.status.addresses],
            addresses_type = [a.type for a in node.status.addresses],

            kubelet_port = node.status.daemon_endpoints.kubelet_endpoint.port,

            arch = node.status.node_info.architecture,
            kernelVersion = node.status.node_info.kernel_version,
            kubeProxyVersion = node.status.node_info.kube_proxy_version,
            kubeletVersion = node.status.node_info.kubelet_version,
            os = node.status.node_info.operating_system,
            osImage = node.status.node_info.os_image,
        ).save()
        self.rel_to_cloud_cluster(node_obj)
