import ast
import time
import commands
import socket
import re
import datetime
import requests
from requests.auth import HTTPBasicAuth

from requests.exceptions import HTTPError

from enmutils.lib import log, mutexer, persistence, config
from enmutils.lib.shell import run_cmd_on_vm, run_cmd_on_ms, run_local_cmd, Command
from enmutils.lib.cache import (get_enm_cloud_native_namespace, is_host_physical_deployment, get_emp,
                                is_enm_on_cloud_native)
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnvironError
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib import (nss_mo_info, node_pool_mgr)
from enmutils_int.lib.nrm_default_configurations.robustness_60k import robustness_60k
from enmutils_int.lib.dit import get_documents_info_from_dit, get_document_content_from_dit

VAPP_KEY = "cloud-ms-1"
NODE_COUNT = 0

EXTRA_SMALL_NETWORK = "extra_small_network"
FIVE_K_NETWORK = "five_k_network"
FIFTEEN_K_NETWORK = "fifteen_k_network"
FORTY_K_NETWORK = "forty_k_network"
SIXTY_K_NETWORK = "sixty_k_network"
EIGHTY_K_NETWORK = "eighty_k_network"
ONE_HUNDRED_K_NETWORK = "one_hundred_k_network"
SOEM_5K_NETWORK = "soem_five_k_network"
TRANSPORT_20K_NETWORK = "transport_twenty_k_network"
TRANSPORT_10K_NETWORK = "transport_ten_k_network"

NE_TYPES = {"RAN": ["5GRadioNode", "MSRBS_V1", "RadioNode", "ERBS", "RBS", "RNC", "BSC"],
            "TRANSPORT": ["Router6274", "Router6672", "Router6675", "SIU02", "CISCO-ASR900", "CISCO-ASR9000",
                          "FRONTHAUL-6020", "FRONTHAUL-6080", "JUNIPER-MX", "JUNIPER-PTX", "JUNIPER-SRX",
                          "JUNIPER-vMX", "JUNIPER-vSRX", "MINI-LINK-6351", "MINI-LINK-6352", "MINI-LINK-6366",
                          "MINI-LINK-665x", "MINI-LINK-669x", "MINI-LINK-CN210", "MINI-LINK-CN510R1",
                          "MINI-LINK-CN510R2", "MINI-LINK-CN810R1", "MINI-LINK-CN810R2", "MINI-LINK-Indoor",
                          "MINI-LINK-PT2020", "TCU02", "Switch-6391", "ESC", "SCU"]}

NETWORK_CELL_COUNT = 'network-cell-count'
NETWORK_TYPE = 'network-type'
NETWORK_KEY_TTL = 21600
NETEX_ENDPOINT = '/managedObjects/query?searchQuery=select%20NetworkElement'
KUBECTL_PATH = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config"

ROBUSTNESS_MAPPING = {SIXTY_K_NETWORK: robustness_60k.get('robustness_60k'),
                      FORTY_K_NETWORK: robustness_60k.get('robustness_60k'), FIFTEEN_K_NETWORK: {},
                      FIVE_K_NETWORK: {}, EXTRA_SMALL_NETWORK: {}, SOEM_5K_NETWORK: {}, TRANSPORT_10K_NETWORK: {},
                      TRANSPORT_20K_NETWORK: {}}

CLOUD_SSH_EXEC_CMD = "ssh -q -i {0} -o UserKnownHostsFile=/dev/null -o stricthostkeychecking=no cloud-user@{1} '{2}'"
PHYSICAL_SSH_EXEC_CMD = "ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0} '{1}'"
CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM = '/var/tmp/enm_keypair.pem'
PROXIES = {"http": None, "https": None}
DDP_HEADERS = {'content-type': 'text/html; charset=UTF-8'}
BASE_URL = "https://{0}.athtem.eei.ericsson.se/php/TOR/system/ne_details.php?site="
END_URL = "LMI_{0}&dir={1}&date={2}&oss=tor"
GET_DDP_AND_DEPLOYMENT_NAME_USING_DDC_UPLOAD = "cat /var/ericsson/ddc_data/config/ddc_upload"
GET_DDP_AND_DEPLOYMENT_NAME_USING_CRONTAB = "crontab -l"


