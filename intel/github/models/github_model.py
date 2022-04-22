from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom
from urllib.parse import urlparse

from core.db.customogm import CustomOGM


class GithubPrincipal(CustomOGM):
    __primarylabel__ = "GithubPrincipal"

    #privesc = RelatedTo("External Cloud Resources", "PRIVESC")
    
    principal = Label(name="GithubPrincipal")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.principal = True


class GithubUser(GithubPrincipal):
    __primarylabel__ = "GithubUser"
    __primarykey__ = "id"

    id = Property()
    name = Property() #login
    person_name = Property() #name
    avatar_url = Property()
    bio = Property()
    blog = Property()
    disk_usage = Property()
    email = Property()
    followers = Property()
    followers_url = Property()
    following = Property()
    following_url = Property()
    gists_url = Property()
    gravatar_id = Property()
    hireable = Property()
    last_modified = Property()
    location = Property()
    public_gists = Property()
    public_repos = Property()
    site_admin = Property()
    role = Property()
    twitter_username = Property()

    teams = RelatedTo("GithubTeam", "MEMBER_OF")
    orgnaizations = RelatedTo("GithubOrganization", "PART_OF")
    owner_repos = RelatedTo("GithubRepo", "OWNER")
    perms_repos = RelatedTo("GithubRepo", "HAS_PERMS")
    branch_push = RelatedTo("GithubBranch", "CAN_PUSH")
    branch_dismiss = RelatedTo("GithubBranch", "CAN_DISMISS")
    branch_merge = RelatedTo("GithubBranch", "CAN_MERGE")
    repos_cos = RelatedTo("GithubRepo", "CODE_OWNER")
    secrets = RelatedTo("GithubSecrets", "CAN_STEAL_SECRET")
    selfhosted_runners = RelatedTo("GithubSelfHostedRunner", "RUN_IN")
    circleci_secrets = RelatedTo("CircleCISecret", "CAN_STEAL_SECRET") #Created by neo4j query

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True


class GithubTeam(GithubPrincipal):
    __primarylabel__ = "GithubTeam"
    __primarykey__ = "id"

    name = Property()
    description = Property()
    id = Property()
    last_modified = Property()
    members_count = Property()
    permission = Property()
    repos_count = Property()
    slug = Property()

    users = RelatedFrom(GithubUser, "MEMBER_OF")
    teams = RelatedTo("GithubTeam", "MEMBER_OF")
    orgnaizations = RelatedTo("GithubOrganization", "PART_OF")
    perms_repos = RelatedTo("GithubRepo", "HAS_PERMS")
    branch_push = RelatedTo("GithubBranch", "CAN_PUSH")
    branch_dismiss = RelatedTo("GithubBranch", "CAN_DISMISS")
    repos_cos = RelatedTo("GithubRepo", "CODE_OWNER")
    secrets = RelatedTo("GithubSecrets", "CAN_STEAL_SECRET")
    selfhosted_runners = RelatedTo("GithubSelfHostedRunner", "CAN_RUN")
    branch_merge = RelatedTo("GithubBranch", "CAN_MERGE")
    circleci_contexts = RelatedTo("CircleCIContext", "CAN_ACCESS")
    circleci_secrets = RelatedTo("CircleCISecret", "CAN_STEAL_SECRET") #Created by neo4j query

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubSecret(CustomOGM):
    __primarylabel__ = "GithubSecret"
    __primarykey__ = "name"

    name = Property()
    description = Property()

    repos = RelatedFrom("GithubRepo", "USES_SECRET")
    orgs = RelatedFrom("GithubOrganization", "USES_SECRET")
    environments = RelatedTo("GithubEnvironment", "PART_OF")
    users = RelatedFrom(GithubUser, "CAN_STEAL_SECRET")
    teams = RelatedFrom(GithubTeam, "CAN_STEAL_SECRET")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubEnvironment(CustomOGM):
    __primarylabel__ = "GithubEnvironment"
    __primarykey__ = "name"

    name = Property()

    secrets = RelatedFrom(GithubSecret, "USES_SECRET")
    repos = RelatedTo("GithubRepo", "PART_OF")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubLeak(CustomOGM):
    __primarylabel__ = "GithubLeak"
    __primarykey__ = "name"

    name = Property()
    description = Property()

    repos = RelatedTo("GithubRepo", "PART_OF")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubSelfHostedRunner(CustomOGM):
    __primarylabel__ = "GithubSelfHostedRunner"
    __primarykey__ = "id"

    name = Property()
    id = Property()
    os = Property()
    status = Property()

    repos = RelatedTo("GithubRepo", "PART_OF")
    users = RelatedFrom(GithubUser, "CAN_RUN")
    teams = RelatedFrom(GithubTeam, "CAN_RUN")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubRepo(CustomOGM):
    __primarylabel__ = "GithubRepo"
    __primarykey__ = "full_name" # So we can generate GithubRepos from GCP

    id = Property()
    allow_merge_commit = Property()
    allow_rebase_merge = Property()
    allow_squash_merge = Property()
    archived = Property()
    created_at = Property()
    default_branch = Property()
    delete_branch_on_merge = Property()
    description = Property()
    fork = Property()
    forks_count = Property()
    full_name = Property()
    has_downloads = Property()
    has_issues = Property()
    has_pages = Property()
    has_projects = Property()
    has_wiki = Property()
    homepage = Property()
    language = Property()
    last_modified = Property()
    name = Property()
    pushed_at = Property()
    size = Property()
    stargazers_count = Property()
    subscribers_count = Property()
    unkown_codeowners = Property()
    no_codeowners = Property()
    updated_at = Property()
    watchers_count = Property()

    teams = RelatedFrom("GithubTeam", "HAS_PERMS")
    teams_cos = RelatedFrom("GithubTeam", "CODE_OWNER")
    users = RelatedFrom("GithubUser", "HAS_PERMS")
    users_cos = RelatedFrom("GithubUser", "CODE_OWNER")
    orgnaizations = RelatedTo("GithubOrganization", "PART_OF")
    owner = RelatedFrom("GithubUser", "OWNER")
    branches = RelatedTo("GithubBranch", "HAS_BRANCH")
    source = RelatedTo("GithubRepo", "HAS_SOURCE")
    secrets = RelatedTo(GithubSecret, "USES_SECRET")
    leaks = RelatedFrom(GithubLeak, "PART_OF")
    environments = RelatedFrom(GithubEnvironment, "PART_OF")
    self_hosted_runners = RelatedFrom(GithubSelfHostedRunner, "RUN_IN")
    webhooks = RelatedTo("GithubWebhook", "HAS_WEBHOOK")
    gcp_source_repos = RelatedFrom("GcpSourceRepo", "IS_MIRROR")
    gcp_cloudbuild_trigger = RelatedFrom("GcpCloudbuildTrigger", "IS_MIRROR")
    circleci_projects = RelatedTo("CircleCIProject", "IN_CIRCLECI")


    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True
    
    @staticmethod
    def get_full_name_from_url(url):
        uparsed = urlparse(url)
        return uparsed.path[1:] if uparsed.path.startswith("/") else uparsed.path
    
    @staticmethod
    def is_github_repo_url(url):
        uparsed = urlparse(url)
        return uparsed.hostname == "github.com" or uparsed.hostname == "www.github.com"


