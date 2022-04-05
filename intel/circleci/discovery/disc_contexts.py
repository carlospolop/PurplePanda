import logging
from intel.circleci.discovery.circleci_disc_client import CircleCIDisc
from intel.circleci.models import CircleCIOrganization, CircleCIContext, CircleCISecret


class DiscContexts(CircleCIDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the contexts of each organization
        """

        self._disc_loop(self.orgs, self._disc_contexts, __name__.split(".")[-1])

    
    def _disc_contexts(self, org, **kwargs):
        """Discover each context"""

        contexts = self.call_circleci_api(self.cred.get_contexts, [], org.split("/")[-1], paginate=True)

        if not contexts:
            return
        
        org_obj = CircleCIOrganization(name=org).save()

        # TODO: The CircleCI API doesn't give the teams that has access to the context, it would be nice to have that info
        for ctxt in contexts:
            ctxt_obj = CircleCIContext(name=ctxt["name"], id=ctxt["id"]).save()
            ctxt_obj.orgs.update(org_obj)
            ctxt_obj.save()
            self._disc_context_secrets(ctxt_obj)


    def _disc_context_secrets(self, ctxt_obj: CircleCIContext):
        """Discover each context secret"""

        secrets = self.call_circleci_api(self.cred.get_context_envvars, [], ctxt_obj.id, paginate=True)

        for secret in secrets:
            name = secret["variable"]
            secret_obj = CircleCISecret(name=name).save()
            secret_obj.contexts.update(ctxt_obj)
            secret_obj.save()
