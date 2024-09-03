import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models import GcpSqlInstance, GcpNetwork, GcpSqlDB
from core.models import PublicIP


class DiscSql(GcpDisc):
    resource = 'sqladmin'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the SQL databases of each project
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_sql_instances, __name__.split(".")[-1])
    

    def _disc_sql_instances(self, p_obj:GcpProject):
        """Discover all the SQL instances of a project"""

        project_name: str = p_obj.name.split("/")[-1]
        http_prep = self.service.instances()#.list(project=project_name)
        instances: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_name})
        for i in instances:
            inst_obj = GcpSqlInstance(
                name = f'{p_obj.name}/instances/{i["name"]}',
                state = i["state"],
                databaseVersion = i.get("databaseVersion", ""),
                backendType = i["backendType"],
                selfLink = i["selfLink"],
                connectionName = i.get("connectionName", ""),
                region = i["region"],
                databaseInstalledVersion = i.get("databaseVersion", ""),
                createTime = i["createTime"],
                requireSsl = i.get("settings", {}).get("ipConfiguration", {}).get("requireSsl", False),
                ipAddresses = [ip["ipAddress"] for ip in i["ipAddresses"]]
            ).save()
            inst_obj.projects.update(p_obj, zone=i["region"])
            inst_obj.save()

            for ip in i["ipAddresses"]:
                if ip["ipAddress"]:
                    ip_obj = PublicIP(name=ip["ipAddress"]).save()
                    inst_obj.public_ips.update(ip_obj)
                    inst_obj.save()
            
            net = i.get("settings", {}).get("ipConfiguration", {}).get("privateNetwork", "")
            if net:
                network_obj = GcpNetwork(name = net).save()
                inst_obj.networks.update(network_obj)
                network_obj.save()
        
            if i.get("serviceAccountEmailAddress"):
                inst_obj.relate_sa(i.get("serviceAccountEmailAddress"), [])
            
            self._disc_sql_databases(p_obj, inst_obj)


    def _disc_sql_databases(self, p_obj:GcpProject, inst_obj:GcpSqlInstance):
        """Discover all the SQL databases of a project"""

        project_name: str = p_obj.name.split("/")[-1]
        http_prep = self.service.databases()#.list(project=project_name)
        databases: List[str] = self.execute_http_req(http_prep, "items", disable_warn=True, list_kwargs={"project": project_name, "instance":inst_obj.name.split("/")[-1]})
        for db in databases:
            db_obj = GcpSqlDB(
                name = "projects/" + db["selfLink"].split("projects/")[-1],
                selfLink = db["selfLink"],
            ).save()
            db_obj.projects.update(p_obj, zone=inst_obj.region)
            db_obj.instances.update(inst_obj)
            db_obj.save()
