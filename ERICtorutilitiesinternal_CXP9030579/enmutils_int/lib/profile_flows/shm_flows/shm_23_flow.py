from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobMiniLink


class Shm23Flow(ShmFlow):

    PLATFORM = "CPP"
    REPEAT_COUNT = "0"
    DESCRIPTION = 'Performs backup on MLTN nodes at 3 AM every Sunday.'

    def execute_flow(self):
        """
        Executes Shm_23 profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]
        while self.keep_running():
            synced_nodes = self.select_required_number_of_nodes_for_profile(user, "time")
            schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
            if synced_nodes:
                backup_job = BackupJobMiniLink(user=user, nodes=synced_nodes, description=self.DESCRIPTION,
                                               repeat_count=self.REPEAT_COUNT, file_name=self.timestamp_str,
                                               profile_name=self.NAME, platform=self.PLATFORM,
                                               schedule_time=shm_schedule_time_strings[0],
                                               schedule_time_strings=schedule_time_strings,
                                               shm_schedule_time_strings=shm_schedule_time_strings)
                try:
                    backup_job.create()
                except Exception as e:
                    self.add_error_as_exception(e)
            else:
                self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
            self.exchange_nodes()
