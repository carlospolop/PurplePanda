import os
import yaml


class PurplePandaConfig():
    def __init__(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = f"{current_path}/../../config.yml"
        with open(self.config_path, "r") as yf:
            self.yaml_loaded = yaml.safe_load(yf)

        self.platforms = [p["name"] for p in self.yaml_loaded["env_vars"]]

    def get_env_var(self, plat_name: str) -> str:
        return next(
            (
                p["env_var"]
                for p in self.yaml_loaded["env_vars"]
                if p["name"] == plat_name
            ),
            "",
        )
