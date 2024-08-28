#!/usr/bin/env python
# ********************************************************************
# Name    : Configure WLVM
# Summary : Tool used to configure Workload VM so that it can be used
#           by workload profiles in Cloud (vENM/cENM) deployments
# ********************************************************************

import commands
import logging
import optparse
import os
import signal
import sys

from enmutils.lib import log
from enmutils_int.lib import configure_wlvm_operations as operations
from enmutils_int.lib import configure_wlvm_packages as packages
from enmutils_int.lib.configure_wlvm_cenm import (
    compare_kubectl_client_and_server_version, create_ddc_secret_on_cluster,
    install_kubectl_client, set_cenm_variables, setup_cluster_connection)
from enmutils_int.lib.configure_wlvm_common import restart_services
from enmutils_int.lib.dit import get_dit_deployment_info

TOOL_NAME = os.path.basename(sys.argv[0])
ABOUT_TEXT = "Configure Workload VM to operate towards cloud ENM"
DEPLOYMENT_NAME_EXAMPLE = "ieatenmc17b27"
LOG_DIR = "/var/log/enmutils"
LOG_PATH_INFO = "Please check logs: {0}/{1}.log".format(LOG_DIR, TOOL_NAME).replace(".py", "")
KUBECTL_PATH = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config"
CLOUD_NATIVE_NAME_SPACE_CMD = "{0} get ingress --all-namespaces 2>/dev/null | egrep uiserv".format(KUBECTL_PATH)


OPERATIONS = [["check_packages", "Check that mandatory packages are installed on Workload VM server"],
              ["configure_ntp", "Configure NTP on Workload VM server"],
              ["set_enm_locations", "Install bashrc variables containing locations of ENM components "
                                    "(e.g. EMP Public IP Address (vENM) or HA Proxy URL (vENM/cENM)"],
              ["fetch_private_key", "Fetch cloud-user private key from DIT and store in local file (vENM)"],
              ["install_cluster_client", "Install kubernetes cluster client (cENM)"],
              ["store_private_key_on_emp", "Store copy of cloud-user keypair file on EMP (vENM)"],
              ["install_ddc", "Install DDC on Workload VM server"],
              ["configure_ddc_on_enm", "Configure DDC on ENM to collect diagnostics data from Workload VM"],
              ["setup_ddc_collection_of_workload_files", "Install 'DDC Plugin for Workload' on Workload VM"],
              ["get_wlvm_hostname_from_dit", "Fetch the hostname of Workload VM from DIT"]]


def check_packages(deployment_name, slogan):
    """
    Checks installed packages

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    return operations.check_packages_flow(log.logger, deployment_name, slogan)


def configure_ntp(deployment_name, slogan):
    """
    Flow that configures NTP

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    return operations.configure_ntp_flow(log.logger, deployment_name, slogan)


def set_enm_locations(deployment_name, slogan):
    """
    Flow that controls the insertion of variables into the .bashrc file

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    deployment_type, _ = get_dit_deployment_info(deployment_name)

    if "cENM" in deployment_type:
        result = set_cenm_variables(deployment_name, slogan)
    else:
        result = operations.set_enm_locations_flow(log.logger, deployment_name, slogan)

    if result:
        restart_services()

    return result


def fetch_private_key(deployment_name, slogan):
    """
    Flow that controls the fetching of the private key from DIT and storing to file

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    deployment_type, _ = get_dit_deployment_info(deployment_name)

    return operations.fetch_private_key_flow(log.logger, deployment_name, slogan) if "vENM" in deployment_type else True


def install_cluster_client(deployment_name, slogan):
    """
    Flow that controls the fetching of the private key from DIT and storing to file

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    deployment_type, dit_documents_info_dict = get_dit_deployment_info(deployment_name)
    is_proxy_required = operations.check_deployment_to_disable_proxy()

    return (setup_cluster_connection(deployment_name, dit_documents_info_dict, slogan, is_proxy_required)
            if "cENM" in deployment_type else True)


def is_cloudnative_namespace_found():
    """
    Determine if we are running on a Cloud Native deployment

    :returns: Boolean if Cloud Native deployment detected
    :rtype: bool
    """
    enm_namespace = None
    rc, stdout = commands.getstatusoutput(CLOUD_NATIVE_NAME_SPACE_CMD)
    if not rc and stdout:
        enm_namespace = stdout.split()[0]
    return bool(enm_namespace)


def update_local_kubectl_version(deployment_name, slogan):
    """
    Flow that updates the kubectl client version if it is diferent from server version on cENM

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    is_proxy_required = operations.check_deployment_to_disable_proxy()
    if is_cloudnative_namespace_found():
        response = compare_kubectl_client_and_server_version(deployment_name, slogan)
        if response:
            return install_kubectl_client(is_proxy_required, response)
    return True


def store_private_key_on_emp(deployment_name, slogan):
    """
    Flow that stores private key on EMP

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    deployment_type, _ = get_dit_deployment_info(deployment_name)

    return (operations.store_private_key_on_emp_flow(log.logger, deployment_name, slogan) if "vENM" in deployment_type
            else True)


def install_ddc(deployment_name, slogan):
    """
    Installs DDC package

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    deployment_type, _ = get_dit_deployment_info(deployment_name)
    is_proxy_required = operations.check_deployment_to_disable_proxy()
    if "cENM" in deployment_type:
        return packages.install_ddccore_release_package(deployment_name, slogan, is_proxy_required)

    return packages.install_ddc_flow(log.logger, deployment_name, slogan)


