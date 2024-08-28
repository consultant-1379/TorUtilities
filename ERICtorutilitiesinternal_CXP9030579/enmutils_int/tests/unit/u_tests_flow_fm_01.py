#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from enmutils_int.lib.profile_flows.fm_flows.fm_01_flow import Fm01
from enmutils_int.lib.workload.fm_01 import FM_01 as fm_01_profile
from testslib import unit_test_utils


class FM01UnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.flow = Fm01()
        self.flow.ALARM_SIZE_DISTRIBUTION = [1000]
        self.flow.ALARM_PROBLEM_DISTRIBUTION = [('Nss Synchronization System Clock Status Change', 'indeterminate')]
        self.nodes = {'MSC': [Mock()], 'BSC': [Mock()], 'RadioNode': [Mock()], 'ERBS': [Mock()]}
        self.user = [Mock()]
        self.flow.BURST_RATE = 24
        self.flow.NUM_USERS = 1
        self.flow.burst_id = '111'
        self.flow.USER_ROLES = "ADMINISTRATOR"
        self.flow.FM_01_TOTAL_ALARMS = 1840000
        self.flow.MSC_BURST_RATE = 0.038
        self.flow.BSC_BURST_RATE = 0.038
        self.flow.PLATFORM_TYPES = ["Cpp", "Msc", "Bsc"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.execute_fm_01_alarm_rate_normal_flow")
    def test_fm_profile_execute_fm_01_alarm_rate_normal_flow__successful(self, mock_flow):
        fm_01_profile().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.stop_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.helper_methods")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.configure_fm_alarm_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_total_number_of_nodes_on_deployment",
           return_value=200)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_num_of_given_type_of_nodes_from_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.sleep")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.load_mgr.wait_for_setup_profile')
    def test__execute_fm_alarm_rate_normal_flow(self, mock_wait_for_setup_profile, mock_sleep, mock_create_user,
                                                mock_get_num_nodes, mock_configure_fm_alarm_burst, *_):
        mock_wait_for_setup_profile.return_value = True
        mock_create_user.return_value = self.user
        mock_get_num_nodes.return_value = {'Cpp': 100, 'Bsc': 16, 'Msc': 0}
        with patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.exchange_nodes") as mock_exchange_nodes:
            with patch('enmutils.lib.log.logger.info') as mock_logger_info:
                self.flow.execute_fm_01_alarm_rate_normal_flow()
                self.assertTrue(mock_wait_for_setup_profile.called)
                self.assertTrue(mock_configure_fm_alarm_burst.called)
                self.assertEqual(mock_logger_info.call_count, 3)
                self.assertTrue(mock_sleep.called)
                self.assertTrue(mock_exchange_nodes.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.helper_methods")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.configure_fm_alarm_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_total_number_of_nodes_on_deployment",
           return_value=200)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_num_of_given_type_of_nodes_from_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.sleep")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.load_mgr.wait_for_setup_profile')
    def test__execute_fm_01_alarm_rate_normal_flow_logs_exception(self, mock_wait_for_setup_profile, mock_sleep,
                                                                  mock_create_user, mock_get_num_nodes,
                                                                  mock_configure_fm_alarm_burst, *_):
        mock_wait_for_setup_profile.return_value = True
        mock_create_user.return_value = self.user
        mock_get_num_nodes.return_value = {'Cpp': 100, 'Bsc': 16, 'Msc': 0}
        with patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.add_error_as_exception") as mock_add_error_as_exception:
            with patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.exchange_nodes") as mock_exchange_nodes:
                with patch('enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.log.logger.info') as mock_logger_info:
                    with patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.stop_burst") as mock_stop_burst:
                        mock_stop_burst.side_effect = Exception
                        self.flow.execute_fm_01_alarm_rate_normal_flow()
                        self.assertTrue(mock_wait_for_setup_profile.called)
                        self.assertTrue(mock_configure_fm_alarm_burst.called)
                        self.assertEqual(mock_logger_info.call_count, 2)
                        self.assertTrue(mock_sleep.called)
                        self.assertTrue(mock_exchange_nodes.called)
                        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_total_number_of_nodes_on_deployment",
           return_value=200)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.get_num_of_given_type_of_nodes_from_deployment",
           return_value={'Cpp': 100, 'Bsc': 100})
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.log.logger.info')
    def test__calculate_initial_alarm_rates_is_successful(self, mock_logger_info, *_):
        self.flow.calculate_initial_alarm_rates(self.user)
        self.assertEqual(mock_logger_info.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
