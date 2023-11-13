from core.utils.discover_saas import DiscoverSaas
from core.utils.purplepanda_prints import PurplePandaPrints

from intel.circleci.discovery.circleci_disc_client import CircleCIDiscClient
from intel.circleci.discovery.disc_orgs import DiscOrgs
from intel.circleci.discovery.disc_contexts import DiscContexts
from intel.circleci.discovery.disc_pipelines import DiscPipelines
from intel.circleci.discovery.disc_projects import DiscProjects


class PurplePandaCircleCI():
    def discover(self, **kwargs):
        cdc: CircleCIDiscClient = CircleCIDiscClient()
        initial_funcs = []
        cred = ""
        initial_funcs.extend(
            DiscoverSaas(
                initial_funcs=[
                    # DiscOrgs(cred["cred"], cred["slugs"], cred["projects"], **kwargs).discover,
                    # DiscContexts(cred["cred"], cred["slugs"], cred["projects"], **kwargs).discover,
                    DiscProjects(
                        cred["cred"], cred["slugs"], cred["projects"], **kwargs
                    ).discover,
                    DiscPipelines(
                        cred["cred"], cred["slugs"], cred["projects"], **kwargs
                    ).discover,
                ],
                parallel_funcs=[],
            ).do_discovery
            for cred in cdc.creds
        )
        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[]
        ).do_discovery()

    def analyze_creds(self):
        gdc: CircleCIDiscClient = CircleCIDiscClient()
        for cred in gdc.creds:
            cred = cred["cred"]
            PurplePandaPrints.print_title("CircleCI")
            PurplePandaPrints.print_key_val("Url", cred.url)
            user_info = cred.get_user_info()
            projects_info = user_info["projects"]
            identities_info = user_info["identities"]

            PurplePandaPrints.print_key_val("Name", user_info.get("name"))
            PurplePandaPrints.print_key_val("Login", user_info.get("login"))
            PurplePandaPrints.print_key_val("Selected email", user_info.get("selected_email"))
            PurplePandaPrints.print_key_val("All emails", user_info.get("all_emails"))
            PurplePandaPrints.print_key_val("Avatar url", user_info.get("avatar_url"))
            PurplePandaPrints.print_key_val("Admin?", user_info.get("admin"))
            PurplePandaPrints.print_key_val("Sign in count", user_info.get("sign_in_count"))
            PurplePandaPrints.print_key_val("Github Oauth Scopes", user_info.get("github_oauth_scopes"))
            PurplePandaPrints.print_key_val("Email Authentication", user_info.get("email_authentication"))
            PurplePandaPrints.print_key_val("Bitbucket Authorized", user_info.get("bitbucket_authorized"))
            PurplePandaPrints.print_key_val("Bitbucket", user_info.get("bitbucket"))
            PurplePandaPrints.print_key_val("Dev Admin", user_info.get("dev_admin"))
            print("")

            PurplePandaPrints.print_title2("Projects Followed")
            for url_proj, _ in projects_info.items():
                PurplePandaPrints.print_val(f"  {url_proj}")
            print("")

            for name, vals in identities_info.items():
                PurplePandaPrints.print_title2(name)
                PurplePandaPrints.print_dict(vals)

            PurplePandaPrints.print_separator()
