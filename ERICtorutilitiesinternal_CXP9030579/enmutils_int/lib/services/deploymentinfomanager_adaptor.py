import base64

from enmutils.lib import log
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.services import service_adaptor, deployment_info_helper_methods as helper
from enmutils_int.lib.services.service_values import POST_METHOD, GET_METHOD

SERVICE_NAME = "deploymentinfomanager"

READ_PIB_URL = "deployment/pib/read"
UPDATE_PIB_URL = "deployment/pib/update"
APACHE_URL = "deployment/apache"
SERVICE_INFO_URL = "deployment/info"
COPY_EMP_KEY_URL = "deployment/copy_emp"

POID_REFRESH = "deployment/poid_refresh"
LMS_PASS_URL = "deployment/lms/password"
CHECK_ENM_ACCESS_URL = "deployment/enm/access"
CHECK_PASS_AGEING_URL = "deployment/password/ageing"
ENIQ_URL = "deployment/eniq"
DEPLOYMENT_TYPE_URL = "deployment/config"


def can_service_be_used(profile=None):
    """
    Determine if service can be used

    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :return: Boolean to indicate if service can be used or not
    :rtype: bool
    """
    return service_adaptor.can_service_be_used(SERVICE_NAME, profile)


def send_request_to_service(method, url, json_data=None, retry=True):
    """
    Send REST request to service

    :param method: Method to be used
    :type method: method
    :param url: Destination URL of request
    :type url: str
    :param json_data: Optional json data to be send as part of request
    :type json_data: dict
    :param retry: Boolean indicating if the REST request should be retired if unsuccessful
    :type retry: bool

    :return: Response from Service
    :rtype: `requests.Response`

    :raises EnvironError: if error thrown in REST request or if response is bad
    """

    response = service_adaptor.send_request_to_service(method, url, SERVICE_NAME, json_data=json_data, retry=retry)
    return response


def get_pib_value_on_enm(enm_service_name, pib_parameter_name, service_identifier=None, enm_service_locations=None):
    """
    Read PIB Value on ENM via Deployment Info Manager Service

    :param pib_parameter_name: Name of PIB Parameter
    :type pib_parameter_name: str
    :param enm_service_name: Name of enm service to get pib parameter value from.
    :type enm_service_name: str
    :param enm_service_locations: Locations of enm service (e.g. hostnames or IP's)
    :type enm_service_locations: list
    :return: Value of PIB parameter
    :param service_identifier: Identify a service
    :type service_identifier: str
    :rtype: str
    """

    if can_service_be_used():
        return read_pib_value(enm_service_name, pib_parameter_name, service_identifier)
    else:
        return enm_deployment.get_pib_value_on_enm(enm_service_name, pib_parameter_name, service_identifier,
                                                   enm_service_locations)


def read_pib_value(enm_service_name, pib_parameter_name, service_identifier=None):
    """
    Read Value of PIB parameter using Deployment Manager service

    :param enm_service_name: ENM service
    :type enm_service_name: str
    :param pib_parameter_name: PIB parameter name
    :type pib_parameter_name: str
    :param service_identifier: Service Identifier
    :type service_identifier: str

    :return: Value of PIB parameter
    :rtype: str
    """
    log.logger.debug("Reading value of PIB parameter from the {0} service".format(SERVICE_NAME))
    json_data = {"enm_service_name": enm_service_name, "pib_parameter_name": pib_parameter_name}
    if service_identifier:
        json_data.update({"service_identifier": service_identifier})
    pib_value = service_adaptor.validate_response(
        send_request_to_service(POST_METHOD, READ_PIB_URL, json_data=json_data, retry=False)).encode('utf-8')

    log.logger.debug("PIB value: {0}".format(pib_value))
    return pib_value


def update_pib_parameter_on_enm(enm_service_name, pib_parameter_name, pib_parameter_value,
                                enm_service_locations=None, service_identifier=None, scope=None):
    """
    Update PIB parameter on ENM

    :param enm_service_name: Name of ENM service
    :type enm_service_name: str
    :param pib_parameter_name: Name of PIB Parameter
    :type pib_parameter_name: str
    :param pib_parameter_value: Value of PIB Paramater
    :type pib_parameter_value: str
    :param enm_service_locations: List of ENM service locations (hostnames or IP addresses)
    :type enm_service_locations: list
    :param service_identifier: Service Identifier
    :type service_identifier: str
    :param scope: Scope
    :type scope: str

    :return: Boolean to indicate that value was set
    :rtype: bool

    :raises EnmApplicationError: if could not set PIB value on ENM
    """
    if can_service_be_used():
        return update_pib_value(enm_service_name, pib_parameter_name, pib_parameter_value, service_identifier, scope)
    else:
        return enm_deployment.update_pib_parameter_on_enm(enm_service_name, pib_parameter_name, pib_parameter_value,
                                                          enm_service_locations, service_identifier, scope)


