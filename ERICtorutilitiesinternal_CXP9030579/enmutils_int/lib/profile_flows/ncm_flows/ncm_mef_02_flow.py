# ********************************************************************
# Name    : Network Connectivity Manager-Metro Ethernet Forum
# Summary : It allows the user to perform node re-alignment for
#           Mini-Link nodes by REST invocation.
# ********************************************************************

import json
import time
from enmutils_int.lib.ncm_manager import ncm_rest_query, fetch_ncm_vm
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib import log, arguments

REALIGN_NODES_ENDPOINT = "/ncm/rest/management/realign-nodes"


class NcmMef02Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
        try:
            if fetch_ncm_vm() in ("1.1.1.1", None):
                raise EnvironError("NCM VM is not configured in this deployment")
            while self.keep_running():
                self.sleep_until_day()
                nodes, _ = check_sync_and_remove(nodes_list, user)
                if nodes:
                    total_nodes = arguments.split_list_into_chunks(nodes, self.NODES_PER_BATCH)
                    self.perform_nodes_realignment(user, total_nodes)
                else:
                    raise EnvironError("No available synced nodes, to perform NCM realign-nodes task")
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_nodes_realignment(self, user, total_nodes):
        """
        Perform node realignment with 500 nodes per each rest invocation
        :type user: enm user
        :param user: enm user to perform operation
        :type total_nodes: list
        :param total_nodes: list of nodes to be realigned
        :raises EnmApplicationError: when realignment rest call failed to execute
        """
        for batch_num, node_list in enumerate(total_nodes):
            log.logger.debug("Executing batch {0}".format(batch_num + 1))
            list_of_node_names = [node.node_id for node in node_list]
            update_json = {"nodes": list_of_node_names}
            data = json.dumps(update_json)
            try:
                ncm_rest_query(user, REALIGN_NODES_ENDPOINT, data)
                if batch_num + 1 != len(total_nodes):
                    log.logger.debug("Sleeping for {0} seconds after batch {1}".format(self.BATCH_SLEEP, batch_num + 1))
                    time.sleep(self.BATCH_SLEEP)
            except Exception as e:
                log.logger.info("{0} error response is {1}".format(self.NAME, e.message))
                raise EnmApplicationError("Unable to send post alignment to {0}: {1}".format(self.NAME, str(e)))
