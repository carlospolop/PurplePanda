from py2neo.ogm import Property, RelatedTo, RelatedFrom, Label
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_perm_models import GcpResource


class GcpPubSubTopic(GcpResource):
    __primarylabel__ = "GcpPubSubTopic"
    __primarykey__ = "name"

    name = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    subscriptions = RelatedFrom("GcpPubSubSubscription", "TOPIC_SUBSCRIBED")
    cloudbuildTriggers = RelatedFrom("GcpCloudbuildTrigger", "TRIGGER")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpPubSubSubscription(GcpResource):
    __primarylabel__ = "GcpPubSubTopic"
    __primarykey__ = "name"

    name = Property()
    pushEndpoint = Property()

    projects = RelatedTo(GcpProject, "PART_OF")
    topics = RelatedTo(GcpPubSubTopic, "TOPIC_SUBSCRIBED")
    cloudbuildTriggers = RelatedFrom("GcpCloudbuildTrigger", "TRIGGER")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True

class GcpPubSubSchema(GcpResource):
    __primarylabel__ = "GcpPubSubSchema"
    __primarykey__ = "name"

    name = Property()
    type = Property()

    projects = RelatedTo(GcpProject, "PART_OF")

    gcp = Label(name="Gcp")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gcp = True