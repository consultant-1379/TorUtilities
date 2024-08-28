import time

from retrying import retry

from enmutils.lib import log
from enmutils.lib.enm_node_management import ShmManagement
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class Shm04Flow(ShmFlow):

    @retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=20000,
           stop_max_attempt_number=20)
    def _verify_sync_status(self, shm_supervision_obj):
        """
        Checks the status of nodes which are inventory synced
        :param shm_supervision_obj: Object of ShmManagement
        :type shm_supervision_obj: `enmutils.lib.enm_node_management.Management`

        :raises EnmApplicationError: Exception raised when all the assinged nodes are not inventory synced
        """
        nodes_sync = shm_supervision_obj.get_inventory_sync_nodes()
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
        if len(nodes_sync) != 0 and len(nodes_sync) == len(nodes_list):
            log.logger.info("Number of nodes with inventory sync enabled are {0}".format(len(nodes_sync)))
        else:
            log.logger.debug('The sync is not completed. Sleeping 20 seconds before re-trying.')
            raise EnmApplicationError(
                "The number of inventory synced nodes are {0} out of {1}".format(len(nodes_sync), len(nodes_list)))

    def execute_flow(self):
        """
        Executes Shm_04 profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        # Instantiate the supervision object
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
        shm_supervision_obj = ShmManagement(user=user, node_ids=[node.node_id for node in nodes_list])
        while self.keep_running():
            self.sleep_until_day()
            try:
                shm_supervision_obj.unsupervise(timeout_seconds=self.TIMEOUT)
            except Exception as e:
                log.logger.debug("Failed to unset inventory supervise on one or more nodes. Response {}".format(e))
                self.add_error_as_exception(e)

            log.logger.info("Sleeping for 2 minutes before enabling inventory sync on the nodes")

            time.sleep(2 * 60)

            try:
                shm_supervision_obj.supervise(timeout_seconds=self.TIMEOUT)
            except Exception as e:
                log.logger.debug("Failed to set inventory supervise on one or more nodes. Response {}".format(e))
                self.add_error_as_exception(e)

            try:
                self._verify_sync_status(shm_supervision_obj)
            except Exception as e:
                log.logger.debug("Failed to check status of inventory sync on one or more nodes.")
                self.add_error_as_exception(e)
