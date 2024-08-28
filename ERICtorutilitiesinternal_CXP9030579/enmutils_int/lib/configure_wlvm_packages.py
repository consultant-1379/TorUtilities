# ********************************************************************
# Name    : Configure WLVM Packages
# Summary : Functional module used by the workload configure tool.
#           Allows the workloadVM configure to manage DDC packages.
# ********************************************************************

import inspect
import subprocess
import commands

from enmutils.lib import log
import enmutils_int.lib.configure_wlvm_operations as operations
from enmutils_int.lib.configure_wlvm_common import (check_if_rpm_package_is_installed, perform_service_operation,
                                                    download_release_package_from_nexus, install_rpm_package)

NEXUS_URL = "https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/content/repositories/releases"

PACKAGES = {'ddc': {'name': "ERICddc_CXP9030294", 'nexus_path': "com/ericsson/cifwk/diagmon"},
            'ddccore': {'name': "ERICddccore_CXP9035927", 'nexus_path': "com/ericsson/oss/itpf/monitoring"}}

ATHTEM_DOMAINNAME = "athtem.eei.ericsson.se"
HTTPS_PROXY_URL = "atproxy1.{0}:3128".format(ATHTEM_DOMAINNAME)

DDC_FLAG_FILE = "/var/tmp/DDC_GENERIC"
PATH_TO_SCRIPTS = "/opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/external_sources/scripts"
DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE_SOURCE = "{}/ddc_plugin_for_workload.sh".format(PATH_TO_SCRIPTS)
DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE = "/root/ddc_plugin_for_workload"
DDC_PLUGINS_DIR = "/var/tmp/ddc_data/config/plugins"
DDC_PLUGIN_FOR_WORKLOAD_DAT_FILE = "{0}/workload.dat".format(DDC_PLUGINS_DIR)
DDC_SERVER_TXT_FILE_ON_ENM = "/var/ericsson/ddc_data/config/server.txt"

NL = "\n"


