from functools import partial

from enmutils.lib.enm_node_management import CmManagement
from enmutils.lib.exceptions import EnvironError
from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class ShmSingleUpgradeFlow(ShmFlow):

    STARTED_NODES = []
    TLS_FLAG = False

    def teardown_unset_timeout(self):
        """
        Teardown method to be used with workload profile teardown
        """
        self.set_unset_mltn_timeout("PARAMS_MLTN_UNSET_TIMEOUT")

    def execute_flow(self):
        """
        Executes the shm upgrade flow (SHM : 24, 27, 31, 33, 36, 40, 42)
        """
        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED")
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        log.logger.debug("*******Entered into single upgrade flow file*********")
        while self.keep_running():
            try:
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
                if self.NAME == "SHM_24":
                    self.STARTED_NODES = synced_nodes
                    self.set_unset_mltn_timeout("PARAMS_MLTN_SET_TIMEOUT")
                    self.teardown_list.append(partial(picklable_boundmethod(self.teardown_unset_timeout)))
                if self.NAME == "SHM_36" and not self.TLS_FLAG:
                    self.download_tls_certs([user])
                    self.TLS_FLAG = True
                self.create_upgrade_and_delete_inactive_upgrade_jobs(user=user, nodes=synced_nodes)
            except Exception as e:
                self.add_error_as_exception(e)
            if self.NAME == "SHM_36":
                self.check_sync_status_and_enable_supervision(user=user, nodes=synced_nodes, ne_type="BSC")
            self.exchange_nodes()

    def create_upgrade_activity(self, user, nodes):
        """
        Creates upgrade jobs for (SHM : 24, 27, 31, 33, 36, 40, 42)

        :param user: `enm_user_2.User`
        :type user: User object to use to make requests
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :rtype: `shm.SoftwarePackage`
        :return: Software package object
        """
        schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
        software_package = ()
        software_package = self.create_upgrade_job(user=user, nodes=nodes, node_limit=self.MAX_NODES,
                                                   schedule_time=shm_schedule_time_strings[0],
                                                   schedule_time_strings=schedule_time_strings,
                                                   shm_schedule_time_strings=shm_schedule_time_strings)
        return software_package

    def delete_inactive_upgrade_activity(self, user, package_nodes, delete_pkg_time):
        """
        Delete inactive upgrade job for SHM

        :param user: `enm_user_2.User`
        :type user: User object to use to make requests
        :type package_nodes: list
        :param package_nodes: List of `enm_node.Node` objects
        :param delete_pkg_time: epoch time value in milli seconds provided to delete backup packages
        :type delete_pkg_time: long
        """
        if self.NAME == "SHM_33":
            self.delete_inactive_upgrade_packages(user=user, nodes=package_nodes, profile_name=self.NAME)
            self.cleanup_after_upgrade(user, package_nodes, profile_name=self.NAME)

    def create_upgrade_and_delete_inactive_upgrade_jobs(self, user, nodes):
        """
        Creates upgrade jobs and delete inactive upgrade jobs for SHM : 24, 27, 31, 33, 36, 40, 42 profiles

        :param user: `enm_user_2.User`
        :type user: User object to use to make requests
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects

        :raises EnvironError: Exception raised when nodes are not synced or started
        """
        upgrade_start_time = self.get_current_epoch_time_in_milliseconds
        log.logger.debug("Time recorded before upgrade starts: {0}".format(upgrade_start_time))
        if nodes:
            software_package = ()
            software_package = self.create_upgrade_activity(user=user, nodes=nodes)
            if software_package and software_package[1]:
                self.delete_inactive_upgrade_activity(user=user, package_nodes=software_package[1],
                                                      delete_pkg_time=upgrade_start_time)
            else:
                log.logger.debug("No Available nodes to check and perform delete inactive upgrade activity")
        else:
            raise EnvironError("No Started nodes exists / Nodes do not have required sync status")

    @staticmethod
    def check_sync_status_and_enable_supervision(user, nodes, ne_type=None):
        """
        Checks for unsynchronized nodes and enables supervision of them.

        :param user: `enm_user_2.User`
        :type user: User object used to make requests
        :type nodes: list
        :param nodes: List of `enm_node.Node` objects
        :type ne_type: string or None
        :param ne_type: network element type eg. BSC
        """
        try:
            str_nodes = [node.node_id for node in nodes]
            log.logger.debug("Verifying the following nodes - {}".format(str_nodes))
            nodes_status = CmManagement.get_status(user, node_ids=str_nodes)
            unsync_nodes = []
            for node, status in nodes_status.items():
                if status == "UNSYNCHRONIZED":
                    unsync_nodes.append(node)
            if unsync_nodes:
                log.logger.debug("Unsync nodes found - {}. Enabling supervision on these nodes!".format(unsync_nodes))
                CmManagement(node_ids=str_nodes, user=user, ne_type=ne_type).supervise()
        except Exception as e:
            log.logger.error("Exception occured while checking and supervising nodes({nodes}) - {error}".format(nodes=str_nodes, error=e))


class Shm24Flow(ShmSingleUpgradeFlow):
    PARAMS_MLTN_SET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x={0};"
    PARAMS_MLTN_UNSET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x=30;"


class ShmUpdateSoftwarePkgNameFlow(ShmSingleUpgradeFlow):
    """
    Profiles use this : SHM_31, SHM_33, SHM_40
    """
    DEFAULT = False


class Shm42Flow(ShmSingleUpgradeFlow):
    PARAMS_MLTN_SET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x={0};"
    PARAMS_MLTN_UNSET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x=30;"
