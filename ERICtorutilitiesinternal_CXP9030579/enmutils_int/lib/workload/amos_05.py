from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.exceptions import EnmApplicationError, SessionNotEstablishedException, EnvironError
from enmutils_int.lib.amos_cmd import MoBatchCmd, get_specific_scripting_iterator
from enmutils_int.lib.amos_executor import set_max_amos_sessions, delete_user_sessions
from enmutils_int.lib.profile_flows.amos_flows.amos_flow import AmosCommonFlow


class AMOS_05(AmosCommonFlow):
    """
    Use Case id:        AMOS_05
    Slogan:             Run MoBatch commands on multiple nodes in parallel on the AMOS KVMS.
    """

    NAME = "AMOS_05"
    BATCH_CMD_CHECK = True

    @staticmethod
    def taskset(mo_batch_cmd, _):
        mo_batch_cmd.execute()

    def run(self):
        mo_batch_cmds = []
        set_max_amos_sessions(self, self.MAX_AMOS_SESSIONS)

        users = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "subnetwork", "primary_type", "node_ip"])
        self.perform_amos_prerequisites(users, nodes)

        self.state = "RUNNING"

        while self.keep_running():
            try:
                if self.BATCH_CMD_CHECK:
                    mo_batch_cmds = []
                    scripting_iterator = get_specific_scripting_iterator()
                    for user, nodes in self.USER_NODES:
                        batch_cmd = MoBatchCmd(nodes, user, self.COMMANDS_LIST, self.NUM_PARALLEL,
                                               scripting_iterator.next(), self.TIMEOUT)
                        mo_batch_cmds.append(batch_cmd)
                    self.BATCH_CMD_CHECK = False
                if mo_batch_cmds:
                    tq = ThreadQueue(mo_batch_cmds, num_workers=len(mo_batch_cmds), func_ref=self.taskset,
                                     args=[self], task_join_timeout=60 * 10, task_wait_timeout=60 * 10)
                    tq.execute()
                    self.process_thread_queue_errors(tq)
                else:
                    raise EnvironError("MoBatchCmd returns empty list {0} as user nodes is {1}"
                                       .format(mo_batch_cmds, self.USER_NODES))
            except Exception as e:
                self.add_error_as_exception(e)
            finally:
                try:
                    delete_user_sessions(users)
                except SessionNotEstablishedException as e:
                    self.add_error_as_exception(EnvironError(e))
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
            self.sleep()


amos_05 = AMOS_05()
