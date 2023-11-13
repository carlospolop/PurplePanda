from typing import List
from github import Github, GithubException, RateLimitExceededException
import yaml
import os
import requests.exceptions
import logging
import time
import traceback
import github

from base64 import b64decode
from core.utils.purplepanda_config import PurplePandaConfig
from functools import wraps
from core.utils.purplepanda import PurplePanda

"""
Example yaml:

github:
- token: "string"
  username: "string"
  password: "string"
  url: "https://api.github.com/graphql"
  org_name: "string"

At least token or username+password need to be filled
URL is optional, provide it only if needed
org_name can be empty or unexistent (but better if provided to use more specific options)
"""


class GithubDiscClient(PurplePanda):
    logger = logging.getLogger(__name__)

    def __init__(self, get_creds=True, config=""):
        super().__init__()
        panop = PurplePandaConfig()

        if config:
            self.env_var_content = config
        else:
            self.env_var = panop.get_env_var("github")
            self.env_var_content = os.getenv(self.env_var)
            assert bool(self.env_var_content), "Github env variable not configured"

        self.github_config: dict = yaml.safe_load(b64decode(self.env_var_content))
        assert bool(self.github_config.get("github", None)), "Github env variable isn't a correct yaml"

        if get_creds:
            self.creds: dict = self._github_creds()

    def _github_creds(self) -> dict:
        """
        Parse github env variable and extract all the github credentials
        """

        creds: dict = []

        for entry in self.github_config["github"]:
            url = entry.get("url")
            org_name = entry.get("org_name", "")
            if entry.get("token"):
                kwargs = {"login_or_token": entry.get("token")}
                str_cred = entry.get("token")

            elif entry.get("username") and entry.get("password"):
                kwargs = {"login_or_token": entry.get("username"), "password": entry.get("password")}
                str_cred = entry.get("username") + ":" + entry.get("password")

            else:
                assert False, f"Github entry doesn't contain token or usernaame+password: {entry}"

            if url: kwargs["base_url"] = url

            cred = Github(**kwargs)

            if org_name:
                try:
                    self.call_github(cred.get_organization, ret_val=None, login=org_name)

                except Exception as e:
                    raise ValueError(
                        f"The creds doesn't have access to the organization {org_name}. Correct the name of the org or remove it. Error: {e}"
                    ) from e

            creds.append({
                "cred": cred,
                "org_name": org_name,
                "str_cred": str_cred
            })

        return creds

    def call_github(self, f, *args, **kwargs):
        """
        Call github API, control errors and return the data.
        """

        # Get ret_val vlue from kwargs
        ret_val = None
        if "ret_val" in kwargs:
            ret_val = kwargs["ret_val"]
            del kwargs["ret_val"]

        try:
            start = time.time()

            error = False
            try:
                ret = f(*args, **kwargs)
            except TypeError:
                error = True

            # Use error var and not put the second call to f in the except to not have hundreds of nested exceptions 
            if error:
                ret = f(self, *args, **kwargs)

            # Resolve the vlues here
            if type(ret) is github.PaginatedList.PaginatedList:
                ret = list(ret)

            if not error:  # Then github API was accessed
                end = time.time()
                func_name = f.__func__.__name__ if hasattr(f, "__func__") else f.__name__
                self.logger.debug(f"Github API access to {func_name} took: {int(end - start)}")

            return ret

        except RateLimitExceededException as e:
            self.logger.error(f"Sleeping 15 mins for rate limit and trying again. Error: {e}")
            time.sleep(15 * 60)
            return self.call_github(f, *args, **kwargs)

        except GithubException as e:
            if all(s not in str(e) for s in ["404", "403"]):
                self.logger.error(f"Github error: {e}")

            return ret_val

        except requests.exceptions.ReadTimeout as e:
            self.logger.error(f"Github timeout, retrying in 10s. Error: {e}")
            time.sleep(10)
            return self.call_github(f, *args, **kwargs)

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Github connection error, retrying in 10s. Error: {e}")
            time.sleep(10)
            return self.call_github(f, *args, **kwargs)

        except Exception as e:
            self.logger.error(f"Github error: {e}")
            self.logger.error(traceback.format_exc())

        return ret_val

    def call_github_decorator(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            """
            The wrapped function should NEVER return None as a expected result !
            """

            if args == (None,):
                self.logger.error("Something is trying to save None")
                return None

            r = self.call_github(f, *args, **kwargs)

            if r is None:
                self.logger.error("Error in decorator, calling it again in 10 secs")
                time.sleep(10)
                return wrapped(self, *args, **kwargs)

            return r

        return wrapped
