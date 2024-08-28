import math
import random
from random import choice, randint
import time
from datetime import datetime, timedelta
from paramiko.ssh_exception import SSHException

from enmutils.lib import log
from enmutils.lib.arguments import get_random_string
from enmutils.lib.cache import (CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                get_emp, is_emp, is_enm_on_cloud_native)
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.shell import (Command, DEFAULT_VM_SSH_KEYPATH, run_cmd_on_vm, run_local_cmd, run_remote_cmd,
                                copy_file_between_wlvm_and_cloud_native_pod)
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.amos_cmd import delete_left_over_sessions, get_specific_scripting_iterator
from enmutils_int.lib.cmcli import (cm_cli_help, cm_cli_home, get_administrator_state, get_bfd, get_cell_attributes,
                                    get_cell_relations, get_cells_zzztemporary34_csirsperiodicity, get_collection,
                                    get_network_sync_status, get_node_cells,
                                    list_objects_in_network_that_match_specific_criteria, set_cell_attributes,
                                    execute_command_on_enm_cli)
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.netex import Collection
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services import deploymentinfomanager_adaptor

_FILE_TEXT = """#!/usr/bin/env python3

import enmscripting, sys
import time
if len(sys.argv) < 2:
    raise RuntimeError('No command specified')

try:
    session = enmscripting.open()
except:
    raise RuntimeError('Failed to successfully login')
else:
    command_string = sys.argv[1]
    commands = command_string.split(';;')
    for command in commands:
        print(">>> Executing: {0}".format(command))
        terminal = session.terminal()
        response = terminal.execute(command)
        request_id = response._handler._last_request_id
        response_code = response.http_response_code()
        if response.is_command_result_available():
            print('Command [{0}] was successful, response code: [{1}], with request_id: [{2}]'.format(command, response_code, request_id))
        else:
            print('Command was not successful {0}: response code: {1}, request_id: {2}'.format(command, response_code, request_id))
            raise RuntimeError('Command was not successful {0}: response code: {1}, request_id: {2}'.format(command, response_code, request_id))
finally:
    enmscripting.close(session)
    """
FILE_EXECUTOR_NAME = "cmcli_command_executor.py"
DIR = "/var/tmp/"
ENMCLI_SCRIPT_DIR = "/home/shared/enmcli/"


class EnmCli01Flow(GenericFlow):

    NODES = []
    NODE_TYPE = 'ENodeB'

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        node_attributes = ['node_id', 'managed_element_type', 'lte_cell_type']
        self.NODES = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        self.NODE_TYPE = self.NODES[0].managed_element_type if self.NODES[0].managed_element_type else self.NODE_TYPE
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            self.create_and_execute_threads(users, thread_count=len(users), args=[self], wait=60 * 60)
            self.sleep()

    @staticmethod
    def task_set(worker, profile):
        """
        UI Flow to be used to run this profile

        :param worker: User with which to perform the creations
        :type worker: `enm_user_2.User`
        :type profile: 'flowprofile.FlowProfile'
        :param profile: Profile to add errors to
        """
        get_cell_type = 'EUtranCellTDD' if profile.NODE_TYPE == 'ENodeB' and profile.NODES[0].lte_cell_type == 'TDD' else 'EUtranCellFDD'
        node_function, cell_type = ('ENodeBFunction', get_cell_type) if profile.NODE_TYPE == 'ENodeB' else ('GNBCUCPFunction', 'NRCellDU')
        try:
            cm_cli_home(user=worker)
            get_network_sync_status(worker)
            time.sleep(15 * 60)
            list_objects_in_network_that_match_specific_criteria(worker, node_function, cell_type)
            time.sleep(15 * 60)
            selection = random.choice([0, 1])
            if selection is 0:
                get_bfd(worker)
            else:
                get_cells_zzztemporary34_csirsperiodicity(worker, profile.NODES[0].node_id, profile.NODE_TYPE, cell_type)
        except Exception as e:
            profile.add_error_as_exception(e)


