import datetime
import re
from time import sleep
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr
from enmutils_int.lib.asu import FlowAutomation
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class AsuFlow(ShmFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        load_mgr.wait_for_setup_profile("SHM_SETUP", state_to_wait_for="COMPLETED")
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES,)[0]
        self.download_tls_certs([user])
        while self.keep_running():
            try:
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
                job_schedule_time = self.get_schedule_time_strings()[1]
                current_time = datetime.datetime.now()
                job_wait_time = (job_schedule_time[0] - current_time).total_seconds()
                if job_wait_time > 0:
                    log.logger.debug(
                        "Sleeping for {0} seconds and thereafter flow will be created as per the scheduled time "
                        "in config file".format(job_wait_time))
                    sleep(job_wait_time)
                if synced_nodes:
                    log.logger.debug("ASU_Profile node allocation process completed")
                    flow = FlowAutomation(
                        nodes=synced_nodes,
                        flow_name=re.sub('[^A-Za-z0-9]+', '', "{0}Time{1}".format(self.NAME, self.get_timestamp_str(
                            timestamp_end_index=8))), user=user)
                    flow.create_flow_automation(self)
                    self.teardown_list.append(picklable_boundmethod(flow.delete_directory_structure))
                else:
                    raise EnmApplicationError("No synced node available for this iteration")
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError("Failed to create flow,"
                                                                " Exception: [{0}]".format(e.message)))
            self.exchange_nodes()
