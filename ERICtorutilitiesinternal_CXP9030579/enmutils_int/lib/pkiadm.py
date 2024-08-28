# ********************************************************************
# Name    : PKI Admin
# Summary : Module which provides functionality related to PKI entity
#           and profile management. Allows the user to create, query,
#           update and delete Profile, End Entity and Entity objects
#           in ENM, primarily used by User Security profiles, allows
#           creation and distribution of certificates in ENM.
# ********************************************************************

from enmutils.lib import log, headers
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError

GET_ALL_PROFILES_URL = "/pki-manager/profiles"


def get_all_certificate_profiles(user, offset=0, limit=3000):
    """
    Query ENM for a list of available certificate profiles

    :type user: `enm_user_2.User`
    :param user: Enm user who will create the entity
    :param offset: Index to start returning values from
    :type offset: int
    :param limit: Maximum number of certificate profiles to return in the request
    :type limit: int

    :return: response.json: dictionary containing all certificate profiles data
    :rtype: dict
    """
    body = {
        "offset": offset,
        "limit": limit,
        "filter": {"name": "", "status": {"active": "true", "inactive": "true"}, "type": ["CERTIFICATE_PROFILE"]}
    }

    response = user.post(GET_ALL_PROFILES_URL, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
    raise_for_status(response, message_prefix="Could not retrieve certificate profiles: ")
    log.logger.debug("Successfully retrieved all certificate profiles.")
    return response.json()


def get_all_entity_profiles(user, offset=0, limit=3000):
    """
    Query ENM for a list of available entity profiles

    :type user: `enm_user_2.User`
    :param user: Enm user who will create the entity
    :param offset: Index to start returning values from
    :type offset: int
    :param limit: Maximum number of entity profiles to return in the request
    :type limit: int

    :return: response.json: dictionary containing all entity profiles data
    :rtype: dict
    """
    body = {
        "offset": offset,
        "limit": limit,
        "filter": {"name": "", "status": {"active": "true", "inactive": "true"}, "type": ["ENTITY_PROFILE"]}
    }

    response = user.post(GET_ALL_PROFILES_URL, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
    raise_for_status(response, message_prefix="Could not retrieve entity profiles: ")
    log.logger.debug("Successfully retrieved all entity profiles.")
    return response.json()


class PKIAdm(object):

    CREATE_CMD = ""
    DELETE_CMD = ""

    GET_ALL_ENTITIES_URL = "/pki-manager/entitylist/fetch"

    def __init__(self, user, name):
        self.name = name
        self.user = user
        self.id = None
        self.type = self.__class__.__name__

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    @property
    def body(self):
        return {}

    def create(self):
        """
        Create an Entity

        :raises: HTTPError
        """
        response = self.user.post(self.CREATE_CMD, json=self.body, headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not create: {0} {1} ".format(self.type, self.name))
        log.logger.debug("Successfully created {0} {1}".format(self.type, self.name))
        if not response.text:
            raise EnmApplicationError("No json to decode: {}".format(response.text))
        elif isinstance(self, Entity):
            self.id = response.json().get('entityInfo').get('id')
        else:
            self.id = response.json().get('id')

    def get_all_entities(self, offset=0, limit=60000):
        """
        Query ENM for a list of available entities

        :param offset: Index to start returning values from
        :type offset: int
        :param limit: Maximum number of profiles to return in the request
        :type limit: int

        :return: List of dictionaries containing entities data
        :rtype: list
        """
        body = {
            "offset": offset,
            "limit": limit
        }
        response = self.user.post(self.GET_ALL_ENTITIES_URL, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not retrieve entities: ")
        log.logger.debug("Successfully retrieved all entities.")
        return response.json()

    def delete(self, pki_id=None, pki_type=None, pki_name=None):
        """
        Delete the Entity, EntityProfile or CertificateProfile based on the subclass

        :raises: HTTPError
        """
        pki_type = self.type if not pki_type else pki_type
        pki_id = self.id if not pki_id else pki_id
        pki_name = self.name if not pki_name else pki_name
        response = self.user.delete_request(self.DELETE_CMD.format(id=pki_id), headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not delete {0}: ".format(pki_type))
        log.logger.debug("Successfully deleted {0}: {1}".format(pki_type, pki_name))

    def _teardown(self):
        """
        Secret teardown method
        """
        self.delete()


class CertificateProfile(PKIAdm):

    CREATE_CMD = "/pki-manager/certificateprofile/save"
    DELETE_CMD = "/pki-manager/profilelist/delete/CERTIFICATE_PROFILE/{id}"

    @property
    def body(self):
        return {
            "type": "CERTIFICATE_PROFILE",
            "name": self.name,
            "version": "V3",
            "active": True,
            "forCAEntity": False,
            "issuer": {"certificateAuthority": {"name": "ENM_E-mail_CA"}},
            "signatureAlgorithm": {"id": 3, "name": "SHA256withRSA"},
            "certificateValidity": "P2Y",
            "skewCertificateTime": "PT60M",
            "subjectUniqueIdentifier": False,
            "issuerUniqueIdentifier": False,
            "keyGenerationAlgorithms": [{"name": "RSA", "keySize": 2048, "id": 22}],
            "subjectCapabilities": {"subjectFields": [{"type": "COMMON_NAME"}]},
            "certificateExtensions":
                {"certificateExtensions": [
                    {"@class": ".BasicConstraints", "critical": False, "isCA": False, "pathLenConstraint": None}]}
        }

    def remove_old_certificate_profiles(self, limit=6000):
        """
        Remove old certificate profiles (i.e.; names starts with Secui) in ENM from previous runs

        :param limit: Maximum number of certificate profiles to return in the request
        :type limit: int
        """
        try:
            log.logger.debug("Attempt to remove the old certificate profiles (which profiles names are "
                             "started with 'Secui') in ENM")
            certificate_profiles = get_all_certificate_profiles(self.user, limit=limit)
            for certificate_profile in certificate_profiles:
                try:
                    if certificate_profile['name'].startswith(self.name.split('_')[0]):
                        pki_name = certificate_profile['name']
                        pki_id = certificate_profile['id']
                        pki_type = certificate_profile['type']
                        self.delete(pki_id=pki_id, pki_name=pki_name, pki_type=pki_type)
                except Exception as e:
                    log.logger.debug("Error encountered revoking, deleting certificate profile: {0}.".format(str(e)))
                    continue
        except Exception as e:
            log.logger.debug("Unable to retrieve list of certificate profiles, error encountered: {0}.".format(str(e)))


class EntityProfile(PKIAdm):

    CREATE_CMD = "/pki-manager/entityprofile/save"
    DELETE_CMD = "/pki-manager/profilelist/delete/ENTITY_PROFILE/{id}"

    @property
    def certificate_profile_id(self):
        all_profiles = get_all_certificate_profiles(self.user)
        certificate_profile = None
        for profile in all_profiles:
            if self.name in profile.values() and "CERTIFICATE_PROFILE" in profile.values():
                certificate_profile = profile.get('id')
        return certificate_profile

    @property
    def body(self):
        return {
            "type": "ENTITY_PROFILE",
            "name": self.name,
            "certificateProfile": {"id": self.certificate_profile_id, "name": self.name},
            "trustProfiles": [],
            "active": True,
            "category": {"id": 0, "name": "UNDEFINED"},
            "keyGenerationAlgorithm": {"name": "RSA", "keySize": "2048", "id": 22},
            "subject": {"subjectFields": [{"type": "COMMON_NAME", "value": self.name}]}
        }

    def remove_old_entity_profiles(self, limit=6000):
        """
        Remove old entity profiles(i.e.; names starts with Secui) in ENM from previous runs

        :param limit: Maximum number of entity profiles to return in the request
        :type limit: int
        """
        try:
            log.logger.debug("Attempt to remove the old entity profiles (which profiles names are "
                             "started with 'Secui') in ENM")
            entity_profiles = get_all_entity_profiles(self.user, limit=limit)
            for entity_profile in entity_profiles:
                try:
                    if entity_profile['name'].startswith(self.name.split('_')[0]):
                        pki_name = entity_profile['name']
                        pki_id = entity_profile['id']
                        pki_type = entity_profile['type']
                        self.delete(pki_id=pki_id, pki_name=pki_name, pki_type=pki_type)
                except Exception as e:
                    log.logger.debug("Error encountered revoking, deleting entity profile: {0}.".format(str(e)))
                    continue
        except Exception as e:
            log.logger.debug("Unable to retrieve list of entity profiles, error encountered: {0}.".format(str(e)))


class Entity(PKIAdm):

    CREATE_CMD = "/pki-manager/v2/entity/save"
    DELETE_CMD = "/pki-manager/entitylist/delete/ENTITY/{id}"
    ISSUE_ENTITY_CERTIFICATE = "/pki-manager/entitylist/issue"
    REVOKE_ENTITY_CERTIFICATE = "/pki-manager/entities/entity/revocation"
    ENTITY_PROFILE_ID = 0
    ENTITY_PROFILE_NAME = "None"

    def __init__(self, user, name, all_profiles=None):
        """
        Init function for class

        :param user: User who will make requests to ENM
        :type user: `enm_user_2.User`
        :param name: Name of the Entity to be created
        :type name: str
        :param all_profiles: list of available entity profiles
        :type all_profiles: list
        """
        super(Entity, self).__init__(user, name)
        self.all_enm_profiles = all_profiles if all_profiles else []

    def set_all_profiles(self):
        """
        Retrieve the list of Entity profiles from ENM
        """
        if not self.all_enm_profiles:
            self.all_enm_profiles = get_all_entity_profiles(self.user, limit=6000)

    def set_entity_profile_name_and_id(self):
        """
        Set entity profile name and profile id.
        """
        for profile in self.all_enm_profiles:
            if profile.get('type') == "ENTITY_PROFILE" and self.name.split('_')[0] not in profile.get('name'):
                self.ENTITY_PROFILE_NAME = profile.get('name')
                self.ENTITY_PROFILE_ID = profile.get('id')
                break

    @property
    def body(self):
        entity_body = {
            "type": "ENTITY",
            "entityInfo": {
                "id": "",
                "name": self.name,
                "active": True,
                "oTP": "",
                "oTPCount": "",
                "subject": {"subjectFields": [{"type": "COMMON_NAME", "value": self.name}]}},
            "otpValidityPeriod": "",
            "category": {"id": 0, "name": "UNDEFINED"},
            "entityProfile": {"id": self.ENTITY_PROFILE_ID, "name": self.ENTITY_PROFILE_NAME},
            "publishCertificatetoTDPS": False,
            "keyGenerationAlgorithm": {"name": "RSA", "keySize": "2048", "id": 22}
        }
        if self.ENTITY_PROFILE_NAME == 'AMOS_EM_USER_EP':
            entity_body['subjectUniqueIdentifierValue'] = self.name
            log.logger.debug("adding subjectUniqueIdentifierValue for AMOS_EM_USER_EP entity profile")
        return entity_body

    def issue(self):
        """
        Issue the Entities Certificate to ENM DPS

        :raises: HTTPError
        """
        body = {
            "name": self.name,
            "type": "ENTITY",
            "chain": True,
            "format": "PKCS12",
            "password": "TestPassw0rd"
        }
        response = self.user.post(self.ISSUE_ENTITY_CERTIFICATE, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not issue entity certificate: ")
        log.logger.debug("Successfully issued certificate for entity {0}".format(self.name))

    def revoke(self, name=None):
        """
        Revoke the Entities Certificate in ENM DPS
        :raises: HTTPError
        """
        body = {
            "entityName": self.name if not name else name,
            "revocationReason": 0
        }
        response = self.user.post(self.REVOKE_ENTITY_CERTIFICATE, json=body, headers=headers.SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not revoke entity certificate: ")
        log.logger.debug("Successfully revoked certificate for entity {0}".format(self.name))

    def _teardown(self):
        """
        Secret Teardown method
        """
        self.revoke()
        self.delete()

    def remove_old_entities(self):
        """
        Remove old entities in ENM from previous runs
        """
        try:
            log.logger.debug("Attempt to remove the old entities in ENM")
            for entity in self.get_all_entities():
                try:
                    if (entity.get('entityInfo') and entity['entityInfo']['status'] != "DELETED" and
                            "Secui_Six" in entity['entityInfo']['name']):
                        pki_name = entity['entityInfo']['name']
                        pki_id = entity['entityInfo']['id']
                        pki_type = entity.get('type')
                        self.revoke(name=pki_name)
                        self.delete(pki_id=pki_id, pki_name=pki_name, pki_type=pki_type)
                except Exception as e:
                    log.logger.debug("Error encountered revoking, deleting entity: {0}.".format(str(e)))
                    continue
        except Exception as e:
            log.logger.debug("Unable to retrieve list of entities, error encountered: {0}.".format(str(e)))
