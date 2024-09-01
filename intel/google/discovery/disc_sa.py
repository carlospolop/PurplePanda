import logging
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_api_key import GcpApiKey
from intel.k8s.models.k8s_model import K8sNamespace, K8sServiceAccount

class DiscServiceAccounts(GcpDisc):
    resource = 'iam'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the service accounts from each project discovered.

        This module will create the service accounts and relate them with the parent project, even default project SAs.
        """

        # Get custom service accounts
        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_sas, __name__.split(".")[-1]+"._disc_sas")

        sas: List[GcpServiceAccount] = GcpServiceAccount.get_all()
        self._disc_loop(sas, self._disc_special_sas, __name__.split(".")[-1]+"._disc_special_sas")


    def _disc_sas(self, p_obj:GcpProject):
        """Discover all the service accounts of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().serviceAccounts()#.list(name=project_name)
        accounts: List[str] = self.execute_http_req(http_prep, "accounts", disable_warn=True, list_kwargs={"name": project_name})
        for sa in accounts:
            sa_name = sa["name"]

            sa_obj = GcpServiceAccount(
                name = sa_name,
                uniqueId = sa["uniqueId"],
                email = sa["email"],
                displayName = sa.get("displayName", ""),
                description = sa.get("description", "")
            ).save()
            sa_obj.projects.update(p_obj)
            sa_obj.save()

            http_prep = self.service.projects().serviceAccounts().keys()#.list(name=sa_name)
            keys: List[str] = self.execute_http_req(http_prep, "keys", list_kwargs={"name": sa_name})
            for key in keys:
                api_key_obj: GcpApiKey = GcpApiKey(
                    name=key["name"],
                    validAfterTime=key["validAfterTime"],
                    validBeforeTime=key["validBeforeTime"],
                    keyAlgorithm=key.get("keyAlgorithm", ""),
                    keyOrigin=key["keyOrigin"],
                    keyType=key["keyType"],
                )
                api_key_obj.service_accounts.update(sa_obj)
                api_key_obj.save()

            self.get_iam_policy(sa_obj, self.service.projects().serviceAccounts(), sa_obj.name)


    def _disc_special_sas(self, sa_obj:GcpServiceAccount):
        """Get information of special service accounts"""

        # Get default service accounts already discovered when checking organization and projects IAMs
        email = sa_obj.email
        if "gserviceaccount.com" == email[-len("gserviceaccount.com"):]:
            if not sa_obj.name:
                sa_obj = self._get_save_sa_info_from_email(sa_obj)
            
            if sa_obj.name:
                self.get_iam_policy(sa_obj, self.service.projects().serviceAccounts(), sa_obj.name)
            else:
                if not "@security-center-api.iam.gserviceaccount.com" in email:
                    self.logger.info(F"Unknown service account with {email} (managed by google?)")
        
        elif ".svc.id.goog[" in email: # GCP-K8s SA example: name-project-1234.svc.id.goog[k8s-namespace/k8s-sa-name]
            k8s_ns_name = email.split(".svc.id.goog[")[1].split("/")[0]
            k8s_sa_name = email.split(".svc.id.goog[")[1].split("/")[1][:-1] #Remove last "]"
            k8s_ns_obj = K8sNamespace(name=k8s_ns_name).save()
            k8s_sa_obj = K8sServiceAccount(name=f"{k8s_ns_name}:{k8s_sa_name}", potential_escape_to_node=False).save()
            k8s_sa_obj.namespaces.update(k8s_ns_obj)
            k8s_sa_obj.save()

            reasons=["KSA->GSA: Workload identity access"]
            title="KSA->GSA: Workload identity access"
            summary="The KSA was given Workload identity access to the GSA. For more info read https://book.hacktricks.xyz/cloud-security/pentesting-kubernetes/kubernetes-access-to-other-clouds"
            limitations=""
            k8s_sa_obj = k8s_sa_obj.privesc_to(sa_obj, reasons=reasons, title=title, summary=summary, limitations=limitations)
