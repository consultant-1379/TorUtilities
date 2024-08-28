# ********************************************************************
# Name    : Automatic Software Update
# Summary : Part of the overall Flow Automation functionality being
#           introduced, existing functionality allows the user to
#           manage end to end flow of SHM operations.
#           Create flows, build flow json from template, create new
#           SHM software package, query flow status.
# ********************************************************************

import datetime
import json
import os
import pkgutil
import time

from jinja2 import Environment, FileSystemLoader
from retrying import retry

from enmutils.lib import filesystem, log, shell
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, JobValidationError, TimeOutError
from enmutils.lib.headers import ASU_CREATE_FLOW_HEADER
from enmutils_int.lib.enm_deployment import get_list_of_scripting_service_ips
from enmutils_int.lib.shm_utilities import SHMUtils
from enmutils_int.lib.shm_job import retry_if_job_validation_error

NEW_FLOW_URL = "/flowautomation/v1/flows/com.ericsson.oss.services.shm.asu.flow/execute"
FLOW_STATUS_URL = "/flowautomation/v1/executions/{0}/report?flow-id=com.ericsson.oss.services.shm.asu.flow"
INT_PACKAGE = pkgutil.get_loader("enmutils_int").filename
Env = Environment(loader=FileSystemLoader(os.path.join(INT_PACKAGE, "templates", "asu")))
ASU_STORE_DIR = "/home/enmutils/asu/{0}"
ASU_INFO = "asu_user_input.json"
ABSOLUTE_FILE_PATH = "{0}/{1}"
PACKAGE_PATH = os.path.join("/home", "enmutils", "shm")
asu_script_dir = os.path.join("/home", "shared", "ASU")
SCRIPTING_FILES = ["radioNodePreInstall.sh", "radioNodePreUpgrade.sh", "radioNodePostUpgrade.sh", "radioNodeCleanup.sh"]


class InvalidFlowException(Exception):
    pass


