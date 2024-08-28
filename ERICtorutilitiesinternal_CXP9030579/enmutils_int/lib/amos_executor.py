# ********************************************************************
# Name    : AMOS Executor
# Summary : Allows the user to manage all aspects of the advanced MO
#           shell interactions.
#           Provides user session management, node management, ldap
#           management, websocket creation, AMOS command construction,
#           AMOS node executor which interacts with the application.
# ********************************************************************

import copy
import re
import ssl
import time
from datetime import datetime, timedelta
from math import ceil
from random import randint
from urlparse import urlparse
import websocket
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.amos_cmd import delete_left_over_sessions
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.ldap import LDAP
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm

AMOS_WEBSOCKET_URL = "wss://%s/terminal-websocket/command/%s"
SOCKET_TIMEOUT = 60 * 60
IDLE_SOCKET_TIMEOUT = 4 * 60 * 1000
LDAP_AUTH_CMD = ('cmedit get {subnetwork},ManagedElement={node_id},SystemFunctions=1,SecM=1,'
                 'UserManagement=1,LdapAuthenticationMethod=1')
LDAP_STATUS_CMD = "{0},{1}".format(LDAP_AUTH_CMD, 'Ldap=1')


def get_radio_erbs_nodes(nodes):
    """
    This method return list of radio and erbs nodes
    :param nodes: List of Node objects
    :type nodes: list
    :return: list of radio and erbs node objects
    :rtype: list
    """
    radio_nodes = []
    erbs_nodes = []
    for node in nodes:
        if node.primary_type == "RadioNode":
            radio_nodes.append(node)
        elif node.primary_type == "ERBS":
            erbs_nodes.append(node)
    log.logger.debug("Radio nodes {0} and Erbs nodes {1}".format(radio_nodes, erbs_nodes))
    return radio_nodes, erbs_nodes


def delete_user_sessions(users):
    """
    This method deletes the user sessions after each iteration
    :param users: List of users
    :type users: list
    """
    session_deleter = get_workload_admin_user()
    for user in users:
        delete_left_over_sessions(user, session_deleter)
        log.logger.debug("Deleting AMOS profile user session for: {username}".format(username=user.username))


def check_ldap_is_configured_on_radio_nodes(profile, user, radio_nodes, name):
    """
    This method is used for configuring ldap on DG2 erbs nodes which are assigned to amos profiles
    :param profile: Profile instance
    :type profile: AMOS
    :param user: User object to be used to make requests
    :type user: enm_user_2.User object
    :param radio_nodes: List of allocated radio nodes to profile
    :type radio_nodes: list
    :param name: Name of the profile
    :type name: str
    :return: Returns LDAP configured radio nodes
    :rtype: list
    """
    log.logger.debug("Configuring ldap on {0} radio nodes ".format(len(radio_nodes)))
    synced, unsynced = check_sync_and_remove(radio_nodes, user)
    log.logger.debug(
        "The number synced {0} nodes and skipping number of unsynced {1} nodes".format(len(synced), len(unsynced)))
    nodes_with_improper_ldap = []

    for node in synced:
        response = user.enm_execute(LDAP_STATUS_CMD.format(subnetwork=node.subnetwork, node_id=node.node_id))
        response_string = "\n".join(response.get_output())
        match_pattern = re.compile(r'0 instance|:\s+\n|null')
        if match_pattern.search(response_string) is not None:
            nodes_with_improper_ldap.append(node)

    if nodes_with_improper_ldap:
        ldap = LDAP(user=user, nodes=nodes_with_improper_ldap, xml_file_name="xml_{0}.xml".format(name),
                    certificate_file_name="certificate_{0}.xml".format(name))
        try:
            ldap.configure_ldap_mo_from_enm()
        except Exception as e:
            profile.add_error_as_exception(e)

        for node in nodes_with_improper_ldap:
            try:
                ldap.set_filter_on_ldap_mo(node)
            except Exception as e:
                log.logger.debug("{0}. Skipping the node {1}".format(e.message, node))
                synced.remove(node)

    log.logger.info("All {0} synced radio nodes have LDAP configured".format(len(synced)))
    return synced


def create_websocket_connection(user):
    """
    :param user: User object to be used to make requests
    :type user: enm_user_2.User object
    :return: Websocket object that could be used to make websocket requests
    :rtype: object
    """
    user.get('/oss/idm/usermanagement/users/{0}'.format(user.username))
    time.sleep(1)
    user.get('/#advancedmoscripting?shell')
    time.sleep(1)
    parsed_url = urlparse(user.session.url())
    cookies = copy.copy(user.session.cookies)
    headers = copy.copy(user.session.headers)
    headers['Sec-WebSocket-Protocol'] = 'any-protocol'
    headers['Sec-WebSocket-Extensions'] = 'permessage-deflate; client_max_window_bits'
    cookies['TorUserID'] = user.username
    cookie = '; '.join('{0}={1}'.format(k, v) for k, v in cookies.items())
    header = [': '.join([k, v]) for k, v in cookies.items()]
    ws_url = AMOS_WEBSOCKET_URL % (parsed_url.netloc, user.username)
    time.sleep(1)
    return websocket.create_connection(ws_url, sslopt={'cert_reqs': ssl.CERT_NONE}, header=header, cookie=cookie,
                                       timeout=60 * 10)


