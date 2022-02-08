import argparse
import logging
import os
from rich.logging import RichHandler
from rich import print
from time import sleep

from core.utils.purplepanda import set_verbose, PurplePanda
import core.utils.purplepanda
from core.utils.purplepanda_config import PurplePandaConfig
from core.utils.purplepanda_prints import PurplePandaPrints
from intel.generic.discovery.analyze_results import AnalyzeResults

from intel.google.purplepanda_google import PurplePandaGoogle
from intel.github.purplepanda_github import PurplePandaGithub
from intel.k8s.purplepanda_k8s import PurplePandaK8s

from intel.github.discovery.github_disc_client import GithubDiscClient
from intel.google.discovery.gcp_disc_client import GcpDiscClient
from intel.k8s.discovery.k8s_disc_client import K8sDiscClient


logger = logging.getLogger("main")
logging.getLogger("googleapiclient.http").setLevel(logging.ERROR)
logging.getLogger("google.auth._default").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)


def main():
    currently_available = PurplePandaConfig().platforms
    currently_available_str = ", ".join(currently_available)

    help_msg=f"""Enumerate different cloud platforms.\n
    Platforms available: {currently_available_str}.\n
    You need to indicate '-e' or '-a' at least.\n
    Google: The tool will try to get info about all the supported resources and find privesc paths within kubernetes and with other clouds/SaaS\n
    Gihub: By default, all the organizations and users the tokens belongs to will be analized. If you just want to analyze specified organizations in the tokens, check the '--github-*' params.\n
    Kubernetes: The tool will try to get info about all the supported resources and find privesc paths within kubernetes and with other clouds/SaaS.\n
    """
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('-a', '--analyze', action='store_true', default=False, required=False, help=f'Fast analysis of the indicated (comma-separated) platform credentials.')
    parser.add_argument('-e', '--enumerate', action='store_true', default=False, required=False, help=f'Enumerate the assets of the indicated (comma-separated) platforms.')
    parser.add_argument('-p', '--platforms', type=str, required=True, help=f'Comma-separated list of platforms to analyze/enumerate. Currently available: {currently_available_str}')
    parser.add_argument('-t', '--threads', type=int, default=15, required=False, help=f'Number of threads to use (default=15)')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, required=False, help=f'Do not remove the progress bar when the task is done')
    parser.add_argument('-d', '--directory', type=str, required=False, help=f'Path to the directory to save an initial analisys of the results in CVS (separator="|") format. If you don\'t indicate any, no analysis will be written to disk')
    
    parser.add_argument('--github-only-org', action='store_true', default=False, required=False, help=f'Only get information of the specified github orgs (no personal repos info')
    parser.add_argument('--github-only-org-and-org-users', action='store_true', default=False, required=False, help=f'Only get information of the specified github orgs and users of the specified orgs')
    parser.add_argument('--github-all-branches', action='store_true', default=False, required=False, help=f'By default data of only default branch of each repo is gathered, set this to get info from all branches of each repo')
    parser.add_argument('--github-no-leaks', action='store_true', default=False, required=False, help=f'Do not try to find leaks in repos')
    parser.add_argument('--github-get-redundant-info', action='store_true', default=False, required=False, help=f'If the passed credentials arent org admin, activating this may get you more info (and will also take more time)')
    parser.add_argument('--github-get-archived', action='store_true', default=False, required=False, help=f'By default not relations of archived repos are gathered')
    parser.add_argument('--github-write-as-merge', action='store_true', default=False, required=False, help=f'By default if the user doesn\'t have perms to see the branch protection, only codeowners and admins are supposed to be able to merge in the branch (low false possitives rate). With this option you can indicate to treat anyone with write permissions as if he has merge permissions (high false possitives rate potencially).')
    
    parser.add_argument('--k8s-get-secret-values', action='store_true', default=False, required=False, help=f'Get the secret values (if you have access')
    parser.add_argument('--gcp-get-secret-values', action='store_true', default=False, required=False, help=f'Get the secret values (if you have access')

    args = parser.parse_args()    
    platforms = args.platforms.lower().split(",")
    analyze = args.analyze
    plat_enumerate = args.enumerate
    directory = args.directory

    if not analyze and not plat_enumerate:
        logger.error(f"Error: Indicate '-a' or '-e'")
        parser.print_help()
        exit(1)
    
    if directory:
        if (not os.path.exists(directory) or not os.path.isdir(directory) or not os.access(directory, os.W_OK)):
            logger.error(f"Error: Output directory doesn't exist or isn't a directory or isn't writable")
            parser.print_help()
            exit(1)
        
        directory = f"{directory}/purplepanda_analisys"
        if not os.path.exists(directory):
            os.mkdir(directory)

    github_only_org = args.github_only_org
    github_only_org_and_org_users = args.github_only_org_and_org_users
    github_all_branches = args.github_all_branches
    github_no_leaks = args.github_no_leaks
    github_get_redundant_info = args.github_get_redundant_info
    github_get_archived = args.github_get_archived
    github_write_as_merge = args.github_write_as_merge

    k8s_get_secret_values = args.k8s_get_secret_values
    gcp_get_secret_values = args.gcp_get_secret_values
    set_verbose(args.verbose)

    # Check the user input platforms are well-written
    for platform in platforms:
        if not platform in currently_available:
            logger.error(f"Error: Platform {platform} wasn't found")
            parser.print_help()
            exit(1)

    # Configuration parsing checks
    if "google" in platforms: GcpDiscClient()
    if "github" in platforms: GithubDiscClient()
    if "k8s" in platforms: K8sDiscClient()

    if analyze:
        if "google" in platforms: PurplePandaGoogle().analyze_creds()
        if "github" in platforms: PurplePandaGithub().analyze_creds()
        if "k8s" in platforms: PurplePandaK8s().analyze_creds()


    elif plat_enumerate:
        # Launch each SaaS discovery module in its own thread (we cannot use diffrent process or they will figth for the progress bar of "rich")
        functions = []
        
        # Google
        if "google" in platforms:
            functions.append((PurplePandaGoogle().discover, "google",
                {
                    "gcp_get_secret_values": gcp_get_secret_values
                }
            ))
        
        # Github
        if "github" in platforms:
            functions.append((PurplePandaGithub().discover, "github", 
                {
                    "github_only_org": github_only_org,
                    "github_only_org_and_org_users": github_only_org_and_org_users,
                    "all_branches": github_all_branches,
                    "github_no_leaks": github_no_leaks,
                    "github_get_redundant_info": github_get_redundant_info,
                    "github_get_archived": github_get_archived,
                    "github_write_as_merge": github_write_as_merge
                }
            ))
        
        # Kubernetes
        if "k8s" in platforms:
            functions.append((PurplePandaK8s().discover, "kubernetes",
                {
                    "k8s_get_secret_values": k8s_get_secret_values
                }
            ))
        
        start_discovery(functions)
    
        # Perform a combined analisys
        AnalyzeResults().discover()

        # If directory specified write some analysis in CSV files
        if directory:
            write_csv_functions = []
            for plat_name in currently_available:
                    write_csv_functions.append((PurplePanda().write_analysis, plat_name, {
                            "name": plat_name, "directory": directory
                        }
                    ))
        
            start_discovery(write_csv_functions, writing_analysis=True)
    
        print("Finished!")


def start_discovery(functions: list, writing_analysis=False):
    threads = []
    for function, name, kwargs in functions:
        if not writing_analysis:
            logger.info(f"Enumerating {name}...")
        else:
            logger.info(f"Writting analysis of {name}...")

        threads.append(core.utils.purplepanda.POOL.submit(function, **kwargs))
    
    while any(not t.done() for t in threads):
        sleep(5)
    
    for t in threads:
        t.result()


if __name__ == "__main__":
    # It's very important to maintain the progress initializated here with the main thread or the whole output could stop working if you init it in a different thread
    with core.utils.purplepanda.PROGRESS:
        PurplePandaPrints.print_logo()
        main()
