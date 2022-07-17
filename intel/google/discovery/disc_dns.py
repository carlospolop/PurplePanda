import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models import GcpManagedZone, GcpResourceRecord
from core.models import PublicIP, PublicDomain


class DiscDns(GcpDisc):
    resource = 'dns'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the dns managed zones from each project discovered.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_managed_zones, __name__.split(".")[-1])
    

    def _disc_managed_zones(self, p_obj:GcpProject):
        """Discover all the managed zones of a project"""

        project_name: str = p_obj.name.split("/")[-1]
        http_prep = self.service.managedZones()#.list(project=project_name)
        managedZones: List[str] = self.execute_http_req(http_prep, "managedZones", disable_warn=True, list_kwargs={"project": project_name})
        for mz in managedZones:
            private_nets = mz.get("privateVisibilityConfig", {}).get("networks", {})
            networks = [n["networkUrl"] for n in private_nets]
            visibility = mz.get("visibility", "")

            mz_obj = GcpManagedZone(
                name = p_obj.name + "/managedZones/" + mz["name"],
                dnsName = mz["dnsName"],
                displayName = mz.get("displayName", ""),
                description = mz.get("description", ""),
                id = mz.get("id", ""),
                nameServers = mz.get("nameServers", []),
                creationTime = mz.get("creationTime", ""),
                visibility = visibility,
                networks = networks
            ).save()
            mz_obj.projects.update(p_obj)
            mz_obj.save()

            if visibility == "public":
                domain = mz["dnsName"][:-1] if mz["dnsName"].endswith(".") else mz["dnsName"]
                dom_obj = PublicDomain(domain=domain).save()
                mz_obj.public_domains.update(dom_obj)
                mz_obj.save()

            self.get_iam_policy(mz_obj, self.service.managedZones(), mz_obj.name)

            self._disc_records(p_obj, mz_obj, visibility)
    
    def _disc_records(self, p_obj:GcpProject, mz_obj: GcpManagedZone, visibility: str):
        """Discover all the dns records of a managed zone"""

        http_prep = self.service.resourceRecordSets()#.list(project=project_name,managedZone=zone)
        rrsets: List[str] = self.execute_http_req(
            http_prep, "rrsets", disable_warn=True, 
            list_kwargs={"managedZone": mz_obj.name.split("/")[-1], "project": p_obj.name.split("/")[-1]}
            )
        
        for rrset in rrsets:
            rrset_obj = GcpResourceRecord(
                name = rrset["name"],
                type = rrset.get("type", ""),
                ttl = rrset.get("ttl", ""),
                rrdata = rrset.get("rrdatas", []),
                signatureRrdata = rrset.get("signatureRrdatas", []),
            ).save()

            if visibility == "public":
                domain = rrset["name"][:-1] if rrset["name"].endswith(".") else rrset["name"]
                dom_obj = PublicDomain(domain=domain).save()
                mz_obj.public_domains.update(dom_obj)
                mz_obj.save()
            
            if rrset.get("type", "") in ["A", "AAAA"]:
                for ip in rrset["rrdatas"]:
                    ip_obj = PublicIP(ip=ip).save()
                    rrset_obj.public_ips.update(ip_obj)
                    rrset_obj.save()
                    dom_obj.public_ips.update(ip_obj)
                    dom_obj.save()