class EnmCli02Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        node_attributes = ['node_id', 'lte_cell_type', 'managed_element_type']
        while self.keep_running():
            node_info = zip(users, self.get_nodes_list_by_attribute(node_attributes=node_attributes))
            self.create_and_execute_threads(node_info, thread_count=len(users), args=[self], join=10,
                                            wait=self.SCHEDULE_SLEEP - 10)
            self.exchange_nodes()
            self.sleep()

    @staticmethod
    def get_new_attribute_values(attribute_default):
        """
        Gets new attribute values and sets them in a dictionary with the attribute name as the key

        :type attribute_default: dict
        :param attribute_default: dictionary of the current attribute values on the node

        :return: dict of attributes and values
        :rtype: dict
        """
        attribute_new_values = {}
        for key, value in attribute_default.items():
            if value == "false":
                attribute_new_values[key] = "true"
            elif value == "true":
                attribute_new_values[key] = "false"
        return attribute_new_values

    @staticmethod
    def task_set(worker, profile):
        """
        UI Flow to be used to run this profile

        :type worker: tuple
        :param worker: Tuple containing a user and node object
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        time.sleep(randint(1, 60 * 10))  # Start at a random point over a ten minute period
        user, node = worker
        get_cell_type = 'EUtranCellTDD' if node.lte_cell_type == 'TDD' else 'EUtranCellFDD'
        cell_type, administrative_state_cell_type, attribute_to_change = (('NRCellCU', 'NRCellDU',
                                                                           ['transmitSib2', 'transmitSib4', 'transmitSib5'])
                                                                          if 'gNodeBRadio'.lower() in node.node_id.lower()
                                                                          else (get_cell_type, get_cell_type,
                                                                                ['cfraEnable', 'acBarringForCsfbPresent',
                                                                                 'acBarringForMoSignallingPresent']))

        try:
            cells_ids = get_node_cells(user, node, cell_type=cell_type)
            admin_state = get_administrator_state(user, node, cell_type=administrative_state_cell_type)
            log.logger.debug('Administrative state for {0} : {1}'.format(node.node_id, admin_state))
            time.sleep(60)
            get_cell_relations(user, node, cell_type=cell_type)
            time.sleep(60)
            attribute_default = get_cell_attributes(user, node, cells_ids[0], attribute_to_change, cell_type=cell_type)
            log.logger.debug('Default values for cell {0} : {1}'.format(cells_ids[0], attribute_default))
            attribute_new_values = profile.get_new_attribute_values(attribute_default)
            set_cell_attributes(user, node, cells_ids[0], attribute_new_values, cell_type=cell_type)
            time.sleep(60)
            set_cell_attributes(user, node, cells_ids[0], attribute_default, cell_type=cell_type)
            time.sleep(60)
            cm_cli_help(user=user)
        except Exception as e:
            profile.add_error_as_exception(e)


class EnmCli03Flow(GenericFlow):

    IS_CLOUD_NATIVE = None

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        self.IS_CLOUD_NATIVE = is_enm_on_cloud_native()
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        node_attributes = ["node_id", "primary_type", "lte_cell_type"]
        nodes = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        cmedit_basic_users, cmedit_standard_users, cmedit_advanced_users, alarms_users = self.load_balance(
            len(users), self.total_commands_sec, self.percentage_cm_bas, self.percentage_cm_std, self.percentage_cm_adv,
            self.percentage_alarm, self.percentage_secadm)
        num_commands = int(math.ceil((self.total_commands_sec * 60 * 15) / len(users)))
        scripting_users = self.get_scripting_iterator(users)
        log.logger.info("cmedit_basic_users: {0}, cmedit_standard_users: {1},"
                        "cmedit_advanced_users: {2}, alarms_users: {3}".format(cmedit_basic_users,
                                                                               cmedit_standard_users,
                                                                               cmedit_advanced_users,
                                                                               alarms_users))
        iterator = 0
        while self.keep_running():
            users_scripting_users = (users, scripting_users)
            command_users = (cmedit_basic_users, cmedit_standard_users, cmedit_advanced_users, alarms_users)
            workers = self.create_commands_list(users_scripting_users, num_commands, command_users, nodes, iterator)
            try:
                if self.IS_CLOUD_NATIVE:
                    self.create_common_directory_in_scripting_cluster(users)
                self._deploy_execution_file()
                self.create_and_execute_threads(workers, thread_count=len(users), args=[self])
                self.delete_user_sessions(users)
                iterator = self.maintain_iter_value(iterator, len(nodes))
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    @staticmethod
    def create_common_directory_in_scripting_cluster(users):
        """
        Creates directory in scripting pod
        :param users: List of users
        :type users: list
        :raises EnvironError: Commands failed to execute in scripting pod
        :raises EnmApplicationError: Failed to connect to remote host
        """
        scripting_host = deploymentinfomanager_adaptor.get_list_of_scripting_service_ips()
        enmcli_dir_create = Command("mkdir -p {0}".format(ENMCLI_SCRIPT_DIR))
        try:
            output_enmcli_create_dir = run_remote_cmd(enmcli_dir_create, scripting_host[0], user=users[0].username,
                                                      password=users[0].password)
        except Exception as e:
            raise EnmApplicationError("Failed to setup connection to remote host. Error Message {0}".format(e))
        if output_enmcli_create_dir.rc != 0:
            raise EnvironError("Directory {0} failed to create in scripting pod {1} and response code is {2}, "
                               "response output is {3}".format(ENMCLI_SCRIPT_DIR, scripting_host[0],
                                                               output_enmcli_create_dir.rc,
                                                               output_enmcli_create_dir.stdout))

    def create_commands_list(self, users_scripting_users, num_commands, command_users, nodes, iterator):
        """
        Builds the list of ScriptingTaskset workers who will perform the commands executions

        :param users_scripting_users: List of users to match to commands, List of scripting iterators
        :type users_scripting_users: tuple
        :param num_commands: Total number of commands to be performed
        :type num_commands: int
        :param command_users: Total basic users, Total standard users, Total advanced users, Total alarm users
        :type command_users: tuple
        :param nodes: List of `enm_node.Node` objects to be used in the command
        :param iterator: Iterates between 2 nodes in nodes
        :type iterator: int
        :type nodes: list
        :return: List of ScriptingTaskset workers
        :rtype: list

        """
        node_type = "eNodeB" if 'LTE' in nodes[iterator].node_id else 'gNodeB'
        cell_type = ('EUtranCellTDD' if nodes[iterator].lte_cell_type == 'TDD' else 'EUtranCellFDD') if node_type == 'eNodeB' else None
        workers = []
        users, scripting_users = users_scripting_users
        cmedit_basic_users, cmedit_standard_users, cmedit_advanced_users, alarms_users = command_users
        for i, user in enumerate(users):
            total_list_commands = []
            for _ in range(num_commands):
                command = self.get_enmcli_command_based_on_users(i, cmedit_basic_users, cmedit_standard_users,
                                                                 cmedit_advanced_users, alarms_users, node_type)
                total_list_commands.append(command)
            log.logger.info("Number of commands run by user {0}: {1}".format(user, len(total_list_commands)))
            log.logger.info("Commands run by user {0}: {1}".format(i, total_list_commands))
            commands_string = ';;'.join(total_list_commands)
            if scripting_users:
                workers.append(ScriptingTaskset(user=users[i], command=commands_string,
                                                scripting_hostname=scripting_users[i],
                                                nodes=[nodes[iterator]], sleep=i * 3, cell_type=cell_type))
        return workers

    def get_enmcli_command_based_on_users(self, iteration, cmedit_basic_users, cmedit_standard_users, cmedit_advanced_users,
                                          alarms_users, node_type):
        """
        Get enmcli command based on cmedit users count and node type

        param iteration: index of iteration
        type iteration: int
        param cmedit_basic_users: count of cmedit basic users
        type cmedit_basic_users: int
        param cmedit_standard_users: count of cmedit standard users
        type cmedit_standard_users: int
        param cmedit_advanced_users: count of cmedit advanced users
        type cmedit_advanced_users: int
        param alarms_users: count of cmedit alarms users
        type alarms_users: int
        param node_type: type of node. gNodeB or eNodeB
        return: returns one cm cli command from enmcli_commands_list
        rtype: str
        """
        if iteration <= cmedit_basic_users:
            command = choice(self.enmcli_commands_list['cmedit_basic'][node_type])
        elif cmedit_basic_users < iteration <= cmedit_standard_users:
            command = choice(self.enmcli_commands_list['cmedit_standard'][node_type])
        elif cmedit_standard_users < iteration <= cmedit_advanced_users:
            command = choice(self.enmcli_commands_list['cmedit_advanced'][node_type])
        elif cmedit_advanced_users < iteration <= alarms_users:
            command = choice(self.enmcli_commands_list['alarm'])
        else:
            command = choice(self.enmcli_commands_list['secadm'])

        return command

    def get_scripting_iterator(self, users):
        """
        Query the deployment for available scripting iterators and assign to the users

        :param users: List of users to provide a scripting iterator to
        :type users: list

        :return: List of assigned scripting iterators
        :rtype: list
        """
        scripting_iterator = []
        scripting_user = []
        try:
            scripting_iterator = get_specific_scripting_iterator()
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError('Profile could not find the scripting cluster. '
                                                            'Error message {0}'.format(str(e))))
        if scripting_iterator:
            for _ in users:
                scripting_user.append(scripting_iterator.next())
        return scripting_user

    def delete_user_sessions(self, users):
        """
        Delete the user sessions not correctly closed

        :param users: List of users to try and delete
        :type users: list

        """
        session_deleter = get_workload_admin_user()
        for user in users:
            try:
                delete_left_over_sessions(user, session_deleter)
            except Exception as e:
                self.add_error_as_exception(e)
                continue

    @staticmethod
    def _make_file_executable():
        """
        Executes the command to make the generated file executable

        :raises EnvironError: raised if command fails
        """
        command_response = run_local_cmd(Command('chmod +x ' + DIR + FILE_EXECUTOR_NAME, timeout=60 * 10))
        if command_response.rc:
            raise EnvironError("Failed to make file executable, response: {0}".format(command_response.stdout))

    @staticmethod
    def _copy_to_emp(emp_ip_address, cmd):
        """
        Copies the executable file to the emp service

        :param emp_ip_address: The ip of the emp
        :type emp_ip_address: str
        :param cmd: Command to be executed
        :type cmd: str

        :raises EnvironError: raised if command fails
        """
        cmd_emp = cmd.format(key=CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, src_path=DIR, file_name=FILE_EXECUTOR_NAME,
                             user='cloud-user', dst_ip=emp_ip_address, path=DIR)
        log.logger.debug("Command to be executed: {0}".format(cmd_emp))
        command_response = run_local_cmd(Command(cmd_emp, timeout=60 * 10))
        if command_response.rc:
            raise EnvironError("Failed to copy file to emp, response: {0}".format(command_response.stdout))

    @staticmethod
    def _copy_to_cloud_scripting_clusters(emp_ip_address, cmd, scp):
        """
        Copy the executable file to the supplied cloud scp

        :param emp_ip_address: The ip of the emp
        :type emp_ip_address: str
        :param cmd: Command to be executed
        :type cmd: str
        :param scp: str
        :type scp: The name of cloud scp service

        :raises EnvironError: raised if command fails
        """
        cmd_scp = cmd.format(key=CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, src_path=DIR, file_name=FILE_EXECUTOR_NAME,
                             user='cloud-user', dst_ip=scp, path=DIR)
        log.logger.debug("Command to be executed: {0}".format(cmd_scp))
        command_response = run_cmd_on_vm(Command(cmd_scp), vm_host=emp_ip_address)
        if command_response.rc:
            raise EnvironError("Failed to copy file to emp, response: {0}".format(command_response.stdout))
        log.logger.debug("Successfully copied files on scripting/scp")
        log.logger.debug("Scripting/scp IP addresses: {0}".format(scp))

    @staticmethod
    def maintain_iter_value(iterator, nodes_count):
        iterator_value = 1 if iterator is 0 and nodes_count > 1 else 0
        return iterator_value

    def _copy_to_scripting_clusters(self, cmd, scp):
        """
        Copy the executable file to the supplied scp

        :param cmd: Command to be executed
        :type cmd: str
        :param scp: str
        :type scp: The name of scp service

        :raises EnvironError: raised if command fails
        """
        if self.IS_CLOUD_NATIVE:
            host_name = enm_deployment.get_pod_hostnames_in_cloud_native("general-scripting")
            for host in host_name:
                command_response = copy_file_between_wlvm_and_cloud_native_pod(host,
                                                                               "/var/tmp/cmcli_command_executor.py",
                                                                               ENMCLI_SCRIPT_DIR, 'to')
                if command_response.rc == 0:
                    break
        else:
            cmd_scp = cmd.format(key=DEFAULT_VM_SSH_KEYPATH, src_path=DIR, file_name=FILE_EXECUTOR_NAME,
                                 user='cloud-user', dst_ip=scp, path=DIR)
            log.logger.debug("Command to be executed: {0}".format(cmd_scp))
            command_response = run_local_cmd(Command(cmd_scp, timeout=60 * 10))
        if command_response.rc:
            raise EnvironError("Failed to copy file, response: {0}".format(command_response.stdout))
        log.logger.debug("Successfully copied files on scripting/scp")
        log.logger.debug("Scripting/scp IP addresses: {0}".format(scp))

    def _deploy_execution_file(self):
        """
        Creates and deploys the python execution file to execute commands on the scripting VMs
        It checks if ENM is running in a physical or cloud deployment

        :raises Exception: raised if dependent step fails
        """
        with open(DIR + FILE_EXECUTOR_NAME, mode='w') as script:
            script.write(_FILE_TEXT)
        cmd = "scp -i {key} -o stricthostkeychecking=no {src_path}{file_name} {user}@{dst_ip}:{path}"
        if is_emp():
            try:
                emp_ip_address = get_emp()
                self._copy_to_emp(emp_ip_address, cmd)
                scripting_distribution = enm_deployment.get_cloud_members_ip_address("scp")
                for scp in scripting_distribution:
                    try:
                        self._copy_to_cloud_scripting_clusters(emp_ip_address, cmd, scp)
                    except Exception as e:
                        self.add_error_as_exception(e)
            except Exception:
                raise
        else:
            scripting_distribution = deploymentinfomanager_adaptor.get_list_of_scripting_service_ips()
            for scp in scripting_distribution:
                try:
                    self._copy_to_scripting_clusters(cmd, scp)
                except Exception as e:
                    self.add_error_as_exception(e)

    @staticmethod
    def task_set(worker, profile):
        """
        Task that will be executed by the thread queue
        :param worker: Worker object to perform the required command(s)
        :type worker: ScriptingTaskset
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        time.sleep(worker.sleep)  # Sleep * 3 seconds to reduce the overlapping of all 100 users
        cmd_timeout = 600  # 10 minutes to match the default time out in enm-scripting library
        log.logger.debug("Running the following command/s on scripting VM: {command}".format(command=worker.command))
        try:
            file_dir = ENMCLI_SCRIPT_DIR if profile.IS_CLOUD_NATIVE else DIR
            command_response = run_remote_cmd(Command("python {DIR}{file_name} '{command}'"
                                                      .format(DIR=file_dir, file_name=FILE_EXECUTOR_NAME,
                                                              command=worker.command), timeout=cmd_timeout),
                                              worker.scripting_hostname, worker.user.username,
                                              password=worker.user.password, new_connection=True)
            if command_response.rc:
                profile.add_error_as_exception(EnmApplicationError("ERROR running command: {1}, response: {0}"
                                                                   .format(command_response.stdout, worker.command)))
        except SSHException as e:
            profile.add_error_as_exception(EnvironError(e.message))
        except Exception as e:
            profile.add_error_as_exception(EnmApplicationError(e.message))

    @staticmethod
    def load_balance(num_users, total_commands_sec, percentage_cm_bas, percentage_cm_std, percentage_cm_adv,
                     percentage_alarm, percentage_secadm):
        """
        Calculates the percentage of commands per command type and user volume

        :param num_users: Total number of users
        :type num_users: int
        :param total_commands_sec: Total commands per second
        :type total_commands_sec: int
        :param percentage_cm_bas: Total basic commands
        :type percentage_cm_bas: float
        :param percentage_cm_std: Total standard commands
        :type percentage_cm_std: float
        :param percentage_cm_adv: Total advanced commands
        :type percentage_cm_adv: float
        :param percentage_alarm: Total alarm commands
        :type percentage_alarm: float
        :param percentage_secadm: Total security commands
        :type percentage_secadm: float

        :return: Tuple containing the user calculations
        :rtype: tuple
        """

        cmedit_basic_users = int(math.ceil((percentage_cm_bas * num_users) / 100))
        cmedit_standard_users = int(round(percentage_cm_std * num_users) / 100)
        cmedit_advanced_users = int(round(percentage_cm_adv * num_users) / 100)
        alarm_users = int(round(percentage_alarm * num_users) / 100)
        secadm_users = int(round(percentage_secadm * num_users) / 100)

        log.logger.info("CMEDIT_bas commands. {0} users 0 to {1}".format(cmedit_basic_users, cmedit_basic_users - 1))
        log.logger.info("CMEDIT_std commands. {0} users {1} to {2}".format(cmedit_standard_users,
                                                                           cmedit_basic_users,
                                                                           cmedit_basic_users + cmedit_standard_users))
        log.logger.info("CMEDIT_adv commands. {0} users {1} to {2}".format(cmedit_advanced_users, cmedit_basic_users +
                                                                           cmedit_standard_users + 1,
                                                                           cmedit_basic_users + cmedit_standard_users +
                                                                           cmedit_advanced_users))
        log.logger.info("ALARM commands. {0} users {1} to {2}".format(alarm_users, cmedit_basic_users +
                                                                      cmedit_standard_users + cmedit_advanced_users + 1,
                                                                      cmedit_basic_users + cmedit_standard_users +
                                                                      cmedit_advanced_users + alarm_users))
        log.logger.info("SECADM commands. {0} users {1} to {2}".format(secadm_users, cmedit_basic_users +
                                                                       cmedit_standard_users + cmedit_advanced_users +
                                                                       alarm_users + 1, cmedit_basic_users +
                                                                       cmedit_standard_users + cmedit_advanced_users +
                                                                       alarm_users + secadm_users))

        log.logger.info("Total number of users: {0}".format(
            cmedit_basic_users + cmedit_standard_users + cmedit_advanced_users + alarm_users + secadm_users))
        log.logger.info("Number of commands run by every user per iteration: {0} ".format(
            int(math.ceil((total_commands_sec * 60 * 15) / num_users))))

        return (cmedit_basic_users - 1,
                cmedit_basic_users + cmedit_standard_users,
                cmedit_basic_users + cmedit_standard_users + cmedit_advanced_users,
                cmedit_basic_users + cmedit_standard_users + cmedit_advanced_users + alarm_users)