def get_network_element_primary_types():
    """
    Query ENM for the list of created NetworkElement neTypes

    :raises ScriptEngineResponseValidationError: raised if the enm query fails or no NetworkElement exist

    :returns: List of found NetworkElement neTypes
    :rtype: list
    """
    user = get_workload_admin_user()
    response = user.enm_execute("cmedit get * NetworkElement.neType")
    output = response.get_output()
    if "Error" in output or output[-1].encode('utf-8').startswith("0 instance(s)"):
        raise ScriptEngineResponseValidationError("Failed to retrieve NetworkElement primary types or NetworkElements"
                                                  " not found.", response=response)
    return [line.split(':')[-1].strip().encode('utf-8') for line in output if "neType" in line]


def sort_and_count_ne_types():
    """
    Sort the NetworkElement neTypes by type and count

    :returns: Dictionary of the sorted and counted NetworkElement neTypes
    :rtype: dict
    """
    ne_types = {}
    enm_ne_types = get_network_element_primary_types()
    for ne_type in enm_ne_types:
        if ne_type not in ne_types.keys():
            ne_types[ne_type] = 0
        ne_types[ne_type] += 1
    return ne_types


def detect_transport_network_and_set_transport_size():
    """
    Determine if the NetworkElement neTypes indicate a Transport network

    :return: Transport key if applicable or None
    :rtype: str
    """
    try:
        ne_type_dict = sort_and_count_ne_types()
    except Exception as e:
        log.logger.info("Could not determine network type, error encountered:: [{0}].Load will be applied based upon "
                        "the network cell count.".format(str(e)))
        return
    if set(ne_type_dict.keys()).intersection(NE_TYPES.get("RAN")):
        log.logger.info("RAN NetworkElement(s) found, load will be applied based upon the network cell count.")
    elif set(ne_type_dict.keys()).intersection(NE_TYPES.get("TRANSPORT")):
        log.logger.info("Transport NetworkElement(s) found, determining transport configuration to be used.")
        return determine_size_of_transport_network(ne_type_dict)
    else:
        log.logger.info("Could not determine network type, load will be applied based upon the network cell count.")


def determine_size_of_transport_network(ne_type_dict):
    """
    Count the total transport NetworkElement neTypes and select the applicable transport configuration

    :return: The respective Transport network key
    :rtype: str
    """
    total_transport_nodes = 0
    for key, value in ne_type_dict.items():
        if key in NE_TYPES.get("TRANSPORT"):
            total_transport_nodes += value
    log.logger.debug("Total transport count\t{0}.".format(total_transport_nodes))
    transport_flag = SOEM_5K_NETWORK if total_transport_nodes <= 5000 else (TRANSPORT_10K_NETWORK if
                                                                            total_transport_nodes <= 10000 else
                                                                            TRANSPORT_20K_NETWORK)
    return transport_flag


def get_total_cell_count():
    """
    Returns the total number of cell instances as available on ENM via cm cli application

    :rtype: int
    :return: Total number of cell instances
    """
    retry_count = 3
    with mutexer.mutex('cell-count-mutex', persisted=True):
        total = persistence.get(NETWORK_CELL_COUNT)
        if total or total == 0:
            return int(total)
        else:
            total = get_cell_count_from_cmedit(retry_count)
            if not total and not detect_transport_network_and_set_transport_size():
                log.logger.debug("Retrieving cell count from DDP")
                total = get_ddp_total_cell_count()
                persistence.set(NETWORK_CELL_COUNT, total, NETWORK_KEY_TTL, log_values=False)
                log.logger.debug("Total cell count discovered: [{0}]".format(total))
                if not total:
                    log.logger.debug(
                        "Cell count couldn't be retrieved from DDP even after {0} retries".format(retry_count))
                    log.logger.debug("Total cell count discovered: [{0}]".format(total))

    return int(total) if total else 0


