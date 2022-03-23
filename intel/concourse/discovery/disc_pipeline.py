import logging
import re
import json

from intel.concourse.discovery.concourse_disc_client import ConcourseDisc
from intel.concourse.models.concourse_model import ConcoursePipeline, ConcourseTeam, ConcoursePipelineGroup, ConcourseSecret, ConcourseJob, ConcoursePlan
from core.models import ContainerImage

class DiscPipelines(ConcourseDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the pipelines and the used secrets
        """

        pipelines = self.call_concourse_api(f=self.cred.list_all_pipelines)
        self._disc_loop(pipelines, self._disc_pipelines, __name__.split(".")[-1])

    
    def _disc_pipelines(self, pipeline, **kwargs):
        """Discover each team"""

        id = pipeline["id"]
        name = pipeline["name"]
        team_name = pipeline["team_name"]
        paused = pipeline["paused"]
        public = pipeline["public"]
        archived = pipeline["archived"]

        pl_obj = ConcoursePipeline(
            id = id,
            name= name,
            team_name = team_name,
            paused = paused,
            public = public,
            archived = archived
        ).save()

        pipe_info = self.call_concourse_api(f=self.cred.get_config, ret_val={}, **{"team_name": team_name, "pipeline_name": name})

        if team_name:
            team_obj = ConcourseTeam(name=team_name).save()
            pl_obj.teams.update(team_obj)        

        if not pipe_info:
            pl_obj.save()
            return
        
        self._disc_pipeline_info(pl_obj, pipe_info)
        
    
    def _disc_pipeline_info(self, pl_obj:ConcoursePipeline, pipe_info: dict):
        """Given the pipe info, obtain the new object"""

        # Get the part where the info is stored
        pipe_info = pipe_info["config"]

        # Get all the secrets (anything between 2 parenthesis)
        secrets = [ s.replace("(","").replace(")", "") for s in set(re.findall(r'\(\([^\)]+\)\)', str(pipe_info))) ]
        for secret in secrets:
            s_obj = ConcourseSecret(name=secret).save()
            pl_obj.secrets.update(s_obj)

        # Get all the resources of the pipeline
        for res in pipe_info.get("resources", []):
            res_obj = self.get_resource_obj(res)
            pl_obj.resources.update(res_obj)

        # Get all the job groups
        for job in pipe_info["jobs"]:
            job_obj = ConcourseJob(name=job["name"]).save()
            
            for i,plan in enumerate(job["plan"]):
                config = plan.get("config", {})
                run = config.get("run", {})
                vars = json.dumps(plan.get("vars", {}))
                plan_obj = ConcoursePlan(
                    name=plan.get("task", f'{job["name"]}-plan{i}'),
                    params=json.dumps(plan.get("params")),
                    runparams=json.dumps(config.get("params")),
                    run=f'{run.get("path", "")} {" ".join(run.get("args", []))}',
                    vars=vars
                ).save()

                if config.get("image_resource"):
                    image_resource = config.get("image_resource")
                    if image_resource.get("type") == "docker-image":
                        repo = image_resource.get("source", {}).get("repository")
                        if repo:
                            contimg_obj = ContainerImage(name=repo).save()
                            plan_obj.run_images.update(contimg_obj)
                            plan_obj = plan_obj.save()
                
                job_obj.plans.update(plan_obj)
            
            job_obj.save()

        # Get all the job groups
        for group in pipe_info.get("groups", []):
            plgroup_obj = ConcoursePipelineGroup(name=group["name"]).save()
            pl_obj.pipelinegroups.update(plgroup_obj)
            
            for job_regex in group["jobs"]:
                for job_obj in ConcourseJob.get_all_by_kwargs(f'_.name =~ "{job_regex.replace("*", ".*")}"'):
                    plgroup_obj.jobs.update(job_obj)
            
            plgroup_obj.save()

        pl_obj.save()
