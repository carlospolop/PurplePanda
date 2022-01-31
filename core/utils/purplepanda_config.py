import os
import yaml


class PurplePandaConfig():
    def __init__(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = current_path + f"/../../config.yml"
        with open(self.config_path, "r") as yf:  
            self.yaml_loaded = yaml.safe_load(yf)
        
        self.platforms = [p["name"] for p in self.yaml_loaded["env_vars"]]
    
    def get_env_var(self, plat_name: str) -> str:
        for p in self.yaml_loaded["env_vars"]:
            if p["name"] == plat_name:
                return p["env_var"]
        return ""