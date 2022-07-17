from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from core.db.customogm import CustomOGM
from core.models import PublicIP, PublicDomain, RunsContainerImage, CodeMirror


class ConcoursePrincipal(CustomOGM):
    __primarylabel__ = "ConcoursePrincipal"

    teams = RelatedTo("ConcourseTeam", "HAS_ROLE")
    
    principal = Label(name="ConcoursePrincipal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.principal = True


class ConcourseUser(ConcoursePrincipal):
    __primarylabel__ = "ConcourseUser"
    __primarykey__ = "name"

    name = Property()
    last_login = Property()

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseGroup(ConcoursePrincipal):
    __primarylabel__ = "ConcourseGroup"
    __primarykey__ = "name"

    name = Property()

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseTeam(ConcoursePrincipal):
    __primarylabel__ = "ConcourseTeam"
    __primarykey__ = "name"

    name = Property()
    id = Property()

    principals = RelatedFrom(ConcoursePrincipal, "HAS_ROLE")
    workers = RelatedFrom("ConcourseWorker", "IN_TEAM")
    pipelines = RelatedFrom("ConcoursePipeline", "IN_TEAM")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseWorker(CustomOGM):
    __primarylabel__ = "ConcourseWorker"
    __primarykey__ = "name"

    name = Property()
    addr = Property()
    baggageclaim_url = Property()
    active_containers = Property()
    active_volumes = Property()
    active_tasks = Property()
    platform = Property()
    team = Property()
    version = Property()
    start_time = Property()
    ephemeral = Property()
    state = Property()

    teams = RelatedTo(ConcourseTeam, "IN_TEAM")
    public_ips = RelatedTo(PublicIP, "HAS_IP")
    public_domains = RelatedTo(PublicDomain, "HAS_DOMAIN")
    resources = RelatedTo("ConcourseResource", "HAS_RESOURCE")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseResource(RunsContainerImage, CodeMirror):
    __primarylabel__ = "ConcourseResource"
    __primarykey__ = "name"

    name = Property()
    type = Property()
    image = Property()
    version = Property()
    privileged = Property()
    unique_version_history = Property()
    source = Property()

    workers = RelatedFrom(ConcourseWorker, "HAS_RESOURCE")
    pipelines = RelatedFrom("ConcoursePipeline", "HAS_RESOURCE")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcoursePipeline(CustomOGM):
    __primarylabel__ = "ConcoursePipeline"
    __primarykey__ = "name"

    name = Property()
    id = Property()
    team_name = Property()
    paused = Property()
    public = Property()
    archived = Property()
    secrets = Property()

    teams = RelatedTo("ConcourseTeam", "IN_TEAM")
    secrets = RelatedTo("ConcourseSecret", "HAS_SECRET")
    pipelinegroups = RelatedTo("ConcoursePipelineGroup", "HAS_GROUP")
    resources = RelatedTo(ConcourseResource, "HAS_RESOURCE")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcoursePipelineGroup(CustomOGM):
    __primarylabel__ = "ConcoursePipelineGroup"
    __primarykey__ = "name"

    name = Property()

    pipelines = RelatedFrom(ConcoursePipeline, "HAS_GROUP")
    jobs = RelatedFrom("ConcourseJob", "IN_GROUP")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseSecret(CustomOGM):
    __primarylabel__ = "ConcourseSecret"
    __primarykey__ = "name"

    name = Property()

    pipelines = RelatedFrom(ConcoursePipeline, "HAS_SECRET")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcourseJob(CustomOGM):
    __primarylabel__ = "ConcourseJob"
    __primarykey__ = "name"

    name = Property()

    pipelinegroups = RelatedFrom(ConcoursePipelineGroup, "IN_GROUP")
    plans = RelatedTo("ConcoursePlan", "HAS_PLAN")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True

class ConcoursePlan(RunsContainerImage):
    __primarylabel__ = "ConcoursePlan"
    __primarykey__ = "name"

    name = Property()
    run = Property()
    runparams = Property()
    params = Property()
    vars = Property()

    jobs = RelatedFrom("ConcourseJob", "HAS_PLAN")

    concourse = Label(name="Concourse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concourse = True