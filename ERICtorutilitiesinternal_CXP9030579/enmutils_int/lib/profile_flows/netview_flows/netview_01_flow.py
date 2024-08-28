from datetime import datetime, timedelta
from random import choice, uniform

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.load_mgr import wait_for_setup_profile
from enmutils_int.lib.load_node import filter_nodes_having_poid_set
from enmutils_int.lib.netview import update_node_location_by_rest, get_node_location_by_rest
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Netview01Flow(GenericFlow):

    def __init__(self, *args, **kwargs):
        self.number_of_locations_created = 0
        self.user = None
        self.SCHEDULED_TIMES = []
        super(Netview01Flow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        wait_for_setup_profile("NETVIEW_SETUP", state_to_wait_for="COMPLETED", timeout_mins=30, sleep_between=60)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid"], profile_name="NETVIEW_SETUP")
        node_dict = {node.node_id: node.poid for node in filter_nodes_having_poid_set(nodes)}
        self.state = "RUNNING"
        self.SCHEDULED_TIMES = [self._set_start_time()]
        if node_dict:
            while self.keep_running():
                self._sleep_until()
                self.SCHEDULED_TIMES = [datetime.now() + timedelta(seconds=self.TIME_INTERVAL)]
                node_id = choice(node_dict.keys())
                try:
                    get_node_location_by_rest(self.user, node_id, node_dict[node_id])
                    update_node_location_by_rest(self.user, node_id, uniform(1, 37.91496), uniform(1, 37.91496))
                except Exception as e:
                    self.add_error_as_exception(EnvironError("Update of coordinates on {0} failed with message {1}"
                                                             .format(node_id, e.message)))
        else:
            self.add_error_as_exception(EnvironError("Profile could not retrieve nodes prepared by the setup profile"))

    @staticmethod
    def _set_start_time():
        """
        Function to set starting time
        """
        current_time = datetime.now()
        if current_time.minute < 7:
            return current_time.replace(minute=7)
        else:
            hour = 0 if current_time.hour == 23 else current_time.hour + 1
            return current_time.replace(hour=hour, minute=7)
