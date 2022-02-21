from typing import List, Optional, Union
import yaml
import logging
import time
import os
import re
from time import sleep
from google.auth import impersonated_credentials, default
from googleapiclient.http import HttpRequest
from base64 import b64decode
import googleapiclient.discovery
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.google.models.gcp_user_account import GcpUserAccount
from intel.google.models.google_group import GoogleGroup
from intel.google.models.gcp_permission import GcpRole
from intel.google.models.gcp_permission import GcpPermission
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_workload_identity_pool import GcpWorkloadIdentityPool
from core.utils.purplepanda_config import PurplePandaConfig
from core.utils.purplepanda import PurplePanda


# This needs to be global to be used as a cache for discovery different modules
KNOWN_ROLES = set()


"""
Example yaml:

google:
- file_path: "string"
  quota_project_id: "string"
  service_account_id: "string"
  scopes:
    - "https://www.googleapis.com/auth/cloud-platform"

file_path is the path to the JSON file containing the user/service account credentials. It's mandatory, if empty default file is used
quota_project_id is optional, provide the name of the project
service_account_id is optional, provide the same of the service account to impersonate to enumerate the environment
scopes is optional, provide a list of scopes if you whish
"""

class GcpDiscClient(PurplePanda):

    logger = logging.getLogger(__name__)

    def __init__(self, get_creds=True, config="") -> None:
        super().__init__()
        self.gcp = True
        panop = PurplePandaConfig()

        if config:
            self.env_var_content = config
        else:
            self.env_var = panop.get_env_var("google")
            self.env_var_content = os.getenv(self.env_var)
            msg = f"Google env variable '{self.env_var}' not configured"
            assert bool(self.env_var_content), msg
        
        self.google_config : dict = yaml.safe_load(b64decode(self.env_var_content))
        assert bool(self.google_config.get("google", None)), "Google env variable isn't a correct yaml"

        if get_creds:
            self.creds = self._google_creds()
        
    
    def _google_creds(self):
        """
        Parse google env variable and extract all the github credentials
        """

        creds : dict = []

        for entry in self.google_config["google"]:

            # Indicate path to credentials via environment variable
            file_path = entry.get("file_path")
            
            # If this doesn;t work check using the function load_credentials_from_file()
            if file_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = file_path
            elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            
            #file_path = file_path if file_path else os.environ["HOME"]+"/.config/gcloud/application_default_credentials.json"
            #self._remove_quota(file_path)

            scopes = entry.get("scopes", ["https://www.googleapis.com/auth/appengine.admin",
                                    "https://www.googleapis.com/auth/accounts.reauth",
                                    "https://www.googleapis.com/auth/userinfo.email",
                                    "openid",
                                    "https://www.googleapis.com/auth/cloud-platform",
                                    "https://www.googleapis.com/auth/compute"])
            
            quota_project_id = entry.get("quota_project_id", "")
            
            kwargs = { "scopes": scopes }
            if quota_project_id:
                kwargs["quota_project_id"] = quota_project_id

            cred, _= default(scopes=scopes, default_scopes=scopes)

            if entry.get("service_account_id"):
                cred = impersonated_credentials.Credentials(source_credentials=cred,
                                                                target_principal=entry.get("service_account_id"),
                                                                target_scopes=scopes)

            creds.append({
                "cred": cred,
                "quota_project_id": quota_project_id
            })
        
        return creds
    
    '''def _remove_quota(self, filepath):
        """Remove quota_project_id from the config file to access more data"""

        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            if config.get("quota_project_id"):
                del config["quota_project_id"]
                with open(filepath, 'w') as f:
                    json.dump(config, f)'''


    def execute_http_req(self, prep_http: googleapiclient.discovery.Resource, extract_field:Optional[str], 
        disable_warn=False, ret_err=False, cont=0, list_kwargs={}, headers={}, status_dis="") -> Union[list, str, dict]:
        """Access Google API sending the prepared http request"""
        
        try:
            ret_values = []
            start = time.time()

            if hasattr(prep_http, "list"):
                final_prep_http: HttpRequest = prep_http.list(**list_kwargs)
            else:
                final_prep_http: HttpRequest = prep_http

            while final_prep_http is not None:
                for k,v in headers.items():
                    final_prep_http.headers[k] = v
                
                resp: dict = final_prep_http.execute(num_retries=3)

                if len(resp) == 0 and not disable_warn:
                    self.logger.debug(f"The http request {final_prep_http.uri}, returned an empty object.")
                
                if extract_field and not extract_field in resp and not disable_warn:
                    self.logger.debug(f"The http request {final_prep_http.uri}, didn't return the expected field '{extract_field}'. It returned the keys {resp.keys()}")
                
                if extract_field:
                    ret_values += resp.get(extract_field, [])
                else:
                    ret_values = resp
                
                if hasattr(prep_http, "list_next"):
                    final_prep_http = prep_http.list_next(final_prep_http, resp)
                else:
                    if "nextPageToken" in resp:
                        if "pageToken=" in final_prep_http.uri: #If a page token in URI, remove it before adding the new one
                            final_prep_http.uri = re.sub(r'&pageToken=[^&]+', '', prep_http.uri)
                        
                        final_prep_http.uri = final_prep_http.uri + "&pageToken=" + resp["nextPageToken"]
                    
                    else:
                        final_prep_http = None
            
            end = time.time()
            self.logger.debug(f"GCP API access took: {int(end - start)}")
            return ret_values
        
        except googleapiclient.discovery.HttpError as e:
            if "403" in str(e) and ("or it is disabled" in str(e) or "or a custom role" in str(e)):
                # If first time and something in _quota_project_id, try without it
                if status_dis == "" and final_prep_http.http.credentials._quota_project_id:
                    prep_http._http.credentials._quota_project_id = ""
                    return self.execute_http_req(prep_http, extract_field=extract_field, disable_warn=disable_warn, ret_err=ret_err, cont=cont+1, list_kwargs=list_kwargs, status_dis="empty")

                # If not first time, try with the objetive project as _quota_project_id
                elif "/projects/" in final_prep_http.uri and status_dis != "terminate":
                    project_name = final_prep_http.uri.split("/projects/")[1].split("/")[0]
                    headers = {"X-Goog-User-Project": project_name}
                    prep_http._http.credentials._quota_project_id = project_name # This is to set the header "X-Goog-User-Project" of the library will change it
                    return self.execute_http_req(prep_http, extract_field=extract_field, disable_warn=disable_warn, ret_err=ret_err, cont=cont+1, list_kwargs=list_kwargs, headers=headers, status_dis="terminate")
            
            if not disable_warn and not "The caller does not have permission" in str(e) and not "403" in str(e) and not "has not been used in project" in str(e):
                self.logger.warning(f"HttpError occurred in {final_prep_http.uri}. Details: %r", e)
            if ret_err:
                return str(e)
            return []            
        
        except Exception as e:
            if cont > 3:
                self.logger.error(f"More than 3 timeouts occurred in {final_prep_http.uri}. Returning empty list. Details: %r.", e)
                return []
                
            self.logger.warning(f"Timeout occurred in {final_prep_http.uri}. Details: %r. Sleeping 10s and rerunning", e)
            sleep(10)
            return self.execute_http_req(prep_http, extract_field=extract_field, disable_warn=disable_warn, ret_err=ret_err, cont=cont+1, list_kwargs=list_kwargs)
    
    def get_iam_policy(self, obj, resource_service, resource_name, **kwargs) -> None:
        """
        Get the IAM policy of a resource and automatically create
        the service accounts, users, and groups, and relate them with the resource
        indicating their roles.
        Also create the roles and relate them with their permissions.
        """

        if str(type(obj)) == "<class 'intel.google.models.gcp_storage.GcpStorage'>":
            prep_http = resource_service.getIamPolicy(bucket=resource_name)
        else:
            prep_http = resource_service.getIamPolicy(resource=resource_name, **kwargs)

        # Make user v3 is used to not get "_withcond_" permissions: https://cloud.google.com/iam/docs/troubleshooting-withcond
        #prep_http.uri = prep_http.uri.replace(".com/v1/", ".com/v3/")
        # Even if you do this you will find "_withcond_" permissions and you won't find some permissions, like permissions to allUsers for cloud functions
        bindings: List[str] = self.execute_http_req(prep_http, "bindings", disable_warn=True)

        accs_to_roles: dict = {}
        for binding in bindings:
            role_name = binding["role"]
            if "_withcond_" in role_name:
                role_name = role_name.split("_withcond_")[0] #Weird case, don't know why the name is incorrect from GCP API
            
            self._get_role_perms(role_name, obj)
            for member in binding["members"]:
                if member.startswith("serviceAccount:"):
                    sa_email = member.replace("serviceAccount:", "")
                    # At this point SAs are unknown yet
                    m_obj: GcpServiceAccount = GcpServiceAccount(
                        email = sa_email,
                        fullName = f"{obj.name}/{member.replace(':','/')}"
                    ).save()
                    m_objs = [m_obj]

                elif member.startswith("user:"):
                    u_email = member.replace("user:", "")
                    m_obj: GcpUserAccount = GcpUserAccount(
                        email = u_email
                    ).save()
                    m_objs = [m_obj]
                
                elif member.startswith("group:"):
                    g_email = member.replace("group:", "")
                    m_obj: GoogleGroup = GoogleGroup(
                        email = g_email
                    ).save()
                    m_objs = [m_obj]
                
                elif member.startswith("domain:"):
                    o_domain = member.replace("domain:", "")
                    m_obj: GcpOrganization = GcpOrganization(
                        domain = o_domain
                    ).save()
                    m_objs = [m_obj]
                
                elif member == "allUsers":
                    m_obj: GcpUserAccount = GcpUserAccount(
                        name = member,
                        email = member + "@gcp.com"
                    ).save()
                    m_objs = [m_obj]
                
                elif member == "allAuthenticatedUsers":
                    m_obj: GcpUserAccount = GcpUserAccount(
                        name = member,
                        email = member + "@gcp.com"
                    ).save()
                    m_objs = [m_obj]
                
                elif member.startswith("projectViewer:"):
                    p_obj = GcpProject.get_by_name("projects/"+member.split(":")[1], or_create=True)
                    p_obj.basic_roles.update(obj, member=member)
                    p_obj.save()
                    m_objs = p_obj.get_basic_viewers()
                
                elif member.startswith("projectEditor:"):
                    p_obj = GcpProject.get_by_name("projects/"+member.split(":")[1], or_create=True)
                    p_obj.basic_roles.update(obj, member=member)
                    p_obj.save()
                    m_objs = p_obj.get_basic_editors()
                
                elif member.startswith("projectOwner:"):
                    p_obj: GcpProject = GcpProject.get_by_name("projects/"+member.split(":")[1], or_create=True)
                    p_obj.basic_roles.update(obj, member=member)
                    p_obj.save()
                    m_objs = p_obj.get_basic_owners()
                
                elif member.startswith("principal:") or member.startswith("principalSet:"):
                    name = member.replace("principal:", "").replace("principalSet:", "")
                    m_obj: GcpWorkloadIdentityPool = GcpWorkloadIdentityPool(name=name).save()
                    m_objs = [m_obj]
                
                elif member.startswith("deleted:"):
                    continue
                
                else:
                    self.logger.error(f"Uknown entity type: {member}")
                    continue
                
                for m_obj in m_objs:
                    if not m_obj.__primaryvalue__ in accs_to_roles:
                        accs_to_roles[m_obj.__primaryvalue__] = {
                            "roles": [role_name],
                            "object": m_obj
                        }
                    else:
                        accs_to_roles[m_obj.__primaryvalue__]["roles"].append(role_name)
        
        for k,v in accs_to_roles.items():
            # Not interested in roles over itself
            if m_obj.__primaryvalue__ != obj.__primaryvalue__ or type(m_obj) != type(obj):
                roles = v["roles"]
                m_obj = v["object"]
                m_obj.has_perm.update(obj, roles=roles)
                m_obj.save()
        
    def _get_role_perms(self, role_name: str, parent_obj, create_parent_rel = False):
        """Gets a role permissions"""

        global KNOWN_ROLES

        if role_name in KNOWN_ROLES:
            return
        
        # Do not check more than once every role
        KNOWN_ROLES.add(role_name)

        iam_v1_svc = self.get_other_svc("iam", "v1")

        if role_name.startswith("organizations/"):
            prep_http = iam_v1_svc.organizations().roles().get(name=role_name)
        
        elif role_name.startswith("projects/"):
            prep_http = iam_v1_svc.projects().roles().get(name=role_name)
        
        elif role_name.startswith("roles/"):
            try:
                prep_http = iam_v1_svc.roles().get(name=role_name)
            except TypeError as e:
                self.logger.error(f"Error getting the role {role_name} : {e}")
                return
        
        else:
            self.logger.error(f"Roles {role_name} with unexpected parent")
            
        resp: dict = self.execute_http_req(prep_http, None)

        if not resp:
            self.logger.error(f"The role {role_name} from {parent_obj.name} wasn't found")
            return

        role_obj: GcpRole = GcpRole(
            name=resp["name"],
            displayName=resp.get("title", ""),
            description=resp.get("description", ""),
            stage=resp.get("stage", ""),
            etag=resp.get("etag", ""),
        ).save()

        if create_parent_rel:
            if type(parent_obj) is GcpProject:
                role_obj.projects.update(parent_obj)
            else:
                role_obj.organization.update(parent_obj)
            role_obj.save()

        permissions: List[str] = resp.get("includedPermissions", [])
        for permission in permissions:
            perm_obj = GcpPermission(name=permission).save()
            role_obj.permissions.update(perm_obj)
        role_obj.save()


