import logging
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_pubsub import GcpPubSubTopic, GcpPubSubSubscription, GcpPubSubSchema

class DiscPubSub(GcpDisc):
    resource = 'pubsub'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the pubsub from each project discovered.

        This module will create the pubsub and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_pubsub, __name__.split(".")[-1])


    def _disc_pubsub(self, p_obj:GcpProject):
        """Discover all the pubsubs of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().topics()#.list(project=project_name)
        topics: List[str] = self.execute_http_req(http_prep, "topics", disable_warn=True, list_kwargs={"project": project_name})
        for topic in topics:
            topic_obj = GcpPubSubTopic(
                name = topic["name"]
            ).save()
            topic_obj.projects.update(p_obj)
            topic_obj.save()

            self.get_iam_policy(topic_obj, self.service.projects().topics(), topic_obj.name)

        http_prep = self.service.projects().subscriptions()#.list(project=project_name)
        subscriptions: List[str] = self.execute_http_req(http_prep, "subscriptions", disable_warn=True, list_kwargs={"project": project_name})
        for sub in subscriptions:
            pushConfig = topic.get("pushConfig", {})
            sub_obj = GcpPubSubSubscription(
                name = topic["name"],
                pushEndpoint = pushConfig.get("pushEndpoint", "")
            ).save()
            sub_obj.projects.update(p_obj)

            topic_name = sub["topic"]
            topic_obj = GcpPubSubTopic(name = topic_name).save()
            sub_obj.topics.update(topic_obj)
            sub_obj.save()

            self.get_iam_policy(sub_obj, self.service.projects().topics(), sub_obj.name)
        

        http_prep = self.service.projects().schemas()#.list(parent=project_name)
        schemas: List[str] = self.execute_http_req(http_prep, "schemas", disable_warn=True, list_kwargs={"parent": project_name})
        for schema in schemas:
            schema_obj = GcpPubSubSchema(
                name = schema["name"],
                pushEndpoint = schema["type"]
            ).save()
            schema_obj.projects.update(p_obj)
            schema_obj.save()

            self.get_iam_policy(schema_obj, self.service.projects().schemas(), schema_obj.name)