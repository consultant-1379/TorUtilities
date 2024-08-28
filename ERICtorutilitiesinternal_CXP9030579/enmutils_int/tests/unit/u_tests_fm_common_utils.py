#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.fm import HISTORICAL
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (get_num_of_given_type_of_nodes_from_deployment,
                                                                     get_total_number_of_nodes_on_deployment,
                                                                     map_alarm_rate_with_nodes, setup_alarm_burst,
                                                                     calculate_alarm_rate_distribution,
                                                                     TimeoutException, execute_burst,
                                                                     FailedNetsimOperation, stop_burst,
                                                                     execute_alarm_monitor_tasks, set_teardown_list,
                                                                     execute_alarm_search_tasks, put_profile_to_sleep,
                                                                     collect_nodes_for_profile,
                                                                     set_up_event_type_and_probable_cause,
                                                                     set_up_alarm_text_size_and_problem_distribution)


class FmCommonUtilsUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock(username='Test_user')
        self.nodes = {'BSC': ['BSC01'], 'MSC-DB-BSP': ['MSC01'], 'MSC-BC-BSP': ['MSC05'], 'MSC-BC-IS': ['MSC08'],
                      'ERBS': ['LTE01'], 'RadioNode': ['LTE01dg2ERBS00001'], 'Router6675': ['CORE01RR66750001']}
        self.nodes_list = [Mock(node_id='LTE01ERBS0001'), Mock(node_id='LTE01ERBS0002')]
        self.node_data = {"managedElements": [node.node_id for node in self.nodes_list], "actionType": "", "uId": ""}
        unit_test_utils.setup()
        self.bsc_rate = 0.038
        self.msc_rate = 0.038
        self.cpp_rate = 0.000955
        self.aml_rate = 1.0
        self.aml_ratio = 0.5
        self.burst_rate = 40
        self.alarm_size_and_sp = [1000, ('Nss Synchronization System Clock Status Change', 'indeterminate')]
        self.burst_id = "777"
        self.snmp_rate = 0.000955
        self.teardown_list = []
        self.profile = Mock()
        self.profile.DURATION = 300
        self.platform_types = ["Cpp", "Msc", "Bsc"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.split")
    def test_get_num_of_given_type_of_nodes_from_deployment_is_successful(self, mock_re_split, mock_re_compile):
        response = Mock()
        response.get_output.return_value = "0 instance(s) found"
        self.user.enm_execute.side_effect = [response, response, response]
        split_result = ["", "0"]
        mock_re_split.side_effect = [split_result, split_result, split_result]
        mock_re_compile.return_value.search.side_effect = [None, True, None, True, None, True]
        result = get_num_of_given_type_of_nodes_from_deployment(self.profile, self.user, self.platform_types)
        self.assertEqual(result, {'Cpp': 0, 'Msc': 0, 'Bsc': 0})

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.split")
    @patch("enmutils.lib.log.logger.debug")
    def test_num_of_given_type_of_nodes_from_deployment_pattern_mismatch(self, mock_logger_debug, mock_re_split,
                                                                         mock_re_compile):
        response = Mock()
        response1 = "CppConnectivityInformation 842 instance(s) found"
        response2 = "MscConnectivityInformation 8 instance(s) found"
        response3 = "Error : 469 "
        response.get_output.side_effect = [response1, response2, response3, response3]
        split_result1 = ["", "842"]
        split_result2 = ["", "8"]
        mock_re_split.side_effect = [split_result1, split_result2]
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.side_effect = [True, True, None, None]
        result = get_num_of_given_type_of_nodes_from_deployment(self.profile, self.user, self.platform_types)
        self.assertEqual(result, {'Cpp': 842, 'Msc': 8, 'Bsc': 0})
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.split")
    def test_num_of_given_type_of_nodes_from_deployment_logs_exception(self, mock_re_split, mock_re_compile, *_):
        response1 = Mock()
        response2 = Mock()
        response_cpp = "CppConnectivityInformation 842 instance(s) found"
        response_msc = "MscConnectivityInformation 8 instance(s) found"
        response1.get_output.return_value = response_cpp
        response2.get_output.return_value = response_msc
        split_result1 = ["", "842"]
        split_result2 = ["", "8"]
        mock_re_split.side_effect = [split_result1, split_result2]
        self.user.enm_execute.side_effect = [response1, response2, Exception]
        mock_re_compile.return_value.search.side_effect = [True, True]
        result = get_num_of_given_type_of_nodes_from_deployment(self.profile, self.user, self.platform_types)
        self.assertEqual(result, {'Cpp': 842, 'Msc': 8})
        self.assertTrue(self.profile.add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.split")
    def test_get_total_number_of_nodes_on_deployment_is_successful_1(self, mock_re_split, mock_re_compile):
        response = Mock()
        response.get_output.return_value = "NetworkElement 1000 instance(s) found"
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = ["", "1000"]
        mock_re_compile.return_value.search.return_value = True
        result = get_total_number_of_nodes_on_deployment(self.profile, self.user)
        self.assertEqual(result, 1000)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.split")
    def test_get_total_number_of_nodes_on_deployment_is_successful_2(self, mock_re_split, mock_re_compile):
        response = Mock()
        response.get_output.return_value = "0 instance(s) found"
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = ["", "0"]
        mock_re_compile.return_value.search.side_effect = [None, True]
        result = get_total_number_of_nodes_on_deployment(self.profile, self.user)
        self.assertEqual(result, 0)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.re.compile")
    def test_get_total_number_of_nodes_on_deployment_does_not_match_pattern(self, mock_re_compile):
        response = Mock()
        response.get_output.return_value = "Error : 508 response error"
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.side_effect = [None, None]
        result = get_total_number_of_nodes_on_deployment(self.profile, self.user)
        self.assertEqual(result, 0)

    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    def test_get_total_number_of_nodes_on_deployment_adds_error_as_exception(self, *_):
        self.user.enm_execute.side_effect = Exception
        get_total_number_of_nodes_on_deployment(self.profile, self.user)
        self.assertTrue(self.profile.add_error_as_exception.called)

    def test_map_alarm_rate_with_nodes_is_successful_if_snmp_rate_greater_than_aml(self):
        self.snmp_rate = 3.0
        expected_result = {'CPP': (self.cpp_rate, ['LTE01']), 'SNMP': (2.0, ['LTE01dg2ERBS00001']),
                           'MSC': (self.msc_rate, ['MSC08', 'MSC01', 'MSC05']), 'BSC': (self.bsc_rate, ['BSC01']),
                           'AML': (self.aml_rate, ['CORE01RR66750001'])}
        alarm_dict = map_alarm_rate_with_nodes(self.nodes, self.bsc_rate, self.msc_rate, self.cpp_rate, self.snmp_rate,
                                               self.aml_rate, self.aml_ratio)
        self.assertEqual(alarm_dict, expected_result)

    def test_map_alarm_rate_with_nodes__sets_proper_snmp_rate_if_no_aml_nodes(self):
        self.snmp_rate = 3.0
        expected_result = {'CPP': (self.cpp_rate, ['LTE01']), 'SNMP': (3.0, ['LTE01dg2ERBS00001']),
                           'MSC': (self.msc_rate, ['MSC08', 'MSC01', 'MSC05']), 'BSC': (self.bsc_rate, ['BSC01']),
                           'AML': (self.aml_rate, [])}
        self.nodes = {'BSC': ['BSC01'], 'MSC-DB-BSP': ['MSC01'], 'MSC-BC-BSP': ['MSC05'], 'MSC-BC-IS': ['MSC08'],
                      'ERBS': ['LTE01'], 'RadioNode': ['LTE01dg2ERBS00001']}
        self.nodes_list = [Mock(node_id='LTE01ERBS0001'), Mock(node_id='LTE01ERBS0002')]
        alarm_dict = map_alarm_rate_with_nodes(self.nodes, self.bsc_rate, self.msc_rate, self.cpp_rate, self.snmp_rate,
                                               self.aml_rate, self.aml_ratio)
        self.assertEqual(alarm_dict, expected_result)

    def test_map_alarm_rate_with_nodes_is_successful_if_snmp_rate_less_than_aml(self):
        expected_result = {'CPP': (self.cpp_rate, ['LTE01']), 'SNMP': (self.snmp_rate, ['LTE01dg2ERBS00001']),
                           'MSC': (self.msc_rate, ['MSC08', 'MSC01', 'MSC05']), 'BSC': (self.bsc_rate, ['BSC01']),
                           'AML': (self.aml_rate, ['CORE01RR66750001'])}
        alarm_dict = map_alarm_rate_with_nodes(self.nodes, self.bsc_rate, self.msc_rate, self.cpp_rate, self.snmp_rate,
                                               self.aml_rate, self.aml_ratio)
        self.assertEqual(alarm_dict, expected_result)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.get_specific_problem_iterator")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.map_nodes_for_profile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.AlarmBurst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.execute_burst")
    def test_setup_alarm_burst(self, mock_alarm_burst, mock_logger_debug, *_):
        mock_alarm_burst.side_effect = [None, Exception, None]
        alarm_dict = {'CPP': (self.cpp_rate, ['LTE01']), 'SNMP': (self.snmp_rate, ['LTE01dg2ERBS00001']),
                      'MSC': (self.msc_rate, ['MSC08', 'MSC01', 'MSC05']), 'BSC': (0, ['BSC01'])}
        setup_alarm_burst(self.profile, alarm_dict, self.burst_id, self.alarm_size_and_sp, 1, 1, self.teardown_list)
        self.assertEqual(mock_alarm_burst.call_count, 3)
        self.assertEqual(mock_logger_debug.call_count, 1)

    def test_calculate_alarm_load_distribution_rate_returns_zero_for_snmp(self):
        node_type_count = {'Msc': 10, 'Bsc': 20, 'Cpp': 200}
        total_node_count = 230
        msc_rate, bsc_rate, cpp_rate, snmp_rate = calculate_alarm_rate_distribution(node_type_count, total_node_count,
                                                                                    self.burst_rate)
        self.assertEqual(msc_rate, 1.7391)
        self.assertEqual(bsc_rate, 3.4783)
        self.assertEqual(cpp_rate, 34.7826)
        self.assertEqual(snmp_rate, 0)

    def test_calculate_alarm_load_distribution_rate_returns_correct_alarm_rates(self):
        node_type_count = {'Msc': 10, 'Bsc': 20, 'Cpp': 200}
        total_node_count = 300
        msc_rate, bsc_rate, cpp_rate, snmp_rate = calculate_alarm_rate_distribution(node_type_count, total_node_count,
                                                                                    self.burst_rate)
        self.assertEqual(msc_rate, 1.3333)
        self.assertEqual(bsc_rate, 2.6667)
        self.assertEqual(cpp_rate, 26.6667)
        self.assertEqual(snmp_rate, 9.3333)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.get_specific_problem_iterator')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.collect_nodes_for_profile',
           return_value=[Mock()] * 3)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.AlarmBurst.start')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.set_teardown_list')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log.logger.debug')
    def test_execute_burst_is_successful_for_snmp(self, mock_debug, *_):
        nodes = [Mock()] * 5
        execute_burst(Mock(), nodes, len(nodes), "111", 0.02, 900, [1, "Node gone"], 9, 1, 1, [], "SNMP")
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.get_specific_problem_iterator')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.collect_nodes_for_profile',
           return_value=[Mock()] * 3)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.AlarmBurst.start_aml')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.set_teardown_list')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log.logger.debug')
    def test_execute_burst_is_successful_for_aml(self, mock_debug, *_):
        nodes = [Mock()] * 5
        execute_burst(Mock(), nodes, len(nodes), "111", 0.02, 900, [1, "Node gone"], 9, 1, 1, [], "AML")
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.get_specific_problem_iterator')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.collect_nodes_for_profile',
           return_value=[Mock()] * 3)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.AlarmBurst.start', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.set_teardown_list')
    def test_execute_burst_raises_timeout_exception(self, mock_set_teardown, *_):
        nodes = [Mock()] * 5
        self.assertRaises(TimeoutException, execute_burst, Mock(), nodes, len(nodes), "111", 0.02, 900,
                          [1, "Node gone"], 9, 1, 1, [], "CPP")
        self.assertEqual(1, mock_set_teardown.call_count)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.get_specific_problem_iterator')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.collect_nodes_for_profile',
           return_value=[Mock()] * 3)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.AlarmBurst.start',
           side_effect=FailedNetsimOperation("Error", nodes=[Mock()]))
    @patch("enmutils_int.lib.profile.Profile")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.set_teardown_list')
    def test_execute_burst_logs_failed_netsim_operation(self, mock_set_teardown, mock_profile, *_):
        nodes = [Mock()] * 5
        execute_burst(mock_profile, nodes, len(nodes), "111", 0.02, 900, [1, "Node gone"], 9, 1, 1, [], "BSC")
        self.assertEqual(1, mock_set_teardown.call_count)
        self.assertEqual(1, mock_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.Burst')
    def test_stop_burst_is_successful(self, mock_burst, mock_log):
        nodes = [Mock()] * 5
        stop_burst(nodes, '111')
        self.assertTrue(mock_burst.return_value.stop.called)
        self.assertFalse(mock_log.logger.debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.Burst')
    def test_stop_burst_for_failed_netsim_operation(self, mock_burst, mock_log):
        nodes = [Mock()] * 5
        mock_burst.return_value.stop.side_effect = FailedNetsimOperation
        stop_burst(nodes, '111')
        self.assertTrue(mock_log.logger.debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.Burst')
    def test_stop_burst_for_exception(self, mock_burst, mock_log):
        nodes = [Mock()] * 5
        mock_burst.return_value.stop.side_effect = Exception
        stop_burst(nodes, '111')
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmsearch_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_open_alarms")
    def test_execute_alarm_search_tasks__is_succesful_for_open_alarms(self, mock_search_for_open_alarms, mock_add_nodes,
                                                                      mock_delete_nodes, mock_alarm_search_help, *_):
        user_dict = {self.user.username: (123456879, 789546213)}
        execute_alarm_search_tasks(self.user, self.node_data, user_dict, self.nodes_list)
        self.assertEqual(mock_add_nodes.call_count, 1)
        self.assertEqual(mock_search_for_open_alarms.call_count, 1)
        self.assertEqual(mock_delete_nodes.call_count, 1)
        self.assertEqual(mock_alarm_search_help.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmsearch_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_historical_alarms")
    def test_execute_alarm_search_tasks__is_succesful_for_historical_alarms(self, mock_search_for_historical_alarms,
                                                                            mock_add_nodes, mock_delete_nodes,
                                                                            mock_alarm_search_help, *_):
        user_dict = {self.user.username: (123456879, 789546213)}
        execute_alarm_search_tasks(self.user, self.node_data, user_dict, self.nodes_list, HISTORICAL)
        self.assertEqual(mock_add_nodes.call_count, 1)
        self.assertEqual(mock_search_for_historical_alarms.call_count, 1)
        self.assertEqual(mock_delete_nodes.call_count, 1)
        self.assertEqual(mock_alarm_search_help.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmsearch_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_historical_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_open_alarms")
    def test_execute_alarm_search_tasks__is_failed(self, mock_search_for_open_alarms, mock_search_for_historical_alarms,
                                                   mock_add_nodes, mock_delete_nodes, mock_alarm_search_help, *_):
        user_dict = {self.user.username: (123456879, None)}
        execute_alarm_search_tasks(self.user, self.node_data, user_dict, self.nodes_list, HISTORICAL)
        self.assertEqual(0, mock_add_nodes.call_count)
        self.assertEqual(0, mock_search_for_historical_alarms.call_count)
        self.assertEqual(0, mock_delete_nodes.call_count)
        self.assertEqual(0, mock_alarm_search_help.call_count)
        self.assertEqual(0, mock_search_for_open_alarms.call_count)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmsearch_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_historical_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarm_search_for_open_alarms")
    def test_execute_alarm_search_tasks__with_empty_user_dictionary(self, mock_search_for_open_alarms,
                                                                    mock_search_for_historical_alarms,
                                                                    mock_add_nodes, mock_delete_nodes,
                                                                    mock_alarm_search_help, *_):
        user_dict = {}
        execute_alarm_search_tasks(self.user, self.node_data, user_dict, self.nodes_list, HISTORICAL)
        self.assertEqual(0, mock_add_nodes.call_count)
        self.assertEqual(0, mock_search_for_historical_alarms.call_count)
        self.assertEqual(0, mock_delete_nodes.call_count)
        self.assertEqual(0, mock_alarm_search_help.call_count)
        self.assertEqual(0, mock_search_for_open_alarms.call_count)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmviewer_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    def test_execute_alarm_monitor_tasks__is_successful(self, mock_add_nodes, mock_delete_nodes,
                                                        mock_alarm_viewer_help, *_):
        user_dict = {self.user.username: (123456879, 789546213)}
        execute_alarm_monitor_tasks(self.user, self.node_data, user_dict, len(self.nodes_list))
        self.assertEqual(mock_add_nodes.call_count, 1)
        self.assertEqual(mock_delete_nodes.call_count, 1)
        self.assertEqual(mock_alarm_viewer_help.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmviewer_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    def test_execute_alarm_monitor_tasks__with_empty_user_dictionary(self, mock_add_nodes, mock_delete_nodes,
                                                                     mock_alarm_viewer_help, mock_log, *_):
        user_dict = {}
        execute_alarm_monitor_tasks(self.user, self.node_data, user_dict, len(self.nodes_list))
        self.assertEqual(0, mock_add_nodes.call_count)
        self.assertEqual(0, mock_alarm_viewer_help.call_count)
        self.assertEqual(0, mock_delete_nodes.call_count)
        self.assertEqual(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.alarmviewer_help")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.add_nodes_to_given_workspace_for_a_user")
    def test_execute_alarm_monitor_tasks__is_failed(self, mock_add_nodes, mock_delete_nodes,
                                                    mock_alarm_viewer_help, *_):
        user_dict = {self.user.username: (123456879, None)}
        execute_alarm_monitor_tasks(self.user, self.node_data, user_dict, len(self.nodes_list))
        self.assertEqual(0, mock_add_nodes.call_count)
        self.assertEqual(0, mock_alarm_viewer_help.call_count)
        self.assertEqual(0, mock_delete_nodes.call_count)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log")
    def test_put_profile_to_sleep__is_succesful(self, mock_log, *_):
        profile = Mock()
        put_profile_to_sleep(profile, 1)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.random")
    def test_set_up_alarm_text_size_and_problem_distribution__is_successful(self, mnock_random, mock_log):
        alarm_size_distribution = [1000, 1000, 1000, 1000, 2000, 2000, 2000, 2000, 3000, 4000]
        alarm_problem_distribution = [('Nss Synchronization System Clock Status Change', 'indeterminate'),
                                      ('EXTERNAL ALARM', 'major')]
        mnock_random.choice.side_effect = [2000, ('Nss Synchronization System Clock Status Change', 'indeterminate')]
        result = set_up_alarm_text_size_and_problem_distribution(alarm_size_distribution, alarm_problem_distribution)
        self.assertEqual(result, [2000, ('Nss Synchronization System Clock Status Change', 'indeterminate')])
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    def test_set_teardown_list__is_success(self):
        burst = Mock()
        teardown_list = []
        set_teardown_list(burst, teardown_list)
        self.assertEqual(len(teardown_list), 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.update_com_ecim_parameters")
    def test_set_up_event_type_and_probable_cause__is_successful(self, mock_update, mock_log):
        mock_update.return_value = (1, 1)
        set_up_event_type_and_probable_cause()
        mock_update.called_with(1, 0)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_common_utils.map_nodes_for_profile")
    def test_collect_nodes_for_profile__is_successful(self, mock_map_nodes, mock_log):
        nodes = [Mock(), Mock()]
        total_nodes = len(nodes)
        collect_nodes_for_profile(nodes, total_nodes)
        self.assertEqual(mock_log.logger.info.call_count, 1)
        mock_map_nodes.called_with(nodes)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
