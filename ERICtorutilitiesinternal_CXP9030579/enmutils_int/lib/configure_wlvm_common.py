# ********************************************************************
# Name    : Configure WLVM Common
# Summary : Functional module used by the workload configure tool.
#           Includes various common functions
# ********************************************************************

import commands
import socket

from enmutils.lib import log
from enmutils.lib.filesystem import does_file_exist

BASHRC_FILE = "/root/.bashrc"
NEXUS_SERVER = "https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443"
HTTPS_PROXY_URL = "atproxy1.athtem.eei.ericsson.se:3128"
SSH_DIR = "/root/.ssh"
SSH_PRIVATE_KEY = "{0}/id_rsa".format(SSH_DIR)
SSH_PUBLIC_KEY = "{0}/id_rsa.pub".format(SSH_DIR)
SSH_AUTHORIZED_KEYS = "{0}/authorized_keys".format(SSH_DIR)


def update_bashrc_file_with_env_variable(variable_name, variable_value):
    """
    Update Environment variable .bashrc file for root user

    :param variable_name: Bashrc variable name (e.g. EMP)
    :type variable_name: str
    :param variable_value: String containing the value of the variable
    :type variable_value: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    log.logger.debug("Updating bashrc file with environment variable: {0}".format(variable_name))
    if does_file_exist(BASHRC_FILE):
        command = "/bin/sed -i '/export.*{0}=/d' {1}".format(variable_name, BASHRC_FILE)
        log.logger.debug("Removing any old entries related to variable via command: {0}".format(command))
        rc, _ = commands.getstatusoutput(command)
        if not rc:
            command = "echo 'export {0}={1}' >> {2}".format(variable_name, variable_value, BASHRC_FILE)
            log.logger.debug("Adding new entry for variable via command: {0}".format(command))
            rc, _ = commands.getstatusoutput(command)
            if not rc:
                log.logger.debug("Variable added")
                return True

    log.logger.info("Environment variable {0} was not added to {1}".format(variable_name, BASHRC_FILE))


def restart_services():
    """
    Function to restart services after environment variable updated in .bashrc

    :return: int to indicate how many services restarted successfully
    :rtype: int
    """
    all_services_restarted = False
    services = ["usermanager", "deploymentinfomanager", "nodemanager", "profilemanager"]
    for service in services:
        restart_command = "/sbin/service {0} restart".format(service)
        response = execute_command(restart_command)
        all_services_restarted += response.get("result")

    log.logger.debug("{0} out of 4 services restarted.".format(all_services_restarted))

    return all_services_restarted


def check_if_rpm_package_is_installed(package_name, package_version=""):
    """
    Check if package is installed

    :param package_name: Package Name
    :type package_name: str
    :param package_version: Package Version
    :type package_version: str
    :return: Boolean to indicate if package is installed or not
    :rtype: bool
    """
    log.logger.debug("Checking if Package {0} is installed (Version info: {1})".format(package_name, package_version))
    command = "rpm -qa | egrep {0}.*{1}".format(package_name, package_version)
    rc, _ = commands.getstatusoutput(command)
    if not rc:
        log.logger.debug("Package already installed")
        return True

    log.logger.debug("Package is not installed")


def download_release_package_from_nexus(package_name, nexus_path, file_path, is_proxy_required):
    """
    Check if package is installed

    :param package_name: Name of Package
    :type package_name: str
    :param nexus_path: Package path on Nexus
    :type nexus_path: str
    :param file_path: Location of where package will be stored once downloaded
    :type file_path: str
    :param is_proxy_required: proxy is used download the release package from nexus, when it was True.
     Otherwise, it will not use proxy.
    :type is_proxy_required: bool

    :return: Boolean to indicate if package is installed or not
    :rtype: bool
    """
    log.logger.debug("Downloading 'RELEASE' package {0} from nexus".format(package_name))

    nexus_redirect_path = "nexus/service/local/artifact/maven/redirect"
    nexus_redirect_parameters = "r=releases&g={0}&a={1}&v=RELEASE&e=rpm".format(nexus_path, package_name)
    nexus_redirect_url = "{0}/{1}?{2}".format(NEXUS_SERVER, nexus_redirect_path, nexus_redirect_parameters)
    command = (("curl -s -x {0} '{1}'".format(HTTPS_PROXY_URL, nexus_redirect_url)) if is_proxy_required
               else ("curl -s '{0}'".format(nexus_redirect_url)))

    log.logger.debug("Using command to fetch path to RPM: {0}".format(command))
    rc, output = commands.getstatusoutput(command)
    if not rc:
        rpm_url = extract_path_to_rpm_from_nexus_redirect(output)
        if rpm_url:
            command = (("curl -s -o {0} -x {1} '{2}'".format(file_path, HTTPS_PROXY_URL, rpm_url))
                       if is_proxy_required else ("curl -s -o {0} '{1}'".format(file_path, rpm_url)))
            log.logger.debug("Using command to fetch RPM: {0}".format(command))
            rc, output = commands.getstatusoutput(command)
            if not rc:
                log.logger.debug("Package downloaded to {0}".format(file_path))
                return True

    log.logger.debug("Package not downloaded")


def extract_path_to_rpm_from_nexus_redirect(message):
    """
    Extract RPM response from Nexus redirect message

    :param message: Nexus redirect message
    :type message: str

    :return: URL of RPM
    :rtype: str
    """
    try:
        rpm_url = message.split("https://")[1]
        return "https://{0}".format(rpm_url)
    except Exception as e:
        log.logger.debug("Unexpected output: {0} - {1}".format(message, e))


def install_rpm_package(file_path):
    """
    Install RPM package

    :param file_path: path to package file
    :type file_path: str
    :return: Boolean to indicate if package is installed or not
    :rtype: bool
    """
    log.logger.debug("Installing package located at {0}".format(file_path))
    command = "rpm -ivh {0} --nodeps".format(file_path)
    log.logger.debug("Using command: {0}".format(command))
    rc, output = commands.getstatusoutput(command)
    if not rc:
        log.logger.debug("Package successfully installed")
        return True

    log.logger.debug("Package installation failed: {0}".format(output))


def perform_service_operation(service_name, operation):
    """
    Perform operation on service

    :param service_name: Service Name
    :type service_name: str
    :param operation: Service operation
    :type operation: str
    :return: Boolean to indicate if service is running or not
    :rtype: bool
    """
    log.logger.debug("Performing {0} operation on service {1}".format(operation, service_name))
    command = "service {0} {1}".format(service_name, operation)
    log.logger.debug("Using command: {0}".format(command))
    rc, output = commands.getstatusoutput(command)
    if not rc:
        log.logger.debug("Command successful")
        return True

    log.logger.debug("Command unsuccessful: '{0}' - {1}".format(command, output))


def create_ssh_keys():
    """
    Create SSH public and private keys

    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    if check_if_ssh_keys_exist():
        return True

    log.logger.debug("Creating ssh keys")
    command = "ssh-keygen -t rsa -N '' -f {0}".format(SSH_PRIVATE_KEY)
    return execute_command(command)["result"]