class EnmCli05Flow(GenericFlow):

    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 0, 20, 0)
    SCHEDULED_TIMES = [start_time + timedelta(hours=hour) for hour in xrange(0, 23, 1)]
    collection = None

    def manage_collection(self, user):
        """
        Instantiates and creates the collection to be used by the profile

        :type user: `enm_user_2.User`
        :param user: User will create the collection
        """
        collection_name = "enmcli_05_collection_{0}".format(get_random_string(size=6))
        self.collection = Collection(user=user, name=collection_name, nodes=self.nodes_list)
        try:
            self.collection.create()
            teardown_collection = Collection(user=user, name=collection_name, nodes=[])
            teardown_collection.id = self.collection.id
            self.teardown_list.append(teardown_collection)
            self.collection.nodes = []
        except Exception as e:
            self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            self.sleep_until_time()
            if not self.collection or not self.collection.id:
                self.manage_collection(users[0])
            try:
                cm_cli_home(users[0])
                get_collection(users[0], self.collection.name)
            except Exception as e:
                self.add_error_as_exception(e)


class ScriptingTaskset(object):
    """
    Object defining the user, command, node and scripting VM to use in relation to running a command in a scripting VM
    """

    def __init__(self, user, command, scripting_hostname, nodes, sleep, cell_type=None):
        self.user = user
        node_id = nodes[0].node_id
        self.ten_node_id = node_id[:-2] + "1*" if node_id[-2] == "0" and node_id[-3] == "0" else node_id[:-1] + "*"
        self.ninetynine_node_id = node_id[:-3] + "0*" if node_id[-3] != "0" else node_id[:-2] + "*"
        begin_date = datetime.today() - timedelta(hours=1)
        self.primary_type = nodes[0].primary_type
        self.command = command.format(node_id=node_id, date=begin_date.strftime('%Y-%m-%dT%H:%M:%S'),
                                      ten_node_id=self.ten_node_id, ninetynine_node_id=self.ninetynine_node_id,
                                      primary_type=self.primary_type, cell_type=cell_type)
        self.node = nodes[0]
        self.sleep = sleep
        self.scripting_hostname = scripting_hostname
        self.name = "{0}.py".format(user.username)


