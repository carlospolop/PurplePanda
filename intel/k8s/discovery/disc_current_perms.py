import logging
import jwt
from kubernetes import client
from typing import List
from intel.k8s.discovery.k8s_disc import K8sDisc
from intel.k8s.models.k8s_model import K8sNamespace, K8sResource, K8sClusterRole, K8sRole, K8sServiceAccount, K8sUser, \
    K8sGroup


class DiscCurrentPerms(K8sDisc):
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover the current user, its groups, and its permissions
        """

        if not self.reload_api(): return
        # Discover current user
        if "authorization" in self.cred.configuration.api_key and " " in self.cred.configuration.api_key[
            "authorization"]:
            jwt_token = self.cred.configuration.api_key["authorization"].split(" ")[1]

            try:
                data = jwt.decode(jwt_token, options={"verify_signature": False, "verify_aud": False})
            except jwt.exceptions.DecodeError as e:
                self.logger.error(f"Error decoding JWT token {jwt_token}: {e}")
                return

            email = data["email"]
            username = data["name"]
            groups = data["groups"]
            user_obj = K8sUser(name=f"{self.cluster_id}-{username}", email=email, potential_escape_to_node=False).save()

            for g in groups:
                group_obj = K8sGroup(name=f"{self.cluster_id}-{g}", potential_escape_to_node=False).save()
                user_obj.groups.update(group_obj)

            user_obj.save()

        elif self.cred.configuration.username:
            username = self.cred.configuration.username
            user_obj = K8sUser(name=f"{self.cluster_id}-{username}", email=email, potential_escape_to_node=False).save()

        else:
            self.logger.error("No username found in this consfiguration, I cannot get current user!")
            return

        # Discover its permissions
        client_cred = client.AuthorizationV1Api(self.cred)

        namespaces: List[K8sNamespace] = K8sNamespace.get_all_by_kwargs(f'_.name =~ "{str(self.cluster_id)}-.*"')
        self._disc_loop(namespaces, self._disc_current_perms, __name__.split(".")[-1],
                        **{"client_cred": client_cred, "user_obj": user_obj})

    def _disc_current_perms(self, ns_obj: K8sNamespace, **kwargs):
        """
        Discover the current user permissions of the current user
        """

        client_cred = kwargs["client_cred"]
        user_obj = kwargs["user_obj"]

        spec = client.V1SelfSubjectRulesReviewSpec(namespace=ns_obj.ns_name)
        body = client.V1SelfSubjectRulesReview(spec=spec)

        current_perms = self.call_k8s_api(f=client_cred.create_self_subject_rules_review, body=body)

        if not current_perms:
            return

        for perm in current_perms.status.resource_rules:
            for res in perm.resources:
                res_obj = K8sResource(name=f"{ns_obj.name}:{res}").save()
                res_obj.users.update(user_obj, role_name="unknown", bind_name="unknown", kind_bind="unknown",
                                     verbs=perm.verbs, apiGroups=perm.api_groups)
                res_obj.save()
