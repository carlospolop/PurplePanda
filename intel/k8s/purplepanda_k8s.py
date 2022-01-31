import jwt

from core.utils.purplepanda_prints import PurplePandaPrints
from core.utils.discover_saas import DiscoverSaas

from intel.k8s.discovery.k8s_disc_client import K8sDiscClient
from intel.k8s.discovery.disc_namespaces import DiscNamespaces
from intel.k8s.discovery.disc_nodes import DiscNodes
from intel.k8s.discovery.disc_pods import DiscPods
from intel.k8s.discovery.disc_daemonsets import DiscDaemonsets
from intel.k8s.discovery.disc_deployments import DiscDeployments
from intel.k8s.discovery.disc_replicaset import DiscReplicaSets
from intel.k8s.discovery.disc_cronjobs import DiscCronjobs
from intel.k8s.discovery.disc_jobs import DiscJobs
from intel.k8s.discovery.disc_replicationcontrollers import DiscReplicationControllers
from intel.k8s.discovery.disc_secrets import DiscSecrets
from intel.k8s.discovery.disc_roles import DiscRoles
from intel.k8s.discovery.disc_serviceaccounts import DiscServiceAccounts
from intel.k8s.discovery.disc_services import DiscServices
from intel.k8s.discovery.disc_ingresses import DiscIngresses
from intel.k8s.discovery.analyze_results import AnalyzeResults


class PurplePandaK8s():
    def discover(self, **kwargs):
        k8sdc : K8sDiscClient = K8sDiscClient()
        initial_funcs = []
        for cred in k8sdc.creds:
            initial_funcs.append(
                DiscoverSaas(
                    initial_funcs = [
                        DiscNamespaces(cred["cred"], **kwargs).discover,
                        DiscNodes(cred["cred"], **kwargs).discover,
                        DiscServiceAccounts(cred["cred"], **kwargs).discover,
                        DiscSecrets(cred["cred"], **kwargs).discover,
                        DiscPods(cred["cred"], **kwargs).discover,
                        DiscDeployments(cred["cred"], **kwargs).discover,
                        DiscJobs(cred["cred"], **kwargs).discover,
                        DiscCronjobs(cred["cred"], **kwargs).discover,
                        DiscDaemonsets(cred["cred"], **kwargs).discover,
                        DiscReplicaSets(cred["cred"], **kwargs).discover,
                        DiscReplicationControllers(cred["cred"], **kwargs).discover,
                        DiscServices(cred["cred"], **kwargs).discover,
                        DiscIngresses(cred["cred"], **kwargs).discover,
                        DiscRoles(cred["cred"], **kwargs).discover,
                    ],
                    parallel_funcs = []
                ).do_discovery
            )
        
        # Launch a thread per set of credentials
        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[AnalyzeResults(cred["cred"], **kwargs).discover]
        ).do_discovery()
    
    def analyze_creds(self):
        k8sdc : K8sDiscClient = K8sDiscClient()
        for cred in k8sdc.creds:
            PurplePandaPrints.print_title("Kubernetes (K8s)")
            cred = cred["cred"]
            PurplePandaPrints.print_key_val("Host", cred.configuration.host)
            
            if cred.configuration.username:
                PurplePandaPrints.print_key_val("Username", cred.configuration.username)
            
            description = cred.configuration.get_host_settings()[0].get("description")
            if description:
                PurplePandaPrints.print_key_val("Description", description)

            if "authorization" in cred.configuration.api_key:
                jwt_token = cred.configuration.api_key["authorization"].split(" ")[1]
                PurplePandaPrints.print_dict(jwt.decode(jwt_token, options={"verify_signature": False}))
            
            PurplePandaPrints.print_separator()
