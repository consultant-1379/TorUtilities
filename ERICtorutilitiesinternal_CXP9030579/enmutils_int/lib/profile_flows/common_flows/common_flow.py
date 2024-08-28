import datetime
import time
from functools import partial
import pexpect

from enmutils.lib import log
from enmutils.lib import shell
from enmutils.lib.enm_node import get_nodes_by_cell_size
from enmutils.lib.exceptions import NotSupportedException, EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.cache import (is_emp, get_ms_host, get_emp, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                is_enm_on_cloud_native, get_enm_cloud_native_namespace)
from enmutils.lib.enm_user_2 import Target, EnmRole
from enmutils_int.lib import node_pool_mgr, winfiol_operations, enm_deployment
from enmutils_int.lib.enm_user import get_workload_admin_user, CustomUser
from enmutils_int.lib.services import nodemanager_adaptor
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils_int.lib.configure_wlvm_common import create_ssh_keys
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (set_up_alarm_text_size_and_problem_distribution,
                                                                     set_up_event_type_and_probable_cause,
                                                                     map_alarm_rate_with_nodes, setup_alarm_burst)
from enmutils_int.lib.shm_utilities import SHMUtils
from enmutils_int.lib import netsim_operations
from enmutils_int.lib.services.deployment_info_helper_methods import build_poid_dict_from_enm_data
from enmutils_int.lib.services.nodemanager_helper_methods import (update_poid_attribute_on_nodes,
                                                                  update_cached_nodes_list)


def verify_and_generate_ssh_keys(profile, machine):
    """
    verify and generate ssh keys.

    :param profile: Profile object
    :type profile: profileObject`
    :param machine: Remote machines
    :type machine: str
    """
    if profile.is_cloud_native:
        log.logger.debug("Removing scripting VIP from known_hosts file on workload VM as "
                         "'Host key verification' failures can sometimes occur while using ssh-copy-id towards VIP, "
                         "due to host changes on the cluster")
        shell.run_local_cmd(shell.Command("ssh-keygen -R {0}".format(machine)))
    else:
        create_ssh_keys()


class PlaceHolderFlow(FlowProfile):
    NOTE = ""

    def execute_flow(self):
        """
        Executes the Placeholder flow
        """
        log.logger.error(self.NOTE)
        self.add_error_as_exception(NotSupportedException(self.NOTE))