def check_if_ssh_keys_exist():
    """
    Check if root ssh keys exist
    :return: Boolean to indicate if keys exist of not
    :rtype: bool
    """
    if does_file_exist("{0}".format(SSH_PRIVATE_KEY)) and does_file_exist("{0}".format(SSH_PUBLIC_KEY)):
        log.logger.debug("SSH keys already exist")
        return True

    log.logger.debug("SSH keys do not already exist")


def update_ssh_authorized_keys():
    """
    Adding SSH public key to authorized_keys

    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.debug("Updating authorized_keys")
    public_key = get_ssh_public_key()
    if (public_key and remove_hostname_entries_from_ssh_authorized_keys() and
            add_ssh_public_key_to_authorized_keys(public_key) and set_file_permissions(SSH_AUTHORIZED_KEYS, "644")):
        log.logger.debug("Operation successful")
        return True

    log.logger.debug("Operation unsuccessful: {0}")


def execute_command(command, log_output=True):
    """
    Execute command locally

    :param command: Command to be executed
    :type command: str
    :param log_output: Boolean to indicate if output should be logged or not
    :type log_output: bool
    :return: Dict of the form: {result: True/False, output: command output}
    :rtype: dict
    """
    if log_output:
        log.logger.debug("Executing command: {0}".format(command))
    rc, output = commands.getstatusoutput(command)
    if not rc:
        if log_output:
            log.logger.debug("Execution successful (rc=0). Output: {0}".format(output))
        return {"result": True, "output": output}

    if log_output:
        log.logger.debug("Execution unsuccessful - Output: '{0}'".format(output))
    return {"result": False, "output": output}


def get_ssh_public_key():
    """
    Get SSH public key

    :return: SSH public key
    :rtype: str
    """
    log.logger.debug("Get ssh public key")
    command = "cat {0}".format(SSH_PUBLIC_KEY)
    return execute_command(command)["output"]


def remove_hostname_entries_from_ssh_authorized_keys():
    """
    Get SSH public key

    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    if not does_file_exist("{0}".format(SSH_AUTHORIZED_KEYS)):
        return True

    log.logger.debug("Remove hostname entries from authorized_keys")
    command = "sed -i '/{0}/d' {1}".format(socket.gethostname(), SSH_AUTHORIZED_KEYS)
    return execute_command(command)["result"]


def add_ssh_public_key_to_authorized_keys(public_key):
    """
    Add SSH public key to authorized_keys

    :param public_key: SSH public key
    :type public_key: str
    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.debug("Add SSH public key to authorized_keys")
    command = "echo '{0}' >> {1}".format(public_key, SSH_AUTHORIZED_KEYS)
    return execute_command(command)["result"]


def set_file_permissions(filepath, permissions):
    """
    Set file permissions

    :param filepath: Path to file
    :type filepath: str
    :param permissions: File permissions
    :type permissions: str
    :return: Boolean to indicate success of operation
    :rtype: bool
    """
    log.logger.debug("Set permissions {0} on file {1}".format(permissions, filepath))
    command = "chmod {0} {1}".format(permissions, filepath)
    return execute_command(command)["result"]
