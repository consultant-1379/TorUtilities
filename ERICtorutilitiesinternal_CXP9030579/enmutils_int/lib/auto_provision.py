# ********************************************************************
# Name    : Auto Provision
# Summary : Primary module for interacting with the Auto Provision
#           application - CMCLI only. Allows the user to view, query,
#           delete, order or integrate compatible projects.
# ********************************************************************

import re
import time

from enmutils.lib import log, shell
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.enm_node_management import CmManagement, FmManagement, PmManagement, ShmManagement
from enmutils.lib.exceptions import EnvironError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils_int.lib.enm_deployment import get_values_from_global_properties, get_pod_hostnames_in_cloud_native
from enmutils_int.lib import common_utils, load_node
from enmutils_int.lib.amos_executor import check_ldap_is_configured_on_radio_nodes
from enmutils_int.lib.services import deployment_info_helper_methods
from retrying import retry


CREATE_NE_CMD = ('cmedit create NetworkElement={node_name} networkElementId={node_id}, neType={primary_type}, '
                 'ossPrefix="{oss_prefix}", timeZone=GMT -ns=OSS_NE_DEF -version=2.0.0')
CREATE_CONNECTIVITY_CMD = ('cmedit create NetworkElement={node_name},ComConnectivityInformation=1 '
                           'ComConnectivityInformationId=1, ipAddress="{node_ip}", port=6513, '
                           'transportProtocol="TLS", snmpAgentPort=161, snmpSecurityLevel=NO_AUTH_NO_PRIV, '
                           'snmpSecurityName=mediation, snmpVersion=SNMP_V3, snmpReadCommunity=public, '
                           'snmpWriteCommunity=public  -ns=COM_MED -version=1.1.0')
