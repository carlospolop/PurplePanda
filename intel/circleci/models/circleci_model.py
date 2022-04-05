from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from core.db.customogm import CustomOGM
from intel.github.models import GithubTeam, GithubRepo, GithubOrganization, GithubBranch
from intel.bitbucket.models import BitbucketOrganization, BitbucketRepo, BitbucketBranch


class CircleCIOrganization(CustomOGM):
    __primarylabel__ = "CircleCIOrganization"
    __primarykey__ = "name"

    name = Property()

    contexts = RelatedFrom("CircleCIContext", "PART_OF")
    projects = RelatedFrom("CircleCIProject", "PART_OF")
    gh_orgs = RelatedFrom(GithubOrganization, "IN_CIRCLECI")
    bk_orgs = RelatedFrom(BitbucketOrganization, "IN_CIRCLECI")

    circleci = Label(name="CircleCI")

    def __init__(self, name, *args, **kwargs):
        if name.lower().startswith("gh/"):
            kwargs["name"] = "github/" + name[3:]
        else:
            kwargs["name"] = name
        super().__init__(*args, **kwargs)

        self.circleci = True

class CircleCIContext(CustomOGM):
    __primarylabel__ = "CircleCIContext"
    __primarykey__ = "name"

    name = Property()
    id = Property()

    orgs = RelatedTo(CircleCIOrganization, "PART_OF")
    secrets = RelatedTo("CircleCISecret", "HAS_SECRET")
    teams = RelatedFrom(GithubTeam, "CAN_ACCESS") # TODO: The CircleCI API doesn't give the teams that has access to the context, it would be nice to have that info

    circleci = Label(name="CircleCI")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circleci = True

class CircleCISecret(CustomOGM):
    __primarylabel__ = "CircleCISecret"
    __primarykey__ = "name"

    name = Property()
    value = Property()

    contexts = RelatedFrom("CircleCIContext", "HAS_SECRET")
    projects = RelatedFrom("CircleCIProject", "HAS_SECRET")
    gh_users = RelatedFrom("GithubUser", "CAN_STEAL_SECRET")
    gh_teams = RelatedFrom("GithubTeam", "CAN_STEAL_SECRET")

    circleci = Label(name="CircleCI")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circleci = True

class CircleCIVar(CustomOGM):
    __primarylabel__ = "CircleCIVar"
    __primarykey__ = "name"

    name = Property()
    value = Property()

    pipelines = RelatedFrom("CircleCIProject", "HAS_VAR")

    circleci = Label(name="CircleCI")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circleci = True

class CircleCIProject(CustomOGM):
    __primarylabel__ = "CircleCIProject"
    __primarykey__ = "name"

    name = Property()
    irc_server = Property()
    irc_keyword = Property()
    irc_password = Property()
    irc_username = Property()
    irc_notify_prefs = Property()

    slack_integration_channel = Property()
    slack_integration_team_id = Property()
    slack_integration_team = Property()
    slack_integration_notify_prefs = Property()
    slack_integration_webhook_url = Property()
    slack_subdomain = Property()
    slack_notify_prefs = Property()
    slack_channel_override = Property()
    slack_api_token = Property()
    slack_channel = Property()
    slack_integration_channel_id = Property()
    slack_integration_access_token = Property()

    vcs_type = Property()
    vcs_url = Property()
    
    aws = Property()
    default_branch = Property()
    flowdock_api_token = Property()
    has_usable_key = Property()
    oss = Property()
    jira = Property()
    ssh_keys = Property()
    feature_flags = Property()

    orgs = RelatedTo(CircleCIOrganization, "PART_OF")
    secrets = RelatedTo(CircleCISecret, "HAS_SECRET")
    vars = RelatedTo(CircleCIVar, "HAS_VAR")
    gh_repos = RelatedFrom(GithubRepo, "IN_CIRCLECI")
    bk_repos = RelatedFrom(BitbucketRepo, "IN_CIRCLECI")

    circleci = Label(name="CircleCI")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circleci = True

