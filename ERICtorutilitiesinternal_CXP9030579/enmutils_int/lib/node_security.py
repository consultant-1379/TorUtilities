# ********************************************************************
# Name    : Node Security
# Summary : Primarily used by Node Security Profiles. Allows the user
#           to perform CRUD operations in various areas of Node
#           security, mainly credential management, trust level
#           certificates, security certificates, SSH key generation,
#           IPSec (IP Security) and management of Security levels,
#           1,2,3, basic querying of security credential information.
# ********************************************************************

import datetime
import math
import os
import re
import time

import lxml.etree as et
from retrying import retry

from enmutils.lib import log, filesystem, config
from enmutils.lib.kubectl_commands import CHECK_SERVICES_CMD_ON_CN
from enmutils.lib.enm_node import get_enm_network_element_sync_states
from enmutils.lib.enm_node_management import FmManagement
from enmutils.lib.exceptions import (EnvironError, ScriptEngineResponseValidationError,
                                     TimeOutError, ValidationError, EnmApplicationError, DependencyException)
from enmutils.lib.headers import SECURITY_REQUEST_HEADERS
from enmutils.lib.shell import Command, run_local_cmd, run_cmd_on_ms, run_cmd_on_vm
from enmutils.lib.cache import is_enm_on_cloud_native, get_enm_cloud_native_namespace, is_emp, get_emp
from enmutils_int.lib.services.nodemanager_helper_methods import node_pool_mgr, persist_node

SECURITY_LEVEL_SET_CMD = 'secadm sl set -l {security_level} -xf file:{xml_file}'
SECURITY_LEVEL_GET_CMD = 'secadm sl get -n "{node_id}"'
SECURITY_LEVEL_GET_VERIFICATION = "Command Executed Successfully"
SLEEP_TIME = 100
MAX_POLL = 10

NODE_SECURITY_CMDS = {
    "SET_NODE_SECURITY_CMDS": {'secadm credentials create --rootusername "{secure_user}" --rootuserpassword '
                               '"{secure_password}" --secureusername "{secure_user}" --secureuserpassword '
                               '"{secure_password}" --normalusername "{normal_user}" --normaluserpassword '
                               '"{normal_password}" -n "{node_id}"': ['MINI-LINK-CN810R1', 'MINI-LINK-CN510R2',
                                                                      'MINI-LINK-6352', 'MINI-LINK-Indoor',
                                                                      'MINILink810R2Node'],
                               'secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                               '"{secure_password}" --nwieasecureusername "{secure_user}" --nwieasecureuserpassword '
                               '{secure_password} --nwiebsecureusername "{secure_user}" --nwiebsecureuserpassword '
                               '{secure_password} -n {node_id}': ['BSC'],
                               'secadm credentials create --secureusername {secure_user} --secureuserpassword '
                               '{secure_password} --nodelist "{node_id}"': ['JUNIPER', 'JUNIPER-MX'],
                               'secadm credentials create --secureusername {secure_user} --secureuserpassword '
                               '{secure_password}  --nodelist "{node_id}"': ['SIU02', 'STN', 'TCU02', 'ESC',
                                                                             'ERS-SupportNode', 'CISCO'],
                               'secadm credentials create --rootusername root --rootuserpassword dummy '
                               '--secureusername "{secure_user}" --secureuserpassword "{secure_password}" '
                               '--normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n '
                               '"{node_id}"': ['FRONTHAUL-6020', 'ERBS', 'RBS', 'RNC', 'MGW'],
                               'secadm credentials create --rootusername admin --rootuserpassword admin '
                               '--secureusername admin --secureuserpassword admin --normalusername admin '
                               '--normaluserpassword admin -n "{node_id}"': ['FRONTHAUL-6080'],
                               'secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                               '"{secure_password}" -n "{node_id}"': ['EME', 'MTAS-TSP', 'vWMG', 'HSS-FE-TSP', 'SBG',
                                                                      'RadioNode', 'VPN-TSP', 'EPG', 'SGSN-MME',
                                                                      'C608', 'vMSC', 'CSCF-TSP', 'vEME', 'ECM', 'BSP',
                                                                      'MSRBS_V1', 'vWCG', 'MSC-DB-BSP', 'VEPG',
                                                                      'Router6274', 'IP-STP', 'MSC-BC-IS', 'Router6675',
                                                                      'CCN-TSP', 'WMG', 'DSC', 'MTAS', 'EPG-SSR',
                                                                      'CSCF', 'cSAPC-TSP', 'SAPC', 'SGSN',
                                                                      'MSC-BC-BSP', 'RadioTNode', 'vBGF', 'SBG-IS',
                                                                      'vIP-STP'],
                               'secadm credentials create --secureusername netsim --secureuserpassword netsim -n '
                               '{node_id}': ['EXTREME'], 'secadm credentials create --rootusername admin '
                                                         '--rootuserpassword authpassword --secureusername admin '
                                                         '--secureuserpassword authpassword --normalusername admin '
                                                         '--normaluserpassword authpassword -n '
                                                         '"{node_id}"': ['Switch-6391', 'Fronthaul-6392',
                                                                         'MINI-LINK-6351', 'MINI-LINK-PT2020'],
                               'secadm credentials create --secureusername netsim --secureuserpassword netsim -n '
                               'ManagementSystem={node_id}': ['ECI-LightSoft'],
                               'secadm credentials create --secureusername "{secure_user}" --secureuserpassword '
                               '"{secure_password}" --ldapuser disable -n "{node_id}"': ['Router6672']},
    "UPDATE_NODE_SECURITY_CMDS":
        {'secadm credentials update --rootusername admin --rootuserpassword authpassword '
         '--secureusername admin --secureuserpassword authpassword --normalusername admin '
         '--normaluserpassword authpassword -n "{node_id}"': ['Fronthaul-6392'],
         'secadm credentials update --secureusername netsim --secureuserpassword netsim -n '
         '{node_id}': ['EXTREME'],
         'secadm credentials update --secureusername "{secure_user}" --secureuserpassword '
         '"{secure_password}" -n "{node_id}"': ['EME', 'MTAS-TSP', 'vWMG', 'HSS-FE-TSP', 'SBG', 'RadioNode',
                                                'VPN-TSP', 'EPG', 'SGSN-MME', 'C608',
                                                'CSCF-TSP', 'vEME', 'BSP', 'MSRBS_V1', 'vWCG',
                                                'VEPG', 'BSC', 'Router6274', 'Router6675',
                                                'Router6672', 'CCN-TSP', 'WMG', 'DSC', 'MTAS',
                                                'EPG-SSR', 'CSCF', 'cSAPC-TSP', 'SAPC', 'SGSN',
                                                'RadioTNode', 'vBGF', 'SBG-IS'],
         'secadm credentials update --rootusername root --rootuserpassword dummy --secureusername '
         '"{secure_user}" --secureuserpassword  "{secure_password}" --normalusername '
         '"{normal_user}" --normaluserpassword "{normal_password}" -n "{node_id}"': ['vIP-STP'],
         'secadm credentials update --secureusername {secure_user} --secureuserpassword '
         '{secure_password} --nodelist "{node_id}"': ['SIU02', 'ECI-LightSoft', 'STN',
                                                      'TCU02', 'ESC', 'ERS-SupportNode',
                                                      'CISCO', 'JUNIPER'],
         'secadm credentials update --rootusername ericsson --rootuserpassword ericsson '
         '--secureusername "{secure_user}" --secureuserpassword "{secure_password}" '
         '--normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n '
         '"{node_id}"': ['MINI-LINK-CN810R1', 'MINI-LINK-CN510R2', 'Switch-6391',
                         'MINI-LINK-6352', 'MINI-LINK-Indoor', 'MINILink810R2Node',
                         'MINI-LINK-6351', 'MINI-LINK-PT2020'],
         'secadm credentials update --rootusername root  --rootuserpassword dummy '
         '--secureusername "{secure_user}"  --secureuserpassword "{secure_password}" '
         '--normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n '
         '"{node_id}"': ['IP-STP'],
         'secadm credentials update --secureusername  {secure_user} --secureuserpassword '
         '{secure_password} --nodelist "{node_id}"': ['JUNIPER-MX'],
         'secadm credentials update --rootusername root --rootuserpassword dummy '
         '--secureusername "{secure_user}" --secureuserpassword "{secure_password}" '
         '--normalusername "{normal_user}" --normaluserpassword "{normal_password}" -n '
         '"{node_id}"': ['FRONTHAUL-6020', 'vMSC', 'ERBS', 'ECM', 'MSC-DB-BSP', 'MSC-BC-IS', 'RBS', 'RNC',
                         'MSC-BC-BSP', 'MGW'],
         'secadm credentials update --rootusername "{root_user}" --rootuserpassword '
         '"{root_password}" --secureusername "{secure_user}" --secureuserpassword '
         '"{secure_password}" --normalusername "{normal_user}" --normaluserpassword '
         '"{normal_password}" -n "{node_id}"': ['FRONTHAUL-6080']}
}


