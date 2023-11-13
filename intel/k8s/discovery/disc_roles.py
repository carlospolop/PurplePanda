import logging
import json
from kubernetes import client
from typing import List, Optional
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sResource, K8sClusterRole, K8sRole, K8sServiceAccount, K8sUser, \
    K8sGroup


class DiscRoles(K8sDisc):
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the clusterroles, clusterrolesbinding, and roles and rolebindings of each namespace
        """

        if not self.reload_api(): return

        # Discover all the roles
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_roles, __name__.split(".")[-1])

        # Discover all the roles bindings on each namespace
        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_bindings, __name__.split(".")[-1])

        # Discover clusterroles info AFTER roles info
        # Discover all the clusterroles
        client_cred = client.RbacAuthorizationV1Api(self.cred)
        cluster_roles = self.call_k8s_api(f=client_cred.list_cluster_role)
        if cluster_roles and cluster_roles.items:
            self._disc_loop(cluster_roles.items, self._disc_cluster_roles, __name__.split(".")[-1])

        # Discover all the cluster role bindings
        self._disc_loop([None], self._disc_bindings, __name__.split(".")[-1])

    def _disc_cluster_roles(self, cr):
        """
        Discover all the cluster roles
        """

        cr_obj = K8sClusterRole(
            name=cr.metadata.name,
            self_link=cr.metadata.self_link,
            uid=cr.metadata.uid,
            labels=json.dumps(cr.metadata.labels)
        ).save()

        if not cr.rules:
            return

        for rule in cr.rules:
            if rule.resources:
                for res in rule.resources:
                    res_obj = K8sResource(name=res).save()
                    cr_obj.resources.update(res_obj, verbs=rule.verbs, apiGroups=rule.api_groups, ns_name=None)

            if rule.non_resource_ur_ls:
                for res in rule.non_resource_ur_ls:
                    res_obj = K8sResource(name=res).save()
                    cr_obj.resources.update(res_obj, verbs=rule.verbs, apiGroups=rule.api_groups, ns_name=None)

        cr_obj.save()

    def _disc_roles(self, ns_obj: K8sNamespace, **kwargs):
        """
        Discover all the roles of each namespace
        """

        client_cred = client.RbacAuthorizationV1Api(self.cred)

        roles = self.call_k8s_api(f=client_cred.list_namespaced_role, namespace=ns_obj.ns_name)

        if not roles or not roles.items:
            return

        for r in roles.items:
            r_obj = K8sRole(
                name=f"{ns_obj.name}:{r.metadata.name}",
                self_link=r.metadata.self_link,
                uid=r.metadata.uid,
                labels=json.dumps(r.metadata.labels)
            ).save()

            if not r.rules:
                continue

            for rule in r.rules:
                if rule.resources:
                    for res in rule.resources:
                        res_obj = K8sResource(name=f"{ns_obj.name}:{res}").save()
                        r_obj.resources.update(res_obj, verbs=rule.verbs, apiGroups=rule.api_groups)

                if rule.non_resource_ur_ls:
                    for res in rule.non_resource_ur_ls:
                        res_obj = K8sResource(name=f"{ns_obj.name}:{res}").save()
                        r_obj.resources.update(res_obj, verbs=rule.verbs, apiGroups=rule.api_groups)

            r_obj.namespaces.update(ns_obj)
            r_obj.save()

    def _disc_bindings(self, ns_obj: Optional[K8sNamespace], **kwargs):
        """
        Discover all the bindings of the clusterroles
        """

        client_cred = client.RbacAuthorizationV1Api(self.cred)

        if ns_obj:
            r_binds = self.call_k8s_api(f=client_cred.list_namespaced_role_binding, namespace=ns_obj.ns_name)
        else:
            r_binds = self.call_k8s_api(f=client_cred.list_cluster_role_binding)

        if not r_binds or not r_binds.items:
            return

        name = ns_obj.name if ns_obj else "cluster"
        self._disc_loop(r_binds.items, self._save_binding, __name__.split(".")[-1] + f"bindings-{name}",
                        **{"ns_obj": ns_obj})

    def _save_binding(self, bind, **kwargs):
        """Given the info about a binding, create it"""

        # ns_obj is None in clusterroles
        ns_obj = kwargs["ns_obj"]
        if not bind.subjects:
            return

        bind_name = bind.metadata.name
        kind_bind = bind.kind
        role_ref = bind.role_ref.kind

        if role_ref.lower() == "clusterrole":
            role_obj = K8sClusterRole(name=bind.role_ref.name).save()
            kind_bind = "ClusterRoleBinding" if not kind_bind else kind_bind
        else:
            role_obj = K8sRole(name=f"{ns_obj.name}:{bind.role_ref.name}").save()
            kind_bind = "RoleBinding" if not kind_bind else kind_bind

        role_name = role_obj.name

        for res, rel in role_obj.resources._related_objects:
            verbs = rel["verbs"]
            apiGroups = rel["api_groups"]

            # If RoleBinding with a ClusterRole, get the resource from the namespace and not the generic one
            ## Note that a RoleBinding can use a ClusterRole, but a ClusterRoleBinding cannot use a Role
            if kind_bind.lower() == "rolebinding" and role_ref.lower() == "clusterrolebinding":
                res_obj = K8sResource(name=f"{ns_obj.name}:{res.name}").save()

            else:
                res_obj = res.save()

            if not bind.subjects:
                self.logger.warning(
                    f"The bind '{bind_name}' of type {kind_bind} inside ns '{ns_obj.name}' (is none, clusterrole) doesn't have subjects")
                continue

            for subject in bind.subjects:
                kind = subject.kind
                name: str = subject.name

                if kind == "ServiceAccount" or (kind == "User" and name.startswith("system:serviceaccount:")):
                    namespace = subject.namespace
                    if namespace is None:  # This seems impossible, but isn't for some reason. If not namespace given just search the SA by name
                        sa_obj = K8sServiceAccount.get_by_kwargs(
                            f'_.name CONTAINS ":{name}" AND _.name CONTAINS "{self.cluster_id}-"')
                        if not sa_obj:
                            self.logger.error(f"Uknown namespace of KSA {name}, privescs from this SA might be lost")
                            continue  # If no namespace and not known the
                    else:
                        if name.startswith("system:serviceaccount:"):
                            name = ":".join(name.split(":")[1:])  # In ca
                        sa_obj = K8sServiceAccount(name=f"{self.cluster_id}-{namespace}:{name}",
                                                   potential_escape_to_node=False).save()
                        ns_obj = self._save_ns_by_name(namespace)
                        sa_obj.namespaces.update(ns_obj)
                        sa_obj.save()

                    # TODO: A different binding may have given the sa/user/group permissions over the res_obj already and we are just saving the last one. Myabe that should be an "add" instead of an "update"
                    res_obj.serviceaccounts.update(sa_obj, role_name=role_name, bind_name=bind_name,
                                                   kind_bind=kind_bind, verbs=verbs, apiGroups=apiGroups)

                elif kind == "User":
                    user_obj = K8sUser(name=f"{self.cluster_id}-{name}", potential_escape_to_node=False).save()
                    res_obj.users.update(user_obj, role_name=role_name, bind_name=bind_name, kind_bind=kind_bind,
                                         verbs=verbs, apiGroups=apiGroups)

                elif kind == "Group":
                    group_obj = K8sGroup(name=f"{self.cluster_id}-{name}", potential_escape_to_node=False).save()
                    res_obj.groups.update(group_obj, role_name=role_name, bind_name=bind_name, kind_bind=kind_bind,
                                          verbs=verbs, apiGroups=apiGroups)

                else:
                    self.logger.error(f"Unkown kind of subject {kind} with name {name}")

            res_obj.save()
