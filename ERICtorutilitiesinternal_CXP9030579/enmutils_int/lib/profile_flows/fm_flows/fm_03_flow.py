from enmutils.lib import log
from enmutils_int.lib import load_mgr, helper_methods
from enmutils_int.lib.profile_flows.common_flows.common_flow import FMAlarmFlow
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (get_num_of_given_type_of_nodes_from_deployment,
                                                                     get_total_number_of_nodes_on_deployment,
                                                                     calculate_alarm_rate_distribution)


class Fm03(FMAlarmFlow):
    MSC_RATE = None
    BSC_RATE = None
    CPP_RATE = None
    SNMP_RATE = None

    def execute_fm_03_alarm_rate_normal_flow(self):
        """
        This function executes the main flow for FM_03
        """
        burst_id = "333"
        load_mgr.wait_for_setup_profile("FM_0506")
        alarm_size_distribution = self.ALARM_SIZE_DISTRIBUTION
        alarm_problem_distribution = self.ALARM_PROBLEM_DISTRIBUTION
        burst_rate = self.BURST_RATE
        platforms = self.PLATFORM_TYPES
        teardown_list = self.teardown_list
        user, = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        items_to_retain = len(teardown_list)
        teardown_list = self.teardown_list
        self.state = "RUNNING"
        node_type_count = get_num_of_given_type_of_nodes_from_deployment(self, user, platforms)
        total_nodes = get_total_number_of_nodes_on_deployment(self, user)
        try:
            self.MSC_RATE, self.BSC_RATE, self.CPP_RATE, self.SNMP_RATE = calculate_alarm_rate_distribution(node_type_count,
                                                                                                            total_nodes,
                                                                                                            burst_rate)
        except Exception as e:
            self.add_error_as_exception(e)

        while self.keep_running():
            self.sleep_until_time()
            try:
                allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "netsim", "simulation",
                                                                                    "primary_type", "node_name"])
                profile_nodes = helper_methods.generate_basic_dictionary_from_list_of_objects(allocated_nodes,
                                                                                              "primary_type")
                log.logger.info("Number of items to be retained in the teardown list : {}".format(items_to_retain))
                log.logger.info(
                    "Storm alarm rates for total network : \n BSC = {0}A/S, MSC = {1}A/S, CPP = {2}A/S, SNMP = {3}A/S".
                    format(self.BSC_RATE, self.MSC_RATE, self.CPP_RATE, self.SNMP_RATE))
                self.configure_fm_alarm_burst(alarm_size_distribution, alarm_problem_distribution, profile_nodes,
                                              burst_id, teardown_list, items_to_retain)
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)


fm_03 = Fm03()
