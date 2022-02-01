import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_bigquery import GcpBqDataset, GcpBqTable

class DiscBigquery(GcpDisc):
    resource = 'bigquery'
    version = 'v2'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the biqeury datasets and tables buckets from each project discovered.

        This module will create the bigqeury datasets and table objects and relate them with the parent project and get the IAM privileges.
        """

        http_prep = self.service.projects()#.list()
        projects: List[dict] = self.execute_http_req(http_prep, "projects")
        self._disc_loop(projects, self._disc_datasets, __name__.split(".")[-1])

    
    def _disc_datasets(self, project: GcpProject):
        """Discover all the datasets of a project"""
        
        project_id: str = project["id"]
        http_prep = self.service.datasets()#.list(projectId=project_id)
        datasets: List[str] = self.execute_http_req(http_prep, "datasets", list_kwargs={"projectId": project_id})

        if datasets:
            p_obj: GcpProject = GcpProject(name=f"projects/{project_id}").save()

        for ds in datasets:
            ds_obj: GcpBqDataset = GcpBqDataset(
                name = ds["id"],
                datasetId = ds["datasetReference"]["datasetId"],
                displayName = ds.get("friendlyName", ""),
                resource_name = f"projects/{project_id}/datasets/{ds['datasetReference']['datasetId']}"
            ).save()
            ds_obj.projects.update(p_obj, zone=ds.get("location", ""))
            ds_obj.save()

            self._disc_tables(ds_obj, project_id)
    
    
    def _disc_tables(self, ds_obj: GcpBqDataset, project_id):
        """Discover all the tables of a dataset"""

        http_prep = self.service.tables()#.list(datasetId=ds_obj.datasetId, projectId=project_id)
        tables: List[str] = self.execute_http_req(http_prep, "tables", disable_warn=True, list_kwargs={"datasetId": ds_obj.datasetId, "projectId": project_id})

        for table in tables:
            table_obj: GcpBqTable = GcpBqTable(
                name = table["id"],
                tableID = table["tableReference"]["tableId"],
                resource_name = f"{ds_obj.resource_name}/tables/{table['tableReference']['tableId']}",
                type = table.get("type", "")
            ).save()
            ds_obj.bgtables.update(table_obj)

            self.get_iam_policy(table_obj, self.service.tables(), table_obj.resource_name)
            #TODO: call self._get_rowAccessPolicies(table_obj, ds_obj.datasetId, project_id)
        
        ds_obj.save()

    def _get_rowAccessPolicies(self, table_obj, ds_id, project_id):
        http_prep = self.service.rowAccessPolicies()#.list(datasetId=ds_id, projectId=project_id, tableId=table_obj.tableID)
        access_policies: List[str] = self.execute_http_req(http_prep, "something", list_kwargs={"datasetId": ds_id, "projectId": project_id, "tableId": table_obj.tableID})
        # TODO: create for loop
        
        # TODO: Get IAM privileges for access policies
        #self.get_iam_policy(access_policy_obj, self.service.rowAccessPolicies(), access_policy_obj.resource_name)
