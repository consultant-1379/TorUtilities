from enmutils.lib import log
from enmutils_int.lib import load_mgr, helper_methods
from enmutils_int.lib.profile_flows.common_flows.common_flow import FMAlarmFlow
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (get_num_of_given_type_of_nodes_from_deployment,
                                                                     get_total_number_of_nodes_on_deployment,
                                                                     stop_burst)


class Fm01(FMAlarmFlow):
    MSC_RATE = None
    BSC_RATE = None
    CPP_RATE = None
    SNMP_RATE = None

    def execute_fm_01_alarm_rate_normal_flow(self):
        """
        This function executes the main flow for FM_01
        """
        burst_id = "111"
        load_mgr.wait_for_setup_profile("FM_0506")
        alarm_size_distribution = self.ALARM_SIZE_DISTRIBUTION
        alarm_problem_distribution = self.ALARM_PROBLEM_DISTRIBUTION
        teardown_list = self.teardown_list
        user, = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        items_to_retain = len(teardown_list)
        self.calculate_initial_alarm_rates(user)
        self.state = "RUNNING"

        while self.keep_running():
            try:
                allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "netsim", "simulation",
                                                                                    "primary_type", "node_name"])
                profile_nodes = helper_methods.generate_basic_dictionary_from_list_of_objects(allocated_nodes,
                                                                                              "primary_type")
                nodes_list = [node for type_nodes in profile_nodes.itervalues() for node in type_nodes if node]
                stop_burst(nodes_list, burst_id)
                log.logger.info("Number of items to be retained in the teardown list : {0}".format(items_to_retain))
                self.configure_fm_alarm_burst(alarm_size_distribution, alarm_problem_distribution, profile_nodes,
                                              burst_id, teardown_list, items_to_retain)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()
            self.exchange_nodes()

    def calculate_initial_alarm_rates(self, user):
        """
        calculate the rate per node type, which is to be applied in alarm burst
        :param user: enm user to perform operations on the deployment
        :type user: enmutils.lib.enm_user_2.User
        """
        msc_burst_rate = self.MSC_BURST_RATE
        bsc_burst_rate = self.BSC_BURST_RATE
        platforms = self.PLATFORM_TYPES
        node_type_count = get_num_of_given_type_of_nodes_from_deployment(self, user, platforms)
        total_nodes = get_total_number_of_nodes_on_deployment(self, user)
        cpp_gsm_nodes = sum(node_type_count.values())
        if total_nodes > cpp_gsm_nodes:
            node_type_count['Snmp'] = total_nodes - cpp_gsm_nodes
        else:
            node_type_count['Snmp'] = 0
        for key, value in node_type_count.iteritems():
            if not value > 0:
                log.logger.warn("{0} type nodes are {1} in deployment".format(key, value))
        log.logger.info("Total Node type count from deployment : {0}".format(node_type_count))
        try:
            total_burst = round(float(self.FM_01_TOTAL_ALARMS) / (24 * 3600), 3)
            log.logger.debug('TOTAL BURST RATE : {0}'.format(total_burst))
            self.MSC_RATE = float(msc_burst_rate) * float(node_type_count['Msc'])
            self.BSC_RATE = float(bsc_burst_rate) * float(node_type_count['Bsc'])
            cpp_snmp_rate = float(total_burst - (self.BSC_RATE + self.MSC_RATE))
            self.CPP_RATE = round(float(cpp_snmp_rate) * (float(node_type_count['Cpp']) / float(total_nodes)), 3)
            self.SNMP_RATE = round(float(cpp_snmp_rate) * (float(node_type_count['Snmp']) / float(total_nodes)), 3)
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.info("Alarm rates for total network : \n BSC = {0}A/S, MSC = {1}A/S, CPP = {2}A/S, SNMP = {3}A/S".
                        format(self.BSC_RATE, self.MSC_RATE, self.CPP_RATE, self.SNMP_RATE))
