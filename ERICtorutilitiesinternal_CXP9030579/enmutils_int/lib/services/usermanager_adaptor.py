import json

from enmutils.lib import log, mutexer, cache
from enmutils.lib.enm_user_2 import User
from enmutils_int.lib import cache_int
from enmutils_int.lib.services import service_adaptor, service_registry, deploymentinfomanager_adaptor
from enmutils_int.lib.services.service_values import POST_METHOD
from enmutils_int.lib.services.usermanager_helper_methods import get_sessions_info

SERVICE_NAME = "usermanager"

GET_USERS_URL = "users"
CREATE_USERS_URL = "users/create"
DELETE_USERS_URL = "users/delete"
GET_USER_SESSIONS_INFO = "users/sessions"


def check_if_service_can_be_used_by_profile(profile):
    """
    Check to see if profile can use service

    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`

    :return: Bool to indicate if service can be used
    :rtype: bool
    """

    return service_adaptor.can_service_be_used(SERVICE_NAME, profile=profile)


def create_users_via_usermanager_service(profile_name, number_of_users, roles):
    """
    Create Users via User Manager service

    :param profile_name: Profile Name
    :type profile_name: str
    :param number_of_users: Number of users to be created
    :type number_of_users: int
    :param roles: List of ENM roles that each user will have
    :type roles: list
    :return: List of BasicUser Objects
    :rtype: list
    """
    service_port, service_host, _ = service_registry.get_service_info_for_service_name(SERVICE_NAME)
    log.logger.debug("Creating users via the {0} WL service ({1}:{2})".
                     format(SERVICE_NAME, service_host, service_port))
    users = get_users_via_service(profile_name, roles=roles)
    if users:
        log.logger.debug("{0} user(s) found. Deleting existing user(s) first".format(len(users)))
        delete_users_via_service(profile_name, roles=roles)
    json_data = {"username_prefix": profile_name, "number_of_users": number_of_users, "user_roles": roles}
    users_info = send_request_to_service("POST", CREATE_USERS_URL, json_data=json_data)
    if not users_info.text[0] == "[":
        users = get_users_via_service(profile_name, roles=roles)
    else:
        users = convert_received_data_to_profile_users(users_info)
    log.logger.debug("Number of Users created by the {0} WL service: {1}".format(SERVICE_NAME, len(users)))
    return users


def delete_users_via_usermanager_service(profile_name):
    """
    Create Users via User Manager service

    :param profile_name: Profile Name
    :type profile_name: str
    """
    service_port, service_host, _ = service_registry.get_service_info_for_service_name(SERVICE_NAME)
    log.logger.debug("Deleting users via the {0} WL service ({1}:{2})".
                     format(SERVICE_NAME, service_host, service_port))

    log.logger.debug("Checking for existing users for {0}".format(profile_name))
    delete_users_via_service(profile_name)
    log.logger.debug("Users have been deleted by the {0} WL service".format(SERVICE_NAME))


def delete_users_via_service(profile_name, roles=None):
    """
    Send request to delete Users via user manager service

    :param profile_name: Profile Name
    :type profile_name: str
    :param roles: List of ENM roles that each user will have
    :type roles: list
    :raises EnvironError: if POST request is unsuccessful
    """

    json_data = {"profile_name": profile_name}
    if roles:
        user_roles = "{0}".format("||".join(roles))
        json_data.update({"user_roles": user_roles})
    url = ("{service_path}?delete_data={delete_data}".format(service_path=DELETE_USERS_URL, delete_data=json_data))
    send_request_to_service("DELETE", url)


def get_users_via_service(profile_name, roles=None):
    """
    Query User manager service to get Users associated with particular username

    :param profile_name: Profile Name
    :type profile_name: str
    :param roles: list of ENM roles
    :type roles: list
    :return: Dictionary of created users
    :rtype: dict
    """
    user_roles_data = "&user_roles={0}".format(",".join(roles)) if roles else ""
    url = ("{service_path}?profile={profile_name}{user_roles_data}"
           .format(service_path=GET_USERS_URL, profile_name=profile_name, user_roles_data=user_roles_data))
    response = send_request_to_service("GET", url)

    users = convert_received_data_to_profile_users(response)

    return users


