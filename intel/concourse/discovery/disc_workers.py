import logging
import validators
from urllib.parse import urlparse

from intel.concourse.discovery.concourse_disc_client import ConcourseDisc
from intel.concourse.models.concourse_model import ConcourseTeam, ConcourseWorker, ConcourseResource
from core.models import PublicIP, PublicDomain

class DiscWorkers(ConcourseDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the workers
        """

        workers = self.call_concourse_api(f=self.cred.get, **{"path": "workers"})
        self._disc_loop(workers, self._disc_workers, __name__.split(".")[-1])

    
    def _disc_workers(self, worker, **kwargs):
        """Discover each worker"""

        wrkr_obj = ConcourseWorker(
            name = worker["name"],
            addr = worker.get("addr", ""),
            baggageclaim_url = worker.get("baggageclaim_url", ""),
            active_containers = worker.get("active_containers", ""),
            active_volumes = worker.get("active_volumes", ""),
            active_tasks = worker.get("active_tasks", ""),
            platform = worker.get("platform", ""),
            team = worker.get("team", ""),
            version = worker.get("version", ""),
            start_time = worker.get("start_time", ""),
            ephemeral = worker.get("ephemeral", False),
            state = worker.get("state", ""),
        ).save()

        if worker["team"]:
            team_obj = ConcourseTeam(name=worker["team"]).save()
            wrkr_obj.teams.update(team_obj)
        
        if worker["addr"]:
            uparsed = urlparse("http://" + worker["addr"]) if not "://" in worker["addr"] else urlparse(worker["addr"])
            hostname = uparsed.hostname
            if validators.domain(hostname) is True:
                dom_obj = PublicDomain(name=hostname).save()
                wrkr_obj.public_domains.update(dom_obj)

            else:
                ip_obj = PublicIP(name=hostname).save()
                wrkr_obj.public_ips.update(ip_obj)
        
        if worker["baggageclaim_url"]:
            uparsed = urlparse("http://" + worker["baggageclaim_url"]) if not "://" in worker["baggageclaim_url"] else urlparse(worker["baggageclaim_url"])
            hostname = uparsed.hostname
            if validators.domain(hostname) is True:
                dom_obj = PublicDomain(name=hostname).save()
                wrkr_obj.public_domains.update(dom_obj)

            else:
                ip_obj = PublicIP(name=hostname).save()
                wrkr_obj.public_ips.update(ip_obj)
        

        for res in worker["resource_types"]:
            res_obj = self.get_resource_obj(res)
            wrkr_obj.resources.update(res_obj)
        
        wrkr_obj.save()
