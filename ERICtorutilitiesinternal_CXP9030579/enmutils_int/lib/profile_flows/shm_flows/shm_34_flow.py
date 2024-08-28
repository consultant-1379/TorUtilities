from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobSpitFire
from enmutils_int.lib.shm_utility_jobs import ShmBackUpCleanUpJob


class Shm34Flow(ShmFlow):

    REPEAT_COUNT = "0"
    PLATFORM = "ECIM"
    DESCRIPTION = 'Performs backup on all Router_6672 nodes, to a maximum of 1000 nodes, in a single job at 23:30'

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]

        while self.keep_running():
            synced_nodes = self.select_required_number_of_nodes_for_profile(user, "time")
            scheduled_time_strings, shm_job_scheduled_time_strings = self.get_schedule_time_strings()
            for scheduled_time_string, shm_job_scheduled_time_string in zip(scheduled_time_strings,
                                                                            shm_job_scheduled_time_strings):
                if synced_nodes:
                    backup_job = BackupJobSpitFire(user, nodes=synced_nodes, repeat_count=self.REPEAT_COUNT,
                                                   description=self.DESCRIPTION, profile_name=self.NAME,
                                                   schedule_time_strings=[scheduled_time_string],
                                                   shm_schedule_time_strings=[shm_job_scheduled_time_string])
                    delete_backup_job = ShmBackUpCleanUpJob(user, nodes=synced_nodes, profile_name=self.NAME,
                                                            platform=self.PLATFORM)
                    self.execute_backup_jobs(backup_job, delete_backup_job, user)
                else:
                    self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
            self.exchange_nodes()