def create_ddc_flag_file(logger):
    """
    Creates DDC flag file

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate whether the operation was successful or not
    :rtype: bool
    """
    logger.info("Creating DDC flag file (%s) locally...%s", DDC_FLAG_FILE, NL)
    command_to_create_ddc_flag_file = "touch {0}".format(DDC_FLAG_FILE)
    try:
        response = subprocess.check_output(command_to_create_ddc_flag_file, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        return True
    else:
        logger.info("Problem encountered while creating DDC flag file with command:%s%s%s",
                    NL, command_to_create_ddc_flag_file, NL)
        return False


def configure_ddc_on_enm_flow(logger, deployment_name, slogan):
    """
    Configures DDC to collect diagnostics data from the workload server

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    if operations.check_if_file_exists(logger, operations.KEYPAIR_FILE_ON_WLVM):
        emp_external_ip_address = operations.get_emp_external_ip_address_from_bashrc(logger)

        if emp_external_ip_address:
            workload_fqdn = operations.get_workload_fqdn(logger)
            if workload_fqdn:
                return add_entry_to_server_txt_file_on_enm(logger, emp_external_ip_address, workload_fqdn)

    return False


def setup_ddc_collection_of_workload_files_flow(logger, deployment_name, slogan):
    """
    Flow to enable DDC collection of profiles.log file

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    if create_ddc_plugin_for_workload_script_file(logger) and create_ddc_plugin_for_workload_dat_file(logger):
        return True

    return False


def add_entry_to_server_txt_file_on_enm(logger, emp_external_ip_address, workload_fqdn):
    """
    Updates DDC's server.txt file with entry related to Workload server

    :param logger: Logging object
    :type logger: logging.Logger
    :param emp_external_ip_address: String containing EMP External IP Address
    :type emp_external_ip_address: str
    :param workload_fqdn: String containing hostname and domain name
    :type workload_fqdn: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    if operations.check_if_file_exists(logger, DDC_SERVER_TXT_FILE_ON_ENM, emp_external_ip_address):
        command_to_add_entry_to_ddc_file = ('''sudo sh -c \\"sed -i '/=WORKLOAD/d' {0}; echo '{1}=WORKLOAD' >> {0}\\"'''
                                            .format(DDC_SERVER_TXT_FILE_ON_ENM, workload_fqdn))
    else:
        command_to_add_entry_to_ddc_file = ('''sudo sh -c \\"echo '{1}=WORKLOAD' > {0}\\"'''
                                            .format(DDC_SERVER_TXT_FILE_ON_ENM, workload_fqdn))

    # Force pseudo terminal with "-tt" if tool called from within another script
    command_to_run_on_emp = ('ssh -tt -i {0} {1} cloud-user@{2} "{3} 2>&1" 2> /dev/null'
                             .format(operations.KEYPAIR_FILE_ON_WLVM, operations.SSH_OPTIONS, emp_external_ip_address,
                                     command_to_add_entry_to_ddc_file))

    logger.info("Adding WORKLOAD entry to %s ...%s", DDC_SERVER_TXT_FILE_ON_ENM, NL)
    try:
        response = subprocess.check_output(command_to_run_on_emp, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        logger.info("WORKLOAD Entry added")
        return True
    else:
        logger.info("Could not add entry to file %s using command:%s%s%s",
                    DDC_SERVER_TXT_FILE_ON_ENM, NL, command_to_run_on_emp, NL)
        return False


def create_ddc_plugin_for_workload_dat_file(logger):
    """
    Creates DDC plugin DAT file to references the DDC Plugin script file

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    logger.info("Checking that DDC package is installed: %s%s", DDC_PLUGIN_FOR_WORKLOAD_DAT_FILE, NL)
    if not (check_package_is_installed(logger, PACKAGES['ddccore']['name']) or
            check_package_is_installed(logger, PACKAGES['ddc']['name'])):
        logger.info("No DDC package installed - it needs to be installed first - re-run tool with install_ddc option\n")
        return False

    logger.info("Creating DDC Plugin folder: %s%s", DDC_PLUGINS_DIR, NL)
    command = 'mkdir -p {0}'.format(DDC_PLUGINS_DIR)
    try:
        response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s - %s", e, e.output)
        return False

    if not response.rstrip():
        logger.info("Plugin dir created\n")
    else:
        logger.info("Plugin dir not created: %s%s", DDC_PLUGINS_DIR, NL)
        return False

    logger.info("Creating DDC Plugin dat file: %s%s", DDC_PLUGIN_FOR_WORKLOAD_DAT_FILE, NL)
    command = "echo 'SCRIPT={0}' > {1}".format(DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE,
                                               DDC_PLUGIN_FOR_WORKLOAD_DAT_FILE)
    try:
        response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%sDDC package needs to be installed - %s", e, NL,
                    e.output)
        return False

    if not response.rstrip():
        logger.info("DDC Plugin dat file created\n")
        return True
    else:
        logger.info("DDC Plugin dat file not created: %s%s", DDC_PLUGIN_FOR_WORKLOAD_DAT_FILE, NL)
        return False


def create_ddc_plugin_for_workload_script_file(logger):
    """
    Creates DDC Plugin script to copy the profiles.log to the DDC output directory

    :param logger: Logging object
    :type logger: logging.Logger
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """

    logger.info("Creating DDC Plugin script file: %s%s", DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE, NL)
    command = "/bin/cp -p {0} {1}".format(DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE_SOURCE,
                                          DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE)
    try:
        response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        logger.info("Setting executable permissions on file... \n")
        command = "chmod 755 {0}".format(DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE)
        try:
            response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if not response.rstrip():
            logger.info("Ensuring script will run with bash... \n")
            command = "bash -n {0}".format(DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE)
            try:
                response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError as e:
                logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
                return False

            if not response.rstrip():
                logger.info("DDC Plugin script file created\n")
                return True

        else:
            logger.info("DDC Plugin script file permissions not set: %s%s",
                        DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE, NL)

    else:
        logger.info("DDC Plugin script file not created: %s%s", DDC_PLUGIN_FOR_WORKLOAD_SCRIPT_FILE, NL)

    return False


