import logging
from intel.concourse.discovery.concourse_disc_client import ConcourseDisc
from intel.concourse.models.concourse_model import ConcourseTeam, ConcourseUser, ConcourseGroup

class DiscTeams(ConcourseDisc):
    logger = logging.getLogger(__name__)
    
    def _disc(self) -> None:
        """
        Discover all the teams and their users and roles
        """

        teams = self.call_concourse_api(f=self.cred.list_teams)
        self._disc_loop(teams, self._disc_teams, __name__.split(".")[-1])

    
    def _disc_teams(self, team, **kwargs):
        """Discover each team"""

        id = team["id"]
        name = team["name"]

        team_obj = ConcourseTeam(id=id, name=name).save()
        for role,mems in team["auth"].items():
            if "users" in mems:
                for user in mems["users"]:
                    user_obj = ConcourseUser(name=user).save()
                    user_obj.teams.update(team_obj, role=role)
                    user_obj.save()
                del mems["users"]
            
            if "groups" in mems:
                for grp in mems["groups"]:
                    grp_obj = ConcourseGroup(name=grp).save()
                    grp_obj.teams.update(team_obj, role=role)
                    grp_obj.save()
                del mems["groups"]
            
            # Check if more than "users" or "groups"
            if len(mems) > 0:
                self.logger.error(f"The team {name} has more members than known: {mems}")