def get_node_security_commands_based_on_node_type(node_type):
    """
    Returns a dictionary with set_node_security_cmd, update_node_security_cmd commands.

    :param node_type:
    :type node_type: string
    :returns: A dictionary contains set_node_security_cmd, update_node_security_cmd for given node_type
    :rtype: dict
    """
    node_security_commands = dict()
    set_node_security_cmd = [cmd[0] for cmd in NODE_SECURITY_CMDS['SET_NODE_SECURITY_CMDS'].iteritems()
                             if node_type in cmd[1]]
    node_security_commands["set_node_security_cmd"] = set_node_security_cmd[0] if set_node_security_cmd else ''
    update_node_security_cmd = [cmd[0] for cmd in NODE_SECURITY_CMDS['UPDATE_NODE_SECURITY_CMDS'].iteritems()
                                if node_type in cmd[1]]
    node_security_commands["update_node_security_cmd"] = (update_node_security_cmd[0] if update_node_security_cmd else '')

    return node_security_commands


def parse_tabular_output(script_engine_response, header_line=0, skip=None, separator='\t', borders=False, multiline=False):
    """
    Returns a dictionary from a script engine tabular response output

    :param script_engine_response: Response output from script engine
    :type script_engine_response: list
    :param header_line: The first line number to start reading from
    :type header_line: integer
    :param skip: Text row to be skipped
    :type skip: string
    :param separator: String to be used as field separator
    :type separator: string
    :param borders: Flag to enable removal of any trailing/leading occurrence of separator
    :type borders: boolean
    :param multiline: Flag to manage outputs where the same item is linked to multiple consecutive lines
    :type multiline: boolean

    :yields: A dictionary built with first row headers as the keys
    :rtype: dict
    """

    index = header_line
    headers = _get_values_from_row(script_engine_response[index], separator=separator, borders=borders)
    item = "Unknown"
    for line in script_engine_response[index + 1:]:
        if line not in ('', skip):
            values = _get_values_from_row(line, separator=separator, borders=borders)
            if len(values) == len(headers):
                if multiline:
                    if values[0] != "":
                        item = values[0]
                    else:
                        values[0] = item
                yield dict(zip(headers, values))


def _get_values_from_row(row, separator, borders):
    """
    Gets the list of values from the response row

    :param row: Script engine row line
    :type row: string
    :param separator: String to be used as field separator
    :type separator: string
    :param borders: Flag to enable removal of any trailing/leading occurrence of separator
    :type borders: boolean
    :returns: List of values
    :rtype: list
    """

    border_string = separator if borders else ""
    return [val.strip() for val in row.strip(border_string).split(separator)]


class SecurityConfig(object):

    def __init__(self, algorithm='SHA1', mode='SCEP', key_size='RSA_2048', level=1, cert_type='OAM'):
        """
        Init method for config object, to hold configuration values to be used by Security object

        :type algorithm: str
        :param algorithm: String representation of the security algorithm to be used MD5,SHA1...
        :type cert_type: str
        :param cert_type: certificate type
        :type mode: str
        :param mode: Enrollment mode to be used
        :type key_size: str
        :param key_size: Size of the key to be generated
        :type level: int
        :param level: Security level, to which the given are requested to change to
        """
        self.algorithm = algorithm
        self.enrollment_mode = mode
        self.key_size = key_size
        self.level = level
        self.cert_type = cert_type