def configure_ddc_on_enm(deployment_name, slogan):
    """
    Configures DDC to collect diagnostics data from the workload server

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    deployment_type, dit_documents_info_dict = get_dit_deployment_info(deployment_name)

    if "cENM" in deployment_type:
        return create_ddc_secret_on_cluster(deployment_name, slogan, dit_documents_info_dict)

    return packages.configure_ddc_on_enm_flow(log.logger, deployment_name, slogan)


def setup_ddc_collection_of_workload_files(deployment_name, slogan):
    """
    Flow to enable DDC collection of profiles.log file

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    return packages.setup_ddc_collection_of_workload_files_flow(log.logger, deployment_name, slogan)


def get_wlvm_hostname_from_dit(deployment_name, slogan):
    """
    Flow to get the hostname of the workload VM

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    return operations.get_wlvm_hostname_from_dit_flow(log.logger, deployment_name, slogan)


def initialize_logger():
    """
    Initialize logging to file and to stdout
    """
    log.logger = logging.getLogger(TOOL_NAME)
    log.logger.handlers = []
    log.logger.setLevel(logging.DEBUG)

    check_log_dir()

    logfile_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler = logging.FileHandler('{0}/{1}.log'.format(LOG_DIR, TOOL_NAME))
    file_handler.setFormatter(logfile_formatter)
    file_handler.setLevel(logging.DEBUG)

    stdout_formatter = logging.Formatter('%(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(logging.INFO)

    log.logger.addHandler(file_handler)
    log.logger.addHandler(stdout_handler)


def check_log_dir():
    """
    Check that log dir exists (create if missing)
    """
    try:
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
    except Exception as e:
        raise SystemExit("Problem accessing log dir ({0}): {1}".format(LOG_DIR, e))


def signal_handler(signum, _):
    """
    Customized Signal Handler called when SIGINT signal received by script

    :param signum: SIGINT signal
    :type signum:
    :param _: *
    :type _: *
    """
    log.logger.info("Exiting ... Status: {0}\n".format(signum))
    sys.exit(signum)


def parse_arguments():
    """
    Function that builds the dictionary of arguments to be used by the script

    Note: This function does not use the docopt module because that module was not available in python2.6
    when this script was originally written. That is is the only available python version installed on the
    Workload VM servers by default and the original intention was to use that version.
    This is why argparse is being used here in this script.
    However, due to TORF-243354, the script was changed to run under Python 2.7 (packaged as part of TorUtils), but
    this function remains unchanged as no changes were needed.

    :return: Dictionary containing the arguments and options being used by the script
    :rtype: dict
    """
    mandatory_argument = "deployment_name"
    mandatory_argument_description = ("where {0} is the name of the Cloud Deployment as per DIT "
                                      "({1}/deployments) e.g. {2}".format(mandatory_argument.upper(),
                                                                          operations.DIT_URL,
                                                                          DEPLOYMENT_NAME_EXAMPLE))

    parser = optparse.OptionParser(prog=TOOL_NAME,
                                   usage="{0} {1} ( Options )".format(TOOL_NAME, mandatory_argument.upper()),
                                   epilog=mandatory_argument_description)

    parser.formatter.max_help_position = 50
    parser.formatter.width = 150

    parser.add_option('--all', help='Executes all options below', action="store_true")

    for operation_item in OPERATIONS:
        argument_name = "--{0}".format(operation_item[0])
        argument_description = operation_item[1]
        parser.add_option(argument_name, help=argument_description, action="store_true")

    (options, arguments) = parser.parse_args()
    options_dict = options.__dict__

    if arguments and len(arguments) == 1:
        if not any([options_dict[option] for option in options_dict]):
            parser.error("At least one of the Options must be provided")

        options_dict[mandatory_argument] = arguments[0]
    else:
        parser.error("The script requires 1 argument ('{0}') ".format(mandatory_argument.upper()))

    return options_dict


def log_errors():
    """
    Function to log some errors

    """
    log.logger.error("\nError: Command line argument validation has failed.")
    log.logger.error("Please run the tool with '-h' or '--help' for full details about command line arguments "
                     "and supported values.\n")


def configure_cloud(argument_dict):
    """
    Function that handles the options passed to the script and calls the appropriate function whose name matches the
    option.

    :param argument_dict: Dictionary of all the possible option passed to the script
    :type argument_dict: dict
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    failures = 0
    deployment_name = argument_dict['deployment_name']
    operations.export_deployment_name(deployment_name)
    for operation_item in OPERATIONS:
        operation_name = operation_item[0]
        operation_description = operation_item[1]

        if ((argument_dict[operation_name] or argument_dict['all']) and
                not globals()[operation_name](deployment_name, operation_description)):
            failures += 1

    return False if failures else True


def cli():
    """
    Function that validates arguments and options passed to script

    """
    signal.signal(signal.SIGINT, signal_handler)
    initialize_logger()

    log.logger.info("{0}:-".format(ABOUT_TEXT))

    try:
        argument_dict = parse_arguments()
    except SystemExit as e:
        if str(e) != "0":
            log_errors()
        raise

    result_code = 1
    if argument_dict:
        try:
            success_configuring_environment = configure_cloud(argument_dict)
            if success_configuring_environment:
                result_code = 0
        except Exception as e:
            log.logger.error(
                "\nERROR: Unexpected exception occurred during configuration attempt: {0}{1}".format(e, operations.NL))
    else:
        log_errors()
        raise SystemExit

    if result_code != 0:
        log.logger.info("\nProblems encountered during script execution and requires investigation."
                        " {0}\n".format(LOG_PATH_INFO))

    return result_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cli())