class EnmCli08Flow(GenericFlow):

    CREATE_CMD = 'cmedit create {0},mode=1 mode-key=1'
    GET_MO_CMD = 'cmedit get {0}'
    UPDATE_CMD = 'cmedit set {0} speed={1}'
    DELETE_CMD = 'cmedit delete {0},mode=1'

    def execute_flow(self):
        """
        Execute the profile flow
        """
        sub_mo = "card=1"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        node = self.get_nodes_list_by_attribute()[0]
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            epg_fdn = self.get_mo(user, self.GET_MO_CMD.format("{0} {1}".format(node.node_id, sub_mo)))
            if epg_fdn:
                for index, cmd in enumerate([self.CREATE_CMD.format(epg_fdn),
                                             self.UPDATE_CMD.format(epg_fdn, 1000),
                                             self.UPDATE_CMD.format(epg_fdn, 100),
                                             self.DELETE_CMD.format(epg_fdn)]):
                    if index:
                        log.logger.debug("Sleeping for {0} seconds before attempting next command.".format(
                            self.SLEEP_TIME_BETWEEN_COMMANDS))
                        time.sleep(self.SLEEP_TIME_BETWEEN_COMMANDS)
                    try:
                        execute_command_on_enm_cli(user, cmd)
                    except Exception as e:
                        self.add_error_as_exception(e)
            else:
                log.logger.debug("No {0} MO found on node: [{1}]".format(sub_mo, node.node_id))
            self.exchange_nodes()

    def get_mo(self, user, cmd):
        """
        Return the MO value based upon the supplied command

        :param user: User who query ENM for the MO
        :type user: `enm_user_2.User`
        :param cmd: Cmedit command sent to ENM
        :type cmd: str

        :return: MO FDN value if found or None
        :rtype: str
        """
        fdn_key = "FDN : "
        mo_fdn = None
        try:
            response = execute_command_on_enm_cli(user, cmd)
            for line in response.get_output():
                if fdn_key in line:
                    mo_fdn = line.split(fdn_key)[-1]
            return mo_fdn
        except Exception as e:
            self.add_error_as_exception(e)
