import logging
from opcode import hasconst
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_secrets import GcpSecret, GcpSecretVersion
from google.cloud import secretmanager


class DiscSecrets(GcpDisc):
    resource = 'secretmanager'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the secrets accesible by the active account.

        This module will relate secrets with parent projects.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_secrets, __name__.split(".")[-1])


    def _disc_secrets(self, p_obj:GcpProject):
        """Discover all the secrets of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().secrets()#.list(parent=project_name)
        secrets: List[str] = self.execute_http_req(http_prep, "secrets", list_kwargs={"parent": project_name})

        for secret in secrets:
            secret_obj:GcpSecret = GcpSecret(
                name=secret["name"],
                createTime=secret["createTime"]
            ).save()
            secret_obj.projects.update(p_obj)
            secret_obj.save()

            http_prep = self.service.projects().secrets().versions()
            versions: List[str] = self.execute_http_req(http_prep, "versions", list_kwargs={"parent": secret["name"]})
            for version in versions:
                sv_obj = GcpSecretVersion(name=version["name"]).save()
                # Read secrets if configured to do so
                if self.gcp_get_secret_values:
                    client = secretmanager.SecretManagerServiceClient()
                    try:
                        resp = client.access_secret_version(name=version["name"])
                        if hasattr(resp, "payload") and hasattr(resp.payload, "data"):
                            sv_obj.value = str(resp.payload.data)
                            sv_obj.save()
                    except Exception:
                        pass
                
                secret_obj.versions.update(sv_obj)
            
            secret_obj.save()
        
            self.get_iam_policy(secret_obj, self.service.projects().secrets(), secret_obj.name)
