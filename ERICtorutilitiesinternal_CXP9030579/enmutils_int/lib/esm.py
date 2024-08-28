# ********************************************************************
# Name    : Ericsson System Monitoring
# Summary : Functional module responsible for interacting with
#           Ericsson System Monitoring service.
#           Allows basic interaction with the ESM service, login,
#           GET requests, external to ENM.
# ********************************************************************

from random import choice
from enmutils.lib.headers import SECURITY_REQUEST_HEADERS
from enmutils.lib import log
from enmutils.lib.cache import is_enm_on_cloud_native

ESM_LOGIN = "/coregui/login"
ESM_PASSWORD = "ericssonadmin"
LOGIN_POST_URL = "{esm_home}/portal/sessionAccess"
LOGOUT_URL = "/coregui/#LogOut"


def esm_login(username, session, esm_home):
    """
    Login into ESM
    :param username: Name of the user to login
    :type username: str
    :param session: ENM Session instance
    :type session: `request.ExternalSession`
    :param esm_home: Base URL for ESM
    :type esm_home: str
    """
    log.logger.debug("Login to ESM with user:{}".format(username))
    esm_login_home = "".join([esm_home, ESM_LOGIN])
    esm_login_response = session.get(esm_login_home)
    esm_login_response.raise_for_status()
    payload = {"username": username, "password": ESM_PASSWORD}
    response = session.post(LOGIN_POST_URL.format(esm_home=esm_home), json=payload, headers=SECURITY_REQUEST_HEADERS)
    if response.status_code != 200:
        response.raise_for_status()
    else:
        log.logger.debug("Logged into ESM with user:{}".format(username))


def esm_logout(username, session, esm_home):
    """
    Logout from ESM
    :param username: Name of the user to logout
    :type username: str
    :param session: ENM Session instance
    :type session: `request.ExternalSession`
    :param esm_home: Base URL for ESM
    :type esm_home: str
    """
    log.logger.debug("Logout the user:{}".format(username))
    esm_logout_response = session.get(esm_home + LOGOUT_URL)
    if esm_logout_response.status_code != 200:
        esm_logout_response.raise_for_status()
    else:
        log.logger.debug("Logged out the user:{}".format(username))


def random_get_request_cn(username, user, esmon_vm_ip=None):
    """
    Perform a random get request in ESM
    :param user: user object
    :type user: user
    :param username: Name of the user performing get request
    :type username: str
    :param esmon_vm_ip: will get esmon_vm_ip
    :type esmon_vm_ip: str
    """
    log.logger.debug("Executing a random get request on the ESM UI with user:{}".format(username))
    cn_deployment = is_enm_on_cloud_native()
    status_overview_url = "/esm-server/#status-overview" if cn_deployment else "/#status-overview"
    user_mgt_url = "/esm-server/#user-management" if cn_deployment else "/#user-management"
    urls = [
        status_overview_url,
        user_mgt_url
    ]
    if cn_deployment:
        ui_response = user.get(choice(urls), headers=SECURITY_REQUEST_HEADERS)
    else:
        ui_response = user.get('https://' + esmon_vm_ip + choice(urls), headers=SECURITY_REQUEST_HEADERS)
    if ui_response.status_code != 200:
        ui_response.raise_for_status()
    else:
        log.logger.debug("Random get request on the ESM UI with user:{0} was successful".format(username))