class GenericFlow(FlowProfile):

    def create_profile_users(self, number_of_users, roles, fail_fast=False, safe_request=False, retry=True):
        """
        Create the user for the profile

        :type number_of_users: int
        :param number_of_users: Number of users to create
        :type roles: list
        :param roles: list of roles to give to users
        :type fail_fast: bool
        :param fail_fast: exit execution if user fails to create
        :type safe_request: bool
        :param safe_request: Ignore certain requests exceptions
        :type roles: list
        :param roles: List of ENM supported user roles
        :type retry: bool
        :param retry: Retry if the user creation fails

        :rtype: list
        :return: List of `enm_user_2.User` objects
        """
        return self.create_users(number=number_of_users, roles=roles, fail_fast=fail_fast,
                                 safe_request=safe_request, retry=retry)

    def create_custom_user_object(self):
        """
        creates a custom user object

        :return: customuser
        :rtype: enmutils_int.lib.enm_user.CustomUser
        """
        roles = []
        if self.USER_ROLES:
            roles.extend(self.USER_ROLES)

        if hasattr(self, "CUSTOM_USER_ROLES"):
            roles.extend(self.CUSTOM_USER_ROLES)

        if hasattr(self, "CUSTOM_TARGET_GROUPS"):
            targets = list(set(Target(tg_group) if isinstance(tg_group, basestring) else tg_group for tg_group
                               in self.CUSTOM_TARGET_GROUPS))
        else:
            targets = [Target("ALL")]

        user_pwd = self.USER_PASSWORD if hasattr(self, "USER_PASSWORD") else "TestPassw0rd"
        auth_mode = self.USER_AUTH_MODE if hasattr(self, "USER_AUTH_MODE") else None

        roles = list(set(EnmRole(role) if isinstance(role, basestring) else role for role in roles))
        custom_user = CustomUser(username=self.USER_NAME, password=user_pwd, roles=roles,
                                 targets=targets, safe_request=False, retry=True, persist=False,
                                 keep_password=True, authmode=auth_mode)
        return custom_user

    def create_custom_user_in_enm(self, user_string="External LDAP user", expected_sleep_time=300):
        """
        creates a custom user in ENM

        :type user_string: str
        :param user_string: user specific to profile
        :type expected_sleep_time: int
        :param expected_sleep_time: time to sleep after creating user

        :return: customuser
        :rtype: enmutils_int.lib.enm_user.CustomUser

        :raises EnmApplicationError: If user creation is not successful even after all the re-tries
        :raises e: if method throws an error
        """
        retries = 0
        custom_user = self.create_custom_user_object()
        while retries < self.NUMBER_OF_RETRIES:
            try:
                custom_user.create()
                log.logger.debug("{0} created successfully in ENM, sleeping for {1} seconds before trying "
                                 "to login".format(user_string, expected_sleep_time))
                time.sleep(expected_sleep_time)
                self.teardown_list.append(custom_user)
                break
            except Exception as e:
                log.logger.debug("Exception : {0}".format(e))
                sleep_time = 120 if retries < 5 else 60 * retries
                log.logger.debug("Failed to create {0} in ENM, sleeping for {1} "
                                 "seconds before retrying.".format(user_string, sleep_time))
                time.sleep(sleep_time)
                retries += 1
        try:
            user_created = custom_user.is_session_established()
            if not user_created:
                raise EnmApplicationError("{0} creation in ENM failed, "
                                          "please check the profile log for more details".format(user_string))
        except Exception as e:
            raise e

        self.user_count += 1

        return custom_user

    def create_and_execute_threads(self, workers, thread_count, func_ref=None, args=None, wait=None, join=None,
                                   last_error_only=True):
        """
        Creates and executes a number of thread, based on the supplied values

        :type workers: list
        :param workers: List of object which will perform the actions once passed into threads
        :type thread_count: int
        :param thread_count: Required number of threads to spawn
        :type func_ref: function
        :param func_ref: Function name on which the thread should work upon
        :type args: list
        :param args: List of additional arguments to supply if required
        :type wait: int
        :param wait: Time to wait in seconds for threads to complete
        :type join: int
        :param join: Time to wait in seconds before attempting to join threads
        :type last_error_only: bool
        :param last_error_only: Add the last error only generated by a ThreadQueue. Reduces over logging
        """
        if not workers:
            self.add_error_as_exception(EnvironError("Empty workers list provided, please check for worker creation "
                                                     "errors."))
            return
        func_ref = func_ref if func_ref else self.task_set
        tq = ThreadQueue(workers, num_workers=thread_count, func_ref=func_ref, args=args, task_wait_timeout=wait,
                         task_join_timeout=join)
        tq.execute()
        self.process_thread_queue_errors(tq, last_error_only=last_error_only)

    @staticmethod
    def task_set(worker, profile):
        """
        Task set for use with thread queue

        :type worker: list
        :param worker: Object to be the worker
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """

    def get_synchronised_nodes(self, nodes, user):
        """
        Returns the list of synchronised nodes

        :type nodes: list
        :param nodes: List of `enm_node.Node` instances
        :type user: `enm_user_2.User`
        :param user: User who will query the sync status
        :rtype: list
        :return: List of `enm_node.Node` instances
        """
        synced = []
        try:
            synced, unsynced = check_sync_and_remove(nodes=nodes, user=user)
            log.logger.debug('Available synced nodes: {0}'.format(len(synced)))
            if unsynced:
                log.logger.debug("Removing {0} non-managed nodes on this iteration.".format(len(unsynced)))
        except Exception as e:
            self.add_error_as_exception(e)
        return synced

    def get_allocated_synced_pm_enabled_nodes(self, user):
        """
        To get the Synced and pm enabled nodes from allocated nodes.

        :rtype: list
        :return: List of synced pm enabled nodes

        :raises EnvironError: if Synced nodes are not available, PM Function is not enabled on all nodes
        """
        node_attributes = ["node_id", "primary_type", "poid", "profiles"]
        log.logger.debug("Getting allocated, synced, PM enabled nodes")
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        if nodes_list:
            synced_nodes = self.get_synchronised_nodes(nodes_list, user)
            if synced_nodes:
                synced_pm_enabled_nodes, _ = enm_deployment.get_pm_function_enabled_nodes(synced_nodes, user)
                if synced_pm_enabled_nodes:
                    return synced_pm_enabled_nodes
                else:
                    raise EnvironError("PM is not enabled on any nodes allocated to the profile")
            else:
                raise EnvironError("None of the allocated node are synced")
        else:
            raise EnvironError("Nodes are not allocated to profile")

    def exchange_nodes(self):
        """
        Exchange the profiles allocated nodes
        """
        try:
            if nodemanager_adaptor.can_service_be_used(self):
                nodemanager_adaptor.exchange_nodes(self)
            else:
                node_pool_mgr.exchange_nodes(self)
        except Exception as e:
            self.add_error_as_exception(e)

    def get_allocated_nodes(self, profile_name):
        """
        Get the list of nodes allocated to a profile

        :param profile_name: Name of profile
        :type profile_name: str
        :return: List of Node objects
        :rtype: list
        """
        try:
            if nodemanager_adaptor.can_service_be_used(self):
                return nodemanager_adaptor.get_list_of_nodes_from_service(profile_name, node_attributes=["all"])
            else:
                return node_pool_mgr.get_pool().allocated_nodes(profile_name)
        except Exception as e:
            self.add_error_as_exception(e)

    def allocate_specific_nodes_to_profile(self, nodes):
        """
        Allocate certain nodes to profile (e.g. if profile needs to use same nodes as another profile)

        :param nodes: List of Node objects
        :type nodes: list
        """
        try:
            if nodemanager_adaptor.can_service_be_used(self):
                nodemanager_adaptor.allocate_nodes(profile=self, nodes=nodes)
            else:
                node_pool_mgr.allocate_nodes(self, nodes)
        except Exception as e:
            self.add_error_as_exception(e)

    @staticmethod
    def generate_configurable_source_ip(ip_list):
        """
        Configurable ipv4 string

        :param ip_list: List of values in an ip
        :type ip_list: list

        :return: String ip
        :rtype: str
        """
        return ".".join([str(ip) for ip in ip_list])

    def update_profile_persistence_nodes_list(self, unused_nodes, nodes_list=None):
        """
        Function to deallocate unused nodes from the profile and to update the self.nodes persistence value of profile
        :param unused_nodes: List of unused nodes which needs to be deallocated from profile
        :type unused_nodes: list
        :param nodes_list: List of allocated nodes to the profile
        :type nodes_list: list
        """
        if unused_nodes:
            log.logger.debug("Starting de-allocation of {0} unused nodes".format(len(unused_nodes)))
            try:
                SHMUtils.deallocate_unused_nodes(unused_nodes, self)
                if nodes_list:
                    self.num_nodes = (len(nodes_list) - len(unused_nodes) if (len(nodes_list) > len(unused_nodes))
                                      else 0)
                else:
                    self.num_nodes -= len(unused_nodes)
                self.persist()
                log.logger.debug("Successfully de-allocated unused nodes {0}".format(len(unused_nodes)))
            except Exception as e:
                self.add_error_as_exception(e)
        else:
            if nodes_list:
                log.logger.debug("Updating num_nodes attribute with {0} number of nodes".format(len(nodes_list)))
                self.num_nodes = len(nodes_list)
                self.persist()
            log.logger.debug("No unused nodes exists for de-allocation.")

    def deallocate_unused_nodes_and_update_profile_persistence(self, synced):
        """
        Function to collect the unused node for de-allocation and call for node deallocation and persistence updation
        :param synced: List of synced nodes which needs to be retained for profile
        :type synced: list
        """
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "profiles"])
        unused_nodes = [node for node in nodes_list if node.node_id not in [sync_node.node_id for sync_node in synced]]
        self.update_profile_persistence_nodes_list(unused_nodes, nodes_list)

    def deallocate_IPV6_nodes_and_update_profile_persistence(self):
        """
        Function to collect the IPV6 nodes for deallocation and call for node deallocation and persitence updation
        """
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_ip", "profiles"])
        ipv6_nodes_list = [node for node in nodes_list if ":" in node.node_ip]
        log.logger.debug("De-allocating the IPV6 nodes [{0}] as they are"
                         " not supported for profile {1}".format(ipv6_nodes_list, self.NAME))
        self.update_profile_persistence_nodes_list(ipv6_nodes_list, nodes_list)

    def get_start_time_today(self):
        """
        Get expected start time for current date
        when profile is scheduled daily on specific times

        :return:    expected start time for the current day (for creation)
        :rtype:     `datetime.datetime`
        """
        time_now = datetime.datetime.now()
        start_time = datetime.datetime.strptime(self.SCHEDULED_TIMES_STRINGS[0], "%H:%M:%S")

        expected_start_time_today = start_time.replace(
            year=time_now.year, month=time_now.month, day=time_now.day,
            hour=start_time.hour, minute=start_time.minute, second=start_time.second)

        return expected_start_time_today

    def get_nodes_with_required_number_of_cells(self):
        """
        Create a list of nodes that have the required cells. Gets nodes by the cell size.
        Gets a full list of nodes as per the profile and then checks for common nodes in both persistence and
        the list of cells node list.

        :raises EnvironError: if no nodes containing the required cells exist.

        :return: list of nodes that have the required cells
        :rtype: list
        """
        try:
            log.logger.debug("Attempting to get nodes that have {0} cells".format(self.NUMBER_OF_CELLS))
            nodes_available_with_the_required_cells = get_nodes_by_cell_size(self.NUMBER_OF_CELLS,
                                                                             get_workload_admin_user())
        except Exception:
            raise EnvironError(
                "There are no nodes available with {0} cells for {1}".format(self.NUMBER_OF_CELLS, self.NAME))

        persisted_nodes = {node.node_name: node for node in self.get_nodes_list_by_attribute(['node_name', 'node_id',
                                                                                              'poid'])}
        nodes_with_the_required_cells = [persisted_nodes[node] for node in
                                         list(set(nodes_available_with_the_required_cells).intersection(
                                             set(persisted_nodes.keys())))]
        return nodes_with_the_required_cells

    def get_end_time(self):
        """
        Gets the end time for the profile
        :return: End time of the run interval
        :rtype: datetime.datetime
        """
        log.logger.debug("Getting end time")
        now = datetime.datetime.now()
        schedule_end = datetime.datetime.strptime(self.RUN_UNTIL, "%H:%M:%S")
        end_time = now.replace(hour=schedule_end.hour, minute=schedule_end.minute, second=schedule_end.second)
        if now > end_time:
            log.logger.debug("Adding a day to end time")
            end_time = end_time + datetime.timedelta(days=1)
            self.sleep_until_time()
        log.logger.debug("End time:{0}".format(end_time))
        return end_time

    def execute_netsim_command_on_netsim_node(self, nodes, netsim_node_command):
        """
        Execute netsim command against simulated node

        :type nodes: list
        :param nodes: List of `enm_node.Node` instances
        :param netsim_node_command: Command to be executed against Netsim Node
        :type netsim_node_command: str
        :return: Result of operation
        :rtype: boolean
        """
        node_ids = [node.node_id for node in nodes]
        log.logger.debug("Executing netsim command against node(s) {0}: {1}".format(node_ids, netsim_node_command))
        try:
            netsim_operation = netsim_operations.NetsimOperation(nodes)
            netsim_operation.execute_command_string(netsim_node_command)
        except Exception as e:
            log.logger.debug("Problem encountered trying to execute command on node(s) {0}: '{1}' - {2}".format(
                node_ids, netsim_node_command, str(e)))
            return False

        log.logger.debug("Execution of netsim command against node(s) {0} completed".format(node_ids))
        return True

    def download_tls_certs(self, users):
        """
        Executes pki commands and download tls certificates
        :param users: List of User Object
        :type users: list
        """
        try:
            winfiol_operations.create_pki_entity_and_download_tls_certs(users)
        except Exception as e:
            self.add_error_as_exception(e)
        self.teardown_list.append(partial(picklable_boundmethod(self.download_tls_certs_teardown_operations), users))

    def download_tls_certs_teardown_operations(self, users):
        """
        Performs teardown activities of pki commands and tls certificates
        :param users: List of User Object
        :type users: list
        """
        winfiol_operations.perform_revoke_activity(users)

    def enable_passwordless_login_for_users(self, child, users, ip_list, is_scripting_vm=False):
        """
        Enable password-less ssh login to scripting cluster for list of users

        :param child: ssh terminal spawned using pexpect
        :type child: pexpect.spawn
        :param users: List of User objects
        :type users: list
        :param ip_list: list of Scripting cluster IP addresses
        :type ip_list: list
        :param is_scripting_vm: By default value is False,Need to pass value with True,
                                if need to enable user passwordless login for scripting pod on CENM.
        :type is_scripting_vm: bool
        """
        profile = self

        for user in users:
            log.logger.debug("Enabling passwordless ssh access to scripting cluster for user: {0}"
                             .format(user.username))

            for ip in ip_list:
                if (self.enable_passwordless_login_for_user(profile, child, user, ip, is_scripting_vm=is_scripting_vm) and
                        self.remove_duplicate_authorized_keys(user, ip) and len(ip_list) > 1):
                    log.logger.debug("No need to repeat operations on other hosts as already successful on one host")
                    break

    @staticmethod
    def remove_duplicate_authorized_keys(user, ip):
        """
        Remove duplicate keys from remote authorized keys file

        :param user: User object
        :type user: enmutils.lib.enm_user_2.User
        :param ip: IP address
        :type ip: str
        :return: boolean to indicate success or not
        :rtype: bool
        """
        log.logger.debug("Remove duplicate keys from remote authorized keys file")

        try:

            remove_duplicates_cmd = "sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.uniq"
            cmd = shell.Command(remove_duplicates_cmd)
            shell.run_remote_cmd(cmd, ip, user.username, password=user.password)

            replace_file_cmd = "mv ~/.ssh/authorized_keys{.uniq,}"
            cmd = shell.Command(replace_file_cmd)
            shell.run_remote_cmd(cmd, ip, user.username, password=user.password)

            log.logger.debug("Duplicate keys removal operation complete")
            return True
        except Exception as e:
            log.logger.debug("Failed to remove duplicate keys - {0}".format(str(e)))

    @staticmethod
    def switch_to_ms_or_emp():
        """
        Spawns a ssh session towards LMS or EMP based on the deployment
        :return: child with ssh terminal logged in as cloud-user
        :rtype: pexpect.spawn
        :raises EnvironError: if ssh connection fails towads the LMS or EMP
        """
        if is_enm_on_cloud_native():
            raise EnvironError("Unsupported deployment, cannot execute ncm restore commands.")
        if is_emp():
            log.logger.debug("Executing ssh to EMP on cloud")
            child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}'.
                                  format('cloud-user', get_emp(), CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, timeout=30))
            child.expect('cloud-user@')
            log.logger.debug("Connected to EMP")
        else:
            ms_host = get_ms_host()
            log.logger.debug("LMS host IP address is :{0}".format(ms_host))
            try:
                child = pexpect.spawn('ssh -o StrictHostKeyChecking=no root@{0}'.format(ms_host), timeout=30)
                child.expect("root@")
                log.logger.debug("Connected to LMS")
            except Exception:
                raise EnvironError("The pexpect timed-out! Please check if there is password-less connection setup"
                                   "between LMS and Workload VM.")
        return child

    @staticmethod
    def enable_passwordless_login_for_user(profile, child, user, machine, is_scripting_vm=False):
        """
        Enable password-less ssh login to remote machines for list of users

        :param profile: Profile object
        :type profile: profileObject`
        :param child: ssh terminal spawned using pexpect
        :type child: pexpect.spawn
        :param user: User object
        :type user: `enm_user_2.User`
        :param machine: Remote machines
        :type machine: str
        :return: Boolean to indicate success of operation
        :rtype: bool
        :param is_scripting_vm: By default value is False,Need to pass value with True,
                                if need to enable user passwordless login for scripting pod on CENM.
        :type is_scripting_vm: bool
        """
        log.logger.debug(
            "Enabling passwordless login for {user} on {machine}".format(user=user.username, machine=machine))
        verify_and_generate_ssh_keys(profile, machine)

        if profile.is_cloud_native and is_scripting_vm:
            shell.run_local_cmd(shell.Command("sed -i '/\\[{0}\\]:5020/d' ~/.ssh/known_hosts".format(machine)))
            cmd = "ssh-copy-id {user}@{machine} -p 5020".format(user=user.username, machine=machine)
        else:
            cmd = "ssh-copy-id {user}@{machine}".format(user=user.username, machine=machine)
        log.logger.debug("Executing command: {0}".format(cmd))
        password_format = "[pP]assword:"
        if child:
            child.sendline(cmd)
        else:
            child = pexpect.spawn(cmd, timeout=30)

        auth_prompt = "Are you sure you want to continue connecting (yes/no)?"

        result = child.expect([auth_prompt, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            log.logger.debug("Confirming connection: yes")
            child.sendline("yes")
            result = child.expect([auth_prompt, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if result == 1:
            log.logger.debug("Issuing password")
            child.sendline(user.password)
            result = child.expect([auth_prompt, password_format, pexpect.EOF, pexpect.TIMEOUT])
        pexpect_copy_cmd_output = child.before
        log.logger.debug("pexpect copy command output :{0}".format(pexpect_copy_cmd_output))
        match_string = "Now try logging into the machine"
        if result == 2 and match_string in str(pexpect_copy_cmd_output):
            log.logger.debug("Passwordless ssh login setup complete for {0}".format(user.username))
            return True
        else:
            log.logger.debug("Problem encountered trying to enable passwordless ssh login")
            return False

    def update_nodes_with_poid_info(self):
        """
        Update nodes with POID info from ENM
        :raises EnvironError: if cant update POID values
        """
        log.logger.debug("Updating nodes with POID info from ENM")
        if self.nodemanager_service_can_be_used:
            log.logger.debug(nodemanager_adaptor.update_poids())
        else:
            enm_poid_dict = build_poid_dict_from_enm_data()
            update_cached_nodes_list()
            failures = update_poid_attribute_on_nodes(enm_poid_dict)
            if failures:
                raise EnvironError("Failed to update POID values in workload pool for {0} node(s).".format(failures))
        log.logger.debug("POID info update complete")


class FMAlarmFlow(GenericFlow):

    def configure_fm_alarm_burst(self, alarm_size_distribution, alarm_problem_distribution, profile_nodes, burst_id,
                                 teardown_list, items_to_retain):
        """
        Configures alarm burst for continuous, peak and storm
        :param alarm_size_distribution: alarm text size
        :type alarm_size_distribution: list
        :param alarm_problem_distribution: alarm specific problem and severity attributes
        :type alarm_problem_distribution: list
        :param profile_nodes: nodes allocated to the profile
        :type profile_nodes: dict
        :param burst_id: unique ID used to trigger the alarm burst
        :type burst_id: str
        :param teardown_list: list containing objects to be removed during profile teardown
        :type teardown_list: list
        :param items_to_retain: number of items that have to be retained in the teardown list for every iteration
        :type items_to_retain: int
        """
        alarm_size_and_problem = set_up_alarm_text_size_and_problem_distribution(alarm_size_distribution,
                                                                                 alarm_problem_distribution)
        (event_type, probable_cause) = set_up_event_type_and_probable_cause()
        try:
            alarm_dict = map_alarm_rate_with_nodes(profile_nodes, self.BSC_RATE, self.MSC_RATE, self.CPP_RATE,
                                                   self.SNMP_RATE, self.AML_RATE, self.AML_RATIO)
            while len(teardown_list) > items_to_retain:
                teardown_list.pop()
            setup_alarm_burst(self, alarm_dict, burst_id, alarm_size_and_problem, event_type, probable_cause,
                              teardown_list)
        except Exception as e:
            self.add_error_as_exception(e)


def get_supported_data_types_from_fls(profile):
    """
    Get supported data types from FLS.
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :return: returns the supported data types.
    :rtype: list
    :raises EnvironError: Unable to get supported data types from FLS.
    """
    if profile.is_cloud_native:
        cmd = ('/usr/local/bin/kubectl exec postgres-0 -n {0} -c postgres -- psql -U postgres -d flsdb -t -c '
               '"select distinct data_type from pm_rop_info"')
        response = shell.run_local_cmd(shell.Command(cmd.format(get_enm_cloud_native_namespace())))
        if not response.rc and response.stdout:
            data_types = [data_type.lstrip() for data_type in response.stdout.split('\n')]
            return data_types
        else:
            raise EnvironError("Unable to get supported data types from FLS due to {0}".format(response.stdout))

    elif profile.is_physical:
        db_hostname = get_active_postgres_db_hostname()
        cmd = ('PGPASSWORD=fls123 /usr/bin/psql -h {0} -U fls -d flsdb -c '
               '"select distinct data_type from pm_rop_info"'.format(db_hostname))
        response = shell.run_cmd_on_ms(shell.Command(cmd))
        if not response.rc and response.stdout:
            data_types = [data_type.lstrip() for data_type in response.stdout.split('\n')[2:-3]]
            return data_types
        else:
            raise EnvironError("Unable to get supported data types from FLS due to {0}".format(response.stdout))
    else:
        postgres_ip = enm_deployment.get_cloud_members_ip_address("postgres")
        get_support_datatypes_cmd = ("ssh -i /ericsson/enm/dumps/.cloud_user_keypair.pem -o StrictHostKeyChecking=no"
                                     " cloud-user@{0} 'PGPASSWORD=fls123 /usr/bin/psql -U fls "
                                     "-d flsdb -c \"select distinct data_type "
                                     "from pm_rop_info\"'".format(postgres_ip[0]))
        response = shell.run_cmd_on_vm(get_support_datatypes_cmd, get_emp())
        if not response.rc and response.stdout:
            data_types = [data_type.lstrip() for data_type in response.stdout.split('\n')[2:-3]]
            return data_types
        else:
            raise EnvironError("Unable to get supported data types from FLS due to {0}".format(response.stdout))


def get_matched_supported_datatypes_with_configured_datatypes(profile):
    """
    Get matched supported data types list with configured data types list.
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :return: returns the matched supported data types list.
    :rtype: list
    :raises EnvironError: FLS provided datatypes list is not matched with configured datatypes list in network file.
    """
    matched_data_types = []
    supported_data_types = get_supported_data_types_from_fls(profile)
    log.logger.debug("Supported datatypes list from FLS: {0}".format(supported_data_types))
    log.logger.debug("Configured datatypes list in network file: {0}".format(profile.DATA_TYPES))
    for datatype in profile.DATA_TYPES:
        for supported_datatype in supported_data_types:
            if supported_datatype.startswith("TOPOLOGY_") and datatype == "TOPOLOGY_*":
                if "TOPOLOGY_*" not in matched_data_types:
                    matched_data_types.append("TOPOLOGY_*")
            elif supported_datatype == datatype:
                matched_data_types.append(supported_datatype)
    log.logger.debug("Matched supported datatypes: {0}".format(matched_data_types))
    if not matched_data_types:
        raise EnvironError("FLS provided datatypes list is not matched with configured datatypes list in network file.")

    return matched_data_types


def get_active_postgres_db_hostname():
    """
    Get Active(ONLINE) postgres db hostname.
    :return: returns the active postgres db hostname.
    :rtype: str
    :raises EnvironError: Unable to find active db host name.
    """
    get_active_db_hostname_cmd = 'sudo /opt/ericsson/enminst/bin/vcs.bsh --groups|grep -i POSTGRES|grep -i online'
    response = shell.run_cmd_on_ms(shell.Command(get_active_db_hostname_cmd))
    if not response.rc and response.stdout and 'ONLINE' in response.stdout:
        db_hostname = response.stdout.split()[2]
        log.logger.debug("Active postgres db host name: {0}".format(db_hostname))
        return db_hostname
    else:
        raise EnvironError("Unable to find active db host name due to {0}".format(response.stdout))


def is_enm_on_rack():
    """
    Checks if the ENM deployment is a rack deployment

    :return: Boolean to indicate if ENM is on rack or not
    :rtype: bool

    """
    log.logger.debug("Checking if ENM deployment is rack")
    is_renm = "Extra_Large_ENM_On_Rack_Servers" in enm_deployment.get_values_from_global_properties(
        "enm_deployment_type")
    return is_renm