class NodeCredentials(object):

    CREATED_VERIFICATION = "All credentials were created successfully"
    UPDATED_VERIFICATION = "All credentials updated successfully"
    REMOVED_VERIFICATION = r"[1-9][0-9]* instance\(s\) deleted"

    REMOVE_NODE_SECURITY_CMD = 'cmedit delete NetworkElement={nodes_list},SecurityFunction=1 NetworkElementSecurity'
    GET_CREDENTIALS_CMD = 'secadm credentials get -n {node}'

    def __init__(self, nodes, user):
        """
        Constructor for NodeCredentials object

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param user: User object
        :type user: enm_user.User
        :param: NodeCredentials instance
        """

        self.nodes = nodes
        self.user = user
        self.secure_user = None
        self.secure_password = None
        self.normal_user = None
        self.normal_password = None
        node_security_commands = get_node_security_commands_based_on_node_type(nodes[0].primary_type)
        self.credentials_create_cmd = node_security_commands['set_node_security_cmd']
        self.credentials_update_cmd_default = node_security_commands['update_node_security_cmd']
        self.credentials_update_cmd = self.credentials_update_cmd_default
        self.credentials_remove_cmd = self.REMOVE_NODE_SECURITY_CMD
        self._attribute_list_default = ['secure_user', 'secure_password', 'normal_user', 'normal_password']
        self._attribute_list = list(self._attribute_list_default)
        self._modify_cmd = None
        self._modify_verification = None

    def create(self, secure_user, secure_password, normal_user, normal_password, permanent=True):
        """
        Creates the security credentials of the nodes

        :param secure_user: The secure username
        :type secure_user: string
        :param secure_password: The secure user password
        :type secure_password: string
        :param normal_user: The non secure username
        :type normal_user: string
        :param normal_password: The non secure user password
        :type normal_password: string
        :param permanent: Flag controlling whether credentials should be permanently stored to the workload nodes
        :type permanent: boolean
        """

        self.secure_user = secure_user
        self.secure_password = secure_password
        self.normal_user = normal_user
        self.normal_password = normal_password
        self._modify_cmd = self.credentials_create_cmd
        self._modify_verification = self.CREATED_VERIFICATION

        self._modify('create', permanent=permanent)

    def update(self, secure_user=None, secure_password=None, normal_user=None, normal_password=None, permanent=False):
        """
        Updates the security credentials of the nodes

        :param secure_user: The secure username
        :type secure_user: string
        :param secure_password: The secure user password
        :type secure_password: string
        :param normal_user: The non secure username
        :type normal_user: string
        :param normal_password: The non secure user password
        :type normal_password: string
        :param permanent: Flag controlling whether credentials should be permanently stored to the workload nodes
        :type permanent: boolean
        :raises RuntimeError: When security credentials are not available
        """

        self.secure_user = secure_user
        self.secure_password = secure_password
        self.normal_user = normal_user
        self.normal_password = normal_password

        self._attribute_list = list(self._attribute_list_default)
        self.credentials_update_cmd = self.credentials_update_cmd_default

        if not secure_user:
            self.credentials_update_cmd = self.credentials_update_cmd.replace(' --secureusername "{secure_user}"', '')
            self._attribute_list.remove('secure_user')
        if not secure_password:
            self.credentials_update_cmd = self.credentials_update_cmd.replace(' --secureuserpassword "{secure_password}"', '')
            self._attribute_list.remove('secure_password')
        if not normal_user:
            self.credentials_update_cmd = self.credentials_update_cmd.replace(' --normalusername "{normal_user}"', '')
            self._attribute_list.remove('normal_user')
        if not normal_password:
            self.credentials_update_cmd = self.credentials_update_cmd.replace(' --normaluserpassword "{normal_password}"', '')
            self._attribute_list.remove('normal_password')

        if not self._attribute_list:
            raise RuntimeError("Unable to update security credentials. At least one username or password must be specified.")

        self._modify_cmd = self.credentials_update_cmd
        self._modify_verification = self.UPDATED_VERIFICATION

        self._modify('update', permanent=permanent)

    def remove(self):
        """
        Removes the security credentials from the nodes
        """

        self._modify_cmd = self.credentials_remove_cmd
        self._modify_verification = self.REMOVED_VERIFICATION
        self._modify('remove')

    def restore(self):
        """
        Restores the original security credentials of the nodes
        """
        self._modify_cmd = self.credentials_update_cmd
        self._modify_verification = self.UPDATED_VERIFICATION
        for node in self.nodes:
            for attribute in self._attribute_list:
                setattr(self, attribute, getattr(node, attribute))
            self._modify('restore', node=node)

    def _modify(self, command, node=None, permanent=False):
        """
        Joint function to perform create/update/remove/restore operations for security credentials of the nodes

        :param command: The type of operation to perform (create, update, remove or restore)
        :type command: string
        :param node: Optional single node; if not present will use all the nodes - used by restore() function
        :type node: enm_node.Node object
        :param permanent: Flag controlling whether credentials should be permanently stored to the workload nodes
        :type permanent: boolean
        :raises ScriptEngineResponseValidationError: when security credentials are not available
        """

        nodes = [node] if node else self.nodes
        node_ids = '","'.join(node.node_id for node in nodes)

        if command == 'remove':
            self._modify_cmd = self.credentials_remove_cmd.format(nodes_list=node_ids.replace('","', ';NetworkElement='))

        response = self.user.enm_execute(
            self._modify_cmd.format(secure_user=self.secure_user, secure_password=self.secure_password, normal_user=self.normal_user, normal_password=self.normal_password, node_id=node_ids))
        if not any(re.search(self._modify_verification, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot {0} security credentials for nodes "{1}". Response was "{2}"'.format(
                    command, node_ids, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully {0}d security credentials for nodes "{1}"'.format(command, node_ids))

        if permanent:
            with node_pool_mgr.mutex():
                for node_item in self.nodes:
                    for attribute in self._attribute_list:
                        setattr(node_item, attribute, getattr(self, attribute))
                        persist_node(node_item)

    def get_credentials_with_delay(self, profile):
        """
        Return the node(s) credentials, with an option to specify a delay between requests
        :type profile: `Profile`
        :param profile: Profile object
        :raises ScriptEngineResponseValidationError: when security credentials are not available
        """
        error_count = 0
        for node in self.nodes:
            try:
                response = self.user.enm_execute(self.GET_CREDENTIALS_CMD.format(node=node.node_id))
                if not any(re.search(r'Command Executed Successfully', value) for value in response.get_output()):
                    raise ScriptEngineResponseValidationError(
                        'Failed to retrieve credentials for node: {0}. Response was: '
                        '{1}'.format(node.node_id, ', '.join(response.get_output())),
                        response=response)
            except Exception as e:
                error_count += 1
                if error_count == 1:
                    profile.add_error_as_exception(e)
            finally:
                time.sleep(5)
        if error_count:
            profile.add_error_as_exception(EnmApplicationError(
                "Error occurred while getting credentials {0} time(s) "
                "in this thread.".format(error_count)))


class NodeSSHKey(object):

    CREATED_VERIFICATION = "Sshkey create command executed"
    UPDATED_VERIFICATION = "Sshkey update command executed"
    DELETED_VERIFICATION = r"[1-9][0-9]* instance\(s\) updated"

    CREATE_CMD = 'secadm sshkey create -n "{node_id}" -t "{algorithm}"'
    UPDATE_CMD = 'secadm sshkey update -n "{node_id}" -t "{algorithm}"'
    DELETE_CMD = 'cmedit set NetworkElement={nodes_list}, SecurityFunction=1, NetworkElementSecurity=1 algorithmAndKeySize=RSA_1024, enmSshPrivateKey="", enmSshPublicKey=""'

    ALGORITHM_DEFAULT = 'RSA_1024'
    ALGORITHM_LIST = ['DSA_1024', ALGORITHM_DEFAULT, 'RSA_2048', 'RSA_4096', 'RSA_8192', 'RSA_16384']

    def __init__(self, nodes, user, algorithm=None):
        """
        Constructor for NodeSHHKey object

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param user: User object
        :type user: enm_user.User
        :param algorithm: Signature algorithm type and key size
        :type algorithm: string
        """

        self.nodes = nodes
        self.user = user
        self.algorithm = self._validate_algorithm(algorithm=algorithm)
        self._modify_cmd = None
        self._modify_verification = None

    def _validate_algorithm(self, algorithm):
        """
        Validates the algorithm selection

        :param algorithm: The ssh keys signature algorithm
        :type algorithm: string
        :raises RuntimeError: When invalid value for the algorithm paramter is passed
        """

        if algorithm:
            if algorithm in self.ALGORITHM_LIST:
                self.algorithm = algorithm
            else:
                raise RuntimeError('Invalid argument value for parameter "algorithm". Accepted values are [{0}]'.format(', '.join(self.ALGORITHM_LIST)))
        else:
            self.algorithm = self.ALGORITHM_DEFAULT

    def create(self, algorithm=None):
        """
        Generates ENM public/private ssh keys and copy them to the nodes

        :param algorithm: Signature algorithm type and key size
        :type algorithm: string
        """

        self._validate_algorithm(algorithm=algorithm)
        self._modify_cmd = self.CREATE_CMD
        self._modify_verification = self.CREATED_VERIFICATION

        self._modify('create')

    def update(self, algorithm=None):
        """
        Updates ENM public/private ssh keys and copy them to the nodes

        :param algorithm: Signature algorithm type and key size
        :type algorithm: string
        """

        self._validate_algorithm(algorithm=algorithm)
        self._modify_cmd = self.UPDATE_CMD
        self._modify_verification = self.UPDATED_VERIFICATION

        self._modify('update')

    def delete(self):
        """
        Deletes ENM public/private ssh keys (they are left on the nodes)
        """

        self.algorithm = self.ALGORITHM_DEFAULT
        self._modify_cmd = self.DELETE_CMD.format(nodes_list=';NetworkElement='.join(node.node_id for node in self.nodes))
        self._modify_verification = self.DELETED_VERIFICATION

        self._modify('delete')

    def _modify(self, command):
        """
        Joint function to perform create/update/delete operations for ssh key pair of the nodes

        :param command: The type of operation to perform (create, update or delete)
        :type command: string
        :raises ScriptEngineResponseValidationError: when ssh key pairs are not found
        """

        node_ids = '","'.join(node.node_id for node in self.nodes)
        response = self.user.enm_execute(
            self._modify_cmd.format(node_id=node_ids, algorithm=self.algorithm))
        if not any(re.search(self._modify_verification, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot {0} ssh key pair for nodes "{1}". Response was "{2}"'.format(
                    command, node_ids, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully {0}d ssh key pair for nodes "{1}"'.format(command, node_ids))


class NodeSecurity(object):

    ALGORITHM_ENABLE_VERIFICATION = "Algorithms updated Successfully"
    WORKFLOW_STATUS_VERIFICATION = r'Total num. \[(\d+)\]'

    ALGORITHM_CHECK_CMD = 'pkiadm configmgmt algo --list --type digest --status enabled'
    ALGORITHM_ENABLE_CMD = 'pkiadm configmgmt algo --enable --name {algorithm}'
    WORKFLOW_STATUS_URL = 'node-security/workflow/getwfstats'

    def __init__(self, nodes, security_config, user, timeout=4 * 60 * 60):
        """
        Constructor for NodeSecurity object

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param user: User object
        :type user: enm_user.User
        :param security_config: Instance of `SecurityConfig`
        :type security_config: `SecurityConfig`
        :param timeout: Time for command to complete (in seconds)
        :type timeout: integer
        """

        self.nodes = nodes
        self.user = user
        self.config = security_config

        self.start_time = None
        self.verify_timeout = timeout
        self.file_name = "{0}.xml".format(self.user.username)
        self.xml_file_path = os.path.join("/tmp/enmutils", self.file_name)

    def _is_algorithm_enabled(self):
        """
        Checks for algorithm status

        :returns: True or False whether the algorithm is enabled
        :rtype: boolean
        """

        response = self.user.enm_execute(self.ALGORITHM_CHECK_CMD)
        return True if any(re.search('^{0}\t'.format(self.config.algorithm), line) for line in response.get_output()) else False

    def _enable_algorithm(self):
        """
        Enables the algorithm
        :raises ScriptEngineResponseValidationError: when algorithm cannot be enabled
        """

        if not self._is_algorithm_enabled():
            response = self.user.enm_execute(self.ALGORITHM_ENABLE_CMD.format(algorithm=self.config.algorithm))
            if not any(re.search(self.ALGORITHM_ENABLE_VERIFICATION, line) for line in response.get_output()):
                raise ScriptEngineResponseValidationError(
                    'Cannot enable {0} algorithm. Response was "{1}"'.format(
                        self.config.algorithm, ', '.join(response.get_output())), response=response)
            log.logger.debug('Successfully enabled {0} algorithm'.format(self.config.algorithm))

    def _create_xml_file(self, nodes=None, profile_name=None):
        """
        Creates the xml file to be used for certificate issue or security level change

        :param profile_name: Name of the profile. Default value is None.
        :type profile_name: str
        :param nodes: nodes to be used to create xml file
        :type nodes: list
        :raises RuntimeError: when failed to create xml file
        """
        root = et.Element('Nodes')
        for node in nodes:
            item = et.SubElement(root, 'Node')
            et.SubElement(item, 'NodeFdn').text = node.node_id
            if not profile_name:
                et.SubElement(item, 'EnrollmentMode').text = "CMPv2_VC" if node.primary_type == 'RadioNode' else self.config.enrollment_mode
                et.SubElement(item, 'KeySize').text = self.config.key_size

        try:
            et.ElementTree(root).write(self.xml_file_path, pretty_print=True)
            log.logger.debug('Successfully created {0} file.'.format(self.xml_file_path))
        except Exception as e:
            raise RuntimeError('Failed to create {0} file. Response: {1}'.format(self.xml_file_path, e))

    def _delete_xml_file(self):
        """
        Deletes the xml file used for certificate issue or security level change
        """

        if self.xml_file_path is not None and filesystem.does_file_exist(self.xml_file_path, verbose=False):
            filesystem.delete_file(self.xml_file_path)

    def _get_number_of_workflows(self):
        """
        Returns the number of pending node security workflows

        :raises EnvironError: when node security status cannot be retrieved
        :returns: The number of workflows
        :rtype: integer
        """

        workflows = None
        response = self.user.get(self.WORKFLOW_STATUS_URL, headers=SECURITY_REQUEST_HEADERS)
        if response.ok:
            for line in response.iter_lines():
                match = re.search(self.WORKFLOW_STATUS_VERIFICATION, line)
                if match:
                    workflows = int(match.group(1))

        if workflows is None:
            raise EnvironError('Unable to retrieve the status of Node Security workflows. Response was "{0}"'
                               .format(response.text))

        return workflows

    def _teardown(self):
        """
        Teardown method to be used with workload profile teardown
        """

        self._delete_xml_file()


class NodeCertificate(NodeSecurity):

    ISSUE_VERIFICATION = "Successfully started a job to issue certificates for nodes"
    REISSUE_VERIFICATION = "Successfully started a job to reissue certificates for nodes"
    CERTIFICATE_STATUS_VERIFICATION = "Command Executed Successfully"

    ISSUE_CMD = 'secadm certificate issue -ct "{cert_type}" -xf file:{xml_file}'
    REISSUE_CMD = 'secadm certificate reissue -ct "{cert_type}" -n "{node_id}"'
    CERTIFICATE_STATUS_CMD = 'secadm certificate get -ct "{cert_type}" -n "{node_id}"'
    JOB_SUMMARY_CMD = 'secadm job get -j {0} --summary'

    def __init__(self, *args, **kwargs):
        """
        Constructor for NodeCertificate object
        """

        self.cert_prev_status = {}
        self.reissue_entity = "ENM_E-mail_CA"
        super(NodeCertificate, self).__init__(*args, **kwargs)

    def _get_certificate_status(self, nodes_list):
        """
        Retrieves the certificate serial number and enrollment state of each node of the list

        :param nodes_list: A list of node ID's
        :type nodes_list: list

        :raises ScriptEngineResponseValidationError: when certificate seraial number cannot be retrieved
        :returns: A dictionary containing node IDs and a tuple with enrollment state and certificate serial number
        :rtype: dict
        """

        node_ids = '","'.join(sorted(nodes_list))
        response = self.user.enm_execute(
            self.CERTIFICATE_STATUS_CMD.format(cert_type=self.config.cert_type, node_id=node_ids))
        if not re.search(self.CERTIFICATE_STATUS_VERIFICATION, response.get_output()[-1]):
            raise ScriptEngineResponseValidationError(
                'Unable to retrieve certificate serial number for nodes "{0}". Response was "{1}"'.format(
                    node_ids, ', '.join(response.get_output())), response=response)
        cert_status = {}
        certificates = parse_tabular_output(response.get_output(), skip=self.CERTIFICATE_STATUS_VERIFICATION)
        for certificate in certificates:
            if len(certificate) == 7:
                node_id = certificate['Node Name'].replace('NetworkElement=', '')
                enroll_state = certificate['Enroll State']
                serial_number = certificate['Serial Number']
                cert_status[node_id] = (enroll_state, serial_number)

        return cert_status

    def _check_certificates(self, nodes_list):
        """
        For every node compares the certificate serial numbers before and after the enrollment
        The IDs of the nodes that completed certificate enrollment are removed from the list

        :param nodes_list: A list of node ID's
        :type nodes_list: list

        """
        cert_new_status = self._get_certificate_status(nodes_list)

        for node_id in nodes_list[:]:
            enroll_state, serial_number = cert_new_status[node_id]
            log.logger.debug('Node certificate status {0} ({1})\t Previous: {2}\t Current: {3}'.format(
                node_id, enroll_state, self.cert_prev_status[node_id][1], serial_number))
            if serial_number.isdigit() and serial_number != self.cert_prev_status[node_id][1]:
                # A new certificate has been successfully stored; remove the node from the checklist
                nodes_list.remove(node_id)

    def issue(self, profile_name, selected_nodes):
        """
        Issues certificates on nodes
        Includes the creation of the required xml input file containing node names

        :param profile_name: Name of the profile
        :type profile_name: str
        :param selected_nodes: selected synchronized nodes after sync verification on profile allocated nodes
        :type selected_nodes: list

        :raises ScriptEngineResponseValidationError: when job cannot be started to issue certificates
        """

        self._enable_algorithm()
        self._create_xml_file(profile_name=profile_name, nodes=selected_nodes)
        self.start_time = datetime.datetime.now()

        response = self.user.enm_execute(
            self.ISSUE_CMD.format(cert_type=self.config.cert_type, xml_file=self.file_name), file_in=self.xml_file_path)
        # expected cmedit_reponse : Successfully started a job to issue certificates for nodes. Perform 'secadm job get
        #                          -j 300659b2-9b5e-4ac2-86a0-ff48a90d794a' to get progress info

        if not any(re.search(self.ISSUE_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot start a job to issue certificates for nodes included in "{0}" file. Response was "{1}"'.format(
                    self.xml_file_path, ', '.join(response.get_output())), response=response)

        # filtering JOB_ID from successful cmedit reponse. example: 300659b2-9b5e-4ac2-86a0-ff48a90d794a
        job_id = response.get_output()[0].split(' -j ')[-1].split('\'')[0]

        log.logger.debug('Successfully started a job with Job ID-{0} to issue certificates for nodes included in "{1}" '
                         'file'.format(job_id, self.xml_file_path))

        job_status_cmd = str(re.split("'*'", response.get_output()[0])[1])
        log.logger.debug("Command to get status for certificate issue job on nodes: '{0}'".format(job_status_cmd))
        check_job_status(self.user, "{0} --summary".format(job_status_cmd), "certificate issue")

    def reissue(self, selected_nodes):
        """
        Reissues certificates on nodes
        A valid certificate must be already present on each node.

        :type selected_nodes: list
        :param selected_nodes: selected synchronized nodes after sync verification on profile allocated nodes
        :raises ScriptEngineResponseValidationError: when job cannot be started to reissue certificates
        """

        self._enable_algorithm()
        self.xml_file_path = None
        self.start_time = datetime.datetime.now()

        node_ids = '","'.join(node.node_id for node in selected_nodes)

        response = self.user.enm_execute(
            self.REISSUE_CMD.format(cert_type=self.config.cert_type, node_id=node_ids))
        # expected cmedit_reponse : Successfully started a job to issue certificates for nodes. Perform 'secadm job get
        #                          -j 300659b2-9b5e-4ac2-86a0-ff48a90d794a' to get progress info

        if not any(re.search(self.REISSUE_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot start a job to reissue certificates for nodes "{0}". Response was "{1}"'.format(
                    node_ids, ', '.join(response.get_output())), response=response)

        # filtering JOB_ID from successful cmedit reponse. example: 300659b2-9b5e-4ac2-86a0-ff48a90d794a
        job_id = response.get_output()[0].split(' -j ')[-1].split('\'')[0]

        log.logger.debug('Successfully started a job with Job ID-{0} to reissue certificates for nodes included in '
                         '"{1}" file'.format(job_id, self.xml_file_path))

        job_status_cmd = str(re.split("'*'", response.get_output()[0])[1])
        log.logger.debug("Command to get status for certificate reissue job on nodes: '{0}'".format(job_status_cmd))
        check_job_status(self.user, "{0} --summary".format(job_status_cmd), "certificate reissue")

    def validate(self, check_certificates=True, fail_fast=False):
        """
        Validates that issue/reissue of certificates is completed in expected time

        :param check_certificates: Flag to enable deeper inspection of certificate enrollment
        :type check_certificates: boolean
        :param fail_fast: Flag to exit execution if workflows are completed but some certificate is still missing, otherwise waits until timeout
        :type fail_fast: boolean
        :raises TimeOutError: when timeout occured for ceritificate enrollment validation
        :raises ValidationError: when certificate enrollment failed for nodes
        """

        timeout_time = self.start_time + datetime.timedelta(seconds=self.verify_timeout)

        if check_certificates:
            incomplete_nodes = self.cert_prev_status.keys()
        check_workflows = True
        done = False
        while datetime.datetime.now() < timeout_time:

            time_left = int((timeout_time - datetime.datetime.now()).total_seconds())
            polling_time = 10
            if check_workflows:
                # Wait for workflows to complete
                log.logger.debug(
                    'Waiting for completion of all the node security workflows. Maximum wait time is "%d" seconds, time left is "%d"' % (self.verify_timeout, time_left))
                pending_workflows = self._get_number_of_workflows()
                if pending_workflows:
                    log.logger.debug('Total number of pending workflows: "%d"' % pending_workflows)
                    # Calculate the polling time, based on the number of pending workflows
                    polling_time = int(math.log(pending_workflows, 3)) * 30 + 10 * (pending_workflows < 3)
                else:
                    log.logger.debug('There are no pending workflows')
                    check_workflows = False
                    time.sleep(5)

            if not check_workflows:
                if check_certificates:
                    self._check_certificates(nodes_list=incomplete_nodes)
                    if not incomplete_nodes:
                        done = True
                    elif fail_fast:
                        raise ValidationError(
                            'Certificate enrollment failed for nodes "{0}"'.format(
                                ', '.join(incomplete_nodes)))
                else:
                    done = True

            if done:
                break

            if datetime.datetime.now() + datetime.timedelta(seconds=polling_time) > timeout_time:
                polling_time = int((timeout_time - datetime.datetime.now()).total_seconds()) + 1
            log.logger.debug('Sleeping for %d seconds' % polling_time)
            time.sleep(polling_time)

        else:
            raise TimeOutError(
                'Time out of "%d" seconds expired for certificate enrollment validation' % self.verify_timeout)

        elapsed_time = int((datetime.datetime.now() - self.start_time).total_seconds())
        log.logger.debug(
            'Successfully completed the certificate enrollment for all %d nodes in "%d" seconds' % (len(self.nodes), elapsed_time))


class NodeTrust(NodeSecurity):

    DISTRIBUTE_VERIFICATION = "Successfully started a job for trust distribution to nodes"
    REMOVE_VERIFICATION = "Successfully started a job for trust removal from nodes"
    TRUST_STATUS_VERIFICATION = "Command Executed Successfully"
    CA_CERTIFICATES_VERIFICATION = "Command Executed Successfully"

    DISTRIBUTE_CMD_WITH_FILE = 'secadm trust distribute -tc "{cert_type}" -ca "{entity}" -nf file:{file_name}'
    DISTRIBUTE_REMOVE_CMD_WITH_FILE = ('secadm trust remove -tc "{cert_type}" -isdn "{issuer}" -sn "{serial_number}" '
                                       '-nf file:{file_name}')
    DISTRIBUTE_CMD_WITHOUT_CA = 'secadm trust distribute -tc "{cert_type}" -nf file:{file_name}'
    TRUST_STATUS_CMD = 'secadm trust get -tc "{cert_type}" -n "{node_id}"'
    CA_CERTIFICATES_CMD = 'pkiadm trustmgmt --list --entitytype ca'

    CA_ENTITIES = {"ENM_E-mail_CA": ["CN=ENM_E-mail_CA,O=ERICSSON,C=SE,OU=BUCI_DUAC_NAM", "", 0]}

    def __init__(self, *args, **kwargs):
        """
        Constructor for NodeTrust object
        """

        super(NodeTrust, self).__init__(*args, **kwargs)

    def _get_ca_certificates(self):
        """
        Retrieves the trust certificate serial number of the CA entities

        :raises ScriptEngineResponseValidationError: when trusted certificates for CA entities cannot be retrieved
        """
        response = self.user.enm_execute(self.CA_CERTIFICATES_CMD)
        if not any(re.search(self.CA_CERTIFICATES_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot retrieve trust certificate for CA entities. Response was "{0}"'.format(
                    ', '.join(response.get_output())), response=response)

        ca_trusts = parse_tabular_output(response.get_output(), header_line=1, skip=self.CA_CERTIFICATES_VERIFICATION)

        for ca_trust in ca_trusts:
            entity_name = ca_trust['Entity Name']
            serial_number = ca_trust['Certificate Serial No.']
            issuer = ca_trust['Issuer']
            if entity_name in self.CA_ENTITIES:
                self.CA_ENTITIES[entity_name][2] = int(serial_number, 16)
                self.CA_ENTITIES[entity_name][1] = self.CA_ENTITIES[entity_name][0].replace(entity_name, issuer)

    def _get_trust_status(self, nodes_list):
        """
        Retrieves the trust information of each node of the list

        :param nodes_list: A list of node ID's
        :type nodes_list: list
        :raises ScriptEngineResponseValidationError: when trust information for nodes cannot be retrieved
        :returns: A dictionary containing node IDs and the number of stored trust certificates
        :rtype: dict
        """

        node_ids = '","'.join(sorted(nodes_list))

        response = self.user.enm_execute(
            self.TRUST_STATUS_CMD.format(cert_type=self.config.cert_type, node_id=node_ids))
        if not re.search(self.TRUST_STATUS_VERIFICATION, response.get_output()[-1]):
            raise ScriptEngineResponseValidationError(
                'Unable to retrieve trust information for nodes "{0}". Response was "{1}"'.format(
                    node_ids, ', '.join(response.get_output())), response=response)
        trust_status = {}
        trusts = parse_tabular_output(response.get_output(), skip=self.TRUST_STATUS_VERIFICATION, multiline=True)
        for trust in trusts:
            if len(trust) == 6:
                node_id = re.sub(r'NetworkElement=(\w+)', r'\1', trust['Node Name'])
                subject = re.sub(r'CN=(\w+).*', r'\1', trust['Subject'])
                serial_number = int(trust['Serial Number'])
                if node_id:
                    trust_status[node_id] = trust_status.get(node_id, 0)
                    if subject in self.CA_ENTITIES and serial_number == self.CA_ENTITIES[subject][2]:
                        trust_status[node_id] += 1

        return trust_status

    def _check_trust(self, nodes_list, num_trusts):
        """
        For every node checks the number of valid stored trust certificates
        The IDs of the nodes that store the required number of trust certificates are removed from the list

        :param nodes_list: A list of node ID's
        :type nodes_list: list
        :param num_trusts: The number of trust certificates to check for
        :type num_trusts: integer

        """

        trust_status = self._get_trust_status(nodes_list)

        for node_id in nodes_list[:]:
            stored_trusts = trust_status[node_id]
            log.logger.debug('Number of trust certificates stored on node {0}:\t {1}'.format(
                node_id, stored_trusts))
            if stored_trusts == num_trusts:
                # The required trust certificates have been successfully stored; remove the node from the checklist
                nodes_list.remove(node_id)

    def distribute(self, nodes_file_name, nodes_file_path, include_ca=True):
        """
        Distributes trust certificates to nodes
        :type nodes_file_name: str
        :param nodes_file_name: nodes file name (nodes.txt)
        :type nodes_file_path: str
        :param nodes_file_path: file path of nodes (nodes.txt)
        :param include_ca: Boolean indicating if need to include ca in trust distribute command or not.
        :type include_ca: bool

       :raises ScriptEngineResponseValidationError: when job cannot be started for trust distribution of nodes
        """
        if not self.CA_ENTITIES.items()[0][1][2]:
            self._get_ca_certificates()

        self.start_time = datetime.datetime.now()
        entity = self.CA_ENTITIES.keys()[0]
        if include_ca:
            cmd = self.DISTRIBUTE_CMD_WITH_FILE.format(cert_type=self.config.cert_type, entity=entity,
                                                       file_name=nodes_file_name)
        else:
            cmd = self.DISTRIBUTE_CMD_WITHOUT_CA.format(cert_type=self.config.cert_type, file_name=nodes_file_name)
        response = self.user.enm_execute(cmd, file_in=nodes_file_path)
        if not any(re.search(self.DISTRIBUTE_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot start a job for trust distribution to nodes {0}. Response was "{1}"'.format(
                    len(self.nodes), ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully started a job for trust distribution to {0} nodes'.format(len(self.nodes)))
        job_status_cmd = str(re.split("'*'", response.get_output()[0])[1])
        log.logger.debug("Command to get status for nodes trust distribution job: '{0}'".format(job_status_cmd))
        check_job_status(self.user, "{0} --summary".format(job_status_cmd), "trust distribution")

    def remove(self, nodes_file_name, nodes_file_path, check_job_status_on_teardown=False):
        """
        Removes trust certificates from nodes

        :type nodes_file_name: str
        :param nodes_file_name: nodes file name (nodes.txt)
        :type nodes_file_path: str
        :param nodes_file_path: file path of nodes (nodes.txt)
        :type check_job_status_on_teardown: bool
        :param check_job_status_on_teardown: Boolean indicating if need to check remove trust job status
                                             on teardown or not.

       :raises ScriptEngineResponseValidationError: when job cannot be started to remove the trust from nodes
        """

        if not self.CA_ENTITIES.items()[0][1][2]:
            self._get_ca_certificates()

        self.start_time = datetime.datetime.now()

        subject, (_, issuer, serial_number) = self.CA_ENTITIES.items()[0]
        response = self.user.enm_execute(
            self.DISTRIBUTE_REMOVE_CMD_WITH_FILE.format(cert_type=self.config.cert_type, issuer=issuer,
                                                        serial_number=serial_number, file_name=nodes_file_name),
            file_in=nodes_file_path)
        if not any(re.search(self.REMOVE_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot start a job to remove trust {0} from nodes {1}. Response was "{2}"'.format(
                    subject, len(self.nodes), ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully started a job to remove trust {0} from {1} nodes'.format(subject,
                                                                                                len(self.nodes)))
        job_status_cmd = str(re.split("'*'", response.get_output()[0])[1])
        log.logger.debug("Command to get status for nodes trust remove job: '{0}'".format(job_status_cmd))
        if not check_job_status_on_teardown:
            check_job_status(self.user, "{0} --summary".format(job_status_cmd), "trust remove")

    def validate(self, action='distribute', check_trusts=True, fail_fast=False):
        """
        Validates that distribution/removal of trust certificates is completed in expected time

        :param action: Selector for trust validation ('distribute' or 'remove')
        :type action: string
        :param check_trusts: Check that network elements store the required number of trust certificates
        :type check_trusts: bool
        :param fail_fast: Flag to exit execution if workflows are completed but the number of stored trust certificates
                          is not as expected, otherwise waits until timeout
        :type fail_fast: boolean
        :raises TimeOutError: when trust validation expired
        :raises ValidationError: when trust failed for nodes
        """

        num_trusts = len(self.CA_ENTITIES) if action == 'distribute' else 0

        timeout_time = self.start_time + datetime.timedelta(seconds=self.verify_timeout)

        if check_trusts:
            incomplete_nodes = [node.node_id for node in self.nodes]
        check_workflows = True
        done = False
        while datetime.datetime.now() < timeout_time:

            time_left = int((timeout_time - datetime.datetime.now()).total_seconds())
            polling_time = 5

            if check_workflows:
                # Wait for workflows to complete
                log.logger.debug(
                    'Waiting for completion of all the node security workflows. Maximum wait time is "%d" seconds, time left is "%d"' % (self.verify_timeout, time_left))
                pending_workflows = self._get_number_of_workflows()
                if pending_workflows:
                    log.logger.debug('Total number of pending workflows: "%d"' % pending_workflows)
                    # Calculate the polling time, based on the number of pending workflows
                    polling_time = int(math.log(pending_workflows, 3)) * 10 + 5 * (pending_workflows < 3)
                else:
                    log.logger.debug('There are no pending workflows')
                    check_workflows = False
                    time.sleep(5)

            if not check_workflows:
                if check_trusts:
                    self._check_trust(nodes_list=incomplete_nodes, num_trusts=num_trusts)
                    if not incomplete_nodes:
                        done = True
                    elif fail_fast:
                        raise ValidationError(
                            'Trust {0} failed for nodes "{1}"'.format(
                                'distribution' if num_trusts else "removal", ', '.join(incomplete_nodes)))
                else:
                    done = True

            if done:
                break

            if datetime.datetime.now() + datetime.timedelta(seconds=polling_time) > timeout_time:
                polling_time = int((timeout_time - datetime.datetime.now()).total_seconds()) + 1
            log.logger.debug('Sleeping for %d seconds' % polling_time)
            time.sleep(polling_time)

        else:
            raise TimeOutError(
                'Time out of "{0}" seconds expired for trust {1} validation'.format(
                    self.verify_timeout, 'distribution' if num_trusts else "removal"))

        elapsed_time = int((datetime.datetime.now() - self.start_time).total_seconds())
        log.logger.debug(
            'Successfully completed the trust {0} for all {1} nodes in "{2}" seconds'.format(
                'distribution' if num_trusts else "removal", len(self.nodes), elapsed_time))


class NodeSecurityLevel(NodeSecurity):

    SECURITY_LEVEL_SET_VERIFICATION = "Security level change initiated"

    def __init__(self, *args, **kwargs):
        """
        Constructor for NodeSecurityLevel object
        """
        super(NodeSecurityLevel, self).__init__(*args, **kwargs)

    def set_level(self, security_level=1):
        """
        Activate/Deactivate CORBA security level of the nodes
        Includes the creation of the required xml input file containing node names and certificate parameters

        :param security_level: The CORBA security level (1 or 2)
        :type security_level: integer
        :raises ScriptEngineResponseValidationError: when job cannot be started to change security level of nodes
        """

        self.config.level = security_level

        self._enable_algorithm()
        self._create_xml_file(self.nodes)
        self.start_time = datetime.datetime.now()

        response = self.user.enm_execute(SECURITY_LEVEL_SET_CMD.format(security_level=self.config.level,
                                                                       xml_file=self.file_name),
                                         file_in=self.xml_file_path)
        if not any(re.search(self.SECURITY_LEVEL_SET_VERIFICATION, line) for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot start a job to change security level for nodes included in "{0}" file. Response was "{1}"'.format(
                    self.xml_file_path, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully started a job to change security level for nodes included in "{0}" file'.format(self.xml_file_path))

    def validate(self, nodes, start_time=None, check_levels=True, fail_fast=False):
        """
        Validates that security level change is completed in expected time

        :param nodes: List of enm_node.Node objects
        :type nodes: list
        :param start_time: Start time of the batch execution
        :type start_time: datetime
        :param check_levels: Flag to enable deeper inspection of security level status
        :type check_levels: boolean
        :param fail_fast: Flag to exit execution if workflows are completed but some security level didn't change, otherwise waits until timeout
        :type fail_fast: boolean
        :raises TimeOutError: when security level change timeout occurs
        :raises ValidationError: when security level change failed for nodes
        """

        start_time = start_time or datetime.datetime.now()
        timeout_time = start_time + datetime.timedelta(seconds=self.verify_timeout)

        if check_levels:
            incomplete_nodes = [node.node_id for node in nodes]

        check_workflows = True
        done = False
        while datetime.datetime.now() < timeout_time:

            time_left = int((timeout_time - datetime.datetime.now()).total_seconds())
            polling_time = 20

            if check_workflows:
                # Wait for workflows to complete
                log.logger.debug(
                    'Waiting for completion of all the node security workflows. Maximum wait time is "%d" seconds, time left is "%d"' % (self.verify_timeout, time_left))
                pending_workflows = self._get_number_of_workflows()
                if pending_workflows:
                    log.logger.debug('Total number of pending workflows: "%d"' % pending_workflows)
                    # Calculate the polling time, based on the number of pending workflows
                    polling_time = int(math.log(pending_workflows, 2)) * 30 + 20 * (pending_workflows < 2)
                else:
                    log.logger.debug('There are no pending workflows')
                    check_workflows = False
                    time.sleep(5)

            if not check_workflows:
                if check_levels:
                    get_nodes_not_at_required_level(nodes_list=incomplete_nodes, user=self.user)
                    if not incomplete_nodes:
                        done = True
                    elif fail_fast:
                        raise ValidationError(
                            'Security level change failed for nodes "{0}"'.format(
                                ', '.join(incomplete_nodes)))
                else:
                    done = True

            if done:
                break

            if datetime.datetime.now() + datetime.timedelta(seconds=polling_time) > timeout_time:
                polling_time = int((timeout_time - datetime.datetime.now()).total_seconds()) + 1
            log.logger.debug('Sleeping for %d seconds' % polling_time)
            time.sleep(polling_time)

        else:
            raise TimeOutError(
                'Time out of "%d" seconds expired for security level change validation' % self.verify_timeout)

        elapsed_time = int((datetime.datetime.now() - self.start_time).total_seconds())
        log.logger.debug(
            'Successfully completed the security level change for all %d nodes in "%d" seconds' % (len(nodes), elapsed_time))

    def _teardown(self):
        """
        Teardown method
        """
        try:
            self.set_level()
        except Exception as e:
            log.logger.warn("Failed to correctly teardown, response {0}".format(e.message))
        finally:
            self._delete_xml_file()


class FTPES(object):

    SECADM_FTPES_STATUS_SINGLE_NODE_CMD = 'secadm ftpes get -n {node_id}'
    SECADM_FTPES_STATUS_MULTIPLE_NODES_CMD = 'secadm ftpes get --nodelist {node_ids}'
    SECADM_JOB_STATUS_CMD = 'secadm job get -j {job_id}'
    SECADM_ACTIVATE_FTPES_SINGLE_NODE_CMD = 'secadm ftpes activate -n {node_id}'
    SECADM_ACTIVATE_FTPES_MULTIPLE_NODES_CMD = 'secadm ftpes activate --nodelist {node_ids}'

    def __init__(self, user, nodes=None):
        self.user = user
        self.nodes = [node.node_id for node in nodes]
        self.job_id = None

    def activate_ftpes_on_nodes(self, nodes):
        """
        Activate the FTPES for the supplied nodes

        :type nodes:    `enm_node.Node`
        :param nodes:   Node to query on enm to activate FTPES

        :raises EnmApplicationError: raised if error is received from command execution.
        """
        cmd = self.SECADM_ACTIVATE_FTPES_MULTIPLE_NODES_CMD.format(node_ids=';'.join(node for node in nodes)) \
            if len(nodes) > 1 else self.SECADM_ACTIVATE_FTPES_SINGLE_NODE_CMD.format(node_id=nodes[0])
        try:
            activate_response = self.user.enm_execute(cmd)
            log.logger.debug('Setting the Job ID for FTPES activation')
            self.job_id = activate_response.get_output()[0].split(' -j ')[-1].split('\'')[0]
            log.logger.debug('Successfully activated FTPES with Job ID: {0}'.format(self.job_id))
        except Exception as e:
            raise EnmApplicationError("Problem encountered trying to execute command: {0}. Error: {1}"
                                      .format(cmd, e))

    def get_ftpes_status(self, node):
        """
        Retrieve the FTPES status for the supplied node.

        :type node:     enm_node.Node`
        :param node:    Node to query on enm for its FTPES status.

        :return:        Response object returned by the command execution
        :rtype:         `enmscripting.Response` object

        :raises EnmApplicationError: raised if error is received from command execution.
        """
        try:
            return self.user.enm_execute(self.SECADM_FTPES_STATUS_SINGLE_NODE_CMD.format(node_id=node)).get_output()

        except Exception as e:
            raise EnmApplicationError("Problem encountered trying to execute secadm command. Error: {0}".format(e))

    @staticmethod
    def enable_fm_supervsion_on_nodes_for_ftpes_activation(nodes):
        """
        Enable FM supervision on supplied nodes.

        :param nodes:   `enm_node.Node`
        :type nodes:    Node to query on enm for its ldap mo status

        :raises EnvironError: raised if error is received from enabling FM supervision.
        """

        try:
            fm_supervision_obj = FmManagement(node_ids=[node for node in nodes])
            fm_supervision_obj.supervise()
        except Exception as e:
            raise EnvironError(e)

    def check_ftpes_are_enabled_on_nodes_and_enable(self, teardown=False):
        """
        Check FTPES are activated on the supplied nodes.

        If FTPES are not activated then FM Supervision is enabled and FTPES activation is triggered on the supplied nodes

        """

        nodes_ftpes_disabled = []
        for node in self.nodes:
            log.logger.debug('Checking the FTPES status for {0}'.format(node))
            ftpes_status = self.get_ftpes_status(node)
            response_string = "\n".join(ftpes_status)
            match_pattern = re.compile(r'{0}\tON\t'.format(node))
            if match_pattern.search(response_string) is None:
                log.logger.debug('FTPES are not activated for: {0}'.format(node))
                nodes_ftpes_disabled.append(node)

        if nodes_ftpes_disabled:
            if not teardown:
                log.logger.debug('Enabling FM Supervision for FTPES activation on nodes: {0}'.format(self.nodes))
                self.enable_fm_supervsion_on_nodes_for_ftpes_activation(nodes_ftpes_disabled)
            log.logger.debug('Activating FTPES on {0} nodes: {1}'.format(len(nodes_ftpes_disabled), nodes_ftpes_disabled))
            self.activate_ftpes_on_nodes(nodes_ftpes_disabled)
            log.logger.debug('Sleeping for 5 minutes until FTPES activation is complete')
            time.sleep(300)
            for node in nodes_ftpes_disabled:
                ftpes_status = self.get_ftpes_status(node)
                if 'ON' not in str(ftpes_status):
                    raise Exception('FTPES are still not activated on Node: {0}. '
                                    'Manual intervention may be needed.'.format(node))


class NodeSNMP(object):

    SET_SNMP_CONNECTIVITY_INFO_VERIFICATION = "instance(s) updated"
    SET_SNMP_VERIFICATION = "Snmp Authpriv Command OK"

    SET_SNMP_CONNECTIVITY_INFO_CMD = ('cmedit set "{node_id}" "{connectivity_information}" snmpVersion="{snmp_version}", snmpSecurityLevel="{snmp_security_level}", snmpSecurityName="{snmp_security_name}"')
    SET_SNMP_CMD = ('secadm snmp authpriv --auth_algo {auth_algo} --auth_password "{auth_password}" --priv_algo {priv_algo} --priv_password "{priv_password}" -n "{node_id}"')  # Different node types have different settings; it will be retrieved from the node class at runtime

    def __init__(self, nodes, user):
        """
        Constructor for NodeSNMP object

        :param nodes: List of enm_node.Node objects - All nodes must be of the same node-type
        :type nodes: list
        :param user: User object
        :type user: enm_user.User
        """

        self.nodes = nodes
        self.user = user

    def set_version(self, snmp_version):
        """
        Configures the SNMP version on the nodes

        :param snmp_version: The SNMP protocol version
        :type snmp_version: string
        :raises ScriptEngineResponseValidationError: when SNMP cannot be set/SNMP connectivity cannot be done
        """

        if snmp_version == 'SNMP_V3':
            config.set_prop('use_snmp_v3', True)

        node_ids = '","'.join(node.node_id for node in self.nodes)
        node_obj = self.nodes[0]
        node_kwargs = {'auth_algo': node_obj.snmp_authentication_method or "NONE",
                       'auth_password': node_obj.snmp_auth_password,
                       'priv_algo': node_obj.snmp_encryption_method or "NONE",
                       'priv_password': node_obj.snmp_priv_password, 'node_id': node_obj.node_id}
        node_kwargs['node_id'] = node_ids

        response = self.user.enm_execute(
            self.SET_SNMP_CMD.format(**node_kwargs))
        if not any(self.SET_SNMP_VERIFICATION in line for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot set SNMP version for node(s) "%s". Response was "%s"' % (
                    node_ids, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully set SNMP version for node(s) "%s"' % node_ids)

        connectivity_information = ("Er6000ConnectivityInformation" if node_obj.primary_type in ['Router6274', 'Router6672', 'Router6675', 'Router6x71'] else "ComConnectivityInformation")
        node_kwargs = {'node_id': node_obj.node_id,
                       'snmp_security_level': node_obj.snmp_security_level,
                       'snmp_security_name': (node_obj.snmp_security_name or "public") if node_obj.primary_type in ['Router6672', 'Router6675'] else (node_obj.snmp_security_name or "NONE"),
                       'snmp_version': snmp_version,
                       'connectivity_information': connectivity_information}

        node_kwargs['node_id'] = node_ids.replace(',', ';')

        response = self.user.enm_execute(
            self.SET_SNMP_CONNECTIVITY_INFO_CMD.format(**node_kwargs))
        if not any(self.SET_SNMP_CONNECTIVITY_INFO_VERIFICATION in line for line in response.get_output()[-2:]):
            raise ScriptEngineResponseValidationError(
                'Cannot set SNMP connectivity for node(s) "%s". Response was "%s"' % (
                    node_ids, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully set SNMP connectivity for node(s) "%s"' % node_ids)


def set_time_out(nodes, num_nodes_per_timeout=150, timeout=600):
    """
    Calculate the total timeout based on number of nodes

    :type nodes: list
    :param nodes: List of `enm_node.Node` instances
    :type num_nodes_per_timeout: int
    :param num_nodes_per_timeout: int, Total number of nodes to be actioned upon per timeout period
    :type timeout: int,
    :param timeout: Timeout in seconds
    :rtype: int
    :return: total timeout
    """
    # Calculate batch timeout
    #   1 - 150 nodes: 10min
    # 151 - 300 nodes: 20min
    # 301 - 450 nodes: 30min
    return timeout * (len(nodes) / num_nodes_per_timeout)


def generate_node_batches(nodes, batch_size=450):
    """
    Generate manageable lists of the provided nodes, no greater than 450

    :type nodes: list
    :param nodes: List of `enm_node.Node` instances
    :type batch_size: int
    :param batch_size: Maximum number of nodes to be allocated to each batch
    :raises RuntimeError: when no nodes are available
    :rtype: list
    :return: List of list(s), containing nodes in batches of no more than 450 nodes
    """
    node_batches = []
    if not nodes:
        raise RuntimeError("No available nodes found")
    nodes_to_batch = nodes
    while nodes_to_batch:
        node_batches.extend([nodes_to_batch[0:batch_size]])
        nodes_to_batch = nodes_to_batch[batch_size:]
    return node_batches


@retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=120, stop_max_attempt_number=3)
def check_sync(node, user):
    """
    Checks the sync status of a given node

    :type node: str
    :param node: String id of the node
    :type user: `enm_user_2.User`
    :param user: Instance of `enm_user_2.User` to execute the sync check
    :rtype: bool
    :return: boolean indicating the current sync status
    :raises EnmApplicationError:  when cmedit get command fails
    """
    try:
        response = user.enm_execute('cmedit get NetworkElement={0},CmFunction=1'.format(node))
    except Exception as e:
        log.logger.debug("Unable to get sync status for node {0}. Retrying".format(node))
        raise EnmApplicationError(e.message)
    if any(re.search(r'(UNSYNCHRONIZED|PENDING|ATTRIBUTE|TOPOLOGY)', line, re.I) for line in response.get_output())\
            or '0 instance(s)' in response.get_output():
        return False
    return True


def check_sync_and_remove(nodes, user):
    """
    Check if node in a synchronised state and if not, removes the node

    :type nodes: list
    :param nodes: List of `enm_node.Node` to sync or remove
    :type user: `enm_user_2.User`
    :param user: Instance of `enm_user_2.User` to execute the sync check

    :rtype: tuple
    :return: Tuple of two lists, containing synced and unsynced nodes
    """
    if nodes:
        enm_network_element_sync_states = get_enm_network_element_sync_states(user)
        unsynced_nodes = [node for node in nodes if enm_network_element_sync_states.get(node.node_id) != "SYNCHRONIZED"]
        nodes = [node for node in nodes if node not in unsynced_nodes]
        log.logger.debug("Returning {0} Synchronised nodes, and {1} unsynchronised nodes.".format(len(nodes),
                                                                                                  len(unsynced_nodes)))
        return nodes, unsynced_nodes
    log.logger.debug("No nodes supplied so no CM Synchronization states will be checked")
    return [], []


def get_level(nodes_list, user):
    """
    Retrieves the security level of each node of the list

    :param nodes_list: A list of node ID's
    :type nodes_list: list
    :type user: `enm_user_2.User`
    :param user: Instance of `enm_user_2.User` to get the level

    :raises ScriptEngineResponseValidationError: when node security level cannot be retrieved
    :raises DependencyException: when secadm command output modified
    :returns: A dictionary containing node IDs and security level
    :rtype: dict
    """
    user = user
    node_ids = '","'.join(sorted(nodes_list))

    response = user.enm_execute(SECURITY_LEVEL_GET_CMD.format(node_id=node_ids))
    if not re.search(SECURITY_LEVEL_GET_VERIFICATION, response.get_output()[-1]):
        raise ScriptEngineResponseValidationError('Unable to retrieve security level for nodes "{0}". '
                                                  'Response was "{1}"'
                                                  .format(node_ids, ', '.join(response.get_output())),
                                                  response=response)

    security_level_status = {}
    security_levels = parse_tabular_output(response.get_output(), skip=SECURITY_LEVEL_GET_VERIFICATION)
    for security_level in security_levels:
        try:
            if security_level['Node Name'] and security_level['Node Security Level']:
                node_id = security_level['Node Name']
                level = security_level['Node Security Level'].replace('level ', '')
                security_level_status[node_id] = int(level)
        except KeyError as e:
            raise DependencyException(host='secserv', command=SECURITY_LEVEL_GET_CMD,
                                      error='Change in column names in command output: {}'.format(e.message))

    return security_level_status


def get_nodes_not_at_required_level(nodes_list, user, required_security_level=1):
    """
    For every node checks the current security level
    The IDs of the nodes that successfully changed the security level are removed from the list

    :param nodes_list: A list of node ID's
    :type nodes_list: list
    :type user: `enm_user_2.User`
    :param user: Instance of `enm_user_2.User` to execute the check
    :param required_security_level: Security level to check is enabled on the node(s)
    :type required_security_level: int
    :raises EnvironError: when there are no nodes with node security

    :returns: A list of node ID's, not yet enabled
    :rtype: list
    """
    security_level_status = get_level(nodes_list, user)
    for node_id in nodes_list[:]:
        security_level = security_level_status[node_id]
        log.logger.debug('Node security level {0}:\t level {1}'.format(node_id, security_level))
        if security_level == required_security_level:
            # The node security level has been successfully changed; remove the node from the checklist
            nodes_list.remove(node_id)
    return nodes_list


def check_services_are_online():
    """
    Check if the required services are online

    :raises EnvironError: when vcs.bsh/kubectl get pods response status was not OK
    """
    services = ["SPS", "PKIRASERV", "SECSERV", "MSCM", "MSFM", "FMALARMPROCESSING"]
    CHECK_SERVICES_CMD = "/opt/ericsson/enminst/bin/vcs.bsh --groups | egrep -i {0} | grep -i online"

    log.logger.debug("Checking if following services are online: {0}".format(services))

    if is_enm_on_cloud_native():
        log.logger.debug("ENM on Cloud native detected")
        for service in services:
            cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(get_enm_cloud_native_namespace(), service))
            response = run_local_cmd(cmd)
            if not response.ok:
                raise EnvironError("Issue occurred while checking {0} on Cloud native, "
                                   "Please check logs".format(service))
    elif is_emp():
        log.logger.debug("ENM on Cloud detected - running command on EMP")
        get_required_services_status_on_cloud(services)
    else:
        log.logger.debug("ENM on Physical detected - running command on LMS")
        for service in services:
            cmd = Command(CHECK_SERVICES_CMD.format(service))
            response = run_cmd_on_ms(cmd)
            if not response.ok:
                raise EnvironError("Issue occurred while checking {0} on Physical, Please check logs".format(service))


def get_required_services_status_on_cloud(services):
    """
    Get SPS, PKIRASERV, SECSERV, MSCM, MSFM, FMALARMPROCESSING services status,
    which services are running (alive) on cloud.

    :param services: list of services (SPS, PKIRASERV, SECSERV, MSCM, MSFM, FMALARMPROCESSING)
    :type services: list

    :raises EnvironError: When sudo consul members response status was not OK.
    """
    CHECK_SERVICES_CMD_ON_CLOUD = "sudo consul members | egrep -i {0} | grep -i alive"

    for service in services:
        response = run_cmd_on_vm(CHECK_SERVICES_CMD_ON_CLOUD.format(service), get_emp())
        if not response.ok:
            raise EnvironError("Issue occurred while checking {0} on Cloud, Please check logs".format(service))


def check_job_status(user, job_status_cmd, job_type):
    """
    Function to be used to get trust distribution/remove or certificate issue/reissue job status

    :param user: profile user
    :type user: user object
    :type user: user object
    :param job_status_cmd: command to execute job status
    :type job_status_cmd: str
    :param job_type: type of job
    :type job_type: str

    :raises EnvironError: If job status has not been completed within expected time/Max_poll
    """
    job_complete_status = False
    poll = 1
    while not job_complete_status and poll <= MAX_POLL:
        log.logger.debug('POLL_COUNT: {0}, MAX_POLL: {1}'.format(poll, MAX_POLL))
        try:
            log.logger.debug("Execute {0} command to get current {1} job "
                             "status".format(job_status_cmd, job_type))
            job_status_response = user.enm_execute(job_status_cmd)
            if job_status_response and "COMPLETED" in job_status_response.get_output()[5]:
                log.logger.debug("Job status has been successfully completed")
                job_complete_status = True
                log.logger.debug("{0} job summary: \n{1}".format(job_type,
                                                                 "\n".join(job_status_response.get_output())))

            if not job_complete_status:
                log.logger.debug("Sleeping for {0} seconds until {1} job status in "
                                 "COMPLETED state..". format(100, job_type))
                time.sleep(SLEEP_TIME)
                poll += 1
        except Exception as e:
            log.logger.debug("Failed to get current {0} job status: {1}".format(job_type, e))
            break
    if poll > MAX_POLL:
        log.logger.debug("Max retries ({0}) reached...".format(MAX_POLL))
        raise EnvironError("{0} job status has not completed within expected time: {1} seconds".format(job_type,
                                                                                                       10 * 100))