def get_package_version_in_enm_repo(logger, package_name):
    """
    Fetches the version of the package that is currently in the ENM repo

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :return: String containing version of package
    :rtype: str
    """
    package_version_in_enm_repo = ""

    emp_external_ip_address = operations.get_emp_external_ip_address_from_bashrc(logger)

    if emp_external_ip_address:
        command_to_query_enm_repo = ("/usr/bin/repoquery --qf  %{{version}} {package_name} | tail -1"
                                     .format(package_name=package_name))
        command_to_get_package_version_on_enm = ('ssh -i {0} {1} cloud-user@{2} "{3}"'
                                                 .format(operations.KEYPAIR_FILE_ON_WLVM, operations.SSH_OPTIONS,
                                                         emp_external_ip_address, command_to_query_enm_repo))
        logger.info("Fetching version of %s from ENM repo...%s", package_name, NL)
        try:
            response = subprocess.check_output(command_to_get_package_version_on_enm, stderr=subprocess.STDOUT,
                                               shell=True)
        except subprocess.CalledProcessError as e:
            logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
            return False

        if response.rstrip() and response.rstrip()[0].isdigit():
            package_version_in_enm_repo = response.rstrip()

        if not package_version_in_enm_repo:
            logger.info("Could not get version of %s from ENM repo using command:%s%s%s", package_name, NL,
                        command_to_get_package_version_on_enm, NL)

    return package_version_in_enm_repo