def get_cell_count_from_cmedit(retry_count):
    """
    Returns the total number of cell instances as available on ENM via cm cli application

    :rtype: int
    :return: Total number of cell instances
    """
    total = None
    user = get_workload_admin_user()
    cmd = 'cmedit get * EUtranCellFDD;EUtranCellTDD;UtranCell;GeranCell;NRCellCU -cn'
    for _ in range(retry_count):
        response = user.enm_execute(cmd, timeout_seconds=1200)
        if response:
            output = response.get_output()
            if output and str(output[-1]).split(' ')[0].isdigit():
                total = int(str(response.get_output()[-1]).split(' ')[0])
                persistence.set(NETWORK_CELL_COUNT, total, NETWORK_KEY_TTL, log_values=False)
                break
            else:
                log.logger.debug("Unexpected response during cell count retrieval - {0}.. Retrying after 10 seconds!".format(output))
                time.sleep(10)
        else:
            log.logger.debug("No response during cell count retrieval.. Retrying after 10 seconds!")
            time.sleep(10)
    else:
        log.logger.info("Cell count couldn't be retrieved even after {0} retries".format(retry_count))
        log.logger.info("Total cell count discovered: [{0}]".format(total))

    return total


def get_ddp_total_cell_count():
    """
    Returns the total number of cell instances as available on DDP

    :rtype: int
    :return: Total number of cell instances
    """
    total = []
    max_cell_count_value = 0
    ddp_hostname, deployment_hostname = get_ddp_and_deployment_hostname()
    if ddp_hostname and deployment_hostname:
        previous_dates, dir_nums = get_historic_date_and_directory_of_ddp()
        for previous_date in previous_dates:
            for dir_num in dir_nums:
                url = BASE_URL.format(ddp_hostname) + END_URL.format(deployment_hostname, dir_num, previous_date)
                cell_count = execute_ddp_url_and_fetch_cell_count(url)
                total.append(cell_count)
                dir_nums.remove(dir_num)
        max_cell_count_value = max(total)
        log.logger.debug("The max cell count value : {0} ".format(max_cell_count_value))
    else:
        log.logger.debug("Total cell count can't be retrieved as this deployment doesn't possess a DDP hostname or "
                         "deployment hostname")
    return max_cell_count_value


def get_ddp_and_deployment_hostname():
    """
    Check the deployment type and return deployment hostname and ddp hostname

    :rtype: string
    :return: deployment hostname and ddp hostname
    """
    ddp_hostname, deployment_hostname = None, None
    try:
        if is_enm_on_cloud_native():
            ddp_hostname, deployment_hostname = get_hostname_in_cloud_native()
        elif config.is_a_cloud_deployment():
            ddp_hostname, deployment_hostname = get_hostname_cloud_deployment()
        elif is_host_physical_deployment():
            ddp_hostname, deployment_hostname = get_hostname_physical_deployment()
    except Exception as e:
        log.logger.debug("Error Encountered - {0}".format(e))

    return ddp_hostname, deployment_hostname


def get_hostname_physical_deployment():
    """
    Check in physical environment and return deployment hostname and ddp hostname

    :rtype: string
    :return: deployment hostname and ddp hostname
    :raises EnvironError: if the output is not ok
    """
    response = run_cmd_on_ms(GET_DDP_AND_DEPLOYMENT_NAME_USING_DDC_UPLOAD)
    if "No such file or directory" in response.stdout:
        response = run_cmd_on_ms(GET_DDP_AND_DEPLOYMENT_NAME_USING_CRONTAB)
        if "no crontab" in response.stdout:
            raise EnvironError("Could not able to get hostname. Check DDP configuration/ddc_upload on the server.")
    ddp_hostname = response.stdout.split("-d")[1].split()[0]
    deployment_hostname = response.stdout.split("-s")[1].split()[0]
    return ddp_hostname, deployment_hostname