def update_pib_value(enm_service_name, pib_parameter_name, pib_parameter_value, service_identifier=None, scope=None):
    """
    Update Value of PIB parameter using Deployment Info Manager service

    :param enm_service_name: ENM service
    :type enm_service_name: str
    :param pib_parameter_name: PIB parameter name
    :type pib_parameter_name: str
    :param pib_parameter_value: PIB parameter value
    :type pib_parameter_value: str
    :param service_identifier: Service Identifier
    :type service_identifier: str
    :param scope: Scope of PIB Parameter
    :type scope: str

    """
    log.logger.debug("Updating value of PIB parameter via the {0} service".format(SERVICE_NAME))
    json_data = {"enm_service_name": enm_service_name, "pib_parameter_name": pib_parameter_name,
                 "pib_parameter_value": pib_parameter_value}
    if service_identifier:
        json_data.update({"service_identifier": service_identifier})
    if scope:
        json_data.update({"scope": scope})
    service_adaptor.validate_response(
        send_request_to_service(POST_METHOD, UPDATE_PIB_URL, json_data=json_data, retry=False))

    log.logger.debug("PIB value updated")


def get_apache_url():
    """
    Request the Apache URL value from the service

    :return: The apache url value if available
    :rtype: str
    """
    log.logger.debug("Retrieving the apache_url value via the {0} service".format(SERVICE_NAME))
    response = service_adaptor.validate_response(send_request_to_service(GET_METHOD, APACHE_URL, retry=False))
    apache_url = response.get('apache_url').encode('utf-8')
    log.logger.debug("Apache URL value: {0}".format(apache_url))
    return apache_url


def get_deployment_service_info(service_name):
    """
    Request the available deployment information for the supplied service identifier

    :param service_name: Name of the service or value available in the global properties
    :type service_name: str

    :return: Available value if any
    :rtype: Any
    """
    log.logger.debug("Retrieving the available deployment info value for: [{0}] from the {1} service".format(
        service_name, SERVICE_NAME))
    json_data = {"enm_value": service_name}
    response = service_adaptor.validate_response(send_request_to_service(POST_METHOD, SERVICE_INFO_URL,
                                                                         json_data=json_data, retry=False))
    service_info = response.get('service_info')
    log.logger.debug("Deployment information value: {0}".format(service_info))
    return service_info


def copy_cloud_user_key_to_emp():
    """
    Request the available cloud user key be copied to the respective EMP host if available.
    """
    log.logger.debug("Attempting to copy cloud user key from workloadVM to EMP host.")
    service_adaptor.print_service_operation_message(send_request_to_service(GET_METHOD, COPY_EMP_KEY_URL, retry=False),
                                                    log.logger)


def poid_refresh():
    """
    Perform POID Refresh in service

    :returns: POID data
    :rtype: dict
    """
    log.logger.debug("Performing POID fetch")
    poid_data = service_adaptor.validate_response(send_request_to_service(GET_METHOD, POID_REFRESH))
    log.logger.debug("POID fetch complete")
    return poid_data


def lms_password_less_access(username=None, password=None, ms_host=None):
    """
    Attempt to configure password less access to the LMS
    """
    json_data = {'username': username, 'ms_host': ms_host, 'password': password}
    if password:
        json_data['password'] = base64.encodestring(password)
    log.logger.debug("Attempting LMS password less access configuration.")
    service_adaptor.print_service_operation_message(send_request_to_service(POST_METHOD, LMS_PASS_URL,
                                                                            json_data=json_data, retry=False),
                                                    log.logger)


def get_eniq_ip_list_check_if_eniq_server():
    """
    Check if the host that the service is running on is included in ENIQ list

    :return: Tuple bool indicating host service is running is list and list of eniq ips
    :rtype: tuple
    """
    log.logger.debug("Checking service host machine is included in ENIQ list {0} service".format(SERVICE_NAME))
    response = service_adaptor.validate_response(send_request_to_service(GET_METHOD, ENIQ_URL, retry=False))
    included_in_eniq_list, eniq_ip_list = response.get('eniq_server'), response.get('eniq_ip_list')
    log.logger.debug("ENIQ list: {0}, service host included in list: [{1}]".format(eniq_ip_list, included_in_eniq_list))
    return included_in_eniq_list, eniq_ip_list


def check_enm_access():
    """
    Check if workload VM has access to ENM deployment
    :return: enm_access and log_info to show if enm is accessible and log information
    :rtype: tuple (bool, str)
    """
    if can_service_be_used():
        response = service_adaptor.validate_response(send_request_to_service(GET_METHOD, CHECK_ENM_ACCESS_URL,
                                                                             retry=False))
        return response.get('enm_access'), response.get('log_info')


def check_password_ageing_policy_status():
    """
    Checks if the ENM Password Ageing Policy is currently enabled
    :return: message
    :rtype: str
    """
    if can_service_be_used():
        return service_adaptor.validate_response(send_request_to_service(
            GET_METHOD, CHECK_PASS_AGEING_URL, retry=False))


def check_deployment_config():
    """
    Request the deployment type from the service
    :return: type of the network
    :rtype: str
    """
    if can_service_be_used():
        return service_adaptor.validate_response(send_request_to_service(
            GET_METHOD, DEPLOYMENT_TYPE_URL, retry=False))
    else:
        deployment_type = helper.get_network_config()
        return deployment_type.replace("_k_", "_")


def get_list_of_scripting_service_ips():
    """
    Get the list of SCP services

    :return: List of scripting cluster ips
    :rtype: list
    """
    if can_service_be_used():
        json_data = {"enm_value": "scripting_service_IPs"}
        return service_adaptor.validate_response(send_request_to_service(
            POST_METHOD, SERVICE_INFO_URL, json_data=json_data, retry=False)).get("service_info")
    else:
        log.logger.debug("Using legacy architecture for fetching list of scripting service IP's!")
        return enm_deployment.get_list_of_scripting_service_ips()
