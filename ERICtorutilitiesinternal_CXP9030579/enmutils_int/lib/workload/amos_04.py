from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.exceptions import EnmApplicationError, SessionNotEstablishedException, EnvironError
from enmutils_int.lib.amos_executor import set_max_amos_sessions, taskset, delete_user_sessions
from enmutils_int.lib.profile_flows.amos_flows.amos_flow import AmosCommonFlow


class AMOS_04(AmosCommonFlow):
    """
    Use Case id:        AMOS_04
    Slogan:             Launch AMOS in Shell Terminal and run commands on multiple nodes in parallel.
    """

    NAME = "AMOS_04"

    def run(self):
        set_max_amos_sessions(self, self.MAX_AMOS_SESSIONS)
        users = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "subnetwork", "primary_type", "node_ip"])
        self.perform_amos_prerequisites(users, nodes)

        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_time()
            log.logger.debug('nodes_tuples: {0}'.format(len(self.USER_NODES)))
            log.logger.debug('Iteration began running')
            tq = ThreadQueue(self.USER_NODES, num_workers=len(self.USER_NODES), func_ref=taskset,
                             args=[self.COMMANDS_LIST, self.VERIFY_TIMEOUT], task_wait_timeout=60 * 25)
            tq.execute()
            self.process_thread_queue_errors(tq)
            try:
                delete_user_sessions(users)
            except SessionNotEstablishedException as e:
                self.add_error_as_exception(EnvironError(e))
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
            log.logger.debug('Iteration finished running')


amos_04 = AMOS_04()
