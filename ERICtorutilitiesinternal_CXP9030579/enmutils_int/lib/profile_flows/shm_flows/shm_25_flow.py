from enmutils_int.lib import load_mgr
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_utilities import SHMUtils


class Shm25Flow(ShmFlow):

    DEFAULT = False

    def execute_flow(self):
        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED")
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"], retry=True)[0]
        synced_nodes = self.select_nodes_based_on_profile_name(user)
        delayed_nodes = synced_nodes[0:len(synced_nodes) / 2]
        try:
            SHMUtils.execute_restart_delay(delayed_nodes)
        except Exception as e:
            self.add_error_as_exception(e)
        try:
            schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
            package_nodes = self.create_upgrade_job(user=user, nodes=synced_nodes[:self.MAX_NODES],
                                                    node_limit=self.MAX_NODES,
                                                    schedule_time=shm_schedule_time_strings[0],
                                                    schedule_time_strings=schedule_time_strings,
                                                    shm_schedule_time_strings=shm_schedule_time_strings)
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            self.cleanup_after_upgrade(user, package_nodes[1], profile_name=self.NAME)
        try:
            SHMUtils.execute_restart_delay(delayed_nodes, delay=60)
        except Exception as e:
            self.add_error_as_exception(e)
