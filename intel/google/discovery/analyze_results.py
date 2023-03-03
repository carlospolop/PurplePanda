import logging
import yaml
import os
from typing import List, Tuple
from intel.google.models.gcp_permission import GcpPermission, GcpRole
from intel.google.models.gcp_perm_models import GcpPrincipal, GcpResource
from intel.google.models.gcp_cluster import GcpCluster
from intel.google.models.gcp_folder import GcpFolder
from core.db.customogm import CustomOGM
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_service_account import GcpServiceAccount
from intel.k8s.models import K8sNamespace, K8sServiceAccount
from .gcp_disc_client import GcpDisc



class AnalyzeResults(GcpDisc):
    resource = 'bigquery'   # Needed to avoid errors, but not used
    version = 'v2'          # Needed to avoid errors, but not used
    logger = logging.getLogger(__name__)
    known_ppal_res = set()
    known_2order_res = dict()

    def _disc(self) -> None:
        """
        Process the found information to be able to find privilege escalation paths easily in the database.
        """

        with open(os.path.dirname(__file__) + "/../info/privesc.yaml", "r") as stream:
            self.analysis_data = yaml.safe_load(stream)

        privesc_data = self.analysis_data["privesc"]
        self._disc_loop(privesc_data, self._disc_privesc_technique, __name__.split(".")[-1])


    def _disc_privesc_technique(self, prives_def):
        """Discover each ppal that can escalate with each defined technique"""

        self.known_2order_res = dict() #Reset these values
        permissions = prives_def["permissions"]
        second_order_permissions = prives_def.get("second_order_permissions", [])
        second_order_relations = prives_def.get("second_order_relations", [])
        only_to_classes = prives_def.get("only_to_classes", False)
        extra_privesc_to = prives_def["extra_privesc_to"]
        running_in = prives_def.get("running_in", [])
        title = prives_def["title"]
        summary = prives_def["summary"]
        relation = prives_def["relation"]
        limitations = prives_def.get("limitations", "")
        self.logger.info(f"Checking privesc: {title}")

        # Remove this when we create anothe DB to store interesting permissions
        if relation != "PRIVESC":
            return

        # If type RUNNING_SA, you need to indicate from which class you want to extract the running SA
        if extra_privesc_to == "RUNNING_SA" and not running_in:
            self.logger.error(f"The privecs technique {title} is of type RUNNING_SA but no class is indicated in 'running_in'. This won't be checked.")
            return 
        
        roles = [p.name for p in self._get_roles_with_permission(permissions[0])]
        first_perm_name = permissions[0]
        permissions = permissions[1:]
            
        # Get the principals that could escalate
        for role in roles:
            ppals_rscs = self._get_principals_with_role(role, only_to_classes, extra_privesc_to, running_in, second_order_relations)
            
            for ppal_rsc in ppals_rscs:
                ppal: GcpPrincipal = ppal_rsc[0]
                ppal_name = ppal.__primaryvalue__

                resources_and_reasons = ppal_rsc[1]
                can_escalate = None # Must be None at begginig to check if the ppal can escalate
                more_reasons = [] # If more than 1 permissions is needed this will host the reasons of the other permissions
            
                # Get each resource and reason the ppal is related with the first permission needed
                for rsc_reasons in resources_and_reasons:
                    res = rsc_reasons[0] # Can be GcpResource, K8sServiceAccount...
                    res_name = res.__primaryvalue__
                    
                    # Update permissions
                    # Too many results
                    #self._update_interesting_permissions(ppal, role, first_perm_name, res, summary)

                    # If not privesc relation, don't continue searching
                    # Uncomment this when we re-activate the previous part
                    #if relation != "PRIVESC":
                    #    continue
                    
                    
                    # Check in the cache if this was already analyzed
                    uniq_name = f"{ppal_name}-{res_name}-{relation}-{title}"
                    if uniq_name in self.known_ppal_res:
                        continue
                    else:
                        self.known_ppal_res.add(uniq_name)
                    
                    # If second_order_permissions and resource not a GcpPrincipal, not interesting
                    if second_order_permissions and not res.__node__.has_label("GcpPrincipal"):
                        continue

                    resources_to_relate: List[GcpResource] = [res] if not second_order_permissions else [] # If second_order_permissions, start empty
                    reasons = [f"{first_perm_name}: {rsc_reasons[1]} to {res.__primaryvalue__}"]
                    projectNumber = self._get_project_number_from_res(res)
                    
                    # Check if the ppal has each required permission inside the project
                    ## If it was already checked and the answer was false, just leave
                    if can_escalate is None:
                        can_escalate, more_reasons, _ = self._has_other_perms_to_escalate(permissions, projectNumber, 
                            ppal, summary, only_to_classes, extra_privesc_to, running_in, is_second_order_relations=bool(second_order_relations))
                    
                    if can_escalate is False:
                        break
                        
                    reasons += more_reasons
                    
                    # Check if "res" contains all the required second order permissions
                    if second_order_permissions:
                        if res.__primaryvalue__ not in self.known_2order_res:
                            self.known_2order_res[res.__primaryvalue__] = self._has_other_perms_to_escalate(second_order_permissions,
                                projectNumber, res, summary, only_to_classes, extra_privesc_to, running_in, is_second_order_perms=True)
                        
                        can_escalate += self.known_2order_res[res.__primaryvalue__][0]
                        reasons += self.known_2order_res[res.__primaryvalue__][1]
                        resources_to_relate = self.known_2order_res[res.__primaryvalue__][2]
                    
                    # If can escalate, create relation
                    if can_escalate and resources_to_relate:

                        # Create the relations
                        for rsc in resources_to_relate:
                            # Check the related resource is a GcpResource
                            if rsc.__node__.has_label("Gcp") and not rsc.__node__.has_label("GcpResource"):
                                self.logger.debug(f"Resource {res.__primaryvalue__} of type {type(res)} is not a GcpResource, so it's not going to be related")
                                continue
                            
                            # Check if the final class is allowed 
                            if only_to_classes and not any(f".{class_name}" in str(type(rsc)) for class_name in only_to_classes):
                                continue
                            
                            # These are always allowed to find other ppals, but maybe we don't want these privesc relations
                            ## comment this to create these relations also
                            #if type(rsc) in [GcpProject, GcpFolder]:
                            #    continue

                            # Do not privesc to yourself
                            if ppal.__primaryvalue__ == rsc.__primaryvalue__ and\
                                type(ppal) == type(rsc):
                                continue

                            ppal = ppal.privesc_to(rsc, reasons=reasons, title=title, summary=summary, limitations=limitations)


    def _update_interesting_permissions(self, ppal:GcpPrincipal, role: str, permission: str, res:GcpResource, summary:str, second_order=False):
        """Given a principal and the interesting permissions discovered, update it"""
        
        if second_order:
            interesting_perm = f"{permission}: Granted by role {role} over {res.__primaryvalue__} to second order intermediary ({summary})"
        else:
            interesting_perm = f"{permission}: Granted by role {role} over {res.__primaryvalue__} ({summary})"
        
        if not ppal.interesting_permissions:
            ppal.interesting_permissions = [interesting_perm]
            ppal.save()
        elif not interesting_perm in ppal.interesting_permissions:
            ppal.interesting_permissions.append(interesting_perm)
            ppal.save()


    def _get_roles_with_permission(self, perm_name: str) -> List[GcpRole]:
        """
        Given a permission return all the roles that contains it
        """

        if "*" in perm_name:
            perms: GcpPermission = GcpPermission.get_all_by_kwargs(f'_.name =~ "{perm_name}"')
            roles = []
            known_roles = []
            for perm in perms:
                for role, _ in perm.roles._related_objects:
                    if not role.__primaryvalue__ in known_roles:
                        roles.append(role)
                        known_roles.append(role.__primaryvalue__)
            return roles
        
        else:
            perm: GcpPermission = GcpPermission.get_by_name(perm_name)
            if perm:
                return [p[0] for p in perm.roles._related_objects]
            else:
                return []

    
    def _get_project_number_from_res(self, res: GcpResource):
        """
        Get the project number of the resource, none if not project number (Workspace or Organization for example)
        """

        projectNumber = None
        if hasattr(res, "projectNumber"):
            projectNumber = getattr(res, "projectNumber")
        else:
            if hasattr(res, "projects"):
                related = res.projects._related_objects
                if len(related) > 0 and len(related[0]) > 0:
                    if hasattr(related[0][0], "projectNumber"):
                        projectNumber = related[0][0].projectNumber # This can put projectNumber as None
        
        return projectNumber


    def _get_principals_with_role(self, role: str, only_to_classes: List[str], extra_privesc_to: str, 
        running_in: list, second_order_relations: List[str]) -> List[Tuple[GcpPrincipal, List[Tuple[GcpResource, str]]]]:
        """
        Given a role, get the principals that have it and the resources they have it over
        """

        principals_with_role = GcpPrincipal.get_all_principals_with_role(role)
        
        ppal_res = []
        for ppal in principals_with_role:
            resources = self._get_assets_from_principal_with_role(ppal, role, only_to_classes, extra_privesc_to, running_in, second_order_relations)
            ppal_res.append((ppal, resources))
        
        return ppal_res


    def _has_other_perms_to_escalate(self, permissions, projectNumber, ppal, summary, only_to_classes: List[str],
        extra_privesc_to: str, running_in: list, is_second_order_perms=False, is_second_order_relations=False):
        """
        Check if a ppal has all the required permissions to be able to escalate.
        This is only looking if the ppal has the rest permissions over SOMETHING in the same project
        TODO: Fix potential False Positives:
        - It might all required permissions but over different objects
        - If is_second_order_relations or is_second_order_perms, just having the permission over anything will return can_escalate as True
        """
        
        can_escalate = True
        reasons = []
        resources_to_relate = []
        for perm in permissions:
            roles = [p.name for p in self._get_roles_with_permission(perm)]
            
            for role in roles:
                can_escalate = False
                rsc_reasons2 = self._get_assets_from_principal_with_role(ppal, role, only_to_classes, extra_privesc_to, running_in, second_order_relations=[])
                
                # If something found, and same projectnumber, it can escalate
                for rsc_reason2 in rsc_reasons2:
                    res2: GcpResource = rsc_reason2[0]
                    projectNumber2 = self._get_project_number_from_res(res2)
                    #self._update_interesting_permissions(ppal, role, perm, res2, summary, second_order=is_second_order_perms)
                    
                    if (projectNumber == projectNumber2) or is_second_order_perms or is_second_order_relations:
                        can_escalate = True                        
                        reasons.append(f"{perm}: {rsc_reason2[1]} to {res2.__primaryvalue__}")
                        
                        if is_second_order_perms: # Only interested in second order resources from second order privescs
                            resources_to_relate.append(rsc_reason2[0])
                        
                        break # Remove this break to get all the reasons
                
                # If already found a role with this permission, go the the next one
                if can_escalate:
                    break
            
            # If the ppal doesn't have any role with the required permission in the same projectnumber, can't escalate
            if not can_escalate:
                break
        
        return (can_escalate, reasons, resources_to_relate)


    def _get_assets_from_principal_with_role(self, ppal: GcpPrincipal, role: str, only_to_classes: List[str], extra_privesc_to: str, 
        running_in: list, second_order_relations: List[str]) -> List[Tuple[GcpResource, str]]:
        """
        Given a principal and a role get all the resources affected from that role.
        Check the defined scopes to also add inherited permissions.
        If only interested in one class, only return that kind of objects
        """

        resources = []
        resources_already = set()

        # If not principal, return empty
        if not ppal.__node__.has_label("GcpPrincipal"):
            return resources

        for resource,roles in ppal.has_perm._related_objects:
            if role in roles["roles"]:
                resource = CustomOGM.node_to_obj(resource.perms.node.end_node)

                resources += self._get_recursive_resources(resource, resources_already, only_to_classes, 
                    extra_privesc_to, role, running_in, second_order_relations, from_obj=[])
        
        return resources


    def _get_recursive_resources(self, res, resources_already, only_to_classes, extra_privesc_to, 
        role, running_in, second_order_relations, from_obj=[]):
        """Given a list of resources a ppal has a role over, get the resouces inheriting it"""

        more_resources = []

        # If already checked, don't bother more
        if res.__primaryvalue__ in resources_already:
            return more_resources
        
        res_class_name = res.__class__.__name__

        # Check if we need to escalate to a relation of the found objects
        if second_order_relations:
            from_obj += [res]
            res = self._get_second_relations([res], second_order_relations) #returned res WILL be a list!
        
        # If interested in SAs running in specific classes, only allow to pass orgs, folders, projects and those classes
        elif running_in:
            if res_class_name in [s["initial_class_name"] for s in self.analysis_data["scope"]]:
                pass
            elif res_class_name in running_in:
                # If class not authorized, get the authorized object
                from_obj += [res]
                res = self._check_privesc_to_res(res, extra_privesc_to) #returned res COULD be a list!
            
        # If not running_in, then all allowed classes are permitted
        elif only_to_classes and not res_class_name in only_to_classes:
            # If class not authorized, get the authorized object
            from_obj += [res]
            res = self._check_privesc_to_res(res, extra_privesc_to) #returned res COULD be a list!
        
        # Instead of 1 final res, several might be given
        if type(res) is list:
            for r in res:
                # second_order_relations has already being check, so send it empty
                more_resources += self._get_recursive_resources(r, resources_already, only_to_classes, 
                    extra_privesc_to, role, running_in, second_order_relations=[], from_obj=from_obj)
        
        # If nothing to relate, or already known, return empty
        elif not res or res.__primaryvalue__ in resources_already:
            return more_resources
        
        elif not res.__primaryvalue__ in resources_already:
            if from_obj:
                more_resources.append((res, f"Indirect role {role} from {' -> '.join([f.__class__.__name__+'('+f.__primaryvalue__+')' for f in from_obj])}"))
            else:
                more_resources.append((res, f"Direct role {role}"))
            
            resources_already.add(res.__primaryvalue__)

            # Get interesting objects from Organizations, Folders and Projects (in that specific order)
            for scope in self.analysis_data["scope"]:
                class_name = scope["initial_class_name"]
                relation_name = scope["relation"]
                if res.__class__.__name__ == class_name:
                    from_obj += [res]
                    
                    # Only search for the relation_name (PART_OF) of the type of objects taht can be interesting
                    ## Those are all the defined in self.analysis_data["scope"] (org, folders and projects)
                    ## and running_in if exists or only_to_classes if it doesn't
                    privesc_to_types = list(set( [s["initial_class_name"] for s in self.analysis_data["scope"]] + (running_in if running_in else only_to_classes) ))
                    cypher_labels = '"' + '", "'.join(privesc_to_types) + '"'
                    objs = res.get_by_relation(relation_name, where=f"EXISTS ((a)<-[:{relation_name}]-(b)) AND any(l in labels(b) WHERE l in [{cypher_labels}])")
                    
                    for obj in objs:
                        more_resources += self._get_recursive_resources(obj, resources_already, only_to_classes, extra_privesc_to, 
                            role, running_in, second_order_relations, from_obj=from_obj)

        return more_resources
                        

    def _check_privesc_to_res(self, res:CustomOGM, extra_privesc_to):
        """Given a resource, check if it's inside the scope to privesc or get the obj where it should privesc"""
        
        obj = None
        # Check if you should escalate to all project SAs
        if extra_privesc_to == "ALL_PROJECT_SAS":
            for obj2, _ in res.projects._related_objects:
                if type(obj2) is GcpProject:
                    obj = obj2

        # Or just to the running SA in the resource
        elif extra_privesc_to == "RUNNING_SA":
            for obj2 in res.get_by_relation("RUN_IN"):
                obj = obj2
        
        elif extra_privesc_to == "K8S_CLUSTER_SAS" and hasattr(res, "k8s_namespaces"):
            obj = []
            res: GcpCluster
            for k8s_obj, _ in res.k8s_namespaces._related_objects:
                k8s_obj: K8sNamespace
                for ksa_obj in K8sServiceAccount.get_all_by_kwargs(f'_.name =~ "^{k8s_obj.name}:.*"'):
                    obj.append(ksa_obj)
        
        return obj


    def _get_second_relations(self, rscs:List[CustomOGM], sor:List[str]) -> List[CustomOGM]:
        """
        Recursively check from all the given resources each second order relation
        until there aren't more relations to check, then, return found objs
        """
        
        if len(sor) > 0:
            rel_name = sor[0]
            sec_rscs = []
            known_cache = set()

            # Get all the relations of all the given resources
            for rsc in rscs:
                for sec_rsc in rsc.get_by_relation(rel_name):
                    cache_name = sec_rsc.__primaryvalue__ + sec_rsc.__primarylabel__
                    if not cache_name in known_cache:
                        known_cache.add(cache_name)
                        sec_rscs.append(sec_rsc)

            sor = sor[1:] #Remove the relation we just check

            # Return calling the same function again
            if sec_rscs:
                return self._get_second_relations(sec_rscs, sor)
            
            else: # Nothing found matching, return nothing
                return []
        
        else:
            return rscs