def set_max_amos_sessions(profile, max_session_value):
    """
     set pib parameter for _maxAmosSessions
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :param max_session_value : User sets the MAX_AMOS_SESSIONS value per AMOS/SCRIPTING cluster VM
    :type max_session_value: int
    :raises EnmApplicationError: When failed to set PIB parameter
    """
    try:
        update_pib_parameter_on_enm(pib_parameter_name="maxAmosSessions",
                                    pib_parameter_value=max_session_value,
                                    enm_service_name="cmserv",
                                    service_identifier="terminal-websocket")
    except Exception as e:
        profile.add_error_as_exception(EnmApplicationError(e.message))


def taskset(user_nodes, commands, verify_timeout):
    """
    UI Flow to be used to run this profile
    :type user_nodes: tuple
    :param user_nodes: list of nodes to run by the user
    :type commands: list of strings
    :param commands: commands to be executed
    :type verify_timeout: int
    :param verify_timeout: time for command to complete (in seconds)
    :raises EnvironError: When node causes exception
    """
    # Amos test in scp-amos
    initialTime = datetime.now()
    log.logger.debug('Task initial time: ' + str(initialTime.year) + '/' + str(initialTime.month) + '/' +
                     str(initialTime.day) + ' ' + str(initialTime.hour) + ':' + str(initialTime.minute) +
                     ':' + str(initialTime.second))
    user, nodes, sleep = user_nodes
    log.logger.debug('USER: ' + str(user) + ' NODES: ' + str(nodes))
    for node in nodes:
        log.logger.debug("USER: {username} with NODE: {node}".format(username=user.username, node=node.node_id))
        time.sleep(sleep)
        log.logger.debug('Sleep: {0}'.format(sleep))
        try:
            amos_node_executor = AmosNodeExecutor(user, node, commands)
            amos_node_executor.run_commands(verify_timeout=verify_timeout)
        except websocket.WebSocketConnectionClosedException as e:
            raise websocket.WebSocketConnectionClosedException(
                'WebSocketConnectionClosedException: Failed amos connection to {0} ({1}). {2}'.format(
                    node.node_id, node.node_ip, str(e)))
        except websocket.WebSocketBadStatusException as e:
            raise websocket.WebSocketBadStatusException(
                'WebSocketBadStatusException: Failed socket connection for {0} to ({1}) {2}. %s %s'.format(
                    user.username, node.node_id, node.node_ip), str(e))
        except Exception as e:
            raise EnvironError('Exception caused by {0}({1}). {2}'.format(node.node_id, node.node_ip, str(e)))
        finally:
            try:
                # amos_node_executor.execute_exit_shell(amos_node_executor.AMOS_EXIT_SHELL + '\n')
                amos_node_executor.close()  # Closing Socket for node
            except Exception:
                log.logger.debug('Socket already closed after encountering exception above.')

    finalTime = datetime.now()
    log.logger.debug('Task end time: ' + str(finalTime.year) + '/' + str(finalTime.month) + '/' + str(finalTime.day) +
                     ' ' + str(finalTime.hour) + ':' + str(finalTime.minute) + ':' + str(finalTime.second))


def construct_command_list(cmd_list, cmds_per_iteration):
    """
    Constructs a list of amos commands which needs to be executed for every iteration of the profile, so that the daily
    totals are achieved with a limit of 138 commands/per user/per hour
    :param cmd_list: commands to be executed as part of the individual AMOS profiles
    :type cmd_list: list
    :param cmds_per_iteration: number of commands to be executed per iteration
    :type cmds_per_iteration: int
    :return: commands to be executed per user for each iteration
    :rtype: list
    """
    num_of_cmds = len(cmd_list)
    multiplier = ceil(cmds_per_iteration / float(num_of_cmds))
    commands = cmd_list * int(multiplier)
    num_of_cmds = len(commands)
    if num_of_cmds > cmds_per_iteration:
        difference = num_of_cmds - cmds_per_iteration
        for _ in range(difference):
            commands.pop()
    return commands


