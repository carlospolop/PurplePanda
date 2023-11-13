import jwt
import random

from core.utils.purplepanda_prints import PurplePandaPrints
from core.utils.discover_saas import DiscoverSaas

from intel.k8s.discovery.k8s_disc_client import K8sDiscClient
from intel.k8s.discovery.disc_namespaces import DiscNamespaces
from intel.k8s.discovery.disc_current_perms import DiscCurrentPerms
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
from intel.k8s.discovery.disc_mutatingwebhookconfigurations import DiscMutatingWebhookConfigurations
from intel.k8s.discovery.analyze_results import AnalyzeResults


class PurplePandaK8s():
    def discover(self, **kwargs):
        config = kwargs.get("config", "")
        if config:
            del kwargs["config"]

        k8sdc: K8sDiscClient = K8sDiscClient(config=config)
        initial_funcs = []
        for cred in k8sdc.creds:
            kwargs["cluster_id"] = kwargs.get("cluster_id", "")
            kwargs["cluster_id"] = kwargs["cluster_id"] or cred.get("cluster_id", "")
            kwargs["cluster_id"] = kwargs["cluster_id"] or str(random.randint(0, 9999))

            initial_funcs.append(
                DiscoverSaas(
                    initial_funcs=[
                        DiscNamespaces(cred["cred"], cred["config"], **kwargs).discover,
                        DiscNodes(cred["cred"], cred["config"], **kwargs).discover,
                        DiscMutatingWebhookConfigurations(cred["cred"], cred["config"], **kwargs).discover,
                        DiscServiceAccounts(cred["cred"], cred["config"], **kwargs).discover,
                        DiscPods(cred["cred"], cred["config"], **kwargs).discover,

                    ],
                    parallel_funcs=[
                        [
                            DiscSecrets(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscDeployments(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscJobs(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscCronjobs(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscDaemonsets(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscReplicaSets(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscReplicationControllers(cred["cred"], cred["config"], **kwargs).discover,
                        ],
                        [
                            DiscCurrentPerms(cred["cred"], cred["config"], **kwargs).discover,
                            DiscRoles(cred["cred"], cred["config"], **kwargs).discover
                        ]
                    ],
                    # In K8s launch an analysis per cred
                    final_funcs=[
                        DiscServices(cred["cred"], cred["config"], **kwargs).discover,
                        DiscIngresses(cred["cred"], cred["config"], **kwargs).discover,
                        AnalyzeResults(cred["cred"], cred["config"], **kwargs).discover
                    ]
                ).do_discovery
            )

        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[]
        ).do_discovery()

    def analyze_creds(self):
        k8sdc: K8sDiscClient = K8sDiscClient()
        for cred in k8sdc.creds:
            PurplePandaPrints.print_title("Kubernetes (K8s)")
            cred = cred["cred"]
            PurplePandaPrints.print_key_val("Host", cred.configuration.host)

            if cred.configuration.username:
                PurplePandaPrints.print_key_val("Username", cred.configuration.username)

            if description := cred.configuration.get_host_settings()[0].get(
                "description"
            ):
                PurplePandaPrints.print_key_val("Description", description)

            if "authorization" in cred.configuration.api_key and " " in cred.configuration.api_key["authorization"]:
                jwt_token = cred.configuration.api_key["authorization"].split(" ")[1]
                try:
                    PurplePandaPrints.print_dict(jwt.decode(jwt_token, options={"verify_signature": False}))
                except Exception:
                    print("There was an error decoding the JWT token, this is raw token:")
                    PurplePandaPrints.print_key_val("Token", jwt_token)

            PurplePandaPrints.print_separator()
