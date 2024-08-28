import time
import datetime

from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib import log
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_utility_jobs import RestartNodeJob


class ShmRestartFlow(ShmFlow):

    DESCRIPTION = "Restart of {0} nodes in a single job."

    def execute_flow(self):
        """
        Executes the restart flow for SHM_28, SHM_47
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]
        hour, minute, second = self.SCHEDULED_TIMES_STRINGS[0].split(':')

        while self.keep_running():
            synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
            schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
            current_time = datetime.datetime.now()
            schedule_time = current_time.replace(hour=int(hour), minute=int(minute) + 20, second=int(second))
            try:
                if synced_nodes:
                    job = RestartNodeJob(user=user, nodes=synced_nodes,
                                         description=self.DESCRIPTION.format(len(synced_nodes)),
                                         profile_name=self.NAME, schedule_time=schedule_time,
                                         shm_schedule_time_strings=shm_schedule_time_strings,
                                         schedule_time_strings=schedule_time_strings)
                    job.create()
                else:
                    raise EnmApplicationError("There are no synced nodes available to run the node restart job")
            except Exception as e:
                self.add_error_as_exception(e)
            log.logger.debug('Sleeping for 10 minutes to allow nodes to sync')
            time.sleep(600)
            self.exchange_nodes()