def get_hostname_cloud_deployment():
    """
    Check in cloud environment and return deployment hostname and ddp hostname

    :rtype: string
    :return: deployment hostname and ddp hostname
    :raises EnvironError: if the output is not ok
    """
    response = run_cmd_on_vm(GET_DDP_AND_DEPLOYMENT_NAME_USING_DDC_UPLOAD, vm_host=get_emp())
    if "No such file or directory" in response.stdout:
        response = run_cmd_on_vm(GET_DDP_AND_DEPLOYMENT_NAME_USING_CRONTAB, vm_host=get_emp())
        if "no crontab" in response.stdout:
            raise EnvironError("Could not able to get hostname. Check DDP configuration/ddc_upload on the server.")
    ddp_hostname = response.stdout.split("-d")[1].split()[0]
    deployment_hostname = response.stdout.split("-s")[1].split()[0]

    return ddp_hostname, deployment_hostname


def get_hostname_in_cloud_native():
    """
    Check in cloud native environment and return deployment hostname and ddp hostname

    :rtype: string
    :return: deployment hostname and ddp hostname
    :raises EnvironError: if the output is not ok
    """
    cmd = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress --all-namespaces 2>/dev/null | egrep ui"
    response = run_local_cmd(Command(cmd))
    if not response.stdout:
        raise EnvironError("Could not able to get hostname. Check Kubernetes configuration on the server.")
    deployment_name = response.stdout.split()[3].split(".")[0]
    document_info_dict = get_documents_info_from_dit(deployment_name)
    ddp_document_number = document_info_dict.get("cENM_site_information")
    deployment_doc_number = document_info_dict.get("cENM_integration_values")
    document_content = get_document_content_from_dit(ddp_document_number)
    deployment_document_content = get_document_content_from_dit(deployment_doc_number)
    ddp_hostname = document_content.get("global").get("ddp_hostname")
    deployment_hostname = deployment_document_content.get("eric-enm-ddc").get("eric-oss-ddc").get("autoUpload").get("ddpid").replace('lmi_', '')

    return ddp_hostname, deployment_hostname


def get_historic_date_and_directory_of_ddp():
    """
    Get three previous date and directory number

    :rtype: int
    :return: date and directory number
    """
    historic_date, directory_num = [], []
    days = [13, 14, 15]
    for day in days:
        previous_date = str(datetime.datetime.today() - datetime.timedelta(days=day)).split()[0]
        historic_date.append(previous_date)
        dir_num = (datetime.datetime.today() - datetime.timedelta(days=day)).strftime('%d%m%y')
        directory_num.append(dir_num)

    return historic_date, directory_num


def execute_ddp_url_and_fetch_cell_count(url):
    """
    Execute the DDP url and fetch the cell instances from DDP and raise environ error if did not get correct output.

    :rtype: int
    :return: Total number of cell instances
    :raises EnvironError: if the output is not ok
    """
    log.logger.debug("Calling rest call to get cell count from DDP")
    response = requests.get(url, proxies=PROXIES, verify=False, auth=HTTPBasicAuth("aptuser", r"]~pR:'Aw6cwpJR4dDY$k85\t"),
                            headers=DDP_HEADERS)
    output = response.text.encode('utf-8')
    code_output = re.search('cellcounts_tableParam', output)
    if not code_output:
        raise EnvironError('Could not retrieve the cells_count_value from DDP, Check DDP page once.')
    cell_count_value = output.split("cellcounts_tableParam =")[1].split('"downloadURL"')[0].split('"data": [')[1].split('],')[-2].split("\n")[-3].split(":")[-1]
    total = int(cell_count_value.decode('utf-8'))

    return total


def is_transport_network():
    """
    Check if network is transport only

    :return: Boolean indicating if the network is a Transport only network
    :rtype: bool
    """
    return get_network_config() in [SOEM_5K_NETWORK, TRANSPORT_10K_NETWORK, TRANSPORT_20K_NETWORK]


