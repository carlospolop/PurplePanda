import subprocess
from core.utils.discover_saas import DiscoverSaas
from core.utils.purplepanda_prints import PurplePandaPrints
from intel.google.discovery.gcp_disc_client import GcpDiscClient, GcpDisc

from intel.google.discovery.disc_groups_users import DiscGroupsUsers
from intel.google.discovery.disc_folders import DiscFolders
from intel.google.discovery.disc_orgs import DiscOrgs
from intel.google.discovery.disc_projects import DiscProjects
from intel.google.discovery.disc_custom_roles_permissions import DiscCustomRolesPermissions
from intel.google.discovery.disc_sa import DiscServiceAccounts
from intel.google.discovery.disc_cloud_functions import DiscCloudFunctions
from intel.google.discovery.disc_storage import DiscStorage
from intel.google.discovery.disc_compute_instances import DiscComputeInstances
from intel.google.discovery.disc_compute_networks import DiscComputeNetworks
from intel.google.discovery.disc_compute_subnetworks import DiscComputeSubnetworks
from intel.google.discovery.disc_composer import DiscComposer
from intel.google.discovery.disc_clusters import DiscClusters
from intel.google.discovery.disc_bigquery import DiscBigquery
from intel.google.discovery.disc_cloud_run import DiscCloudRun
from intel.google.discovery.disc_pubsub import DiscPubSub
from intel.google.discovery.disc_secrets import DiscSecrets
from intel.google.discovery.disc_cloudbuild import DiscCloudbuild
from intel.google.discovery.disc_sourcerepo import DiscSourceRepos
from intel.google.discovery.disc_kms import DiscKMS
from intel.google.discovery.disc_dns import DiscDns
from intel.google.discovery.disc_sql import DiscSql
from intel.google.discovery.disc_org_policies import DiscOrgPolicies
from intel.google.discovery.analyze_results import AnalyzeResults


class PurplePandaGoogle():

    def discover(self, **kwargs):
        config = kwargs.get("config", "")
        gdc: GcpDiscClient = GcpDiscClient(config=config)
        initial_funcs = []
        for cred in gdc.creds:
            initial_funcs.append(
                DiscoverSaas(
                    initial_funcs=[
                        DiscOrgs(cred=cred["cred"], **kwargs).discover,
                        DiscFolders(cred=cred["cred"], **kwargs).discover,
                        DiscProjects(cred=cred["cred"], **kwargs).discover,
                        DiscOrgPolicies(cred=cred["cred"], **kwargs).discover,
                        DiscCustomRolesPermissions(cred=cred["cred"], **kwargs).discover,
                        DiscServiceAccounts(cred=cred["cred"], **kwargs).discover,
                        DiscGroupsUsers(cred=cred["cred"], **kwargs).discover,
                        DiscStorage(cred=cred["cred"], **kwargs).discover,
                        DiscComputeSubnetworks(cred=cred["cred"], **kwargs).discover,  # Needed by DiscClusters
                        DiscClusters(cred=cred["cred"], **kwargs).discover,
                        DiscSecrets(cred=cred["cred"], **kwargs).discover
                    ],

                    parallel_funcs=[
                        [DiscKMS(cred=cred["cred"], **kwargs).discover],
                        [DiscComposer(cred=cred["cred"], **kwargs).discover],
                        [DiscBigquery(cred=cred["cred"], **kwargs).discover],
                        [
                            DiscComputeInstances(cred=cred["cred"], **kwargs).discover,
                            DiscComputeNetworks(cred=cred["cred"], **kwargs).discover,
                        ],
                        [DiscPubSub(cred=cred["cred"], **kwargs).discover],
                        [DiscCloudRun(cred=cred["cred"], **kwargs).discover],
                        [DiscCloudFunctions(cred=cred["cred"], **kwargs).discover],
                        [DiscCloudbuild(cred=cred["cred"], **kwargs).discover],
                        [DiscSourceRepos(cred=cred["cred"], **kwargs).discover],
                        [DiscDns(cred=cred["cred"], **kwargs).discover],
                        [DiscSql(cred=cred["cred"], **kwargs).discover]
                    ],
                    final_funcs=[DiscServiceAccounts(cred=cred["cred"], **kwargs).discover]
                    # Re-discover and re-relate possible missing SAs with projects
                ).do_discovery
            )

        # In GCP just launch an analysis at the end of all the creds
        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[AnalyzeResults(cred="").discover]
        ).do_discovery()

    def analyze_creds(self):
        gdc: GcpDiscClient = GcpDiscClient()
        for cred in gdc.creds:
            PurplePandaPrints.print_title("Google")
            cmd = ["gcloud", "config", "list"]
            if hasattr(cred["cred"], "service_account_email"):
                cmd.append(f"--impersonate-service-account={cred['cred'].service_account_email}")

            (output, err) = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            for line in output.splitlines():
                line = line.decode("utf-8")
                if "=" in line:
                    PurplePandaPrints.print_key_val(line.split("=")[0].strip(), line.split("=")[1].strip())
                else:
                    print(line)

            gd = GcpDisc(cred["cred"], resource="cloudresourcemanager", version="v1")
            prep_http = gd.service.organizations().search(body={})
            if organizations := gd.execute_http_req(prep_http, "organizations"):
                PurplePandaPrints.print_title2("Organizations")
                for o in organizations:
                    PurplePandaPrints.print_key_val("  Organization", f"{o['displayName']} ({o['name']})")
                    PurplePandaPrints.print_key_val("  Workspace Owner ID", o['owner']['directoryCustomerId'])
                    print("")

            PurplePandaPrints.print_separator()
