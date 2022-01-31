import logging
from typing import List
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

        # Get privescs
        self._disc_loop(privesc_techs, self._check_privesc_tech, __name__.split(".")[-1])
    

    def _check_privesc_tech(self, privesc_tech):
        """Check each privesc check"""

        save_ppal = False
        for ppal_obj in K8sUser.get_all() + K8sGroup.get_all() + K8sServiceAccount.get_all():
            objs_to_privesc = self._get_ppal_privesc(privesc_tech, ppal_obj)
            title = privesc_tech["title"]
            relation = privesc_tech["relation"]
            
            for _, obj_to_privesc in objs_to_privesc.items():
                to_privesc_ppal_obj = obj_to_privesc["ppal_obj"].save()
                reason = obj_to_privesc["reason"]
                
                # If not a ppal we don't want to escalate privs to it
                if "K8sPrincipal" not in to_privesc_ppal_obj.__node__._labels:
                    continue
                
                # Do not privesc to yourself
                if ppal_obj.__primaryvalue__ == to_privesc_ppal_obj.__primaryvalue__ and\
                    type(ppal_obj) == type(to_privesc_ppal_obj):
                    continue
                
                if relation.upper() == "PRIVESC":
                    privesc_rel_name = f"{ppal_obj.__primaryvalue__}->{to_privesc_ppal_obj.__primaryvalue__}"
                    if not privesc_rel_name in self.already_privesc:
                        save_ppal = True
                        ppal_obj.privesc_to.update(to_privesc_ppal_obj, reason=reason, title=title)
                        self.already_privesc.add(privesc_rel_name)
                
                else:
                    self.logger.error(f"Uknown relation {relation}")
                                
                if obj_to_privesc["escape_to_node"] and not ppal_obj.potential_escape_to_node:
                    save_ppal = True
                    ppal_obj.potential_escape_to_node = True
        
            if save_ppal:
                ppal_obj.save()


    def _create_known_groups_relations(self):
        """
        There are some important default groups we need to consider
        """

        # All users are member of system:authenticated
        query = """MATCH (group:K8sGroup{name:"system:authenticated"})
                MATCH (users:K8sUser)
                MERGE (users)-[:MEMBER_OF]->(group)
                return group"""

        graph.evaluate(query)

        # All service accounts are inside "system:serviceaccounts"
        query = """MATCH (group:K8sGroup{name:"system:serviceaccounts"})
                MATCH (sas:K8sServiceAccount)
                MERGE (sas)-[:MEMBER_OF]->(group)
                return group"""

        graph.evaluate(query)

        # All SAs of a namespace are inside system:serviceaccounts:mynamespace
        namespaces:List[K8sNamespace] = K8sNamespace.get_all()
        self._disc_loop(namespaces, self._create_sas_ns_groups, __name__.split(".")[-1])


    def _create_sas_ns_groups(self, ns_obj):
        """Given the namespace crete the group that groups all the SAs of the namespace"""

        group_obj = K8sGroup(name=f"system:serviceaccounts:{ns_obj.name}").save()
        for sa_obj, _ in ns_obj.serviceaccounts._related_objects:
            if type(sa_obj) is not K8sServiceAccount:
                self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__}found as service account in namespace {ns_obj.name}")
            else:
                group_obj.serviceaccounts.update(sa_obj)
        
        group_obj.save()


    def _get_ppal_privesc(self, privesc_tech:dict, ppal_obj: K8sPrincipal) -> dict:
        """
        Given a privesc technique and a principal object, check if the principal can use it to escalate
        """

        verbs = privesc_tech["verbs"]
        resources = privesc_tech["resources"]
        privesc_to = privesc_tech.get("privesc_to", "")
        class_name = privesc_tech.get("class_name", "")
        assert privesc_to or class_name, "There is a privesc tecnique without privesc_to and class_name"

        privecs_to_node_resources = self.analysis_data["extra_info"]["privecs_to_node_resources"]
        
        privect_to_objs = {}
        for res_obj, rel in ppal_obj.resources._related_objects:
            rel_verbs = rel["verbs"]
            apiGroups = rel["api_groups"]
            role_name = rel["role_name"]
            bind_name = rel["bind_name"]

            affected_resource_name = res_obj.name.split(":")[-1].lower()
            # Check if the resource is affected
            if not affected_resource_name == "*" and not any(res in affected_resource_name for res in resources): # The any is used so "pods" inside "pods/log" gives true (check TODO in privesc.yaml)
                continue

            # Check the ppal has all the required verbs permissions
            if not "*" in rel_verbs and not all(v in rel_verbs for v in verbs):
                continue
            
            for _, ppal_obj in self._get_privesc_to_objs(privesc_to, class_name, res_obj.name).items():

                privect_to_objs[ppal_obj["ppal_obj"].__primaryvalue__] = {
                    "ppal_obj": ppal_obj["ppal_obj"],
                    "reason": f"The {'ClusterRole' if res_obj.name == affected_resource_name else 'Role'} '{role_name}' assigned by the binding '{bind_name}' fullfil the necessary privesc permissions '{', '.join(verbs)}' with the set of permissions '{', '.join(rel_verbs)}' over the resource '{res_obj.name}'. {ppal_obj['extra_reason']}",
                    "escape_to_node": res_obj.name in privecs_to_node_resources
                }
        
        return privect_to_objs
            
    
    def _get_privesc_to_objs(self, privesc_to: str, class_name: str, res_name: str):
        """
        Given a privesc_to info, get all the affected objects the ppal can escalate to
        """
        
        privect_to_objs = {}
        ns_name = res_name.split(":")[0]
        
        # Relate to all SAs in the namespace (if ClusterRole, in all)
        if privesc_to == "Namespace SAs":
            if len(res_name.split(":")) == 1:
                for sa_obj in K8sServiceAccount.get_all():
                    privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
            
            else:
                for sa_obj, rel in K8sNamespace(name=ns_name).save().serviceaccounts._related_objects:
                    if type(sa_obj) is not K8sServiceAccount:
                        self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__}found as service account in namespace {ns_name.name} for privesc")
                    else:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
        
        # Relate to the SA running in the resource inside a namespace (if ClusterRole, in all) and to all the SAs whose secret token can be accesed by the item
        elif privesc_to == "Running SA":
            assert class_name, "class_name needs to be specified with 'Running SA' privesc_to"
            K8sKlass = globals()[class_name]
            
            for item in K8sKlass.get_all():
                # If namespace dependant and object not related with the namespace, continue
                if ns_name and not any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in item.namespaces._related_objects):
                    continue
                
                for sa_obj, _ in item.serviceaccounts._related_objects:
                    if type(sa_obj) is not K8sServiceAccount:
                        self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__} found as service account from item {item.__primaryvalue__} for privesc")
                    else:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
                
                # The object might be also related to secrets (like a pod having them mounted) taht can be also stealed
                if hasattr(item, "secrets"):
                    for secret, _ in item.secrets._related_objects:
                        for sa_obj, _ in secret.serviceaccounts._related_objects:
                            if type(sa_obj) is not K8sServiceAccount:
                                self.logger.error(f"Type {type(sa_obj)} with name {sa_obj.__primaryvalue__} found as service account from secret {secret.name} for privesc")
                            else:
                                privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": f"Note that he SA secret can be accessed by {item.__primaryvalue__}."}
            
        # Relate to all the privescs in the namespace (if ClusterRole, in all)
        elif privesc_to == "roles":
            ppals_obj = K8sPrincipal.get_all_with_relation("PRIVESC", get_only_end=True)
            # TODO: Indicate in the extra_reson which role/rolebind to patch to escalate priileges.
            # APPARENTLY THIS TEHCNIQUE IS NO LONGER WORKING SO IT'S NOT NEEDED
            # extra_reason = "This is possible abusing the "
            for ppal_obj in ppals_obj:
                if not ns_name or not hasattr(ppal_obj, "namespaces"):
                    privect_to_objs[ppal_obj.__primaryvalue__] = {"ppal_obj": ppal_obj, "extra_reason": ""}
                
                else:
                    if any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in ppal_obj.namespaces._related_objects):
                        privect_to_objs[ppal_obj.__primaryvalue__] = {"ppal_obj": ppal_obj, "extra_reason": ""}
        
        # Relate to the class objects inside a namespace (if ClusterRole, in all)
        elif not privesc_to and class_name:
            K8sKlass = globals()[class_name]
            # ClusterRole or Global ppal (User or Group)
            if not ns_name or not hasattr(K8sKlass, "namespaces"):
                for obj in K8sKlass.get_all():
                    privect_to_objs[obj.__primaryvalue__] = {"ppal_obj": obj, "extra_reason": ""}
            
            else:
                # Has namespace, so look for the SAs of that namespace
                for item in K8sKlass.get_all():
                    if not any(ns_obj.name.lower() == ns_name.lower() for ns_obj, _ in item.namespaces._related_objects):
                        continue
                    
                    for sa_obj, _ in item.serviceaccounts._related_objects:
                        privect_to_objs[sa_obj.__primaryvalue__] = {"ppal_obj": sa_obj, "extra_reason": ""}
        
        else:
            self.logger.error(f"Unknown combination of privesc_to ({privesc_to}) and class_name ({class_name})")

        return privect_to_objs
