import logging
from typing import List
from tld import get_tld

from core.models.models import PublicDomain, PublicIP
from intel.github.models.github_model import GithubRepo
from core.utils.purplepanda import PurplePanda
from core.db.customogm import graph

class AnalyzeResults(PurplePanda):
    logger = logging.getLogger(__name__)
    known_ppals_with_role = {}
    task_name = "Generic"
    
    def discover(self) -> None:
        self._disc()
    

    def _disc(self) -> None:
        """
        After getting all the info from all the modules, obtain more information from the found data.
        """

        # Get the domain info before the IPs info
        domains: List[PublicDomain] = PublicDomain.get_all()
        self._disc_loop(domains, self._get_domain_info, __name__.split(".")[-1]+"._get_domain_info")

        ips: List[PublicIP] = PublicIP.get_all()
        self._disc_loop(ips, self._get_ip_info, __name__.split(".")[-1]+"._get_ip_info")

        self._disc_loop([None], self._get_repos_privescs, __name__.split(".")[-1]+"._get_repos_privescs")
        
    
    def _get_domain_info(self, dom_obj: PublicDomain):
        """Get info from all the PublicDomains discovered"""

        is_real = get_tld(dom_obj.name, fix_protocol=True, fail_silently=True) is not None
        dom_obj.is_real = is_real
        dom_obj.save()

        if is_real:
            for ip in self.get_domain_ips(dom_obj.name):
                ip_private = self.is_ip_private(ip)
                
                if not ip_private:
                    dom_obj.is_external = True
                
                ip_obj = PublicIP(ip=ip, is_private=ip_private).save()
                dom_obj.public_ips.update(ip_obj)
            
            dom_obj.save()
            

    def _get_ip_info(self, ip_obj: PublicIP):
        """Get info from all the PublicIps discovered"""
        
        ip_obj.isprivate = self.is_ip_private(ip_obj.ip)
        ip_obj.save()
        self.get_open_ports(ip_obj)

    def _get_repos_privescs(self, _):
        """
        Relate potential privilege escalations by merging into a repo:
        - If a resource mirror a repo and has a RUN_IN relation, can escalate to there
        - If a resource mirror a repo and has a relation to another resource with a RUN_IN relation, can escalate to there
        """

        query1 = """MATCH (ppal)-[r_merge:CAN_MERGE]->(b)<-[r_branch:HAS_BRANCH]-(repo)<-[r_mirror:IS_MIRROR]-(mirror)<-[r_run_in:RUN_IN]-(sa)
                MERGE (ppal)-[:PRIVESC {title:"Can merge in executed mirror code", reason:"Can merge in "+repo.full_name+" which is mirrored by "+mirror.name+" which run the SA"}]->(sa)
                return ppal """
        
        query2 = """MATCH (ppal)-[r_merge:CAN_MERGE]->(b)<-[r_branch:HAS_BRANCH]-(repo)<-[r_mirror:IS_MIRROR]-(mirror)-[r]-(res)<-[r_run_in:RUN_IN]-(sa)
                MERGE (ppal)-[:PRIVESC {title:"Can merge in executed mirror code", reason:"Can merge in "+repo.full_name+" which is mirrored by "+mirror.name+" which is used by "+res.name+" which run the SA"}]->(sa)
                return ppal """

        graph.evaluate(query1)
        graph.evaluate(query2)
