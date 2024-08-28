import base64
import commands
import json

import pexpect
from flask import Blueprint, request

from enmutils.lib import cache, filesystem, log, mutexer, shell
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.shell import Command
from enmutils_int.lib.enm_deployment import get_pib_value_on_enm, update_pib_parameter_on_enm
from enmutils_int.lib.services import deployment_info_helper_methods as helper
from enmutils_int.lib.services.deployment_info_helper_methods import (check_if_password_ageing_enabled,
                                                                      get_cloud_native_service_vip)
from enmutils_int.lib.services.service_common_utils import (create_and_start_background_scheduled_job,
                                                            get_json_response, abort_with_message,
                                                            create_and_start_once_off_background_scheduled_job)
from enmutils_int.lib.services.service_values import URL_PREFIX

SERVICE_NAME = "deploymentinfomanager"

application_blueprint = Blueprint(SERVICE_NAME, __name__, url_prefix=URL_PREFIX)

ENM_IP_DICT_MUTEX_KEY = "mutex-enm-ip-value-key"
ENM_IP_DICT = {}
# OS Keys
LMS_HOST_KEY = "LMS_HOST"
EMP_HOST_KEY = "EMP"
ENM_URL_KEY = "ENM_URL"

CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP = '/ericsson/enm/dumps/.cloud_user_keypair.pem'
CLOUD_TEMP_KEY = "/tmp/.enm_keypair.pem"
CLOUD_KEY_COPY_CMD = "scp -i {0} -o stricthostkeychecking=no {0} cloud-user@{1}:{2}"
CLOUD_KEY_MOVE_CMD = "ssh -i {0} -o stricthostkeychecking=no cloud-user@{1} 'sudo mv {2} {3}'"

GLOBAL_PROPERTIES = "/ericsson/tor/data/global.properties"
UI_PRES_SERVER = "egrep UI_PRES_SERVER {global_properties}".format(global_properties=GLOBAL_PROPERTIES)
PHYSICAL_HA_PROXY_CMD = "ssh -q -o StrictHostKeyChecking=no {lms_host} {ui_pres_server}"
VENM_HA_PROXY_CMD = "ssh -i /var/tmp/enm_keypair.pem -o StrictHostKeyChecking=no cloud-user@{emp_host} {ui_pres_server}"
KUBECTL_PATH = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config"
CLOUD_NATIVE_POD_CMD = "{0} get pods".format(KUBECTL_PATH)
CLOUD_NATIVE_NAME_SPACE_CMD = "{0} get ingress --all-namespaces 2>/dev/null | egrep uiserv".format(KUBECTL_PATH)
SCHEDULER_INTERVAL_MINS = 60
JOB, JOB1, JOB2 = None, None, None

DIT_URL = "https://atvdit.athtem.eei.ericsson.se"
WLVM_SETUP_CONF_URL = ("https://eteamspace.internal.ericsson.com/display/ERSD/Setting"
                       "+up+a+Workload+VM+server")


def at_startup():
    """
    Start up function to be executed when service is created
    """
    log.logger.debug("Running startup functions")
    global JOB, JOB1

    funcs = [get_os_environ_keys, get_haproxy_host, parse_global_properties,
             get_cloud_native_namespace, fetch_and_parse_cloud_native_pods, fetch_and_update_emp_key_if_no_longer_valid,
             copy_enm_keypair_to_emp, get_general_scripting_ips_for_cloud_native]

    for func in funcs:
        try:
            log.logger.debug("# Starting function: {0}".format(str(func.func_name)))
            func()
            log.logger.debug("# Function complete: {0}".format(str(func.func_name)))
        except Exception as e:
            log.logger.debug("Failed to execute {0}, exception_encountered: [{1}]".format(func.func_name, str(e)))

    if not JOB:
        JOB = create_and_start_background_scheduled_job(at_startup, SCHEDULER_INTERVAL_MINS,
                                                        "{0}_HOURLY".format(SERVICE_NAME), log.logger)
    if not JOB1:
        create_and_start_once_off_background_scheduled_job(helper.fetch_and_parse_nss_mo_files,
                                                           "{0}_ONCE_OFF".format(SERVICE_NAME), log.logger)
        JOB1 = create_and_start_background_scheduled_job(helper.fetch_and_parse_nss_mo_files, SCHEDULER_INTERVAL_MINS * 6,
                                                         "{0}_QUARTERLY".format(SERVICE_NAME), log.logger)
    log.logger.debug("Startup complete")


