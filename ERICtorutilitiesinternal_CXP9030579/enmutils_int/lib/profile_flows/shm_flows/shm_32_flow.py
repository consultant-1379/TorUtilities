from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobMiniLink6352


class Shm32Flow(ShmFlow):

    DESCRIPTION = "Performs backup on all MINI-LINK-6352 nodes, to a maximum of 500 nodes, in a single job at 2:30"
    REPEAT_COUNT = "0"
    PLATFORM = "MINI_LINK_OUTDOOR"

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        while self.keep_running():
            try:
                self.deallocate_IPV6_nodes_and_update_profile_persistence()
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "time")
                schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
                if synced_nodes:
                    backup_job = BackupJobMiniLink6352(user=user, nodes=synced_nodes, repeat_count=self.REPEAT_COUNT,
                                                       description=self.DESCRIPTION, profile_name=self.NAME,
                                                       platform=self.PLATFORM, file_name=self.timestamp_str,
                                                       shm_schedule_time_strings=shm_schedule_time_strings,
                                                       schedule_time_strings=schedule_time_strings)
                    backup_job.create()
                else:
                    self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
            except Exception as e:
                self.add_error_as_exception(e)
            self.exchange_nodes()
