import time
from enmutils.lib import log
from enmutils.lib.arguments import split_list_into_chunks
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.ops import Ops
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Ops01Flow(GenericFlow):
    TLS_FLAG = False

    def execute_flow(self):
        """
        Executes the flow for OPS_01 profile
        """
        self.ops = Ops()  # pylint: disable=attribute-defined-outside-init
        self.state = "RUNNING"
        ops_host_list = self.ops.host_list
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_name"])
        number = len(ops_host_list)
        users = self.create_profile_users(number, self.USER_ROLES, safe_request=True)
        self.deallocate_unused_nodes_and_update_profile_persistence(nodes)
        while self.keep_running():
            self.sleep_until_time()
            try:
                if not self.TLS_FLAG:
                    self.download_tls_certs(users)
                    for user, vm in zip(users, ops_host_list):
                        self.ops.create_password_less_to_vm(user, vm)
                    self.TLS_FLAG = True
                user_nodes = self.create_workers(nodes, ops_host_list, users)
                self.create_and_execute_threads(workers=user_nodes, thread_count=len(user_nodes), args=[self],
                                                wait=self.THREAD_QUEUE_TIMEOUT, join=self.THREAD_QUEUE_TIMEOUT)
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)

    def create_workers(self, nodes, host_list, users):
        """
        Creates the workers needed for parallel execution

        :param nodes: Nodes
        :type nodes: list
        :param host_list: Host names
        :type host_list: list
        :param users: Users (enm_user.User)
        :type users: list

        :return: list of workers
        :rtype: list
        """
        final_workers = []
        split_size = len(host_list)
        host_user_index = len(host_list) - 1
        for node_list in split_list_into_chunks(nodes, split_size):
            session_count_values = self.split_session_count(len(node_list))
            for index, node in enumerate(node_list):
                final_workers.append(
                    [users[host_user_index], node, session_count_values[index], host_list[host_user_index]])
            host_user_index -= 1 if host_user_index else host_user_index
        return final_workers

    def split_session_count(self, nodes_count):
        """
        Splits session count as needed

        :param nodes_count: Nodes count
        :type nodes_count: int

        :return: list of workers
        :rtype: list
        """
        max_session_count_per_node = self.MAX_SESSION_COUNT_PER_NODE
        if self.SESSION_COUNT < max_session_count_per_node:
            return [self.SESSION_COUNT] * nodes_count
        else:
            count_integer, remainder = divmod(self.SESSION_COUNT, nodes_count)
            count_integer = max_session_count_per_node if count_integer > max_session_count_per_node else count_integer
            count_values = []
            for i in range(nodes_count):
                count_values.append(count_integer)
            for i in range(remainder):
                count_values[i] += 1
            return count_values

    @staticmethod
    def task_set(worker, profile):  # pylint: disable=arguments-differ
        """
        Task that will be executed by the thread queue
        :param worker: users, nodes and hosts
        :type worker: tuple
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        :raises EnmApplicationError: if there is an error in response from ENM
        """
        user, node, session_count, host = worker
        logfile = None

        try:
            log.logger.debug("{0} user launches {1} OPS NUI sessions on {2} node on {3} host"
                             .format(user.username, session_count, node.node_id, host))
            logfile = profile.ops.run_blade_runner_script_on_host(user, node.node_name, host, session_count)
        except Exception as e:
            profile.add_error_as_exception(e)

        time.sleep(30 * 60)

        try:
            if logfile is None:
                raise EnmApplicationError("Could not get the ops log file directory from {0} server".format(host))
            else:
                log.logger.debug("Checking the number of OPS cli sessions created on host: {host}".format(host=host))
                profile.ops.check_sessions_count(user, host, logfile, session_count)
        except Exception as e:
            profile.add_error_as_exception(e)