def get_apache_url():
    """
    Route to GET to ENM apache url

    GET /deployment/apache

    :raises HTTPException: 500 raised if GET request fails
    :raises RuntimeError: if there is no hostname for Apache

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        hostname = get_haproxy_host()
        if not hostname:
            raise RuntimeError("Could not get hostname for Apache, please check logs for more information.")
        return get_json_response(message={'apache_url': 'https://{0}'.format(hostname)})
    except Exception as e:
        abort_with_message(
            "Failed to retrieve ENM Apache URL.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def get_deployment_info():
    """
    Route to POST to query for deployment information

    POST /deployment/info

    :raises HTTPException: 404 raised if No matching information

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    request_data = request.get_json()

    service_name = request_data.get('enm_value')
    deployment_info = ENM_IP_DICT.get(service_name)
    if deployment_info:
        return get_json_response(message={'service_info': deployment_info})
    else:
        abort_with_message("No available information for: [{0}], please ensure the deployment information requested is "
                           "correct.".format(service_name), log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR,
                           http_status_code=404)


def copy_emp_key():
    """
    Route to GET to ENM keypair added to the EMP

    GET /deployment/copy_emp

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        copied = copy_enm_keypair_to_emp()
        return get_json_response(
            message="Successfully copied ENM key pair to EMP." if copied else "Not a vENM deployment nothing to copy.")
    except Exception as e:
        abort_with_message(
            "Failed to copy ENM key pair to EMP.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def get_haproxy_host():
    """
    Builds the base FQDN Apache URL

    :returns: hostname for "haproxy"
    :rtype: str
    """
    if not ENM_IP_DICT.get('haproxy'):
        with mutexer.mutex(ENM_IP_DICT_MUTEX_KEY, persisted=True):
            determine_ha_proxy()
    return ENM_IP_DICT.get('haproxy')


def determine_ha_proxy():
    """
    Determine where hostname value will be based upon flags set on the workloadVM
    """
    if ENM_IP_DICT.get(LMS_HOST_KEY):
        get_ha_proxy_value_physical_or_venm()
    elif ENM_IP_DICT.get(EMP_HOST_KEY):
        get_ha_proxy_value_physical_or_venm(venm=True)
    elif ENM_IP_DICT.get(ENM_URL_KEY):
        get_ha_proxy_value_cloud_native()
    elif helper.is_deployment_vapp():
        get_ha_proxy_vapp()
    else:
        log.logger.debug("Could not detect OS environ variables to identify deployment type.")


def get_ha_proxy_value_physical_or_venm(venm=False):
    """
    Query LMS for the Ha Proxy value
    """
    log_msg = ("LMS Host set in OS environ, querying LMS for HA Proxy value." if not venm else
               "EMP Host set in OS environ, querying EMP for UI PRES SERVER value.")
    log.logger.debug(log_msg)
    global ENM_IP_DICT
    cmd = (PHYSICAL_HA_PROXY_CMD.format(lms_host=ENM_IP_DICT.get(LMS_HOST_KEY), ui_pres_server=UI_PRES_SERVER) if
           not venm else VENM_HA_PROXY_CMD.format(emp_host=ENM_IP_DICT.get(EMP_HOST_KEY),
                                                  ui_pres_server=UI_PRES_SERVER))
    rc, output = commands.getstatusoutput(cmd)
    if not rc:
        hostname = output.split("=")[-1]
        ENM_IP_DICT['haproxy'] = hostname
        log.logger.debug("Setting ENM hostname value to: [{0}]".format(hostname))
    else:
        log.logger.debug("Could not retrieve {1}, response: [{0}]".format(
            output, "LMS HA PROXY" if not venm else "EMP UI PRES SERVER"))


def get_ha_proxy_value_cloud_native():
    """
    Query kubernetes for UI serv address
    """
    log.logger.debug("ENM URL Host set in OS environ, querying ingress for UISERV value.")
    global ENM_IP_DICT
    rc, output = helper.get_uiserv_address()
    ui_serv = output
    if not rc and ENM_IP_DICT.get(ENM_URL_KEY) and ENM_IP_DICT.get(ENM_URL_KEY) in ui_serv:
        log.logger.debug("Setting ENM hostname value to: [{0}]".format(ui_serv))
        ENM_IP_DICT['haproxy'] = ui_serv
    else:
        log.logger.debug("Could not retrieve or mismatch between ENV variable, ENM URL {1} and Cloud Native UISERV "
                         "address detected: [{0}]".format(output, ENM_IP_DICT.get(ENM_URL_KEY)))


def get_ha_proxy_vapp():
    """
    Query global properties for UI PRES SERVER
    """
    log.logger.debug("Vapp hostname detected, querying for ha proxy.")
    global ENM_IP_DICT
    rc, output = commands.getstatusoutput(UI_PRES_SERVER)
    if not rc:
        hostname = output.split("=")[-1]
        ENM_IP_DICT['haproxy'] = hostname
        log.logger.debug("Setting vApp hostname value to: [{0}]".format(hostname))
    else:
        log.logger.debug("Could not retrieve {1}, response: [{0}]".format(output, "vApp HA PROXY"))


def get_os_environ_keys():
    """
    Check for matching ENV keys and add to dict if found
    """
    log.logger.debug("Checking for OS environment variables.")
    global ENM_IP_DICT
    for key in [LMS_HOST_KEY, EMP_HOST_KEY, ENM_URL_KEY]:
        cmd = "source ~/.bashrc; echo ${0}"
        rc, output = commands.getstatusoutput(cmd.format(key))
        if not rc and output:
            log.logger.debug("Bashrc file value:: [{0}] found for key:: [{1}]".format(output.strip(), key))
            ENM_IP_DICT[key] = output.strip()
    log.logger.debug("Completed checking for OS environment variables.")


def parse_global_properties():
    """
    Fetch, parse and add available global property values to the service dictionary
    """
    properties = get_lines_from_global_properties()
    if properties:
        for enm_property in properties:
            split_property = enm_property.split('=', 1)
            key, value = split_property[0], split_property[-1]
            if key and value and value != '""' and ENM_IP_DICT.get(key) != value.split(','):
                value = value.split(',')
                log.logger.debug("Adding Key: [{0}] with value: {1} to service dictionary.".format(key, value))
                ENM_IP_DICT[key] = value


def get_lines_from_global_properties():
    """
    Read in the lines of the global properties file

    :return: List containing the lines from the global properties file
    :rtype: list
    """
    properties = []
    if helper.is_deployment_vapp():
        properties = filesystem.get_lines_from_file(GLOBAL_PROPERTIES)
    elif ENM_IP_DICT.get(LMS_HOST_KEY) or ENM_IP_DICT.get(EMP_HOST_KEY):
        host = ENM_IP_DICT.get(LMS_HOST_KEY) or ENM_IP_DICT.get(EMP_HOST_KEY)
        user = "root" if ENM_IP_DICT.get(LMS_HOST_KEY) else "cloud-user"
        properties = filesystem.get_lines_from_remote_file(GLOBAL_PROPERTIES, host, user)
    return properties


def is_deployment_cloud_native():
    """
    Determine if we are running on a Cloud Native deployment

    :returns: Boolean if Cloud Native deployment detected
    :rtype: bool
    """
    log.logger.debug("Checking if deployment is Cloud Native deployment.")
    enm_namespace = None
    enm_url = get_haproxy_host()
    rc, stdout = commands.getstatusoutput(CLOUD_NATIVE_NAME_SPACE_CMD)
    if not rc and stdout and enm_url in stdout:
        enm_namespace = stdout.split()[0]
    return bool(enm_namespace)


def fetch_and_parse_cloud_native_pods():
    """
    Query KUBECTL for the list of PODs
    """
    if is_deployment_cloud_native():
        cmd = (CLOUD_NATIVE_POD_CMD if not ENM_IP_DICT.get("cloud_native_namespace") else
               "{0} -n {1}".format(CLOUD_NATIVE_POD_CMD, ENM_IP_DICT.get('cloud_native_namespace')))
        rc, output = commands.getstatusoutput(cmd)
        if not rc:
            pods = [_.split()[0] for _ in output.split("\n")[1:] if _.split()]
            if pods:
                ENM_IP_DICT['cloud_native_pods'] = pods
        else:
            log.logger.debug("Failed to retrieve POD values with command: [{0}], output returned: [{1}]."
                             "".format(cmd, output))


def get_cloud_native_namespace():
    """
    Query KUBECTL for the namespace based upon the uiserv value
    """
    if is_deployment_cloud_native():
        rc, output = commands.getstatusoutput(CLOUD_NATIVE_NAME_SPACE_CMD)
        namespace = output.split()[0] if output.split() else ""
        if not rc and namespace:
            ENM_IP_DICT["cloud_native_namespace"] = namespace
        else:
            log.logger.debug("Failed to retrieve Cloud Native namespace value with command: [{0}], output returned: "
                             "[{1}].".format(CLOUD_NATIVE_NAME_SPACE_CMD, output))


def read_pib():
    """
    Route to POST to read the value of PIB parameter on ENM

    POST /deployment/pib/read

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        enm_service_name = request_data.get('enm_service_name')
        pib_parameter_name = request_data.get('pib_parameter_name')
        service_identifier = request_data.get('service_identifier', None)

        pib_value = get_pib_value_on_enm(enm_service_name, pib_parameter_name, service_identifier)
        log.logger.debug("Successfully read PIB value for {0}: {1}".format(pib_parameter_name, pib_value))
        return get_json_response(message=pib_value)

    except Exception as e:
        abort_with_message("Failure occurred during attempt to read PIB value", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def copy_enm_keypair_to_emp():
    """
    Copy the deployment key to the EMP VM

    :raises EnvironError: raised if the key fails to copy or move to EMP

    :returns: Boolean indicating if the operation was a success
    :rtype: bool
    """
    log.logger.debug("Checking if cloud-user ssh private key needs to be copied to EMP.")
    if ENM_IP_DICT.get(EMP_HOST_KEY):
        error_msg = "Failed to {2} cloud-user key to using command: [{0}], command output: [{1}]"
        cmd = CLOUD_KEY_COPY_CMD.format(helper.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, ENM_IP_DICT.get(EMP_HOST_KEY),
                                        CLOUD_TEMP_KEY)
        rc, output = commands.getstatusoutput(cmd)
        if rc:
            raise EnvironError(error_msg.format(cmd, output, "copy"))
        cmd = CLOUD_KEY_MOVE_CMD.format(helper.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, ENM_IP_DICT.get(EMP_HOST_KEY),
                                        CLOUD_TEMP_KEY, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP)
        rc, output = commands.getstatusoutput(cmd)
        if rc:
            raise EnvironError(error_msg.format(cmd, output, "move"))
        log.logger.debug("Successfully copied ENM key pair to EMP.")
        return True


def update_pib():
    """
    Route to POST to update the value of PIB parameter on ENM

    POST /deployment/pib/update

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        enm_service_name = request_data.get('enm_service_name')
        pib_parameter_name = request_data.get('pib_parameter_name')
        pib_parameter_value = request_data.get('pib_parameter_value')
        service_identifier = request_data.get('service_identifier', None)
        scope = request_data.get('scope', None)

        update_pib_parameter_on_enm(enm_service_name, pib_parameter_name, pib_parameter_value,
                                    service_identifier=service_identifier, scope=scope)
        log.logger.debug("Successfully updated PIB value for {0}".format(pib_parameter_name))
        return get_json_response()

    except Exception as e:
        abort_with_message("Failure occurred during attempt to update PIB value", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def poid_refresh():
    """
    Route to fetch POID info from ENM.

    GET /deployment/poid_refresh

    :raises HTTPException: 500 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        log.logger.debug("Fetching POID from ENM")
        enm_poid_dict = helper.build_poid_dict_from_enm_data()
        return get_json_response(message=enm_poid_dict)

    except Exception as e:
        abort_with_message("Failure occurred while fetching POID info from ENM", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def fetch_and_update_emp_key_if_no_longer_valid():
    """
    Retrieve the latest ENM key from DIT if available and update if needed
    """
    deployment_name = get_cloud_deployment_name()
    if deployment_name and ENM_IP_DICT.get(EMP_HOST_KEY):
        log.logger.debug("Requesting ENM key for deployment: [{0}].".format(deployment_name))
        url_to_get_key_pair_file = (r"{dit_url}/api/deployments/?q=name={deployment_name}\&fields=enm\(private_key\)"
                                    .format(dit_url=DIT_URL, deployment_name=deployment_name))
        curl_command_to_get_key_pair_file = "curl -s {0}".format(url_to_get_key_pair_file)
        rc, output = commands.getstatusoutput(curl_command_to_get_key_pair_file)
        if not rc and "RSA PRIVATE KEY" in output:
            json_data = json.loads(output)
            update_existing_emp_key(json_data[0]["enm"]["private_key"].encode('utf-8'))
    else:
        log.logger.debug("Could not determine deployment name: [{0}] and EMP HOST value: [{1}].".format(
            deployment_name, ENM_IP_DICT.get(EMP_HOST_KEY)))


def get_cloud_deployment_name():
    """
    Determine the name of the deployment

    :return: Name of the deployment
    :rtype: str
    """
    deployment_name = None
    log.logger.debug("Fetching Cloud deployment name.")
    if ENM_IP_DICT.get(EMP_HOST_KEY) and ENM_IP_DICT.get('UI_PRES_SERVER'):
        deployment_name = ENM_IP_DICT.get('UI_PRES_SERVER')[0].split('-')[0]
    else:
        cmd = "source ~/.bashrc; echo $DEPLOYMENTNAME"
        rc, output = commands.getstatusoutput(cmd)
        if not rc and output:
            deployment_name = output.strip()
    return deployment_name


def update_existing_emp_key(emp_key):
    """
    Check if the EMP key is available or does not match the latest fetched key

    :param emp_key: Latest fetched key from DIT
    :type emp_key: str
    """
    if (not filesystem.does_file_exist(helper.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM) or
            ("".join([line for line in filesystem.get_lines_from_file(
                helper.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM)]) != emp_key.replace("\n", ""))):
        log.logger.debug("Updating Cloud deployment cloud user key value to latest.")
        command = 'echo "{0}" > {1}; chmod 600 {1}'.format(emp_key, helper.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM)
        rc, output = commands.getstatusoutput(command)
        if rc:
            log.logger.debug("Failed to correctly update enm key pair, command output: [{0}].".format(output))
        else:
            log.logger.debug("Successfully updated enm key pair.")
    else:
        log.logger.debug("Key not available or no update required.")


def setup_lms_password_less_access(username=None, password=None, ms_host=None):
    """
    Attempt to configure SSH PasswordLess access to the supplied MS Host

    :param username: User who will connect and add ssh key to the host
    :type username: str
    :param password: Password of the user who will connect and add ssh key to the host
    :type password: str
    :param ms_host: Name or IP of the host to connect to and add the key
    :type ms_host: str

    :raises EnvironError: raised if the commands fail or not values are available
    """
    user = username if username else "root"
    user_expect = '{0}@'.format(user)
    host = None
    try:
        host = ms_host if ms_host else ENM_IP_DICT.get(LMS_HOST_KEY)
        passwd = password if password else cache.get_workload_vm_credentials()[1]
        cmd = "ssh -o StrictHostKeyChecking=no {0}@{1}".format(user, host)
        copy_cmd = "ssh-copy-id {0}@{1}".format(user, host)
        with pexpect.spawn(cmd) as child:
            child.expect(user_expect)
            child.sendline(copy_cmd)
            child.expect('password:')
            child.sendline(passwd)
            child.expect(user_expect)
            log.logger.debug("Completed password less access commands.")
    except Exception as e:
        msg = "Failed to correctly create password less access to host: [{0}], error encountered: {1}.".format(
            host, str(e))
        log.logger.debug(msg)
        raise EnvironError(msg)


def lms_password_less_access():
    """
    Route to trigger password-less access setup on LMS host

    POST /deployment/lms/password

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        if helper.is_deployment_vapp():
            vapp_message = "Already on LMS - No need for password-less access"
            log.logger.debug(vapp_message)
            return get_json_response(message=vapp_message)
        request_data = request.get_json()
        username = request_data.get('username')
        password = request_data.get('password')
        if password:
            password = base64.decodestring(password.encode('utf-8'))
        ms_host = request_data.get('ms_host')
        log.logger.debug("Attempting to setup password less access.")
        setup_lms_password_less_access(username=username, password=password, ms_host=ms_host)
        return get_json_response(message="Password less actions complete, to confirm access created successfully, "
                                         "please connect to your host.")

    except Exception as e:
        abort_with_message("Failure occurred attempting to setup password less access.", log.logger,
                           SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def get_eniq():
    """
    Route to GET workloadVM in list of ENIQ servers

    GET /deployment/eniq

    :raises HTTPException: 500 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        is_eniq, eniq_list = helper.is_eniq_server(emp=ENM_IP_DICT.get(EMP_HOST_KEY), lms=ENM_IP_DICT.get(LMS_HOST_KEY))
        return get_json_response(message={'eniq_server': is_eniq, 'eniq_ip_list': eniq_list})
    except Exception as e:
        abort_with_message(
            "Failed to confirm if server is ENIQ server.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def password_ageing():
    """
    Route to check if ENM Password Ageing Policy is enabled

    GET /deployment/password/ageing

    :raises HTTPException: 500 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        log.logger.debug('Establishing if ENM Password Ageing Policy is enabled')
        log_info = check_if_password_ageing_enabled()
        return get_json_response(message=log_info)
    except Exception as e:
        abort_with_message("Failure occured when checking if ENM Password Ageing Policy is enabled", log.logger,
                           SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def deployment_config():
    """
    Route to get network config

    GET /deployment/config

    :return: config of the deployment
    :rtype: str
    """
    try:
        network_type = helper.get_network_config()
        return get_json_response(message=network_type.replace("_k_", "_"))
    except Exception as e:
        abort_with_message("Failure occured when checking deployment config", log.logger,
                           SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def enm_access():
    """
    Route to check if workload has access to ENM

    GET /deployment/enm/access

    :raises HTTPException: 500 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        log.logger.debug('Establishing if ENM is accessible to workload')
        enm_access_available, log_info = is_enm_accessible_to_workload()
        return get_json_response(message={'enm_access': enm_access_available, 'log_info': log_info})
    except Exception as e:
        abort_with_message("Failure occured when checking if ENM is accessible to workload", log.logger,
                           SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def is_enm_accessible_to_workload():
    """
    Checks type of deployment and execute command to ensure password-less access to ENM deployment
    @return: enm_access to show if enm is accessible and log information
    @rtype: tuple (bool, str)
    """
    log.logger.debug("Establishing if workload VM has access to ENM")
    if ENM_IP_DICT.get(LMS_HOST_KEY):
        message = "Establishing root ssh access to LMS"
        cmd = "/usr/bin/ssh -q $LMS_HOST hostname"
        label = "Physical"
    elif ENM_IP_DICT.get(EMP_HOST_KEY):
        message = "Establishing cloud-user access to EMP"
        cmd = "/usr/bin/ssh -i /var/tmp/enm_keypair.pem cloud-user@$EMP exit"
        label = "vENM"
    elif ENM_IP_DICT.get(ENM_URL_KEY):
        message = "Checking that cluster is running and accessible"
        cmd = "{0} cluster-info".format(KUBECTL_PATH)
        label = "cENM"
    elif helper.is_deployment_vapp():
        message = "Vapp detected - already on LMS"
        cmd = ""
        label = "vApp"
    else:
        message = ("Unable to determine ENM type to establish if workload has access to ENM. Please check "
                   "Workload VM setup page: {0}".format(WLVM_SETUP_CONF_URL))
        cmd = ""
        label = "Unknown"

    return run_cmd_on_different_deployment_types(message, cmd, label)


def run_cmd_on_different_deployment_types(message, cmd, label):
    """
    Runs local commands locally on different deployments
    @param message: Statement to log before executing the command
    @type message: str
    @param cmd: command to be executed on the deployment
    @type cmd: str
    @param label: type of deployment
    @type label: str
    @return: enm_access to show if enm is accessible and log information
    @rtype: tuple (bool, str)
    """
    log.logger.debug(message)
    if cmd:
        cmd = Command(cmd)
        response = shell.run_local_cmd(cmd)
        if not response.ok:
            wlvm_setup_reference = ("Please check Workload VM setup page: {0}".format(WLVM_SETUP_CONF_URL))
            return False, "Workload VM does not have access to {0}. {1}".format(label, wlvm_setup_reference)
        else:
            success_message = "Workload VM has access to {0}".format(label)
            log.logger.debug(success_message)
            return True, success_message
    else:
        if label == "vApp":
            return True, message
        else:
            return False, message


def get_general_scripting_ips_for_cloud_native():
    """
    Updates ENM_IP_DICT with scripting service ips for cloud native deployment, if namespace is detected
    """
    global ENM_IP_DICT
    if ENM_IP_DICT.get("cloud_native_namespace"):
        ENM_IP_DICT["scripting_service_IPs"] = [get_cloud_native_service_vip("general-scripting")]