def check_package_is_installed(logger, package_name, package_version=None):
    """
    Checks to see if package of certain version is installed

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :param package_version: String containing version of package
    :type package_version: str
    :return: Boolean to indicate whether the package is installed or not
    :rtype: bool
    """
    if package_version:
        command_to_check_package_installed = "rpm -qa | egrep {0} | egrep -c {1}".format(package_name, package_version)
        version_msg = ", version {0} ".format(package_version)
    else:
        command_to_check_package_installed = "rpm -qa | egrep -c {0}".format(package_name)
        version_msg = ""

    logger.info("Checking to see if package %s%s is installed ...%s(%s)", package_name,
                version_msg, NL, command_to_check_package_installed)
    try:
        response = subprocess.check_output(command_to_check_package_installed, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Package not installed: %s%s", e, NL)
        return False

    if response.rstrip() and response.rstrip() != "0":
        logger.info("Package is installed\n")
        start_ddc_service(logger)
        return True
    else:
        logger.info("Problem encountered checking install of package using command:%s%s%s", NL,
                    command_to_check_package_installed, NL)
        return False


def start_ddc_service(logger):
    """
    Starts the DDC service if needed

    :param logger: Logging object
    :type logger: logging.Logger
    """
    logger.info("Checking ddc service to see if it needs to be started")
    status_command = "service ddc status"

    try:
        response = subprocess.check_output(status_command, stderr=subprocess.STDOUT, shell=True)
        logger.info("DDC Service status: {0}".format(response.rstrip()))
    except subprocess.CalledProcessError as e:
        if "DDC not running" in e.output:
            logger.info("Service installed but not running. Starting ddc service now")
            start_command = "service ddc start"
            try:
                response = subprocess.check_output(start_command, stderr=subprocess.STDOUT, shell=True)
                logger.info("Result: {0}".format(response.rstrip()))
            except subprocess.CalledProcessError as e:
                logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        else:
            logger.info("Service not installed: %s%s - %s", e, NL, e.output)


def remove_old_rpm_versions(logger, package_name):
    """
    Removes old versions of a particular package from the server

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :return: Boolean to indicate whether the operation was successful or not
    :rtype: bool
    """
    command_to_remove_old_rpm_versions = "rm -f {0}/{1}.*rpm".format(operations.STORAGE_PATH, package_name)
    logger.info("Removing any stored versions of %s package in %s...%s", package_name, operations.STORAGE_PATH, NL)
    try:
        response = subprocess.check_output(command_to_remove_old_rpm_versions, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if not response.rstrip():
        return True
    else:
        logger.info("Problem encountered removing old packages with command: %s%s",
                    command_to_remove_old_rpm_versions, NL)
        return False


def fetch_package_from_nexus(logger, package_name, package_path, package_version):
    """
    Downloads package of a particular version from nexus

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :param package_version: String containing version of package
    :type package_version: str
    :param package_path: Path to package on Nexus
    :type package_path: str
    :return: Boolean to indicate whether the operation was successful or not
    :rtype: str
    """
    path_to_package_filename = "{0}/{1}-{2}.rpm".format(operations.STORAGE_PATH, package_name, package_version)
    path_to_rpm = "{0}/{1}/{0}-{1}.rpm".format(package_name, package_version)

    parameters_for_https_proxy = "-e use_proxy=yes -e https_proxy={0}".format(HTTPS_PROXY_URL)

    command_to_wget_rpm = ("wget -O {local_file_path} {nexus_url}/{appl_path}/{rpm_path} {proxy_parameters} 2>&1"
                           .format(local_file_path=path_to_package_filename, nexus_url=NEXUS_URL,
                                   appl_path=package_path, rpm_path=path_to_rpm,
                                   proxy_parameters=parameters_for_https_proxy))

    logger.info("Attempting to fetch package %s from Nexus via cmd: %s %s", package_name, command_to_wget_rpm, NL)
    try:
        response = subprocess.check_output(command_to_wget_rpm, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during fetch of package {0} using command:{1}{2}{1} - {3} - {4}"
                    .format(package_name, NL, command_to_wget_rpm, str(e), e.output))
        return False

    if response and "saved" in response:
        return True
    else:
        logger.info("Problem encountered during fetch of package {0} using command:{1}{2}{1}"
                    .format(package_name, NL, command_to_wget_rpm))
        return False


def install_package(logger, package_name, package_version):
    """
    Installs package of a particular version

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :param package_version: String containing version of package
    :type package_version: str
    :return: Boolean to indicate whether the operation was successful or not
    :rtype: bool
    """
    logger.info("Package %s is stored in following directory: %s%s", package_name, operations.STORAGE_PATH, NL)

    command_to_install_package = ("rpm -ivh {0}/{1}-{2}.rpm --nodeps"
                                  .format(operations.STORAGE_PATH, package_name, package_version))

    logger.info("Attempting to install %s package locally...%s", package_name, NL)
    try:
        response = subprocess.check_output(command_to_install_package, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    if response.rstrip():
        return check_package_is_installed(logger, package_name, package_version)
    else:
        logger.info("Problem encountered during install of packages using command:%s%s%s",
                    NL, command_to_install_package, NL)
        return False


def uninstall_package(logger, package_name):
    """
    Uninstalls package

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Package name
    :type package_name: str
    :return: Boolean to indicate whether the operation was successful or not
    :rtype: bool
    """
    command_to_uninstall_package = "rpm -e {0}".format(package_name)

    logger.info("Attempting to uninstall %s package ...%s", package_name, NL)
    try:
        subprocess.check_output(command_to_uninstall_package, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        logger.info("Problem encountered during command execution: %s%s - %s", e, NL, e.output)
        return False

    return not check_package_is_installed(logger, package_name)


def install_ddccore_release_package(deployment_name, slogan, is_proxy_required):
    """
    Installs Release version of DDCcore package

    :param deployment_name: Deployment Name
    :type deployment_name: str
    :param slogan: Description of operation
    :type slogan: str
    :param is_proxy_required: proxy is used to install the ddccore release package,
    when it was True. Otherwise, it will not use proxy.
    :type is_proxy_required: bool

    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    log.logger.info("Deployment: {0} - Option: {1}".format(deployment_name, slogan))

    package_name, nexus_path = PACKAGES["ddccore"]["name"], PACKAGES["ddccore"]["nexus_path"]
    file_path = "/tmp/{0}.rpm".format(package_name)

    log.logger.debug("Touching DDC flag file: {0}".format(DDC_FLAG_FILE))
    commands.getstatusoutput("touch {0}".format(DDC_FLAG_FILE))

    if (check_if_rpm_package_is_installed(package_name) or
            (download_release_package_from_nexus(package_name, nexus_path, file_path, is_proxy_required) and
             install_rpm_package(file_path))):

        if not perform_service_operation("ddc", "status"):
            perform_service_operation("ddc", "start")

        log.logger.info("Package ddccore installation operation has completed successfully")
        return True

    log.logger.info("Package ddccore installation failed")


def install_ddc_flow(logger, deployment_name, slogan):
    """
    Installs DDC or DDC Core package

    :param logger: Logging object
    :type logger: logging.Logger
    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: String
    :param slogan: String from OPERATIONS that corresponds to script option that matches name of this function
    :type slogan: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Deployment: %s%sOption: %s - %s%s", deployment_name, NL, inspect.stack()[0][3], slogan, NL)

    logger.info("Attempting to connect to ENM to get package versions from repo there...")
    if operations.check_if_file_exists(logger, operations.KEYPAIR_FILE_ON_WLVM):
        ddccore_version_in_enm_repo = get_package_version_in_enm_repo(logger, PACKAGES['ddccore']['name'])
        ddc_version_in_enm_repo = get_package_version_in_enm_repo(logger, PACKAGES['ddc']['name'])

        if ddccore_version_in_enm_repo:
            logger.info("DDC Core package found in ENM repo")
            return install_ddccore_package(logger, ddccore_version_in_enm_repo)
        else:
            logger.info("DDC Core package not found in ENM repo")
            return install_ddc_package(logger, ddc_version_in_enm_repo)

    return False


def install_ddccore_package(logger, ddccore_version_in_enm_repo):
    """
    Installs DDC Core package if not already installed

    :param logger: Logging object
    :type logger: logging.Logger
    :param ddccore_version_in_enm_repo: Package Version
    :type ddccore_version_in_enm_repo: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    if check_package_is_installed(logger, PACKAGES['ddccore']['name']):
        logger.info("DDC Core package already installed on workload VM.")
        return True
    if check_package_is_installed(logger, PACKAGES['ddc']['name']):
        logger.info("DDC package already installed on workload VM - Removing")
        if not uninstall_package(logger, PACKAGES['ddc']['name']):
            return False

    return fetch_and_install_package(logger, PACKAGES['ddccore']['name'], PACKAGES['ddccore']['nexus_path'],
                                     ddccore_version_in_enm_repo)


def install_ddc_package(logger, ddc_version_in_enm_repo):
    """
    Installs DDC package if not already installed

    :param logger: Logging object
    :type logger: logging.Logger
    :param ddc_version_in_enm_repo: Package Version
    :type ddc_version_in_enm_repo: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    logger.info("Checking if DDC package installed on Workload VM")
    if check_package_is_installed(logger, PACKAGES['ddc']['name']):
        return True

    return fetch_and_install_package(logger, PACKAGES['ddc']['name'], PACKAGES['ddc']['nexus_path'],
                                     ddc_version_in_enm_repo)


def fetch_and_install_package(logger, package_name, package_path, package_version_in_repo):
    """
    Fetches Package from Nexus and Installs the same package

    :param logger: Logging object
    :type logger: logging.Logger
    :param package_name: Name of package
    :type package_name: str
    :param package_path: Path to package on Nexus
    :type package_path: str
    :param package_version_in_repo: Package Version
    :type package_version_in_repo: str
    :return: Boolean to indicate success or failure of operation
    :rtype: bool
    """
    if (remove_old_rpm_versions(logger, package_name) and
            fetch_package_from_nexus(logger, package_name, package_path, package_version_in_repo) and
            create_ddc_flag_file(logger)):
        return install_package(logger, package_name, package_version_in_repo)

    return False
