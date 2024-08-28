from enmutils_int.lib import helper_methods
from enmutils_int.lib.cmcli import cm_cli_home
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.fm import (collect_erbs_network_logs, collect_eNodeB_network_logs,
                                 collect_sgsn_network_logs, collect_mgw_network_logs)
from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue


class Fm25(GenericFlow):
    """
    Class for FM_25 Network log management.
    """

    def execute_flow_fm_25(self):
        """
        This function executes the main flow for FM_25
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True,
                                          retry=True)
        self.state = "RUNNING"

        while self.keep_running():

            self.sleep_until_time()
            allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
            profile_nodes = helper_methods.generate_basic_dictionary_from_list_of_objects(allocated_nodes,
                                                                                          "primary_type")
            thread_list = []
            # Execute a number of netlog uploads for each user
            if 'ERBS' in profile_nodes:
                erbs_nodes = profile_nodes.get("ERBS")
                num_of_erbs_nodes_per_user = len(erbs_nodes) / 2
                tq1_1 = ThreadQueue(work_items=users[:1], num_workers=len(users[:1]), func_ref=self._ui_tasks_for_netlog,
                                    task_join_timeout=None, task_wait_timeout=self.SLEEP_TIME,
                                    args=[erbs_nodes[:num_of_erbs_nodes_per_user]])
                thread_list.append(tq1_1)
                tq1_2 = ThreadQueue(work_items=users[1:2], num_workers=len(users[1:2]), func_ref=self._ui_tasks_for_netlog,
                                    task_join_timeout=None, task_wait_timeout=self.SLEEP_TIME,
                                    args=[erbs_nodes[num_of_erbs_nodes_per_user:]])
                thread_list.append(tq1_2)
            if 'RadioNode' in profile_nodes:
                tq2 = ThreadQueue(work_items=users[2:3], num_workers=len(users[2:3]), func_ref=self._ui_tasks_for_netlog,
                                  task_join_timeout=None, task_wait_timeout=self.SLEEP_TIME,
                                  args=[profile_nodes['RadioNode']])
                thread_list.append(tq2)
            if 'SGSN-MME' in profile_nodes:
                tq3 = ThreadQueue(work_items=users[3:4], num_workers=len(users[3:4]), func_ref=self._ui_tasks_for_netlog,
                                  task_join_timeout=None, task_wait_timeout=self.SLEEP_TIME,
                                  args=[profile_nodes['SGSN-MME']])
                thread_list.append(tq3)
            if 'MGW' in profile_nodes:
                tq4 = ThreadQueue(work_items=users[4:5], num_workers=len(users[4:5]), func_ref=self._ui_tasks_for_netlog,
                                  task_join_timeout=None, task_wait_timeout=self.SLEEP_TIME,
                                  args=[profile_nodes['MGW']])
                thread_list.append(tq4)

            log.logger.info("Starting {0} threads for {1} different type of nodes allocated to the profile".
                            format(len(users), len(profile_nodes)))

            for tq in thread_list:
                tq.execute()
                self.process_thread_queue_errors(tq)
            self.exchange_nodes()

    @staticmethod
    def _ui_tasks_for_netlog(user, nodes):
        """
        :param user: enm user instance to be used to perform the flow
        :type user: `lib.enm_user.User`
        :param nodes: list of `lib.enm_node.Node` instances to be used to perform this flow
        :type nodes: list
        """
        cm_cli_home(user=user)
        node_type = nodes[0].primary_type
        log.logger.info("Start collecting {0} logs".format(node_type))
        for node in nodes:
            if node_type == 'MGW':
                log.logger.info("Start collecting logs for the node {}".format(node.node_id))
                collect_mgw_network_logs(user, node)
            elif node_type == 'RadioNode':
                log.logger.info("Start collecting logs for the node {}".format(node.node_id))
                collect_eNodeB_network_logs(user, node)
            elif node_type == 'SGSN-MME':
                log.logger.info("Start collecting logs for the node {}".format(node.node_id))
                collect_sgsn_network_logs(user, node)
            else:
                log.logger.info("Start collecting logs for the node {}".format(node.node_id))
                collect_erbs_network_logs(user, node)
