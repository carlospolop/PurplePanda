import logging
import yaml
import os

from intel.k8s.models.k8s_model import *
from .k8s_disc import K8sDisc
from core.db.customogm import graph


class AnalyzeResults(K8sDisc):
    logger = logging.getLogger(__name__)
    already_privesc = set()

    def _disc(self) -> None:
        """
        Process the found information to be able to find privilege escalation paths easily in the database.
        """

        with open(os.path.dirname(__file__) + "/../info/privesc.yaml", "r") as stream:
            self.analysis_data = yaml.safe_load(stream)
        
        privesc_techs = self.analysis_data["privesc"]

        # Create known groups relations
        self._create_known_groups_relations()

        # Set escape to node
        self._potential_escape_to_node()

        # Create GSAs run in pods
        self._gcp_sas_running_in_pod()

        # Get privescs
        self._disc_loop(privesc_techs, self._check_privesc_tech, __name__.split(".")[-1])
    

    def _check_privesc_tech(self, privesc_tech):
        """Check each privesc check"""

        for ppal_obj in K8sUser.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"') + K8sGroup.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"') + K8sServiceAccount.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
            objs_to_privesc = self._get_ppal_privesc(privesc_tech, ppal_obj)
            title = privesc_tech["title"]
            summary = privesc_tech["summary"]
            limitations = privesc_tech.get("limitations", "")
            relation = privesc_tech["relation"]
            
            for _, obj_to_privesc in objs_to_privesc.items():
                to_privesc_ppal_obj = obj_to_privesc["ppal_obj"].save()
                reason = obj_to_privesc["reason"]

                # Update interesting permission
                self._update_interesting_permissions(ppal_obj, reason)
                
                # If not a ppal we don't want to escalate privs to it
                if "K8s" in to_privesc_ppal_obj.__node__._labels and "K8sPrincipal" not in to_privesc_ppal_obj.__node__._labels:
                    continue
                
                # Do not privesc to yourself
                if ppal_obj.__primaryvalue__ == to_privesc_ppal_obj.__primaryvalue__ and\
                    type(ppal_obj) == type(to_privesc_ppal_obj):
                    continue
                
                if obj_to_privesc["escape_to_node"] and not ppal_obj.potential_escape_to_node:
                    ppal_obj.potential_escape_to_node = True
                    ppal_obj.save()
                
                if relation.upper() == "PRIVESC":
                    privesc_rel_name = f"{ppal_obj.__primaryvalue__}->{to_privesc_ppal_obj.__primaryvalue__}"
                    if not privesc_rel_name in self.already_privesc:
                        ppal_obj = ppal_obj.privesc_to(to_privesc_ppal_obj, reasons=[reason], title=title, summary=summary, limitations=limitations)
                        self.already_privesc.add(privesc_rel_name)
                
                else:
                    self.logger.error(f"Uknown relation {relation}")


    def _create_known_groups_relations(self):
        """
        There are some important default groups we need to consider
        """

        # All users are member of system:authenticated
        query = '''MERGE (auth_group:K8s:K8sPrincipal:K8sGroup{name:"'''+self.cluster_id+'''-system:authenticated"})
                WITH auth_group
                MATCH (users:K8sUser) WHERE users.name =~ "'''+self.cluster_id+'''-.*"
                MERGE (users)-[:MEMBER_OF]->(auth_group)
                WITH auth_group
                MATCH (groups:K8sGroup) WHERE groups.name <> "'''+self.cluster_id+'''-system:authenticated" AND groups.name =~ "'''+self.cluster_id+'''-.*"
                MERGE (groups)-[:MEMBER_OF]->(auth_group)
                return auth_group'''

        graph.evaluate(query)

        # All service accounts are inside "system:serviceaccounts"
        query = '''MERGE (group:K8s:K8sPrincipal:K8sGroup{name:"'''+self.cluster_id+'''-system:serviceaccounts"})
                WITH group
                MATCH (sas:K8sServiceAccount) WHERE sas.name =~ "'''+self.cluster_id+'''-.*"
                MERGE (sas)-[:MEMBER_OF]->(group)
                return group'''

        graph.evaluate(query)


        query = '''MATCH (ns:K8sNamespace)<-[:PART_OF]-(sa:K8sServiceAccount) WHERE ns.name =~ "'''+self.cluster_id+'''-.*"
                MERGE (group:K8s:K8sPrincipal:K8sGroup{name:"'''+self.cluster_id+'''-system:serviceaccounts:"+ns.ns_name})
                MERGE (group)<-[:MEMBER_OF]-(sa)
                RETURN group'''

        graph.evaluate(query)
    

    def _potential_escape_to_node(self):

        query = """MATCH(p:K8sPod)
            WHERE p.host_network OR
            p.host_pid OR
            any(path IN p.host_path WHERE any( regex IN ["/", "/proc.*", "/sys.*", "/dev.*", "/var", "/var/", "/var/log.*", "/var/run.*", ".*docker.sock", ".*crio.sock", ".*/kubelet.*", ".*/pki.*", "/home/admin.*", "/etc.*", ".*/kubernetes.*", ".*/manifests.*", "/root.*"] WHERE regex =~ replace(path, "\\\\", "\\\\\\\\") ))
            SET p.potential_escape_to_node = true
            RETURN p"""
        
        graph.evaluate(query)

        query = """MATCH(c:K8sContainer)
            WHERE c.sc_privileged = True OR
            size(c.sc_capabilities_add) > 0
            SET c.potential_escape_to_node = true
            RETURN c"""
        
        graph.evaluate(query)
    
    def _gcp_sas_running_in_pod(self):
        """If the GCP cluster has a SA, it's accessible from the pods"""

        query = """MATCH(p:K8sPod)-[:PART_OF]->(ns:K8sNamespace)-[:PART_OF]->(:GcpCluster)<-[r:RUN_IN]-(sa:GcpServiceAccount)
            MERGE (p)<-[:RUN_IN {scopes: r.scopes}]-(sa)
            RETURN p
            """
        
        graph.evaluate(query)
    

    def _update_interesting_permissions(self, ppal:K8sPrincipal, reason: str):
        """Given a principal and the interesting permissions discovered, update it"""
        
        if not ppal.interesting_permissions:
            ppal.interesting_permissions = [reason]
            ppal = ppal.save()
        elif not reason in ppal.interesting_permissions:
            ppal.interesting_permissions.append(reason)
            ppal = ppal.save()


    def _get_ppal_privesc(self, privesc_tech:dict, ppal_obj: K8sPrincipal) -> dict:
        """
        Given a privesc technique and a principal object, check if the principal can use it to escalate
        """

        verbs = privesc_tech["verbs"]
        resources = privesc_tech["resources"]
        privesc_to = privesc_tech.get("privesc_to", "")
        privesc_to_cloud = privesc_tech.get("privesc_to_cloud", False)
        class_name = privesc_tech.get("class_name", "")
        assert privesc_to or class_name, "There is a privesc tecnique without privesc_to and class_name"

        privescs_to_node_resources = self.analysis_data["extra_info"]["privescs_to_node_resources"]
        
        privect_to_objs = {}
        for res_obj, rel in ppal_obj.resources._related_objects:
            rel_verbs = rel["verbs"]
            apiGroups = rel["api_groups"]
            role_name = rel["role_name"]
            bind_name = rel["bind_name"]

            # Resource name can be like "pods" or "namespace_name:pods", so we get the "-1" splitting by ":"
            affected_resource_name = res_obj.name.split(":")[-1].lower()
            
            # Check if the resource is affected
            if not affected_resource_name == "*" and not any(res in affected_resource_name for res in resources): # The any is used so "pods" inside "pods/log" gives true (check TODO in privesc.yaml)
                continue

            # Check the ppal has all the required verbs permissions
            if not "*" in rel_verbs and not all(v in rel_verbs for v in verbs):
                continue
            
            for _, ppal_obj in self._get_privesc_to_objs(privesc_to, privesc_to_cloud, class_name, res_obj.name).items():

                privect_to_objs[ppal_obj["ppal_obj"].__primaryvalue__] = {
                    "ppal_obj": ppal_obj["ppal_obj"],
                    "reason": f"The {'ClusterRole' if res_obj.name == affected_resource_name else 'Role'} '{role_name}' assigned by the binding '{bind_name}' fullfil the necessary privesc permissions '{', '.join(verbs)}' with the set of permissions '{', '.join(rel_verbs)}' over the resource '{res_obj.name}'. {ppal_obj['extra_reason']}",
                    "escape_to_node": res_obj.name in privescs_to_node_resources
                }
        
        return privect_to_objs
            
    
    def _get_privesc_to_objs(self, privesc_to: str, privesc_to_cloud: bool, class_name: str, res_name: str):
        """
        Given a privesc_to info, get all the affected objects the ppal can escalate to
        """
        
        privect_to_objs = {}
        ns_name = res_name.split(":")[0]
        
        # Relate to all SAs in the namespace (if ClusterRole, in all)
        if privesc_to == "Namespace SAs":
            if len(res_name.split(":")) == 1:
                # Privesc to all the clusters SAs
                for sa_obj in K8sServiceAccount.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
                    privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
                
                # Privesc to all the GSA of the cluster
                if privesc_to_cloud:
                    for pod_obj in K8sPod.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
                        self.escalate_to_cloud_ppals(privect_to_objs, pod_obj, privesc_to_cloud)
            
            else:
                ns_obj = K8sNamespace(name=ns_name).save()
                for sa_obj, rel in ns_obj.serviceaccounts._related_objects:
                    # Coger todos los GSA en el namespace y escalar a ellos
                    if type(sa_obj) is not K8sServiceAccount:
                        self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__} found as service account in namespace {ns_name.name} for privesc")
                    else:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
                
                # Privesc to all the GSA running in the pods of the cluster
                if privesc_to_cloud:
                    for pod_obj, _ in ns_obj.pods._related_objects:
                        self.escalate_to_cloud_ppals(privect_to_objs, pod_obj, privesc_to_cloud)
        
        # Relate to the SA running in the resource inside a namespace (if ClusterRole, in all) and to all the SAs whose secret token can be accesed by the item
        elif privesc_to == "Running SA":
            assert class_name, "class_name needs to be specified with 'Running SA' privesc_to"
            K8sKlass = globals()[class_name]
            
            for item in K8sKlass.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
                # If namespace dependant and object not related with the namespace, continue
                if ns_name and not any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in item.namespaces._related_objects):
                    continue
                
                for sa_obj, _ in item.serviceaccounts._related_objects:
                    if type(sa_obj) is not K8sServiceAccount:
                        self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__} found as service account from item {item.__primaryvalue__} for privesc")
                    else:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}

                # Privesc to the running GSA inside the object (if any)
                self.escalate_to_cloud_ppals(privect_to_objs, item, privesc_to_cloud)
                
                # The object might be also related to secrets (like a pod having them mounted) that can be also stealed
                if  hasattr(item, "secrets"):
                    for secret, _ in item.secrets._related_objects:
                        for sa_obj, _ in secret.serviceaccounts._related_objects:
                            if type(sa_obj) is not K8sServiceAccount:
                                self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__} found as service account from secret {secret.name} for privesc")
                            else:
                                privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": f"Note that he SA secret can be accessed by {item.__primaryvalue__}."}

        # Relate to the class objects inside a namespace (if ClusterRole, in all)
        # To the cloud, from K8s via "RUN_IN" relations we can only escape from Pods. As a Pod isn a Principal in K8s
        ## you won't be able to escape to the cloud using the techniques that specifies the K8s Pricipal to escape to
        elif not privesc_to and class_name:
            K8sKlass = globals()[class_name]
            # ClusterRole or Global ppal (User or Group)
            if not ns_name or not hasattr(K8sKlass, "namespaces"):
                for obj in K8sKlass.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
                    privect_to_objs[obj.__primaryvalue__] = {"ppal_obj": obj, "extra_reason": ""}
            
            else:
                # Has namespace, so look for the SAs of that namespace
                for item in K8sKlass.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"'):
                    if not any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in item.namespaces._related_objects):
                        continue
                    
                    for sa_obj, _ in item.serviceaccounts._related_objects:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
        
        # Relate to all the privescs in the namespace (if ClusterRole, in all)
        # APPARENTLY THIS TEHCNIQUE IS NO LONGER WORKING SO IT'S NOT NEEDED
        #elif privesc_to == "roles":
        #    ppals_obj = K8sPrincipal.get_all_with_relation("PRIVESC", get_only_end=True)
            # TODO: Indicate in the extra_reson which role/rolebind to patch to escalate priileges.
            # extra_reason = "This is possible abusing the "
        #    for ppal_obj in ppals_obj:
        #        if not ns_name or not hasattr(ppal_obj, "namespaces"):
        #            privect_to_objs[ppal_obj.__primaryvalue__] = {"ppal_obj": ppal_obj, "extra_reason": ""}
        #        
        #        else:
        #            if any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in ppal_obj.namespaces._related_objects):
        #                privect_to_objs[ppal_obj.__primaryvalue__] = {"ppal_obj": ppal_obj, "extra_reason": ""}
        
        else:
            self.logger.error(f"Unknown combination of privesc_to ({privesc_to}) and class_name ({class_name})")

        return privect_to_objs
    

    def escalate_to_cloud_ppals(self, privect_to_objs, k8s_obj, privesc_to_cloud):
        """
        Given the dict tof ppals to escalate to, the object where GSAs might be running and the bool
        indicating if an escalation is needed. Decide if it's possible to escalate.
        """
        # Privesc to the running GSA inside the object (if any)
        if privesc_to_cloud and hasattr(k8s_obj, "running_gcp_service_accounts"):
            for gcp_sa_obj, _ in k8s_obj.running_gcp_service_accounts._related_objects:
                if gcp_sa_obj.__primaryvalue__ is not None: #For some reason py2neo sometimes duplicates the GSA, but one of them has None in email
                    privect_to_objs[gcp_sa_obj.__primaryvalue__] = {"ppal_obj": gcp_sa_obj, "extra_reason": f"SA running in {k8s_obj.name}"}