class AmosNodeExecutor(object):
    NODE_CONNECT_CMD = 'amos %s\n'
    AMOS_EXIT_SHELL = 'exit'

    def __init__(self, user, node, commands):
        """
        :param user: User object to use to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param node: Nodes child objects to be used for this flow
        :type node: enmutils.lib.enm_node.Node
        :param commands: list of commands to be executed
        :type commands: list
        :raises WebSocketTimeoutException: Socket gets timed out
        :raises WebSocketConnectionClosedException: When amos connection is failed towards node
        :raises WebSocketBadStatusException: When socket connection is failed
        :raises Exception: When an environment error occurs
        :raises WebSocketConnectionClosedException: When amos is not able to connect to node
        :raises WebSocketException: When Unable to fetch Host Details
        :raises EnvironError: When unable to get host details
        """
        self.user = user
        self.node = node
        self.commands = commands

        # def establish_websocket(self):
        log.logger.debug('Before creating Socket: {0}({1})'.format(self.node.node_id, self.node.node_ip))
        try:
            self.ws = create_websocket_connection(self.user)
        except websocket.WebSocketTimeoutException as e:
            raise websocket.WebSocketTimeoutException(
                'WebSocketTimeoutException: Verify node {0}({1}) is started and is currently added to ENM correctly '
                'with its security credentials. %s'.format(self.node.node_id, self.node.node_ip), str(e))
        except websocket.WebSocketBadStatusException as e:
            raise websocket.WebSocketBadStatusException(
                'Unsuccessfully created socket to AMOS KVM for user {0} using node {1}({2}). %s %s'.format(
                    self.user.username, self.node.node_id, self.node.node_ip), str(e))
        except websocket.WebSocketException as e:
            raise EnvironError("Unable to get Host Details: {0}".format(str(e)))
        except Exception:
            raise
        log.logger.debug('Socket created: {0}({1})'.format(self.node.node_id, self.node.node_ip))

    def connect(self):
        log.logger.debug('Before amos connection to node: {0}({1})'.format(self.node.node_id, self.node.node_ip))
        if self.execute(self.NODE_CONNECT_CMD % self.node.node_id, match='Not OK'):
            log.logger.debug(
                'Unsuccessfully connected amos to node {0}({1})'.format(self.node.node_id, self.node.node_ip))
            raise websocket.WebSocketConnectionClosedException(
                'Unsuccessfully connected amos to node {0}({1})'.format(self.node.node_id, self.node.node_ip))
        else:
            log.logger.debug(
                'Successfully connected amos to node: {0}'.format(self.NODE_CONNECT_CMD % self.node.node_ip))

    def execute(self, cmd, match=None, verify_timeout=20 * 60):
        """
        :param cmd: command to be executed
        :type cmd: str
        :param match: string to be matched against the response output received from the amos websocket connection
        :type match: str
        :param verify_timeout: time for command to complete (in seconds)
        :type verify_timeout: int
        :returns: Response of the command sent
        :rtype: bool
        """
        found = False
        self.ws.send(cmd)
        log.logger.info('Command sent: ' + cmd)
        timeout_time = datetime.now() + timedelta(seconds=verify_timeout)
        while datetime.now() < timeout_time:
            resp = self.ws.recv()
            output = str(resp).strip()
            if self.is_prompt(output):
                break
            if not found and match and re.search(match, resp):
                log.logger.debug('Error launching amos: {0}'.format(str(resp)))
                found = True
        return found

    def execute_exit_shell(self, cmd):
        """
        :param cmd: command to be executed
        :type cmd: str
        """
        log.logger.debug('Execution of shell command: {0}'.format(cmd))
        self.ws.send(cmd)
        resp = self.ws.recv()
        log.logger.debug(resp)
        if self.is_exit_shell(resp):
            log.logger.debug('Executed exit of shell command: {0}'.format(cmd))

    def execute_exit(self, cmd):
        """
        :param cmd: command to be executed
        :type cmd: str
        """
        time.sleep(2)
        log.logger.debug('Execution of amos command: {0}'.format(cmd))
        self.ws.send(cmd)
        resp = self.ws.recv()
        log.logger.debug(resp)
        if self.is_exit(resp):
            log.logger.debug('Executed exit of amos command: {0}'.format(cmd))

    def is_prompt(self, message):
        match = re.compile(r'\W*[a-zA-Z0-9]+>$')
        result = match.search(message)
        return True if result else False

    def is_exit(self, message):
        return 'Bye...' in message

    def is_exit_shell(self, message):
        return 'exit' in message

    def run_commands(self, wait_time=randint(2, 10), verify_timeout=60 * 20):
        self.connect()
        log.logger.debug('Begin to run all commands in node: {0}({1})'.format(self.node.node_id, self.node.node_ip))
        try:
            for command in self.commands:
                self.execute(command + '\n', verify_timeout=verify_timeout)
                log.logger.debug(
                    "Executed command: '{0}' in {1} ({2})".format(command, self.node.node_id, self.node.node_ip))
        finally:
            log.logger.debug('Finally exiting amos shell for node: {0}({1})'.format(self.node.node_id,
                                                                                    self.node.node_ip))
            self.execute_exit('exit' + '\n')
            time.sleep(wait_time)
            self.execute_exit_shell(self.AMOS_EXIT_SHELL + '\n')

    def close(self):
        log.logger.debug('Closing Socket for node {0}({1})'.format(self.node.node_id, self.node.node_ip))
        try:
            self.ws.close()
            log.logger.debug('Socket closed for node {0}({1})'.format(self.node.node_id, self.node.node_ip))
        except websocket.WebSocketConnectionClosedException:
            log.logger.debug('Socket already closed in close method')

    def _teardown(self):
        log.logger.debug('Teardown Socket for node {0}({1})'.format(self.node.node_id, self.node.node_ip))
        try:
            self.execute('exit' + '\n')
            self.execute_exit_shell(self.AMOS_EXIT_SHELL + '\n')
        except Exception:
            log.logger.debug('Socket already closed in teardown method')
            raise
        finally:
            self.close()
            log.logger.debug('Socket is now closed')
