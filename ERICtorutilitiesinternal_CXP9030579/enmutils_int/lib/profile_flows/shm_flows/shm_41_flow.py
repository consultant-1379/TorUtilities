import datetime
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobRouter6675
from enmutils_int.lib.shm_utility_jobs import ShmBackUpCleanUpJob


class Shm41Flow(ShmFlow):

    REPEAT_COUNT = "0"
    PLATFORM = "ECIM"
    DESCRIPTION = 'Performs backup on Router_6675 nodes at 11:30 PM every day'

    def execute_flow(self):
        """
        Executes the backup profile flow for Router6675 nodes
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]

        while self.keep_running():
            try:
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "time")
                scheduled_time_strings, shm_job_scheduled_time_strings = self.get_schedule_time_strings()
                for scheduled_time_string, shm_job_scheduled_time_string in zip(scheduled_time_strings, shm_job_scheduled_time_strings):
                    if datetime.datetime.now() > shm_job_scheduled_time_string:
                        continue
                    if synced_nodes:
                        backup_job = BackupJobRouter6675(user, nodes=synced_nodes, repeat_count=self.REPEAT_COUNT,
                                                         description=self.DESCRIPTION, profile_name=self.NAME,
                                                         file_name=self.timestamp_str, platform=self.PLATFORM,
                                                         schedule_time=shm_job_scheduled_time_string,
                                                         schedule_time_strings=[scheduled_time_string],
                                                         shm_schedule_time_strings=[shm_job_scheduled_time_string])
                        delete_backup_job = ShmBackUpCleanUpJob(user, nodes=synced_nodes, profile_name=self.NAME,
                                                                platform=self.PLATFORM)
                        self.execute_backup_jobs(backup_job, delete_backup_job, user)
                    else:
                        self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
            except Exception as e:
                self.add_error_as_exception(e)
            self.exchange_nodes()