class GithubOrganization(CustomOGM):
    __primarylabel__ = "GithubOrganization"
    __primarykey__ = "name"

    id = Property()
    name = Property() #login
    avatar_url = Property()
    billing_email = Property()
    blog = Property()
    collaborators = Property()
    company = Property()
    created_at = Property()
    default_repository_permission = Property()
    description = Property()
    disk_usage = Property()
    email = Property()
    followers = Property()
    following = Property()
    gravatar_id = Property()
    has_organization_projects = Property()
    has_repository_projects = Property()
    last_modified = Property()
    location = Property()
    members_can_create_repositories = Property()
    owned_private_repos = Property()
    plan = Property()
    private_gists = Property()
    public_gists = Property()
    public_repos = Property()
    private_repos = Property()
    two_factor_requirement_enabled = Property()

    teams = RelatedFrom(GithubTeam, "PART_OF")
    users = RelatedFrom(GithubUser, "PART_OF")
    repos = RelatedFrom(GithubRepo, "PART_OF")
    secrets = RelatedTo(GithubSecret, "USES_SECRET")
    circleci_orgs = RelatedTo("CircleCIOrganization", "IN_CIRCLECI")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubBranch(CustomOGM):
    __primarylabel__ = "GithubBranch"
    __primarykey__ = "full_name"

    last_modified = Property()
    name = Property()
    protected = Property()
    full_name = Property()

    known_protections = Property()
    allow_force_pushes = Property()
    allow_deletions = Property()
    enforce_admins = Property()
    required_signatures = Property()
    required_status_checks = Property()
    require_code_owner_reviews = Property()
    required_approving_review_count = Property()
    dismiss_stale_reviews = Property()

    repos = RelatedFrom(GithubRepo, "HAS_BRANCH")
    users_dimiss = RelatedFrom(GithubUser, "CAN_DISMISS")
    users_push = RelatedFrom(GithubUser, "CAN_PUSH")
    teams_dimisss = RelatedFrom(GithubTeam, "CAN_DISMISS")
    teams_push  = RelatedFrom(GithubTeam, "CAN_PUSH")
    users_merge = RelatedFrom(GithubUser, "CAN_MERGE")
    teamss_merge = RelatedFrom(GithubTeam, "CAN_MERGE")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True

class GithubWebhook(CustomOGM):
    __primarylabel__ = "GithubWebhook"
    __primarykey__ = "name"

    name = Property()
    insecure_ssl = Property()

    repos = RelatedFrom(GithubRepo, "HAS_WEBHOOK")
    public_ips = RelatedTo("PublicIP", "HAS_IP")
    public_domains = RelatedTo("PublicDomain", "HAS_DOMAIN")

    github = Label(name="Github")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = True