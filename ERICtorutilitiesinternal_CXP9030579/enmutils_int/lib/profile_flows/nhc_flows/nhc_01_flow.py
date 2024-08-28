from datetime import datetime, timedelta
from enmutils.lib import log
from enmutils_int.lib.nhc_cmd import NHCCmds
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Nhc01(GenericFlow):

    SCHEDULED_TIMES = []
    TIMEOUT = 30

    def execute_nhc_01_flow(self):
        start_time = datetime.strptime(self.START_TIME, "%H:%M:%S")
        stop_time = datetime.strptime(self.STOP_TIME, "%H:%M:%S")
        time_now = datetime.now()
        next_day = time_now + timedelta(days=1)
        first_run = time_now.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        last_run = time_now.replace(day=next_day.day, month=next_day.month, year=next_day.year, hour=stop_time.hour,
                                    minute=stop_time.minute, second=stop_time.second)
        self.get_scheduled_times(first_run, last_run)
        user, = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)
        nhc_run_command = NHCCmds(user=user, timeout=self.TIMEOUT)

        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_time()
            nodes = generate_basic_dictionary_from_list_of_objects(
                self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"]), "primary_type")
            for node_type in nodes.iterkeys():
                try:
                    nhc_run_command.execute(nodes[node_type])
                except Exception as e:
                    self.add_error_as_exception(e)
            self.exchange_nodes()

    def get_scheduled_times(self, first_run, last_run):
        """
        generate the scheduled times for the profile to run based on the start, stop and sleep times
        :param first_run: time when the profile should start the first iteration
        :type first_run: datetime
        :param last_run: time when the profile should stop execution and go to sleep
        :type last_run: datetime
        """
        sleep_time = timedelta(minutes=self.NHC_SLEEP)
        self.SCHEDULED_TIMES.append(first_run)
        next_run = first_run
        while (next_run + sleep_time) < last_run:
            next_run = next_run + sleep_time
            self.SCHEDULED_TIMES.append(next_run)
        log.logger.info("Number of scheduled runs for the profile : {}".format(len(self.SCHEDULED_TIMES)))
