import logging
from intel.concourse.discovery.concourse_disc_client import ConcourseDisc
from intel.concourse.models.concourse_model import ConcourseUser

class DiscActiveUsers(ConcourseDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the teams and their users and roles
        """

        users = self.call_concourse_api(f=self.cred.get, path="users")
        self._disc_loop(users, self._disc_active_users, __name__.split(".")[-1])

    
    def _disc_active_users(self, user, **kwargs):
        """Discover each active user"""

        if not "connector" in user or not "username" in user:
            return
        
        name = f'{user["connector"]}:{user["username"]}'
        ConcourseUser(name=name, last_login=user["last_login"]).save()
