# ********************************************************************
# Name    : Configure WLVM Operations
# Summary : Functional module used by the workload configure tool.
#           Allows user to perform a host of workloadVM configuration
#           tasks, fetching EMP key, setting local ENV variables,
#           setting NTP server.
# ********************************************************************

import inspect
import json
import subprocess
import time

from enmutils.lib import log

BASHRC_FILE = "/root/.bashrc"
STORAGE_PATH = "/var/tmp"
KEYPAIR_FILE_ON_WLVM = "{0}/enm_keypair.pem".format(STORAGE_PATH)
KEYPAIR_FILE_ON_EMP = "{0}/.enm_keypair.pem".format(STORAGE_PATH)
DIT_URL = "https://atvdit.athtem.eei.ericsson.se"
DIT_SED_PARAMETERS_KEYWORDS = ["parameter_defaults", "parameters"]

NL = "\n"

NTP_CONFIG_FILE = "/etc/ntp.conf"
NTP_SUBNET = "159.107.173"
NTP_SUBNET_OFFSET1 = "12"
NTP_SUBNET_OFFSET2 = "3"

SSH_OPTIONS = "-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

ATHTEM_DOMAINNAME = "athtem.eei.ericsson.se"


def check_packages_flow(logger, deployment_name, slogan):
    """
    Checks installed packages
    Note: In the original documentation, the mandatory packages were as follows
    "python-setuptools", "rsync", "wget", "openssh-clients", "openjdk"
    However, TorUtils includes openjdk in its own rpm so this is not needed

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    mandatory_packages = ["python-setuptools", "rsync", "wget", "openssh-clients"]

    check_packages_command = "/bin/rpm -qa | egrep '{0}'".format("|".join(mandatory_packages))
    try:
        response = subprocess.check_output(check_packages_command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if response.rstrip():
        packages_found = []
        packages_missing = []

        for package_name in mandatory_packages:
            if package_name in response.rstrip():
                packages_found.append(package_name)
            else:
                packages_missing.append(package_name)

        if len(packages_found) >= len(mandatory_packages):
            logger.info("All required packages installed: %s%s", mandatory_packages, NL)
            return True
        else:
            logger.info("Following mandatory packages are missing - cannot proceed: %s%s", packages_missing, NL)

    return False


def add_ntp_configuration(logger):
    """
    Adds extra NTP configuration to the server

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    command_to_remove_any_server_entries = "/bin/sed -i '/server {0}.*/d' {1}".format(NTP_SUBNET, NTP_CONFIG_FILE)
    logger.info("Removing old server entries: %s", command_to_remove_any_server_entries)

    try:
        response = subprocess.check_output(command_to_remove_any_server_entries, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        required_server_lines = ["server {0}.{1} prefer".format(NTP_SUBNET, NTP_SUBNET_OFFSET1),
                                 "server {0}.{1}".format(NTP_SUBNET, NTP_SUBNET_OFFSET2)]

        echo_commands = ["echo '{0}' >> {1}".format(line, NTP_CONFIG_FILE) for line in required_server_lines]
        logger.info("Adding server entries to ntp config file: %s", echo_commands)

        for echo_command in echo_commands:
            try:
                subprocess.check_output(echo_command, stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError as e:
                logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
                return False

        command_to_check_server_entries = "egrep -c 'server {0}' {1}".format(NTP_SUBNET, NTP_CONFIG_FILE)
        try:
            response = subprocess.check_output(command_to_check_server_entries, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        # Should now be 2 entries in the ntp.conf file
        if response.rstrip() and response.rstrip() == "2":
            if not restart_ntp(logger):
                logger.info("Potential problem encountered trying to restart ntp")
            return True

    logger.info("Problem encountered trying to configure ntp")
    return False


def restart_ntp(logger):
    """
    Function that restarts ntp service on Workload VM

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate success or not
    :rtype: bool
    """
    command_to_restart_ntpd = "service ntpd restart"
    logger.info("Restarting ntp service: %s", command_to_restart_ntpd)
    try:
        response = subprocess.check_output(command_to_restart_ntpd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    ntp_service_is_running = False
    if response.rstrip() and "Starting ntpd" in response.rstrip():
        command_to_check_ntpd_status = "service ntpd status"
        checks = 1
        # Will wait for NTP service to come online - potentially not happen straight away
        while checks <= 3:
            logger.info("Checking status of ntp service: %s", command_to_check_ntpd_status)
            try:
                response = subprocess.check_output(command_to_check_ntpd_status, stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError as e:
                logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
                return False

            if response.rstrip() and "is running" in response.rstrip():
                ntp_service_is_running = True
                break

            logger.info("Not running yet - Sleeping for 5s before rechecking")
            time.sleep(5)
            checks += 1

        if ntp_service_is_running:
            return enable_ntp_service_at_reboot(logger)
        else:
            logger.info("Ntp service failed to restart")

    return False


def enable_ntp_service_at_reboot(logger):
    """
    Enables NTP Service to run after reboot

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    command_to_enable_ntp_at_reboot = "chkconfig ntpd on"
    logger.info("Enabling ntp service at reboot: %s", command_to_enable_ntp_at_reboot)
    try:
        response = subprocess.check_output(command_to_enable_ntp_at_reboot, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        command_to_ntp_enabled_at_reboot = "chkconfig --list ntpd"
        logger.info("Check ntp service enabled at reboot (requires: '3:on'): %s",
                    command_to_ntp_enabled_at_reboot)
        try:
            response = subprocess.check_output(command_to_ntp_enabled_at_reboot, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if response.rstrip() and "3:on" in response.rstrip():
            return True
        else:
            logger.info("Problem running command: %s%s", command_to_ntp_enabled_at_reboot, NL)
    else:
        logger.info("Unable to enable ntp at reboot using command: %s%s", command_to_enable_ntp_at_reboot, NL)

    return False


def check_if_ntp_synchronized(logger, max_checks):
    """
    Runs ntpstat command to check status of NTP service

    :param logger: Logging object
    :type logger: logging.Logger
    :param max_checks: Maximum number of checks to perform on NTP status
    :type max_checks: int
    :return: Boolean to indicate if service is running or not
    :rtype: bool
    """
    command_to_check_ntp_status = "/usr/bin/ntpstat"
    logger.info("Checking ntp status via command: %s", command_to_check_ntp_status)

    response = ""
    attempt = 1
    while attempt <= max_checks:
        try:
            response = subprocess.check_output(command_to_check_ntp_status, stderr=subprocess.STDOUT, shell=True)
            break
        except subprocess.CalledProcessError as e:
            if max_checks != 1:
                logger.info("ntp server not sync'd yet - this can take up to 5 mins after service restart: %s%s - %s",
                            e, NL, e.output)
                logger.info("Sleeping for 5s ... before retry")
                time.sleep(5)
            attempt += 1

    if response and "synchronised to NTP server" in response:
        return True

    logger.info("Server not synchronized with NTP server")
    return False


def configure_ntp_flow(logger, deployment_name, slogan):
    """
    Flow that configures NTP

    :param logger: Logging object
    :type logger: logging.Logger
    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    logger.info("Checking if server is NTP synchronized...")
    if not check_if_ntp_synchronized(logger, max_checks=1):
        logger.info("...not NTP synchronized - configuring NTP on server")
        if add_ntp_configuration(logger):
            if check_if_ntp_synchronized(logger, max_checks=3):
                logger.info("...NTP synchronized now")
            else:
                logger.info("...can take some time for ntp sync to complete")
            logger.info("NTP Configuration complete")
            return True

        logger.info("Problem encountered while adding NTP configuration")
        return False

    logger.info("...already NTP synchronized - NTP Configuration complete")
    return True


def fetch_sed_id(logger, deployment_name):
    """
    Fetches SED ID from DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :return: String containing SED ID from DIT
    :rtype: str
    """
    sed_id = ""
    logger.info("Querying DIT API to fetch SED_ID ...\n")
    url_to_get_sed_id = r"{dit_url}/api/deployments/?q=name={deployment_name}\&fields=enm\(sed_id\)" \
        .format(dit_url=DIT_URL, deployment_name=deployment_name)

    curl_command_to_get_sed_id = "curl -s {0}".format(url_to_get_sed_id)
    try:
        response = subprocess.check_output(curl_command_to_get_sed_id, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return ""

    if response.rstrip():
        try:
            json_data = json.loads(response)
        except ValueError:
            return ""

        if json_data and "enm" in json_data[0].keys() and "sed_id" in json_data[0]["enm"].keys():
            sed_id = json_data[0]["enm"]["sed_id"]

    if not sed_id:
        logger.info("Could not get sed_id from DIT using command: %s%s", curl_command_to_get_sed_id, NL)
        return ""
    return sed_id


def fetch_emp_external_ip(logger, sed_id):
    """
    Fetches the EMP External IP Address from DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param sed_id: String containing the SED ID of the deployment in DIT
    :type sed_id: str
    :return: String containing the EMP External IP Address
    :rtype: str
    """
    logger.info("Querying DIT API to fetch EMP Public IP Address from SED ...\n")
    sed_parameter_key = "emp_external_ip_list"

    fields_content = r"fields=content\({parameters_keyword}\({sed_parameter_key}\)\)"

    url_to_get_emp_ip = (r"{dit_url}/api/documents/{sed_id}?{fields_content}"
                         .format(dit_url=DIT_URL, sed_id=sed_id, fields_content=fields_content))
    curl_command = "curl -s {0}".format(url_to_get_emp_ip)

    sed_value = fetch_parameter_value_from_sed_on_dit(logger, curl_command, sed_parameter_key)
    logger.info("Value of '{0}' is '{1}'".format(sed_parameter_key, sed_value))
    return sed_value


def fetch_httpd_fqdn(logger, sed_id):
    """
    Fetches the Haproxy from DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param sed_id: String containing the SED ID of the deployment in DIT
    :type sed_id: str
    :return: String containing the Haproxy of the ENM deployment in DIT
    :rtype: str
    """
    logger.info("Querying DIT API to fetch HA Proxy from SED ...\n")
    sed_parameter_key = "httpd_fqdn"

    fields_content = r"fields=content\({parameters_keyword}\({sed_parameter_key}\)\)"

    url_to_get_emp_ip = (r"{dit_url}/api/documents/{sed_id}?{fields_content}"
                         .format(dit_url=DIT_URL, sed_id=sed_id, fields_content=fields_content))
    curl_command = "curl -s {0}".format(url_to_get_emp_ip)

    sed_value = fetch_parameter_value_from_sed_on_dit(logger, curl_command, sed_parameter_key)
    logger.info("Value of '{0}' is '{1}'".format(sed_parameter_key, sed_value))
    return sed_value


def fetch_parameter_value_from_sed_on_dit(logger, curl_command, sed_parameter_key):
    """
    Fetch parameter value from SED on DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param curl_command: Curl command
    :type curl_command: str
    :param sed_parameter_key: SED Parameter Name
    :type sed_parameter_key: str
    :return: SED Parameter value
    :rtype: str
    """
    sed_value = ""

    for index, dit_parameters_keyword in enumerate(DIT_SED_PARAMETERS_KEYWORDS):
        command = curl_command.format(parameters_keyword=dit_parameters_keyword, sed_parameter_key=sed_parameter_key)
        logger.info("Trying command: {0}".format(command))

        try:
            if not sed_value:
                output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                sed_value = extract_sed_value_from_output(output, dit_parameters_keyword, sed_parameter_key)
        except subprocess.CalledProcessError as e:
            if not index:
                logger.info("Retrying alternative DIT rest interface: {0} - {1}".format(e, e.output))
                continue
            else:
                logger.info("Problem encountered during command execution: {0} - {1}".format(e, e.output))

    if not sed_value:
        logger.info("Unable to get {0} for deployment from DIT using command: {1}"
                    .format(sed_parameter_key, curl_command))
    return sed_value


def extract_sed_value_from_output(output, dit_parameters_keyword, sed_parameter_key):
    """
    Extract value of SED parameter from output

    :param output: Command Output
    :type output: str
    :param dit_parameters_keyword: Keyword used to identify the SED parameters dictionary in DIT
    :type dit_parameters_keyword: str
    :param sed_parameter_key: SED parameter Name
    :type sed_parameter_key: str

    :return: SED value
    :rtype: str
    """
    sed_parameter_value = ""

    if output and output.rstrip():
        try:
            json_data = json.loads(output)
        except ValueError:
            return ""

        if (json_data and "content" in json_data.keys() and dit_parameters_keyword in json_data["content"] and
                sed_parameter_key in json_data["content"][dit_parameters_keyword]):
            sed_parameter_value = json_data["content"][dit_parameters_keyword][sed_parameter_key]

    return sed_parameter_value


def update_bashrc_file_with_variable(logger, variable_identifier, variable_value):
    """
    Updates the root user's .bashrc file with a variable and it's value

    :param logger: Logging object
    :type logger: logging.Logger
    :param variable_identifier: String containing the identifier of the variable (e.g. EMP)
    :type variable_identifier: str
    :param variable_value: String containing the value of the variable
    :type variable_value: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    logger.info("Updating bashrc file with required variables...\n")
    command_to_check_if_bashrc_file_exists = "[ -f {0} ] && echo 'True' || echo 'False'".format(BASHRC_FILE)
    try:
        response = subprocess.check_output(command_to_check_if_bashrc_file_exists, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if "False" in response.rstrip():
        logger.info("The mandatory bashrc file {0} doesnt exist on this server - cannot proceed %s", BASHRC_FILE)
        return False

    variable_name = "EMP" if "emp" in variable_identifier else "ENM_URL"

    command_to_remove_any_old_entries_in_bashrc = "/bin/sed -i '/export.*{0}=/d' {1}".format(variable_name, BASHRC_FILE)
    try:
        response = subprocess.check_output(command_to_remove_any_old_entries_in_bashrc, stderr=subprocess.STDOUT,
                                           shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        command_to_add_new_entry = 'echo "export {0}={1}" >> {2}'.format(variable_name, variable_value, BASHRC_FILE)
        try:
            response = subprocess.check_output(command_to_add_new_entry, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if not response.rstrip():
            logger.info("Variable %s added to %s%s", variable_name, BASHRC_FILE, NL)
            return True

    logger.info("Variable %s was not added to %s%s", variable_name, BASHRC_FILE, NL)
    return False


def set_enm_locations_flow(logger, deployment_name, slogan):
    """
    Flow that controls the insertion of variables into the .bashrc file

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    sed_id = fetch_sed_id(logger, deployment_name)

    set_variables_success_count = 0
    if sed_id:
        emp_external_ip = fetch_emp_external_ip(logger, sed_id)
        if emp_external_ip:
            if update_bashrc_file_with_variable(logger, "emp_external_ip", emp_external_ip):
                set_variables_success_count += 1
        else:
            logger.info(
                "EMP IP Address %s is not set in DIT for deployment %s - cannot complete task successfully%s",
                "emp_external_ip", deployment_name, NL)

        httpd_fqdn = fetch_httpd_fqdn(logger, sed_id)
        if httpd_fqdn:
            if update_bashrc_file_with_variable(logger, "httpd_fqdn", httpd_fqdn):
                set_variables_success_count += 1
        else:
            logger.info("HAproxy %s is not set in DIT for deployment %s - cannot complete task successfully%s",
                        "httpd_fqdn", deployment_name, NL)

    else:
        logger.info("SED_ID is not set in DIT for deployment %s - cannot proceed%s", deployment_name, NL)

    return True if set_variables_success_count == 2 else False


def fetch_keypair_data_from_dit(logger, deployment_name):
    """
    Fetches the cloud-user ssh private key and stores it in a local file

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :return: Private key
    :rtype: str
    """
    logger.info("Querying DIT API to fetch cloud-user key-pair file ...\n")

    url_to_get_key_pair_file = (r"{dit_url}/api/deployments/?q=name={deployment_name}\&fields=enm\(private_key\)"
                                .format(dit_url=DIT_URL, deployment_name=deployment_name))

    curl_command_to_get_key_pair_file = "curl -s {0}".format(url_to_get_key_pair_file)
    try:
        response = subprocess.check_output(curl_command_to_get_key_pair_file, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return ""

    if response.rstrip():
        try:
            json_data = json.loads(response)
        except ValueError:
            return ""

        if (json_data and isinstance(json_data, list) and "enm" in json_data[0].keys() and
                "private_key" in json_data[0]["enm"].keys()):
            return json_data[0]["enm"]["private_key"]

    else:
        logger.info("Unable to fetch data for deployment from DIT using command: %s%s",
                    curl_command_to_get_key_pair_file, NL)

    return ""


def write_keypair_data_to_file(logger, private_key):
    """
    Writes the cloud-user ssh private key to local file and sets appropriate permissions on the file

    :param logger: Logging object
    :type logger: logging.Logger
    :param private_key: String containing the ssh private key for the cloud-user
    :type private_key: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Creating local file (%s) containing the cloud-user ssh private key ...%s", KEYPAIR_FILE_ON_WLVM, NL)
    command = 'echo "{0}" > {1}'.format(private_key, KEYPAIR_FILE_ON_WLVM)

    try:
        response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        command = 'cat {0}'.format(KEYPAIR_FILE_ON_WLVM)

        try:
            response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if "END RSA PRIVATE KEY" not in response.rstrip():
            logger.info("Appears that key pair file doesnt contain RSA key %s", NL)
            return False
        logger.info("The cloud-user ssh private key has been written to file: %s%s", KEYPAIR_FILE_ON_WLVM, NL)

        logger.info("Setting permissions...\n")
        command = 'chmod 600 {0}'.format(KEYPAIR_FILE_ON_WLVM)
        try:
            response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if not response.rstrip():
            logger.info("Correct permissions set on cloud-user ssh private key: %s%s", KEYPAIR_FILE_ON_WLVM, NL)
            return True
        else:
            logger.info("Could not set permissions (600) on cloud-user ssh private key: %s%s", KEYPAIR_FILE_ON_WLVM, NL)
    else:
        logger.info("The cloud-user ssh private key could not be written to file: %s%s", KEYPAIR_FILE_ON_WLVM, NL)

    return False


def fetch_private_key_flow(logger, deployment_name, slogan):
    """
    Flow that controls the fetching of the private key from DIT and storing to file

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    private_key_data = fetch_keypair_data_from_dit(logger, deployment_name)
    key_written_success = False
    if private_key_data:
        if write_keypair_data_to_file(logger, private_key_data):
            key_written_success = True
    else:
        logger.info("private_key is not set in DIT for deployment %s%s", deployment_name, NL)

    return True if key_written_success else False


def store_private_key_on_emp_flow(logger, deployment_name, slogan):
    """
    Flow that stores private key on EMP

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    command = ""
    if check_if_file_exists(logger, KEYPAIR_FILE_ON_WLVM):
        emp_external_ip_address = get_emp_external_ip_address_from_bashrc(logger)
        if emp_external_ip_address:
            logger.info("Copying key file (%s) to EMP...\n", KEYPAIR_FILE_ON_WLVM)
            try:
                command = "scp -i {0} {1} {0} cloud-user@{2}:{3}".format(KEYPAIR_FILE_ON_WLVM, SSH_OPTIONS,
                                                                         emp_external_ip_address, KEYPAIR_FILE_ON_EMP)
                subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError as e:
                logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
                return False

            if check_if_file_exists(logger, KEYPAIR_FILE_ON_EMP, emp_external_ip_address):
                logger.info("File successfully copied to EMP %s", NL)
                return True

    logger.info("Unable to copy the cloud-user SSH private_key file (%s) to EMP %s - command: %s", KEYPAIR_FILE_ON_WLVM,
                NL, command)
    return False


def check_if_file_exists(logger, path_to_file, emp_external_ip_address=None):
    """
    Function to check if a file exists on some host

    :param logger: Logging object
    :type logger: logging.Logger
    :param path_to_file: String containing the path to the file
    :type path_to_file: str
    :param emp_external_ip_address: String containing EMP External IP Address
    :type emp_external_ip_address: str
    :return: Boolean to indicate whether the file exists or not
    :rtype: str
    """
    command_to_check_if_file_exists = "[ -f {0} ] && echo 'True' || echo 'False'".format(path_to_file)

    if emp_external_ip_address:
        msg = "on ENM"
        ssh_command = 'ssh -i {0} {1} cloud-user@{2}'.format(KEYPAIR_FILE_ON_WLVM, SSH_OPTIONS, emp_external_ip_address)

        command_to_run_on_host = '{0} "{1}"'.format(ssh_command, command_to_check_if_file_exists)
    else:
        msg = "locally"
        command_to_run_on_host = "{0}".format(command_to_check_if_file_exists)

    logger.info("Checking if file (%s) exists %s...%s", path_to_file, msg, NL)
    try:
        response = subprocess.check_output(command_to_run_on_host, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if response.rstrip() and 'True' in response.rstrip():
        return True

    logger.info("The file does not exist %s: %s%s", msg, path_to_file, NL)

    return False


def get_emp_external_ip_address_from_bashrc(logger):
    """
    Fetches the EMP External IP Address from the root user's .bashrc file

    :param logger: Logging object
    :type logger: logging.Logger
    :return: String containing the EMP External IP address
    :rtype: str
    """
    emp_external_ip_address = ""

    logger.info("Getting EMP IP Address from bashrc...\n")
    command_to_get_emp_external_ip_address_from_bashrc = "egrep EMP= {0} | tail -1 | cut -f2 -d'='".format(BASHRC_FILE)
    try:
        response = subprocess.check_output(command_to_get_emp_external_ip_address_from_bashrc, stderr=subprocess.STDOUT,
                                           shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if response.rstrip():
        emp_external_ip_address = response.rstrip()
    else:
        logger.info("Could not get EMP External IP address from bashrc file using command:%s%s%s",
                    NL, command_to_get_emp_external_ip_address_from_bashrc, NL)

    return emp_external_ip_address


def get_workload_fqdn(logger):
    """
    Constructs the FQDN based on the hostname of the current server (assumes it is workload server)

    :param logger: Logging object
    :type logger: logging.Logger
    :return: String containing FQDN of workload server
    :rtype: str
    """
    workload_fqdn = ""

    logger.info("Getting FQDN of workload server...\n")
    command_to_get_hostname = "hostname | tail -1"
    try:
        response = subprocess.check_output(command_to_get_hostname, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return ""

    if response.rstrip():
        workload_fqdn = "{0}.{1}".format(response.rstrip(), ATHTEM_DOMAINNAME)
    else:
        logger.info("Problem encountered while getting hostname using command:%s%s%s",
                    NL, command_to_get_hostname, NL)

    return workload_fqdn


def fetch_workload_id(logger, deployment_name):
    """
    Fetches the Workload ID from DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :return: String containing the workload_id
    :rtype: str
    """
    logger.info("Querying DIT API to fetch Workload ID ...\n")
    url_to_get_workload_id = r"{dit_url}/api/deployments/?q=name={deployment_name}\&fields=documents" \
        .format(dit_url=DIT_URL, deployment_name=deployment_name)

    curl_command_to_get_workload_id = "curl -s {0}".format(url_to_get_workload_id)
    try:
        response = subprocess.check_output(curl_command_to_get_workload_id, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return ""

    if response.rstrip():
        return parse_workload_id_data(logger, response, curl_command_to_get_workload_id)
    return ""


def parse_workload_id_data(logger, response, curl_command_to_get_workload_id):
    """
    Parses curl response to extract workload id

    :param logger: Logging object
    :type logger: logging.Logger
    :param response: Curl response
    :type response: str
    :param curl_command_to_get_workload_id: Curl command used
    :type curl_command_to_get_workload_id: str
    :return: String containing Workload ID
    :rtype: str
    """
    workload_id = ""
    try:
        json_data = json.loads(response)
    except ValueError:
        return ""

    if json_data and isinstance(json_data, list) and "documents" in json_data[0].keys():
        for item in json_data[0]["documents"]:
            if "schema_name" in item.keys() and item["schema_name"] == "workload":
                workload_id = item["document_id"]

    if not workload_id:
        logger.info("Could not get workload_id from DIT using command: %s%s", curl_command_to_get_workload_id, NL)
        return ""

    return workload_id


def fetch_workload_vm_hostname(logger, workload_id):
    """
    Fetches the hostname of the workload VM from DIT

    :param logger: Logging object
    :type logger: logging.Logger
    :param workload_id: String containing the workload_id
    :type workload_id: str
    :return: String containing the workload VM
    :rtype: str
    """
    workload_vm_hostname = ""

    logger.info("Querying DIT API to fetch Workload VM hostname ...\n")
    url_to_get_hostname = r"{dit_url}/api/documents/{workload_id}?fields=content\(vm\(hostname,type\)\)" \
        .format(dit_url=DIT_URL, workload_id=workload_id)

    curl_command_to_get_hostname = "curl -s {0}".format(url_to_get_hostname)

    try:
        response = subprocess.check_output(curl_command_to_get_hostname, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return ""

    if response.rstrip():
        try:
            json_data = json.loads(response)
        except ValueError:
            return ""

        if (json_data and "content" in json_data.keys() and "vm" in json_data["content"] and
                json_data["content"]["vm"] and "hostname" in json_data["content"]["vm"][0]):
            workload_vm_hostname = json_data["content"]["vm"][0]["hostname"]

    if not workload_vm_hostname:
        logger.info("Unable to get Workload VM hostname for deployment from DIT using command: %s%s",
                    curl_command_to_get_hostname, NL)
        return ""

    return workload_vm_hostname


def get_wlvm_hostname_from_dit_flow(logger, deployment_name, slogan):
    """
    Flow to get the hostname of the workload VM

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    workload_id = fetch_workload_id(logger, deployment_name)

    if workload_id:
        workload_vm_hostname = fetch_workload_vm_hostname(logger, workload_id)
        if workload_vm_hostname:
            logger.info("The workload_vm hostname for this deployment is: %s%s", workload_vm_hostname, NL)
            return True

    return False


def export_deployment_name(deployment_name):
    """
    Adds the deployment name entry to .bashrc file

    :param deployment_name: Name of the cloud deployment
    :type deployment_name: str
    """
    bashrc_entry = "export DEPLOYMENTNAME={0}".format(deployment_name)
    log.logger.debug("Adding deployment name [{0}] entry to {1} file\n".format(deployment_name, BASHRC_FILE))
    sed_command = 'sed -i "/export DEPLOYMENTNAME=/d" {0}; echo "{1}" >> {0}'.format(BASHRC_FILE, bashrc_entry)
    try:
        subprocess.check_output(sed_command, stderr=subprocess.STDOUT, shell=True)
        log.logger.debug("Value of '{0}' is added to '{1}'.".format(bashrc_entry, BASHRC_FILE))
    except subprocess.CalledProcessError as e:
        log.logger.info("Problem encountered during command execution: {0}\n - {1}".format(e, e.output))


def check_deployment_to_disable_proxy():
    """
    Check the deployment to disable proxy or not for workload configuration on workload vm.
    :return: returns False (proxy not required), when workload vm name matched with seli/sero, otherwise returns True
    :rtype: bool
    """
    wlvm_name = get_workload_fqdn(log.logger)
    log.logger.info("workload vm name: {0}".format(wlvm_name))
    if wlvm_name:
        for wlvm_keyword in ["seli", "sero"]:
            if wlvm_keyword in wlvm_name:
                log.logger.info("Workload vm is configuring without using proxy")
                return False
    return True
