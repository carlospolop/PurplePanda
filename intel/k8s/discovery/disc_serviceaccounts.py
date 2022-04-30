import logging
import json
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sServiceAccount, K8sSecret
from intel.google.models import GcpServiceAccount

class DiscServiceAccounts(K8sDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the service accounts and the secrets that contains their tokens
        """

        if not self.reload_api(): return
        client_cred = client.CoreV1Api(self.cred)
        namespaces:List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_sas, __name__.split(".")[-1], **{"client_cred": client_cred})

    
    def _disc_sas(self, ns_obj:K8sNamespace, **kwargs):
        """Discover all the service accounts of a namespace"""

        client_cred = kwargs["client_cred"]
        sas = self.call_k8s_api(f=client_cred.list_namespaced_service_account, namespace=ns_obj.ns_name)
        if not sas or not sas.items:
            return
        
        ns_name = ns_obj.name
        for sa in sas.items:
            sa_obj = K8sServiceAccount(
                name = f"{ns_name}:{sa.metadata.name}",
                self_link = sa.metadata.self_link,
                uid = sa.metadata.uid,
                labels = json.dumps(sa.metadata.labels),
                iam_amazonaws_role_arn = sa.metadata.annotations.get("eks.amazonaws.com/role-arn", "") if sa.metadata.annotations else "",
                annotations = json.dumps(sa.metadata.annotations) if sa.metadata.annotations else "",
                potential_escape_to_node = False
            ).save()

            if sa.metadata.annotations and "iam.gke.io/gcp-service-account" in sa.metadata.annotations.keys():
                gcp_sa_email = sa.metadata.annotations.get("iam.gke.io/gcp-service-account")
                gcpsa_obj = GcpServiceAccount(email=gcp_sa_email).save()

                reasons=["KSA->GSA: Workload identity access"]
                title="KSA->GSA: Workload identity access"
                summary="The KSA was given Workload identity access to the GSA. For more info read https://book.hacktricks.xyz/cloud-security/pentesting-kubernetes/kubernetes-access-to-other-clouds"
                limitations=""

                sa_obj = sa_obj.privesc_to(gcpsa_obj, reasons=reasons, title=title, summary=summary, limitations=limitations)

            if sa.secrets:
                for secret in sa.secrets:
                    secret_obj = K8sSecret(name = f"{ns_name}:{secret.name}").save()
                    secret_obj.namespaces.update(ns_obj)
                    secret_obj.save()
                    sa_obj.secrets.update(secret_obj)

            sa_obj.namespaces.update(ns_obj)
            sa_obj.save()