CREATE_SECURITY_CMD = ('secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                       '"{secure_password}" -n "{node_name}"')
CREATE_SNMP_CMD = ('secadm snmp authpriv --auth_algo NONE --auth_password "None" --priv_algo NONE '
                   '--priv_password "None" -n "{node_name}"')
DELETE_NRM_DATA_CMD = 'cmedit action NetworkElement={node_name},CmFunction=1 deleteNrmDataFromEnm'
DELETE_NE_CMD = 'cmedit delete NetworkElement={node_name} -ALL'


class AutoProvision(object):

    LICENCE = 'AP_FAT1023077.txt'
    DELETE_CMD = "ap delete {argument}"
    VIEW_CMD = "ap view {argument}"
    STATUS_CMD = "ap status {argument}"
    ORDER_CMD = "ap order {argument}"
    DOWNLOAD_CMD = "ap download {argument} {artifact_or_nodes}"

    COMECIM_NAMING = ['svc_CM_vip_ipaddress',
                      'cd /tmp/node-discovery-ecim-test-client/bin/sh/ ; ./ecim-node-up.sh']
    SUPPORTED_TYPES = ['RadioNode']

    def __init__(self, user, project_name=None, nodes=None, profile=None):
        """
        Constructor for  object

        :type user : enm_user.User object
        :param user: user we use to create the Role
        :type project_name: str
        :param project_name: String identifier of an existing project
        :type profile: enmutils_int.lib.Profile
        :param profile: Profile object to persist
        :type nodes: `enm_node.Node` instance
        :param nodes: node object to perform download action upon
        """
        self.user = user
        self.project_name = project_name
        self.nodes = nodes
        self.profile = profile

    @classmethod
    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=6000, stop_max_attempt_number=3)
    def delete_nodes_from_enm(cls, user, nodes):
        """
        Deletes `enm_node.Node` instances from ENM

        :type user: `enm_user_2.User`
        :param user: Enm user who will perform the deletion
        :type nodes: list
        :param nodes: List of `load_node.LoadNodeMixin` instances
        """
        for node in nodes:
            cmd = "cmedit get NetworkElement={0}"
            response = user.enm_execute(cmd.format(node.node_id))
            if '0 instance(s)' not in response.get_output():
                cls._unmanage_delete_node(node, user)
                time.sleep(5)
            response = user.enm_execute(cmd.format(node.node_name))
            if '0 instance(s)' not in response.get_output():
                log.logger.debug("Secondary check for node before deletion, response\t{0}"
                                 .format(response.get_output()[0]))
                ap_node = load_node.BaseLoadNode(node_id=node.node_name)
                cls._unmanage_delete_node(ap_node, user)

    @classmethod
    def _unmanage_delete_node(cls, node, user):
        """
        Disable supervision and delete the supplied node

        :param node: Load node object to be unmanaged and deleted
        :type node: load_node.LoadNodeMixin`
        :param user: User who will execute the commands in ENM
        :type user: `enm_user_2.User`

        :raises EnmApplicationError: raised if the node operation fails
        """
        try:
            cls.disable_supervision_and_delete_node(user, node)
        except Exception as e:
            raise EnmApplicationError("Failed to unmanage, delete nodes correctly: {0}".format(str(e)))

    @classmethod
    def disable_supervision_and_delete_node(cls, user, node):
        """
        Delete NetworkElement from ENM

        :param user: User who will execute the commands in ENM
        :type user: `enm_user_2.User`
        :param node: Node to disable supervision by ENM
        :type node: `enm_node.Node`
        """
        cls.toggle_supervision(node, user, operation="unsupervise")
        commands = [DELETE_NRM_DATA_CMD.format(node_name=node.node_name),
                    DELETE_NE_CMD.format(node_name=node.node_name)]
        for cmd in commands:
            response = user.enm_execute(cmd)
            log.logger.debug("Command response\t{0}".format(response.get_output()))

    def populate_nodes_on_enm(self):
        """
        Populate nodes on ENM that project has deleted. (Currently only RadioNode)
        """
        for node in self.nodes:
            try:
                self.create_and_supervise_node(node)
            except Exception as e:
                log.logger.debug("Encountered exception with populate operation: {0}".format(str(e)))

    def create_and_supervise_node(self, node):
        """
        Create the NetworkElement in ENM

        :param node: Node to create in ENM
        :type node: `enm_node.Node`
        """
        commands = [CREATE_NE_CMD.format(node_name=node.node_name, node_id=node.node_id,
                                         primary_type=node.primary_type, oss_prefix=node.oss_prefix),
                    CREATE_CONNECTIVITY_CMD.format(node_name=node.node_name, node_ip=node.node_ip),
                    CREATE_SECURITY_CMD.format(node_name=node.node_name, secure_user=node.secure_user,
                                               secure_password=node.secure_password),
                    CREATE_SNMP_CMD.format(node_name=node.node_name)]
        for cmd in commands:
            response = self.user.enm_execute(cmd)
            log.logger.debug("Command response\t{0}".format(response.get_output()))
        try:
            self.poll_until_enm_can_retrieve_network_element(node)
        except EnmApplicationError as e:
            log.logger.debug("Failed to query ENM for NetworkElement value, error encountered: [{0}]".format(
                str(e)))
        self.toggle_supervision(node, self.user)

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_exponential_multiplier=5000,
           stop_max_attempt_number=3)
    def poll_until_enm_can_retrieve_network_element(self, node):
        """
        Poll ENM for the NetworkElement

        :param node: Node object to be used to query ENM
        :type node: `enm_node.BaseNode`

        :raises EnmApplicationError: raised if the NetworkElement command fails or is not found.
        """
        cmd = "cmedit get {0}".format(node.node_id)
        try:
            response = self.user.enm_execute(cmd)
            if "1 instance(s)" not in response.get_output():
                raise EnmApplicationError("NetworkElement for node {0} not found, attempting retry.".format(
                    node.node_id))
            log.logger.debug("NetworkElement for node {0} found.".format(node.node_id))
        except Exception as e:
            raise EnmApplicationError(str(e))

    @classmethod
    def toggle_supervision(cls, node, user, operation="supervise"):
        """
        Toggle supervision on the node, Enables CM, FM  and PM Management

        :param node: Node to enable supervision by ENM
        :type node: `enm_node.Node`
        :param user: User who will execute the commands in ENM
        :type user: `enm_user_2.User`
        :param operation: The operations to perform, valid options supervise|unsupervise
        :type operation: str
        """
        object_functions = [getattr(PmManagement.get_management_obj(nodes=[node], user=user), operation),
                            getattr(CmManagement.get_management_obj(nodes=[node], user=user), operation),
                            getattr(FmManagement.get_management_obj(nodes=[node], user=user), operation)]
        if operation == "unsupervise":
            object_functions.insert(2, getattr(ShmManagement.get_management_obj(nodes=[node], user=user), operation))
        for object_function in object_functions:
            try:
                object_function()
            except ScriptEngineResponseValidationError as e:
                log.logger.debug(str(e))

    @staticmethod
    def _check_response(expected, response, msg):
        if any(expected.upper() in value.upper() for value in response.get_output()):
            raise ScriptEngineResponseValidationError("Failed to %s. Response was: %s" %
                                                      (msg, ' '.join(response.get_output())), response=response)

    def _teardown(self):
        """
        Secret teardown method
        """
        try:
            self.delete_project()
        except Exception as e:
            log.logger.debug("Failed to delete project, response: {}".format(e.message))
        finally:
            self.populate_nodes_on_enm()
            try:
                check_ldap_is_configured_on_radio_nodes(self.profile, self.user, self.nodes, self.project_name)
            except Exception as e:
                raise EnmApplicationError("Problem Encountered when configuring LDAP on nodes.Exception: {0}".format(e))
            path = common_utils.get_internal_file_path_for_import("etc", "data", self.project_name)
            try:
                cmd = shell.Command('rm -rf {0}.zip'.format(path))
                shell.run_local_cmd(cmd)
            except Exception as e:
                raise EnvironError("Failed to delete project .zip, Exception: {0}".format(e.message))

    def import_project(self, file_name):
        """
        Import is used to import a Standard Project File or Batch Project File into ENM

        :type file_name: str
        :param file_name: String representation of the given .zip file

        :raises EnvironError: raised if an invalid project name is supplied

        :return: Response from the command execution
        :rtype: list
        """
        if not self.project_name:
            raise EnvironError("Invalid file path provided, unable to import project.")
        project = common_utils.get_internal_file_path_for_import("etc", "data", file_name)
        response = self.execute_safe_command(self.ORDER_CMD.format(argument="file:{0}".format(file_name)),
                                             file_in=project)
        self._check_response('Error', response, "import project")
        return response.get_output()

    def delete_project(self, node=None, retain_ne=False):
        """
        Delete is used to delete a project or node from AP in ENM

        :type node: `enm_node.Node` instance
        :param node: node object to perform download action upon
        :type retain_ne: bool
        :param retain_ne: Boolean value to determine whether or not to retain the network element on the enm instance

        :raises EnvironError: raised if project name is none

        :return: Response from the command execution
        :rtype: list
        """
        if not self.project_name:
            raise EnvironError("Could not determine project name, please ensure project was correctly created.")
        argument = "-n {0}".format(node.node_id) if node else "-p {0}".format(self.project_name)
        if retain_ne:
            argument = "-i {0}".format(argument)
        response = self.execute_safe_command(self.DELETE_CMD.format(argument=argument))
        self._check_response("Error", response, "delete project")
        return response.get_output()

    def download_artifacts(self, artifact=None, node=None, ordered=False, timeout=None):
        """
        Download is used to download node related sample and schema artifacts,
        imported artifacts or artifacts generated during the ordering of a node.

        :type artifact: str
        :param artifact: String representation of the artifact requested for download, i.e ERBS, RadioNode
        :type node: `enm_node.Node` instance
        :param node: node object to perform download action upon
        :type ordered: bool
        :param ordered: Boolean to indicate if the node has been ordered for integration
        :param timeout: number of seconds to wait for command to respond
        :type timeout: int

        :raises ValueError: raised if artifact and node are none

        :return: Response from the command execution
        :rtype: list
        """
        if not artifact and not node:
            raise ValueError("At least one, of type artifact or node required to perform download.")

        argument = "-o -n" if ordered else "-i -n"
        if not node:
            argument = "-x"
        artifact_or_nodes = node.node_id if node else artifact
        response = self.execute_safe_command(self.DOWNLOAD_CMD.format(argument=argument,
                                                                      artifact_or_nodes=artifact_or_nodes),
                                             timeout=timeout)
        self._check_response("Error", response, "download artifact")
        return response.get_output()

    def view(self, view_all=False, node=None, timeout=None):
        """
        View is used to display a list of all projects, individual project details or node details.

        :type view_all: bool
        :param view_all: Boolean condition to determine if view all is required
        :type node: `enm_node.Node` instance
        :param node: `enm_node.Node` object to perform status action upon
        :param timeout: number of seconds to wait for command to respond
        :type timeout: int

        :raises: ScriptEngineResponseValidationError

        :return: Response from the command execution
        :rtype: list
        """
        argument = "-n {0}".format(node.node_id) if node else "-p {0}".format(self.project_name)
        if view_all:
            argument = ""
        response = self.execute_safe_command(self.VIEW_CMD.format(argument=argument), timeout=timeout)
        self._check_response("Error", response, "view project details")
        return response.get_output()

    def status(self, status_all=False, node=None, timeout=None):
        """
        Status is used to display the current integration status of all projects,
        individual projects or individual nodes.

        :type status_all: bool
        :param status_all: Boolean condition to determine if status all is required
        :type node: `enm_node.Node` instance
        :param node: `enm_node.Node` object to perform status action upon
        :param timeout: number of seconds to wait for command to respond
        :type timeout: int

        :return: Response from the command execution
        :rtype: list
        """
        argument = "-n {0}".format(node.node_id) if node else "-p {0}".format(self.project_name)
        if status_all:
            argument = ""
        response = self.execute_safe_command(self.STATUS_CMD.format(argument=argument), timeout=timeout)
        self._check_response("Error", response, "status project details")
        log.logger.debug("Recorded response is : {0}".format(response.get_output()))
        return response.get_output()

    def order(self, node=None):
        """
        Order is used to order integration for a project or a node

        :type node: `enm_node.Node` instance
        :param node: node object to perform order action upon

        :return: Response from the command execution
        :rtype: list
        """
        argument = "-n {0}".format(node.node_id) if node else "-p {0}".format(self.project_name)
        response = self.execute_safe_command(self.ORDER_CMD.format(argument=argument))
        self._check_response("Error", response, "order project")
        return response.get_output()

    def execute_safe_command(self, command, file_in=None, timeout=600):
        """
        Execute the provided command handling exceptions

        :param command: Command to be executed on ENM
        :type command: str
        :param file_in: Path to file
        :type file_in: str
        :param timeout: number of seconds to wait for command to respond
        :type timeout: int

        :raises EnmApplicationError: raised if command execution fails on ENM

        :return: Response received from ENM
        :rtype: response object
        """
        try:
            return self.user.enm_execute(command, file_in=file_in, timeout_seconds=timeout)
        except Exception as e:
            raise EnmApplicationError(str(e))

    def integrate_node(self, node=None):
        """
        Attempts to integrate the project nodes, or user provided node

        :type node: `enm_node.Node` instance
        :param node: node object to perform integrate action upon
        """
        if not node:
            for node in self.nodes:
                self._send_node_up(node)
        self._send_node_up(node)

    def exists(self):
        """
        Check if the project exists in ENM cli

        :rtype: bool
        :return: boolean
        """
        exists = False
        try:
            if any(self.project_name in line for line in self.view(view_all=True)):
                exists = True
        except Exception as e:
            log.logger.debug("Exception occurred when querying ENM for project details. Response: {}".format(str(e)))
        return exists

    def validate_response(self, response):
        """
        Validates the node-up command response

        :param response: a shell.response object
        :type response: Response

        :raises EnvironError: raised if command execution fails
        """
        if (any([re.search(r'\s*error|failed\s*', response.stdout, re.I)]) and
                "Error creating SnmpIpv6Address" not in response.stdout):
            raise EnvironError("Failed to send Node up notification, Response was {0}".format(response.stdout))
        elif "Error creating SnmpIpv6Address" in response.stdout:
            log.logger.info("Error creating SnmpIpv6Address : Invalid String arg. \n The above statement is result of "
                            "third party tool which gives this string as a response for ipv6 nodes used by design. "
                            "This error can be ignored")

    def _send_node_up(self, node):
        """
        Sends the node up notification to the naming service

        :type node: `enm_node.Node` instances
        :param node: node object to perform node up action upon

        :raises EnvironError: raised if command execution fails
        """
        log.logger.debug("Attempting to send node-up notification for {0}".format(node.node_name))
        if node.primary_type not in self.SUPPORTED_TYPES:
            return
        cmd_params = {
            self.SUPPORTED_TYPES[0]: self.COMECIM_NAMING
        }
        service_ip_identifier = cmd_params.get(node.primary_type)[0]
        naming_service_ip_info = ([deployment_info_helper_methods.get_cloud_native_service_vip('mscm')] if is_enm_on_cloud_native() else get_values_from_global_properties(service_ip_identifier))
        if not naming_service_ip_info or not len(naming_service_ip_info):
            raise EnvironError("Failed to get naming service ip from global properties")
        cmd = '{0} {1} {2} {3}'.format(cmd_params.get(node.primary_type)[1], naming_service_ip_info[0], node.node_ip,
                                       node.node_name)
        if is_enm_on_cloud_native():
            ap_serv_hostnames = get_pod_hostnames_in_cloud_native("apserv")
            response = shell.run_cmd_on_cloud_native_pod('apserv', ap_serv_hostnames[0], cmd)
        else:
            response = shell.run_cmd_on_emp_or_ms(cmd=cmd, **{'timeout': 60})
        self.validate_response(response)
        log.logger.debug("Successfully node-up notification has been sent for {0}".format(node.node_name))
