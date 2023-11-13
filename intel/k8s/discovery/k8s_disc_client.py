import logging
import os
import yaml
import requests
import subprocess
from os.path import exists
from shutil import which

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

            self.k8s_config: dict = yaml.safe_load(b64decode(self.env_var_content))
            assert bool(self.k8s_config.get("k8s", None)), "Kubernetes env variable isn't a correct yaml"
            self.creds: dict = self._k8s_creds()

    def _k8s_creds(self):
        creds: list = []

        for entry in self.k8s_config["k8s"]:
            if cred := self._get_cred(entry):
                creds.append(cred)
        return creds

    def _get_cred(self, entry):
        if entry.get("file_path"):
            assert exists(entry.get("file_path")), "Indicated file path to config doesn't exist"

            if which("kubectl") is None:
                self.logger.error("Kubectl not found, it won't be possible to refresh the kubernetes token")

            else:  # Call kubectl to reload the token to use (I could't find any other way to do this through python)
                env = {"KUBECONFIG": entry.get("file_path"), "PATH": os.getenv("PATH")}
                subprocess.Popen(['kubectl', '--request-timeout', '5s', 'get', 'namespaces'], env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()

            api_client = config.kube_config.new_client_from_config(config_file=entry.get("file_path"))

        else:
            api_client = self._extracted_from__get_cred_16(entry)
        try:
            # Test that the Kube-API is accessible
            requests.get(api_client.configuration.host, verify=False, timeout=10)
            return {"cred": api_client, "cluster_id": entry.get("cluster_id", ""), "config": entry}

        except Exception:
            self.logger.error(f"I cannot check Kubernetes because I cannot access {api_client.configuration.host}")
            return None

    # TODO Rename this here and in `_get_cred`
    def _extracted_from__get_cred_16(self, entry):
        token = entry.get("token")
        assert token, "Token no specified"

        url = entry.get("url")
        assert url, "URL not specified"

        configuration = client.Configuration()
        configuration.verify_ssl = False
        configuration.debug = False
        configuration.api_key_prefix['authorization'] = 'Bearer'
        configuration.api_key['authorization'] = token
        configuration.host = url
        return client.ApiClient(configuration)