def get_network_config():
    """
    Determine which configuration file will be used

    :return: The configuration which will be selected based upon the underlying network
    :rtype: str
    """
    network_key = persistence.get(NETWORK_TYPE)
    if not network_key:
        network_key = detect_transport_network_and_set_transport_size()
        if not network_key:
            total_cell_count = get_total_cell_count()
            if not total_cell_count:
                network_key = FORTY_K_NETWORK
            elif total_cell_count < 1000:
                network_key = EXTRA_SMALL_NETWORK
            elif total_cell_count <= 7500:
                network_key = FIVE_K_NETWORK
            elif total_cell_count < 27500:
                network_key = FIFTEEN_K_NETWORK
            elif total_cell_count <= 50000:
                network_key = FORTY_K_NETWORK
            elif total_cell_count <= 70000:
                network_key = SIXTY_K_NETWORK
            elif total_cell_count <= 90000:
                network_key = EIGHTY_K_NETWORK
            else:
                network_key = ONE_HUNDRED_K_NETWORK
    return network_key


def get_robustness_configuration():
    """
    Select the relevant robustness configuration dictionary based upon the determined network key

    :return: Robustness dictionary
    :rtype: dict
    """
    log.logger.debug("Selecting applicable robustness configuration.")
    network_key = get_network_config()
    return ROBUSTNESS_MAPPING.get(network_key)


def build_poid_dict_from_enm_data():
    """
    Build POID dictionary from ENM data

    :return: Dictionary of Node ID, POID values
    :rtype: dict
    """
    log.logger.debug("Building POID dictionary from ENM data")
    enm_poid_dict = {}
    try:
        user = get_workload_admin_user()
        enm_ne_poid_data = get_all_enm_network_element_objects(user).json()
    except Exception as e:
        log.logger.debug("Error encountered while trying to fetch info from ENM: {0}".format(e))
    else:
        errors = False
        for node in enm_ne_poid_data:
            if not node.get('mibRootName') or not node.get('poId'):
                errors = True
                continue

            enm_poid_dict[node['mibRootName']] = node['poId']

        if errors:
            log.logger.debug("Unexpected data received from ENM while processing POID info")
        else:
            log.logger.debug("POID info from ENM has been read for {0} NetworkElements"
                             .format(len(enm_poid_dict.keys())))
            return enm_poid_dict


def get_all_enm_network_element_objects(user):
    """
    Get all NetworkElement objects from ENM

    :param user: object to be used to make http requests
    :type user: enm_user_2.User
    :return: response
    :rtype: `Response` object
    :raises HTTPError: if the response is not ok
    """

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = user.get(NETEX_ENDPOINT, headers=headers)
    if not response.ok:
        raise HTTPError("Unable to get data from Network Explorer", response=response)

    return response


def is_eniq_server(emp=None, lms=None):
    """
    Check if the local machine is integrated as an ENIQ server

    :return: Tuple containing list of ENIQs and bool indicating a match to our IP
    :rtype: tuple
    """
    is_eniq = False
    eniq_ip_list = []
    hostname_to_match = get_local_ip()
    if not any([emp, lms]):
        log.logger.debug("Unable to determine if ENIQ Server is integrated.")
    else:
        eniq_install_file_cmd = ("cat /ericsson/pmic1/eniq_integration_details.txt" if emp else
                                 "cat /var/log/eniq_integration_details.txt")
        cmd = (CLOUD_SSH_EXEC_CMD.format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, emp, eniq_install_file_cmd) if emp
               else PHYSICAL_SSH_EXEC_CMD.format(lms, eniq_install_file_cmd))
        rc, output = commands.getstatusoutput(cmd)
        if not rc and output:
            eniq_ip_list = parse_eniq_ip_values(output)
        if hostname_to_match:
            is_eniq = any([_ for _ in eniq_ip_list if _ == hostname_to_match])

    return is_eniq, list(set(eniq_ip_list))


