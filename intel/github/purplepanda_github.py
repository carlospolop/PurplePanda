from py2neo.integration import Table

from core.utils.discover_saas import DiscoverSaas
from core.utils.purplepanda_prints import PurplePandaPrints
from core.db.customogm import graph

from intel.github.discovery.github_disc_client import GithubDiscClient
from intel.github.discovery.github_disc import GithubDisc
from intel.github.discovery.analyze_results import AnalyzeResults


class PurplePandaGithub():
    def discover(self, **kwargs):
        gdc : GithubDiscClient = GithubDiscClient()
        initial_funcs = []
        for cred in gdc.creds:
            initial_funcs.append(
                DiscoverSaas(
                    initial_funcs = [
                        GithubDisc(cred["cred"], cred["org_name"], cred["str_cred"], **kwargs).discover
                    ],
                    parallel_funcs = []
                ).do_discovery
            )
        
        # Launch a thread per set of credentials
        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[AnalyzeResults(cred["cred"], cred["org_name"], cred["str_cred"], **kwargs).discover]
        ).do_discovery()


    def analyze_creds(self):
        gdc : GithubDiscClient = GithubDiscClient()
        for cred in gdc.creds:
            PurplePandaPrints.print_title("Github")
            PurplePandaPrints.print_key_val("Configured organization", cred.get('org_name'))

            c = cred["cred"]
            user = gdc.call_github(c.get_user)
            PurplePandaPrints.print_key_val("Cred username", f"{user.name} ({user.login})")
            if user.email: PurplePandaPrints.print_key_val("Cred email", user.email)
            if user.bio: PurplePandaPrints.print_key_val("Cred bio", user.bio)
            if user.blog: PurplePandaPrints.print_key_val("Cred blog", user.blog)
            if user.repos_url: PurplePandaPrints.print_key_val("Cred repos", user.repos_url)
            print("")
            PurplePandaPrints.print_title2("Organizations")

            for org in gdc.call_github(user.get_orgs):
                PurplePandaPrints.print_key_val("  Organization", f"{org.name} ({org.login})")
                if org.description: PurplePandaPrints.print_key_val("  Description", org.description)
                if org.total_private_repos: PurplePandaPrints.print_key_val("  Total Private Repos", org.total_private_repos)
                print("")
            
            PurplePandaPrints.print_separator()
