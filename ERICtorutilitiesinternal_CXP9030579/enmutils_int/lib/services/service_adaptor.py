import commands

import requests
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.services import service_registry
from retrying import retry

URL_HEADER = {"Content-Type": "application/json",
              "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
              "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
              "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate",
              "Connection": "keep-alive"}
RETRY_TIME_SECS = 30
API_VERSION = "/api/v1"
PROXIES = {"http": None, "https": None}


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=RETRY_TIME_SECS * 1000)
def send_request_to_service(method, url, service_name, json_data=None, retry=True):
    """
    Send REST request to the service

    :param method: Method to be used
    :type method: method
    :param url: Destination URL of request
    :type url: str
    :param service_name: The name of the service to send the request to
    :type service_name: str
    :param json_data: Optional json data to be send as part of request
    :type json_data: dict
    :param retry: Boolean indicating if a retry should be attempted
    :type retry: bool

    :return: Response from queried service
    :rtype: `requests.Response`
    :raises EnvironError: if error thrown in REST request or if response is bad
    """
    service_port, service_host, _ = service_registry.get_service_info_for_service_name(service_name)
    full_url = ("http://{service_host}:{service_port}{api_version}/{url}".format(service_host=service_host,
                                                                                 service_port=service_port,
                                                                                 api_version=API_VERSION, url=url))
    data_content = "(data:{0})".format(json_data) if json_data else ""
    log.logger.debug(
        "Sending {0} request to Workload Profiles Service {1} URL {2} {3}.\n".format(method, service_name, full_url,
                                                                                     data_content))

    try:
        if method == "DELETE":
            response = requests.delete(full_url, proxies=PROXIES)
        elif method == "POST":
            response = requests.post(full_url, json=json_data, proxies=PROXIES)
        else:
            response = requests.get(full_url, proxies=PROXIES)

    except Exception as e:
        message = ("Exception occurred while sending request to service: {0} :: retrying in {1}s ..."
                   .format(e, RETRY_TIME_SECS))
        log.logger.debug(message)
        raise EnvironError(message)

    if not response.ok and retry:
        message = ("Response NOK after sending request to service {0} :: "
                   "URL: {1} :: Status code: {2} :: Reason: {3}".format(service_name, response.url,
                                                                        response.status_code, response.reason))
        details = ("Details of error encountered by service: {0} :: retrying in {1}s ...".format(
            response.text[131:-5], RETRY_TIME_SECS))

        log.logger.debug(message)
        log.logger.debug(details)
        raise EnvironError("{0}. {1}".format(message, details))

    log.logger.debug("{0} request to service {1} returned successfully".format(method, service_name))
    return response


def can_service_be_used(service_name, profile=None):
    """
    Determine if service can be used

    :param service_name: Name of service
    :type service_name: str
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :return: Boolean to indicate if service can be used or not
    :rtype: bool
    """
    priority = profile.priority if profile else None
    if profile and getattr(profile, "IGNORE_SOA", False):
        log.logger.debug("IGNORE_SOA is set - will not use services")
        return

    service_can_be_used = True if (service_registry.can_service_be_used(service_name, priority) and
                                   is_service_running(service_name)) else False
    log.logger.debug("Service {0} can be used: {1}".format(service_name, service_can_be_used))
    return service_can_be_used


def is_service_running(service_name):
    """
    Check if service is running and ready to accept requests

    :param service_name: Name of service
    :type service_name: str
    :return: Boolean to indicate if service is running or not
    :rtype: bool
    """
    command = "service {0} status".format(service_name)
    output = commands.getoutput(command)
    running_text = "{0} is running and listening".format(service_name)
    running_status = True if running_text in output else False

    if not running_status:
        log.logger.debug("Warning: Service {0} is not running".format(service_name))

    return running_status


def validate_response(response):
    """
    Validate response from the service

    :param response: Response from the service
    :type response: `requests.Response`
    :return: Message received in the response
    :rtype: Any

    :raises EnvironError: if the request was unsuccessful
    """
    if response.ok and response.json().get("success"):
        return response.json().get("message")

    raise EnvironError("Request was unsuccessful: {0}".format(response.content))


def print_service_operation_message(response, logger):
    """
    Prints the output of the node operation if successful

    :param response: Response from Service Adaptor service
    :type response: `requests.Response`
    :param logger: Logger instance provided by the calling service
    :type logger: `log.logger`

    :raises RuntimeError: raised if the RC in the response is 599
    """
    if response.ok:
        logger.info(response.json().get("message"))
    elif response.status_code in [599]:
        raise RuntimeError(response.json().get("message"))
