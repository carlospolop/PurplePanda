import logging
import os
import yaml
import requests
from os.path import exists

from kubernetes import client, config
from base64 import b64decode

from core.utils.purplepanda import PurplePanda
from core.utils.purplepanda_config import PurplePandaConfig


"""
Example yaml:

k8s:
- token: "string"
  url: "string"
  cluster_id: "string"

- file_path: "string"
  cluster_id: "string"
"""

class K8sDiscClient(PurplePanda):
    logger = logging.getLogger(__name__)

    def __init__(self, get_creds=True, config=""):
        super().__init__()
        panop = PurplePandaConfig()

        if get_creds:
            # If given config, use that one, if not, use the env var
            if config:
                self.env_var_content = config
            else:
                self.env_var = panop.get_env_var("k8s")
                self.env_var_content = os.getenv(self.env_var)
                assert bool(self.env_var_content), "Kubernetes env variable not configured"
            
            self.k8s_config : dict = yaml.safe_load(b64decode(self.env_var_content))
            assert bool(self.k8s_config.get("k8s", None)), "Kubernetes env variable isn't a correct yaml"
            self.creds : dict = self._k8s_creds()
    
    def _k8s_creds(self):
        creds : list = []

        for entry in self.k8s_config["k8s"]:
            if entry.get("file_path"):
                assert exists(entry.get("file_path")), "Indicated file path to config doesn't exist"
                api_client = config.kube_config.new_client_from_config(config_file=entry.get("file_path"))

            else:
                token = entry.get("token")
                assert token, "Token no specified"
                
                url = entry.get("url")
                assert url, "URL not specified"
                
                configuration = client.Configuration()
                configuration.verify_ssl=False
                configuration.debug = False
                configuration.api_key_prefix['authorization'] = 'Bearer'
                configuration.api_key['authorization'] = token
                configuration.host = url
                api_client = client.ApiClient(configuration)            
            
            try:
                # Test that the Kube-API is accessible
                requests.get(api_client.configuration.host, verify=False)
                creds.append({"cred": api_client, "cluster_id": entry.get("cluster_id", "")})
            except:
                self.logger.error(f"I cannot check Kubernetes because I cannot access {api_client.configuration.host}")
                pass
        
        return creds