class GcpDisc(GcpDiscClient):
    resource: str
    version: str
    logger = logging.getLogger(__name__)

    def __init__(self, cred, **kwargs) -> None:
        super().__init__(get_creds=False) #Do not get the creds as here we already have them
        if kwargs.get("resource"): self.resource = kwargs.get("resource")
        if kwargs.get("version"): self.version = kwargs.get("version")
        self.gcp_get_secret_values = kwargs.get("gcp_get_secret_values", False)
        self.cred = cred
        self.service = googleapiclient.discovery.build(self.resource, self.version, credentials=cred, cache_discovery=False)
        self.task_name = "Google"
    
    def get_other_svc(self, resource: str, version: str):
        return googleapiclient.discovery.build(resource, version, credentials=self.cred, cache_discovery=False)
    
    def _get_save_sa_info_from_email(self, sa_obj: GcpServiceAccount) -> GcpServiceAccount:
        """
        Given a service account with an emial try to find for information about it
        """

        svc = self.get_other_svc('iam', 'v1')
        http_prep = svc.projects().serviceAccounts().get(name=f"projects/-/serviceAccounts/{sa_obj.email}")
        sa_info: dict = self.execute_http_req(http_prep, disable_warn=True, extract_field=None)
        if sa_info and sa_info.get("name"):
            sa_obj.name = sa_info["name"]
            sa_obj.description = sa_info.get("description", "")
            sa_obj.displayName = sa_info.get("displayName", "")
            sa_obj.uniqueId = sa_info.get("uniqueId", "")

            proj_obj = GcpProject(name=f"projects/{sa_info['projectId']}").save()
            sa_obj.projects.update(proj_obj)
            sa_obj.save()
        
        return sa_obj