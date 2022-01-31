import logging
from typing import List

from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_cloudbuild import GcpCloudbuildBuild, GcpCloudbuildTrigger
from intel.google.models.gcp_storage import GcpStorage
from intel.google.models.gcp_pubsub import GcpPubSubTopic, GcpPubSubSubscription
from intel.google.models.gcp_secrets import GcpSecret, GcpSecretVersion
from intel.google.models.gcp_source_repos import GcpSourceRepo
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.github.models.github_model import GithubRepo


class DiscCloudbuild(GcpDisc):
    resource = 'cloudbuild'
    version = 'v1'
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the cloud build builds and trigegrs from each project discovered.

        This module will create the cloudbuilds builds and triggers.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_builds, __name__.split(".")[-1])
        self._disc_loop(projects, self._disc_triggers, __name__.split(".")[-1])


    def _disc_builds(self, p_obj):
        """
        Discover all the cloudbuild builds inside the project and relate them with the
        parent project, service account and bucket.
        """

        project_id: str = p_obj.name.split("/")[1]
        http_prep = self.service.projects().builds()#.list(projectId=project_id)
        builds: List[str] = self.execute_http_req(http_prep, "builds", disable_warn=True, list_kwargs={"projectId": project_id})
        for build in builds:
            bucket, bucketObject, repoProjectId, repoName, repoDir, branchName, tagName, commitSha = "", "", "", "", "", "", "", ""
            source = build["source"]
            
            bucketSource = source.get("storageSource", source.get("storageSourceManifest", {}))
            if bucketSource:
                bucket = bucketSource["bucket"]
                bucketObject = bucketSource["object"]
            
            repoSource = source.get("repoSource", {})
            if repoSource:
                repoProjectId = repoSource.get("projectId", project_id)
                repoName = repoSource["repoName"]
                repoDir = repoSource["dir"]
                branchName = repoSource["branchName"]
                tagName = repoSource["tagName"]
                commitSha = repoSource["commitSha"]

            build_obj = GcpCloudbuildBuild(
                name = build["name"],
                id = build["id"],
                images = build.get("images", []),
                logsBucket = build.get("logsBucket", ""),
                tags = build.get("tags", []),
                bucket = bucket,
                bucketObject = bucketObject,
                repoProjectId = repoProjectId,
                repoName = repoName,
                repoDir = repoDir,
                branchName = branchName,
                tagName = tagName,
                commitSha = commitSha
            ).save()
            build_obj.projects.update(p_obj)

            if bucket:
                bucket_obj: GcpStorage = GcpStorage(name=bucket).save()
                build_obj.buckets.update(bucket_obj, object = bucketObject)
            
            if repoSource:
                sr_name = f"projects/{repoProjectId}/repos/{repoName}"
                sr_obj: GcpSourceRepo = GcpSourceRepo(name = sr_name).save()
                build_obj.sourceRepos.update(sr_obj)
            
            # TODO: Add storageSourceManifest as potential source
            # TODO: Add secrets and available secrets
            build_obj.save()

            # According to https://cloud.google.com/build/docs/cloud-build-service-account
            sa_email = build.get("serviceAccount", f"{p_obj.projectNumber}@cloudbuild.gserviceaccount.com")
            sa_email = sa_email if not "/" in sa_email else sa_email.split("/")[-1]
            build_obj.relate_sa(sa_email, [])


    def _disc_triggers(self, p_obj):
        """
        Discover all the cloudbuild triggers inside the project and relate them with the
        parent project, service account, pubsub subscriptions and topic and cloudbuild build.
        """

        project_id: str = p_obj.name.split("/")[1]
        http_prep = self.service.projects().triggers()#.list(projectId=project_id)
        triggers: List[str] = self.execute_http_req(http_prep, "triggers", disable_warn=True, list_kwargs={"projectId": project_id})
        
        for trigger in triggers:
            triggerTemplate = trigger.get("triggerTemplate", {})
            triggerRepoProjectId = triggerTemplate.get("projectId", "")
            triggerRepoName = triggerTemplate.get("repoName", "")
            triggerRepoDir = triggerTemplate.get("dir", "")
            triggerBranchName = triggerTemplate.get("branchName", "")
            triggerTagName = triggerTemplate.get("tagName", "")
            triggerCommitSha = triggerTemplate.get("commitSha", "")
            
            github = trigger.get("github", {})
            pr = github.get("pullRequest", {})
            ps = github.get("push", {})
            ghOwner = github.get("owner", "")
            ghName = github.get("name", "")
            ghEnterpriseConfigResourceName = github.get("enterpriseConfigResourceName", "")
            ghPRBranch = pr.get("branch", "")
            ghInvertRegex = pr.get("invertRegex", False)
            ghPSBranch = ps.get("branch", "")
            ghPSTag = ps.get("tag", "")
            gh_repo_full_name = ghOwner + "/" + ghName

            gitFileSource = trigger.get("gitFileSource", {})
            gitFilePath = gitFileSource.get("path", "")
            gitFileUri = gitFileSource.get("uri", "")
            gitFileRevision = gitFileSource.get("revision", "")

            trigger_obj = GcpCloudbuildTrigger(
                name = trigger["name"],
                id = trigger["id"],
                resourceName = trigger.get("resourceName", ""),
                description = trigger.get("description", ""),
                tags = trigger.get("tags", []),

                triggerRepoProjectId = triggerRepoProjectId,
                triggerRepoName = triggerRepoName,
                triggerRepoDir = triggerRepoDir,
                triggerBranchName = triggerBranchName,
                triggerTagName = triggerTagName,
                triggerCommitSha = triggerCommitSha,

                triggerGhOwner = ghOwner,
                triggerGhName = ghName,
                triggerGhEnterpriseConfigResourceName = ghEnterpriseConfigResourceName,
                triggerGhPRBranch = ghPRBranch,
                triggerGhInvertRegex = ghInvertRegex,
                triggerGhPSBranch = ghPSBranch,
                triggerGhPSTag = ghPSTag,

                triggerWebhook = trigger.get("webhookConfig", {}).get("secret", ""),

                triggerPubSubSubscription = trigger.get("pubsubConfig", {}).get("subscription", ""),
                triggerPubSubTopic = trigger.get("pubsubConfig", {}).get("topic", ""),

                disabled = trigger.get("disabled", False),
                ignoredFiles = trigger.get("ignoredFiles", []),
                includedFiles = trigger.get("includedFiles", []),
                approvalRequired = trigger.get("approvalConfig", {}).get("approvalRequired", False),
                filter = trigger.get("filter", ""),
                autodetect = trigger.get("autodetect", False),
                filename = trigger.get("filename", ""),

                gitFilePath = gitFilePath,
                gitFileUri = gitFileUri,
                gitFileRevision = gitFileRevision
            ).save()
            trigger_obj.projects.update(p_obj)

            # Relate with source
            sourceToBuild = trigger.get("sourceToBuild", {})
            if sourceToBuild.get("repoType", "").upper() == "GITHUB":
                gh_repo_obj = GithubRepo(full_name=GithubRepo.get_full_name_from_url(sourceToBuild["uri"])).save()
                trigger_obj.github_repos.update(gh_repo_obj)
            
            elif len(gh_repo_full_name) > 3:
                gh_repo_obj = GithubRepo(full_name=gh_repo_full_name).save()
                trigger_obj.github_repos.update(gh_repo_obj)

            # relate with possible pub/sub trigger
            pubsubinfo = trigger.get("pubsubConfig", {})
            if pubsubinfo.get("subscription"):
                subs_obj: GcpPubSubSubscription = GcpPubSubSubscription(name=pubsubinfo.get("subscription")).save()
                trigger_obj.pubsubSubscriptions_trigger.update(subs_obj)
            
            if pubsubinfo.get("topic"):
                topic_obj: GcpPubSubTopic = GcpPubSubTopic(name=pubsubinfo.get("topic")).save()
                trigger_obj.pubsubTopics_trigger.update(topic_obj)
            
            # Relate with possible webhook trigger
            if trigger.get("webhookConfig", {}).get("secret", ""):
                secret_version_name = trigger["webhookConfig"]["secret"]
                secret_name = trigger["webhookConfig"]["secret"].split("/versions/")[0]
                secret_obj = GcpSecret(name=secret_name).save()
                secret_v_obj = GcpSecretVersion(name=secret_version_name).save()
                secret_obj.versions.update(secret_v_obj)
                secret_obj.save()
                trigger_obj.secrets_trigger.update(secret_obj)
            
            # Relate with possible trigger
            if triggerRepoProjectId and triggerRepoName:
                sr_repo_name = f"projects/{triggerRepoProjectId}/repos/{triggerRepoName}"
                sr_obj = GcpSourceRepo(name=sr_repo_name).save()
                trigger_obj.sourcerepos_trigger.update(sr_obj)
            
            if trigger.get("build",{}).get("id"):
                build_obj: GcpCloudbuildBuild = GcpCloudbuildBuild(id=trigger.get("build")["id"]).save()
                trigger_obj.cloudbuildBuilds.update(build_obj)
            
            trigger_obj.save()
            
            # According to https://cloud.google.com/build/docs/api/reference/rest/v1/projects.locations.triggers#BuildTrigger.GitFileSource
            sa_email = trigger.get("serviceAccount", f"{p_obj.projectNumber}@system.gserviceaccount.com")
            sa_email = sa_email if not "/" in sa_email else sa_email.split("/")[-1]
            trigger_obj.relate_sa(sa_email, [])