def parse_eniq_ip_values(output):
    """
    Function to parse the output of the cat command executed on the selected ENIQ file

    :param output: Output of the cat command executed on the selected ENIQ file
    :type output: str

    :return: List of parsed ip addreses if any
    :rtype: list
    """
    eniq_ip_key = "eniq ip address = "
    eniq_ip_list = []
    for line in output.split("\n"):
        if eniq_ip_key in line:
            eniq_ip_list.extend(ast.literal_eval(line.split(eniq_ip_key)[-1].split("\n")[0]))
    return eniq_ip_list


def get_local_ip():
    """
    Get the IP of the host machine, where the service is running

    :return: String containing the IP of the local host
    :rtype: str
    """
    rc, output = commands.getstatusoutput('hostname -i')
    if not rc and output:
        return output
    else:
        log.logger.debug("Unable to determine local hostname IP address, rc: [{0}], output: [{1}].".format(rc, output))


def check_if_password_ageing_enabled():
    """
    Check if the ENM Password Ageing Policy is currently enabled
    :return: warning message if Password ageing policy is enabled
    :rtype: str
    """
    user = get_workload_admin_user()
    response = user.get('/oss/idm/config/passwordsettings/enmuser')
    ageing_policy = response.json().get('passwordAgeing')
    policy_enabled = ageing_policy.get('enabled')
    if policy_enabled:
        max_age = ageing_policy.get('pwdMaxAge') or 90
        expire_warning = ageing_policy.get('pwdExpireWarning') or 7
        message = ("\nENM Password Ageing Policy is currently enabled. Password max age is currently: "
                   "[{0}] days and expiry warning is: [{1}] days. Password Ageing may impact workload created"
                   " user(s).\nRun SECUI_03 to disable password ageing policy (SECUI_03 runs at 12:00 am daily) "
                   "or change policy manually via ENM System Settings if the profile is not executable due"
                   " to password ageing."
                   .format(max_age, expire_warning))
        return message


def output_network_basic():
    """
    Logs the basic network details
    """
    base_file_path = "/opt/ericsson/enmutils/nrm_default_configurations/{}"
    nrm_file_mappings = {EXTRA_SMALL_NETWORK: base_file_path.format("extra_small_network.py"),
                         FIVE_K_NETWORK: base_file_path.format("five_network.py"),
                         SOEM_5K_NETWORK: base_file_path.format("soem_five_network.py"),
                         FIFTEEN_K_NETWORK: base_file_path.format("fifteen_network.py"),
                         FORTY_K_NETWORK: base_file_path.format("forty_network.py"),
                         SIXTY_K_NETWORK: base_file_path.format("sixty_network.py"),
                         TRANSPORT_10K_NETWORK: base_file_path.format("transport_ten_network.py"),
                         TRANSPORT_20K_NETWORK: base_file_path.format("transport_twenty_network.py")}
    if config.has_prop("ROBUSTNESS") and config.get_prop("ROBUSTNESS"):
        network_file_path = base_file_path.format("robustness_60k.py")
    else:
        network_file_path = nrm_file_mappings.get(persistence.get(NETWORK_TYPE))

    log.logger.info(log.cyan_text("Workload Config\t{0}".format(network_file_path)))
    log.logger.info(log.cyan_text("Determined network size: {0} Cells total.".format(
        persistence.get(NETWORK_CELL_COUNT))))


def get_uiserv_address():
    """
    Get uiserv ingress address from cluster
    :return: Tuple contain return code and command output
    :rtype: tuple
    """

    uiserv_json_path = "'{.items[?(@.metadata.name==\"uiserv\")].spec.rules[0].host}'"
    cmd = "{0} get ingress -A -o=jsonpath={1} 2>/dev/null".format(KUBECTL_PATH, uiserv_json_path)
    log.logger.debug("Fetching address of uiserv: '{0}'".format(cmd))
    rc, output = commands.getstatusoutput(cmd)
    return rc, output.split(' ')[0].strip()