def send_request_to_service(method, url, json_data=None):
    """
    Send REST request to UserManager service

    :param method: Method to be used
    :type method: method
    :param url: Destination URL of request
    :type url: str
    :param json_data: Optional json data to be send as part of request
    :type json_data: dict

    :return: Response from Usermanager service
    :rtype: `requests.Response`

    :raises EnvironError: if error thrown in RESt request or if response is bad
    """

    response = service_adaptor.send_request_to_service(method, url, SERVICE_NAME, json_data=json_data)
    return response


def convert_received_data_to_profile_users(response):
    """
    Convert received data from Usermanager service to User objects

    :param response: Response to HTTP Rest request
    :type response: requests.Response
    :return: List of BasicUser objects
    :rtype: list
    """
    log.logger.debug("Converting Data to BasicUser. Received Data: {}".format(response.text))
    users = []
    received_data = json.loads(response.text)
    for user_info in received_data:
        users.append(BasicUser(**user_info))

    return users


def get_profile_sessions_info(profiles):
    """
    Provides the top 10 sessions hoarders and the number of sessions per profile

    :param profiles: list of profile Objects
    :type profiles: list

    :return: Dictionary of numbers of sessions per profile and list of top 10 sessions hoarders
    :rtype: tuple
    """
    log.logger.debug("Fetching profile sessions information from usermanager service")
    profile_names = [profile.NAME for profile in profiles]
    if service_adaptor.can_service_be_used(SERVICE_NAME):
        json_data = {"profiles": profile_names}
        response = service_adaptor.validate_response(send_request_to_service(
            POST_METHOD, GET_USER_SESSIONS_INFO, json_data=json_data))
        profile_sessions, session_hoarders = response.get('profile_sessions'), response.get('session_hoarders')
    else:
        profile_sessions, session_hoarders = get_sessions_info(profile_names)
    return profile_sessions, session_hoarders


class BasicUser(User):
    """
    Extends the enm_user_2.User class.
    """

    def __str__(self):
        """
        Overrides __builtin__ __str__

        :return: String username variable
        :rtype: str
        """
        return "{0}".format(self.username)

    def __repr__(self):
        """
        Overrides __builtin__ __repr__

        :return: Returns the value of __str__
        :rtype: str
        """
        return self.__str__()

    @staticmethod
    def get_apache_url_from_service():
        """
        Get the Apache URL from the local service if available

        :return: Apache URL value if available
        :rtype: str
        """
        log.logger.debug("Fetching ENM_URL")
        try:
            if deploymentinfomanager_adaptor.can_service_be_used():
                url = deploymentinfomanager_adaptor.get_apache_url()
            else:
                url = cache.get_apache_url()
            log.logger.debug("Setting local cache value of ENM_URL to {0} with TTL of {1}s"
                             .format(url, cache_int.CACHE_TTL_TIME_SECS))
            cache_int.set_ttl("ENM_URL", url)
            return url
        except Exception as e:
            log.logger.debug("Unable to retrieve Apache URL, error encountered: [{0}].".format(str(e)))

    def open_session(self, reestablish=False, url=None):
        """
        Override the parent class open session to query service for URL

        :param reestablish: bool that forces the session to be reestablished or not
        :type reestablish: bool
        :param url: FQDN Apache URL of the ENM system the session will be opened against.
        :type url: str or None
        """
        with mutexer.mutex("fetch-cached-enm-url", log_output=True):
            log.logger.debug("Fetching ENM_URL value from local cache")
            enm_url = cache_int.get_ttl("ENM_URL")
            if not enm_url:
                log.logger.debug("ENM_URL value not set in local cache")
                enm_url = self.get_apache_url_from_service()
        url = url or enm_url
        super(BasicUser, self).open_session(reestablish=reestablish, url=url)