class FlowAutomation(object):

    def __init__(self, nodes, flow_name, user):
        self.nodes = nodes
        self.flow_name = flow_name
        self.user = user
        self.node_variants = None

    @staticmethod
    def get_template(template):
        """
        Returns the .json template

        :param template: Path to template to be returned
        :type template: str

        :return: returns the requested template
        :rtype: Template
        """
        log.logger.debug("Attempting to get required {0} for ASU flow creation".format(template))
        return Env.get_template(template)

    def prepare_asu_user_input_json_file(self, software_package_names):
        """
        Generates the asu_user_input_file.json

        :param software_package_names: software packages which has nodeType, nodevariant, package
        :type software_package_names: list
        :raises EnmApplicationError: when there is issue in creating asu input file
        """
        log.logger.debug("Starting ASU template file update with nodes and upgrade package details")
        asu_file_path = "{0}/{1}".format(ASU_STORE_DIR.format(self.flow_name), ASU_INFO)
        log.logger.debug("Attempting to update file {0} with nodes and package details".format(asu_file_path))
        node_ids = [node.node_id for node in self.nodes]
        software_package_json = json.dumps(software_package_names, indent=2, sort_keys=True)
        with open(asu_file_path, "w+") as asu_file:
            asu_file.write(self.get_template(ASU_INFO).render(node_ids=",".join(node_ids),
                                                              software_packages=software_package_json))
            asu_file.seek(0)
            log.logger.debug("ASU_Profile user input json file content is:\n{0}".format(asu_file.read()))
        log.logger.debug("Successfully updated file {0} with nodes and package details".format(asu_file_path))

    def prepare_software_package_json_for_asu_json_file(self, software_package):
        """
        Generates the asu_user_input_file.json

        :param software_package: new package which is created for upgrade
        :type software_package: str
        :return: returns software_package_list
        :rtype: list
        """
        software_package_json = {"nodeType": "RadioNode", "runningNodeVariant": "", "targetPackageName": ""}
        software_package_list = []
        for node_variant in self.node_variants:
            software_package_json["runningNodeVariant"] = node_variant
            software_package_json["targetPackageName"] = software_package
            temp_dict = software_package_json.copy()
            software_package_list.append(temp_dict)
        return software_package_list

    def create_flow(self, file_name, file_path):
        """
        Creates new flow in Flow-Automation application

        :param file_name: asu import file name used flow creation
        :type file_name: str
        :param file_path: asu import file absolute path used flow creation
        :type file_path: str
        :return: returns flow_name created or None
        :rtype: str
        :raises EnmApplicationError: when flow is not created correctly
        :raises HttpError: when response is not correct
        """
        log.logger.debug("Attempting to create ASU new flow with name {0}".format(self.flow_name))
        payload = {"name": self.flow_name, "file-name": file_name}
        files = {"flow-input": open(file_path, "rb")}
        response = self.user.post(NEW_FLOW_URL, data=payload, files=files, headers=ASU_CREATE_FLOW_HEADER)
        log.logger.debug("ASU_Profile_Flow_Creation response_status_code is: {0} and response_request_header is: {1}"
                         .format(response.status_code, response.request.headers))
        raise_for_status(response, message_prefix="Failed to create new flow with id {0}".format(self.flow_name))
        log.logger.debug("Completed creating ASU new flow with name {0}".format(self.flow_name))
        if "name" in response.json():
            return response.json()["name"]
        else:
            raise EnmApplicationError("Could not retrieve flow name from the response output {0}".format(response))

    def create_directory_structure(self, asu_folder):
        """
        Create a valid ASU directory structure
        :param asu_folder: path of asu tmp folder directory
        :type asu_folder: str
        """
        log.logger.debug("Attempting to create directory structure {0}".format(asu_folder))
        if not filesystem.does_dir_exist(asu_folder):
            filesystem.create_dir(asu_folder)
        log.logger.debug("Successfully created directory structure {0}".format(asu_folder))

    def execute_commands_in_scripting_vm(self, list_of_scripting_vms):
        """
        Executes the commands of directory check, empty file creation(pre-install, pre-upgrade, post-upgrade),
        inflate content into file, gives executable permissions to file for the scripting VM
        :param list_of_scripting_vms: list of scripting VM hostname or ip address
        :type list_of_scripting_vms: list
        :raises EnvironError: When scripting VM is not available in the deployment or
                            commands failed to execute in scripting VM
        """
        if list_of_scripting_vms:
            scripting_host = list_of_scripting_vms[0]
            log.logger.debug("List of available scripting VM's are: {0} and chosen scripting VM is {1}"
                             .format(list_of_scripting_vms, scripting_host))
            if is_enm_on_cloud_native():
                self.execute_commands_in_scripting_vm_in_cloud_native(scripting_host)
            else:
                self.execute_commands_in_scripting_vm_in_phy_or_cloud(scripting_host)
        else:
            raise EnvironError("Scripting VM is not available, Unable to create scripts in {0} directory"
                               .format(asu_script_dir))

    def execute_commands_in_scripting_vm_in_phy_or_cloud(self, scripting_host):
        """
        Executes the commands of directory check, empty file creation(pre-install, pre-upgrade, post-upgrade, cleanup),
        inflate content into file, gives executable permissions to file for the scripting VM of physical or cloud
        :param scripting_host: scripting VM hostname or ip address
        :type scripting_host: str
        :raises EnvironError: When scripting VM is not available in the deployment or
                            commands failed to execute in scripting VM
        """
        asu_dir_check = "sudo ls {0}".format(asu_script_dir)
        output_asu_dir_check = shell.run_cmd_on_vm(asu_dir_check, scripting_host)
        if output_asu_dir_check.rc != 0:
            asu_dir_create = "sudo mkdir -p {0}".format(asu_script_dir)
            output_asu_create_dir = shell.run_cmd_on_vm(asu_dir_create, scripting_host)
            if output_asu_create_dir.rc != 0:
                raise EnvironError(
                    "Directory {0} failed to create in scripting VM {1} and response code is {2}, response output "
                    "is {3}".format(asu_script_dir, scripting_host, output_asu_create_dir.rc,
                                    output_asu_create_dir.stdout))
        cmd_create_script_file_in_vm = "sudo touch {path};sudo chmod 777 {path};sudo echo 'amos $1 cvls' > {path}"
        for script in SCRIPTING_FILES:
            path = os.path.join(asu_script_dir, script)
            output_install_scripts = shell.run_cmd_on_vm(cmd_create_script_file_in_vm.format(path=path),
                                                         scripting_host)
            if output_install_scripts.rc == 0:
                log.logger.debug("{0} file created successfully with Read/write/Execute permissions in "
                                 "Scripting VM {1}".format(script, scripting_host))
            else:
                raise EnvironError("Command: {0} failed to execute in scripting VM {1}"
                                   .format(cmd_create_script_file_in_vm.format(path=path), scripting_host))

    def execute_commands_in_scripting_vm_in_cloud_native(self, scripting_host):
        """
        Executes the commands of directory check, empty file creation(pre-install, pre-upgrade, post-upgrade, cleanup),
        inflate content into file, gives executable permissions to file for the scripting VM of cloudnative
        :param scripting_host: scripting VM hostname or ip address
        :type scripting_host: str
        :raises EnvironError: When scripting VM is not available in the deployment or
                            commands failed to execute in scripting VM
        """
        asu_dir_check = shell.Command("ls {0}".format(asu_script_dir))
        output_asu_dir_check = shell.run_remote_cmd(asu_dir_check, scripting_host,
                                                    self.user.username, self.user.password)
        if output_asu_dir_check.rc != 0:
            asu_dir_create = shell.Command("mkdir -p {0}".format(asu_script_dir))
            output_asu_create_dir = shell.run_remote_cmd(asu_dir_create, scripting_host, self.user.username,
                                                         self.user.password)
            if output_asu_create_dir.rc != 0:
                raise EnvironError(
                    "Directory {0} failed to create in scripting VM {1} and response code is {2}, response output "
                    "is {3}".format(asu_script_dir, scripting_host, output_asu_create_dir.rc,
                                    output_asu_create_dir.stdout))
        cmd_create_script_file_in_vm = "touch {path};chmod 777 {path};echo 'amos $1 cvls' > {path}"
        for script in SCRIPTING_FILES:
            path = os.path.join(asu_script_dir, script)
            cmd = cmd_create_script_file_in_vm.format(path=path)
            output_install_scripts = shell.run_remote_cmd(shell.Command(cmd), scripting_host, self.user.username,
                                                          self.user.password)
            if output_install_scripts.rc == 0:
                log.logger.debug("{0} file created successfully with Read/write/Execute permissions in "
                                 "Scripting VM {1}".format(script, scripting_host))
            else:
                raise EnvironError("Command: {0} failed to execute in scripting VM {1}"
                                   .format(cmd_create_script_file_in_vm.format(path=path), scripting_host))

    def create_install_scripts_in_scripting_vm(self):
        """
        Creates Pre-Install, Pre-Upgrade, Post-Upgrade scripts in Scripting VM
        :raises EnvironError: When scripting VM is not listed or deployment unsupported
        """
        scripting_ips = get_list_of_scripting_service_ips()
        self.execute_commands_in_scripting_vm(scripting_ips)

    def check_status_and_wait_flow_to_complete(self, profile_object, flow_name):
        """
        Waits and checks for the flow status to be "COMPLETED"
        :param profile_object: profile object ASU_01
        :type profile_object: object
        :param flow_name: asu flow name used to check status
        :type flow_name: str
        :raises TimeOutError: when job state cannot be verified within given time
        :raises EnmApplicationError: when job status not in EXECUTING state
        """
        log.logger.debug("Attempting to get asu flow {0} status".format(flow_name))
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=profile_object.JOB_WAIT_TIME)
        while datetime.datetime.now() < expiry_time:
            asu_job = self._get_flow_response(flow_name).json()
            status = asu_job["header"]["status"]
            if status in ["COMPLETED"]:
                success_nodes = int(asu_job["body"]["reportSummary"]["numNodesSuccess"])
                total_nodes = int(asu_job["body"]["reportSummary"]["numberOfNodes"])
                if success_nodes == total_nodes:
                    log.logger.debug("Status of the ASU Flow Job {0} is {1} with {2} nodes".format(flow_name, status,
                                                                                                   success_nodes))
                else:
                    log.logger.debug("ASU_Profile Flow Execution failed with {0} nodes and json response of flow "
                                     "execution is:\n{1}".format(total_nodes - success_nodes, asu_job))
                    raise EnmApplicationError("Status of ASU Flow Job {0} is {1}, with {2} out of {3} nodes in"
                                              " SUCCESS state".format(flow_name, status, success_nodes, total_nodes))
                return
            elif status in ["FAILED_EXECUTE"]:
                raise EnmApplicationError("ASU Flow Job {0} in {1} state.".format(flow_name, status))
            elif status not in ["EXECUTING", "SETTING_UP", "CONFIRM_EXECUTE"]:
                raise EnmApplicationError("ASU Flow Job changed to unexpected status. HTTPResponse was {0}"
                                          .format(str(asu_job)))
            log.logger.debug("Sleeping for {0} seconds before re-trying..".format(30))
            time.sleep(30)
        raise TimeOutError("Cannot verify the status of flow {0}".format(flow_name))

    @retry(retry_on_exception=retry_if_job_validation_error, wait_fixed=60000, stop_max_attempt_number=3)
    def _get_flow_response(self, flow_name):
        """
        Attempt to retrieve the flow results using flow-name
        :param flow_name: asu flow name used to check status
        :type flow_name: str
        :return: response object
        :rtype:  list
        :raises JobValidationError: when unable to get flow status
        """
        flow_url = FLOW_STATUS_URL.format(flow_name)
        log.logger.debug("Attempting to get the flow status using URL {0}".format(flow_url))
        response = self.user.get(flow_url)
        if not response.ok:
            raise JobValidationError("Cannot get flow status, status was {0}"
                                     " text was {1}".format(response.status_code, response.text), response=response)
        response_output = response.json()
        validate_header = "header" not in response_output
        validate_body = "body" not in response_output
        validate_status = "header" in response_output and "status" not in response_output["header"]
        validate_report_summary = "body" in response_output and "reportSummary" not in response_output["body"]
        validate_nodes_count = ("body" in response_output and "reportSummary" in response_output["body"] and
                                "numNodesSuccess" not in response_output["body"]["reportSummary"] and
                                "numberOfNodes" not in response_output["body"]["reportSummary"])
        if any([validate_header, validate_body, validate_status, validate_report_summary, validate_nodes_count]):
            log.logger.debug("GET request to {0} returned no results. Retrying a max of 3 times.".format(flow_url))
            log.logger.debug("Sleeping 60 seconds before re-trying.")
            raise JobValidationError("GET request to {0} returned no results."
                                     "Max retries reached.".format(flow_url), response=response)
        log.logger.debug("Successfully fetched ASU job status using URL {0}".format(flow_url))
        log.logger.debug("Current Flow status and description:: {0}".format(response.json()["header"]))
        return response

    def get_new_radio_node_pkg(self, profile_name):
        """
        Attempt to create and import a new radionode software package

        :param profile_name: ASU_01 profile name
        :type profile_name: str

        :return: Newly created radionode package name
        :rtype:  str
        :raises EnmApplicationError: when creating software package
        """
        log.logger.debug("Starting creation of new radio node package")
        try:
            package = SHMUtils.create_and_import_software_package(self.user, self.nodes,
                                                                  profile_name=profile_name,
                                                                  local_path=PACKAGE_PATH)
            self.node_variants = getattr(package.get("software_package"), "node_variants")
        except Exception as e:
            raise EnmApplicationError("Error when creating new radionode package {0}".format(e))
        return getattr(package.get("software_package"), "new_package")

    def create_flow_automation(self, profile_object):
        """
        Utility function to create an ASU flow and check the status respectively
        :param profile_object: ASU_01 profile object
        :type profile_object: object
        """
        try:
            asu_folder = ASU_STORE_DIR.format(self.flow_name)
            log.logger.debug("Starting ASU FLOW CREATION PROCESS....")
            self.create_directory_structure(asu_folder)
            asu_package_name = self.get_new_radio_node_pkg(profile_object.NAME)
            log.logger.debug("ASU_Profile_Selected_Package is: {0}".format(asu_package_name))
            software_package_config = self.prepare_software_package_json_for_asu_json_file(asu_package_name)
            self.prepare_asu_user_input_json_file(software_package_config)
            self.create_install_scripts_in_scripting_vm()
            flow_name = self.create_flow(ASU_INFO, ABSOLUTE_FILE_PATH.format(asu_folder, ASU_INFO))
            log.logger.debug("Sleeping for 60 secs after ASU_FLOW_Creation via Rest call")
            time.sleep(60)
            self.check_status_and_wait_flow_to_complete(profile_object, flow_name)
            log.logger.debug("Completed ASU FLOW CREATION PROCESS.")
        except Exception as e:
            profile_object.add_error_as_exception(e)

    def delete_directory_structure(self):
        """
        Delete the ASU folder which was created earlier for generating json input file purpose
        """
        asu_folder = ASU_STORE_DIR.format(self.flow_name)
        if filesystem.does_dir_exist(asu_folder):
            filesystem.remove_dir(asu_folder)
