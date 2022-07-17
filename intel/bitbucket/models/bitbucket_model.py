from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom
from urllib.parse import urlparse

from core.db.customogm import CustomOGM


class BitbucketOrganization(CustomOGM):
    __primarylabel__ = "BitbucketOrganization"
    __primarykey__ = "name"

    name = Property()

    repos = RelatedFrom("BitbucketRepo", "PART_OF")
    circleci_orgs = RelatedTo("CircleCIOrganization", "IN_CIRCLECI")

    bitbucket = Label(name="Bitbucket")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bitbucket = True

class BitbucketRepo(CustomOGM):
    __primarylabel__ = "BitbucketRepo"
    __primarykey__ = "full_name"

    full_name = Property()
    name = Property()

    orge = RelatedTo(BitbucketOrganization, "PART_OF")
    circleci_projects = RelatedTo("CircleCIProject", "IN_CIRCLECI")
    branches = RelatedTo("BitbucketBranch", "HAS_BRANCH")

    bitbucket = Label(name="Bitbucket")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bitbucket = True
    
    @staticmethod
    def get_full_name_from_url(url):
        uparsed = urlparse(url)
        return uparsed.path[1:].replace(".git", "") if uparsed.path.startswith("/") else uparsed.path.replace(".git", "")

    @staticmethod
    def is_bitbucket_repo_url(url):
        uparsed = urlparse(url)
        return uparsed.hostname == "bitbucket.org" or uparsed.hostname == "bitbucket.org"

class BitbucketBranch(CustomOGM):
    __primarylabel__ = "BitbucketBranch"
    __primarykey__ = "full_name"

    full_name = Property()
    name = Property()

    repos = RelatedFrom(BitbucketRepo, "HAS_BRANCH")

    bitbucket = Label(name="Bitbucket")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bitbucket = True