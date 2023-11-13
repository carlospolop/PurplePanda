from core.utils.discover_saas import DiscoverSaas
from core.utils.purplepanda_prints import PurplePandaPrints

from intel.concourse.discovery.concourse_disc_client import ConcourseDiscClient
from intel.concourse.discovery.disc_teams import DiscTeams
from intel.concourse.discovery.disc_workers import DiscWorkers
from intel.concourse.discovery.disc_pipeline import DiscPipelines
from intel.concourse.discovery.disc_active_user import DiscActiveUsers


class PurplePandaConcourse():
    def discover(self, **kwargs):
        gdc: ConcourseDiscClient = ConcourseDiscClient()
        initial_funcs = []
        cred = ""
        initial_funcs.extend(
            DiscoverSaas(
                initial_funcs=[
                    DiscTeams(cred["cred"], **kwargs).discover,
                    DiscWorkers(cred["cred"], **kwargs).discover,
                    DiscPipelines(cred["cred"], **kwargs).discover,
                    DiscActiveUsers(cred["cred"], **kwargs).discover,
                ],
                parallel_funcs=[],
            ).do_discovery
            for cred in gdc.creds
        )
        DiscoverSaas(
            initial_funcs=initial_funcs,
            parallel_funcs=[],
            final_funcs=[]
        ).do_discovery()

    def analyze_creds(self):
        gdc: ConcourseDiscClient = ConcourseDiscClient()
        for cred in gdc.creds:
            PurplePandaPrints.print_title("Concourse")
            PurplePandaPrints.print_key_val("Url", cred.url)

            PurplePandaPrints.print_title2("Teams")
            for t in cred.list_teams():
                PurplePandaPrints.print_key_val(f"  {t['id']}", t["name"])

            PurplePandaPrints.print_separator()
