import logging
import json
from typing import List
from .gcp_disc_client import GcpDisc
from intel.google.models.gcp_project import GcpProject
from intel.google.models import GcpKMSKeyRing, GcpKMSKey, GcpKMSKeyVersion


class DiscKMS(GcpDisc):
    resource = 'cloudkms'
    version = 'v1'
    logger = logging.getLogger(__name__)

    def _disc(self) -> None:
        """
        Discover all the cloud functions from each project discovered.

        This module will create the KMS key rings and keys and relate them with the parent project.
        """

        projects: List[GcpProject] = GcpProject.get_all()
        self._disc_loop(projects, self._disc_keyrings, __name__.split(".")[-1])

    def _disc_keyrings(self, p_obj: GcpProject):
        """Discover all the KMS Keys Rings of a project"""

        project_name: str = p_obj.name
        http_prep = self.service.projects().locations()  # .list(name=project_name)

        locations: List[str] = self.execute_http_req(http_prep, "locations", disable_warn=True,
                                                     list_kwargs={"name": project_name})

        if not locations:
            return

        # Checking each location of each project might take a lot of time
        # so by default check only one: "global"
        if not self.gcp_get_kms:
            locations = locations[:1]
            locations[0]["locationId"] = "global"

        for loc in locations:
            parent_fullname: str = loc["name"]
            loc_name: str = loc["locationId"]
            http_prep = self.service.projects().locations().keyRings()  # .list(parent=parent_fullname)
            keyrings: List[str] = self.execute_http_req(http_prep, "keyRings", disable_warn=True,
                                                        list_kwargs={"parent": parent_fullname})

            for keyring in keyrings:
                keyring_obj = GcpKMSKeyRing(
                    name=keyring["name"],
                    createTime=keyring.get("createTime", ""),
                ).save()
                keyring_obj.projects.update(p_obj, zone=loc_name)
                keyring_obj.save()

                self.get_iam_policy(keyring_obj, self.service.projects().locations().keyRings(), keyring_obj.name)
                self._disc_keys(p_obj, keyring_obj)

    def _disc_keys(self, p_obj: GcpProject, keyring_obj: GcpKMSKeyRing):
        """Discover all the KMS Keys of a keyring"""

        http_prep = self.service.projects().locations().keyRings().cryptoKeys()  # .list(parent=parent_fullname)
        cryptokeys: List[str] = self.execute_http_req(http_prep, "cryptoKeys", disable_warn=True,
                                                      list_kwargs={"parent": keyring_obj.name})
        for cryptokey in cryptokeys:
            cryptokey_obj = GcpKMSKey(
                name=cryptokey["name"],
                purpose=cryptokey.get("purpose", ""),
                createTime=cryptokey.get("createTime", ""),
                nextRotationTime=cryptokey.get("nextRotationTime", ""),
                labels=json.dumps(cryptokey.get("labels", {})),
                importOnly=cryptokey.get("importOnly", False),
                destroyScheduledDuration=cryptokey.get("destroyScheduledDuration", ""),
                cryptoKeyBackend=cryptokey.get("cryptoKeyBackend", ""),
                rotationPeriod=cryptokey.get("rotationPeriod", ""),
            ).save()
            cryptokey_obj.projects.update(p_obj)
            cryptokey_obj.keyrings.update(keyring_obj)
            cryptokey_obj.save()

            if version := cryptokey.get("primary", {}):
                cryptokeyversion_obj = GcpKMSKeyVersion(
                    name=version["name"],
                    state=version.get("state", ""),
                    createTime=version.get("createTime", ""),
                    protectionLevel=version.get("protectionLevel", ""),
                    algorithm=version.get("algorithm", ""),
                    generateTime=version.get("generateTime", ""),
                    destroyTime=version.get("destroyTime", ""),
                    destroyEventTime=version.get("destroyEventTime", ""),
                    importJob=version.get("importJob", ""),
                    importTime=version.get("importTime", ""),
                    importFailureReason=version.get("importFailureReason", ""),
                    reimportEligible=version.get("reimportEligible", False),
                    externalProtectionLevelOptions=json.dumps(version.get("externalProtectionLevelOptions", {}))
                ).save()
                cryptokeyversion_obj.projects.update(p_obj)
                cryptokeyversion_obj.keys.update(cryptokey_obj)
                cryptokeyversion_obj.save()

            self.get_iam_policy(cryptokey_obj, self.service.projects().locations().keyRings().cryptoKeys(),
                                cryptokey_obj.name)
