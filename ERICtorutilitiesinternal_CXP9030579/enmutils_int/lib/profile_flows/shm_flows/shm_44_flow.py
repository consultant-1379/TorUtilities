from enmutils_int.lib import load_mgr
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class Shm44Flow(ShmFlow):

    DEFAULT = False

    def execute_flow(self):
        """
        Executes the upgrade profile flow for SCU nodes
        """
        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED")
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]

        while self.keep_running():
            try:
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
                schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
                self.create_upgrade_job(user=user, nodes=synced_nodes, node_limit=self.MAX_NODES,
                                        schedule_time=shm_schedule_time_strings[0],
                                        schedule_time_strings=schedule_time_strings,
                                        shm_schedule_time_strings=shm_schedule_time_strings)
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)