def get_cloud_native_service_ips(service_name, namespace=None):
    """
    Gets the ip addresses of the service clusters required

    :param service_name: Name to Identify the service
    :type service_name: str
    :param namespace: Cloud Native Namespace
    :type namespace: str
    :return: service ips with ports
    :rtype: list
    :return: service ips without
    :rtype: list
    """
    log.logger.debug("Fetching the Service IP for identifier {0}".format(service_name))
    namespace = namespace if namespace else get_enm_cloud_native_namespace()
    scripting_ip_list_with_ports = []
    scripting_ip_list_without_ports = []
    # only gets ipv4 Ips https://regex101.com/r/EvDH9i/1
    cmd = (r"{0} get ericingress -n {1} 2>/dev/null | grep -P '(^|\s)general-scripting-[0-9](?=\s|$)'".format(
        KUBECTL_PATH, namespace))
    rc, stdout = commands.getstatusoutput(cmd)
    if not rc and stdout:
        ip_list = re.findall(r"(.*?) ", stdout)
        ip_list = filter(None, ip_list)
        ip_list = [item for item in ip_list if service_name not in item]
        for ip in ip_list:
            ip_and_port = ip.split(':', )
            scripting_ip_list_with_ports.append("{0} -p {1}".format(ip_and_port[0], ip_and_port[1]))
            scripting_ip_list_without_ports.append(ip_and_port[0])
        log.logger.debug("IPs for identifier with ports{0}".format(scripting_ip_list_with_ports))
        log.logger.debug("IPs for identifier without ports {0}".format(scripting_ip_list_without_ports))
        return scripting_ip_list_with_ports, scripting_ip_list_without_ports
    log.logger.debug("Unable to fetch IPs")
    return [], []


def get_cloud_native_service_vip(vip_identifier, namespace=None):
    """
    Get the Service Virtual IP (VIP) from ENM Cloud Native cluster

    :param vip_identifier: VIP Identifier
    :type vip_identifier: str
    :param namespace: Cloud Native Namespace
    :type namespace: str

    :return: Virtual IP
    :rtype: str
    """

    log.logger.debug("Fetching the Service VIP for identifier {0}".format(vip_identifier))
    namespace = namespace if namespace else get_enm_cloud_native_namespace()
    cmd = ("{0} get ericingress -n {1} 2>/dev/null | egrep {2}"
           .format(KUBECTL_PATH, namespace, vip_identifier))
    rc, stdout = commands.getstatusoutput(cmd)
    if not rc and stdout:
        vip = stdout.split()[1].split(":")[0]
        log.logger.debug("VIP for identifier {0}".format(vip))
        return vip
    log.logger.debug("Unable to fetch VIP")
    return ""


def is_deployment_vapp():
    """
    Determine if we are running on a vApp

    :returns: Boolean if vApp detected
    :rtype: bool
    """
    log.logger.debug("Checking if deployment is vApp.")
    output = socket.gethostname()
    return bool(output == VAPP_KEY)


def fetch_and_parse_nss_mo_files():
    """
    Fetch and parse available NetSim Mo files
    """
    log.logger.debug("Fetch and parse available NetSim MO files")
    if is_transport_network():
        log.logger.debug("Transport only network detected, no netsim MO information files to be collected.")
        return
    log.logger.debug("Generating netsim MO information files.")
    try:
        redis_nodes = node_pool_mgr.get_all_nodes_from_redis([])
        global NODE_COUNT
        if NODE_COUNT and len(redis_nodes) and len(redis_nodes) != NODE_COUNT:
            for nss_file in [nss_mo_info.CARDINALITY_FILE, nss_mo_info.MO_FILE]:
                rc, _ = commands.getstatusoutput("rm -f {0}".format(nss_file))
                if not rc:
                    log.logger.debug("Successfully removed MO file: [{0}]".format(nss_file))
                    NODE_COUNT = len(redis_nodes)
        nss_mo = nss_mo_info.NssMoInfo(node_pool_mgr.group_nodes_per_netsim_host(redis_nodes))
        nss_mo.fetch_and_parse_netsim_simulation_files()
    except Exception as e:
        log.logger.debug("Failed to generate one or more files, error encountered: {0}.".format(str(e)))
