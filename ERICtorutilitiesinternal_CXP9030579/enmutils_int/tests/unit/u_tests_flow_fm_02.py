#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from enmutils_int.lib.profile_flows.fm_flows.fm_02_flow import Fm02
from testslib import unit_test_utils


class FM02UnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.flow = Fm02()
        self.flow.ALARM_SIZE_DISTRIBUTION = [1000]
        self.flow.ALARM_PROBLEM_DISTRIBUTION = [('Nss Synchronization System Clock Status Change', 'indeterminate')]
        self.flow.TOTAL_NODES = 1
        self.flow.burst_id = '222'
        self.nodes = Mock()
        self.flow.BURST_RATE = 40
        self.flow.PLATFORM_TYPES = ["Cpp", "Msc", "Bsc"]
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "ADMINISTRATOR"
        self.flow.teardown_list = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_total_number_of_nodes_on_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_num_of_given_type_of_nodes_from_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.helper_methods")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.keep_running", side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.load_mgr.wait_for_setup_profile", side_effect=[False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.calculate_alarm_rate_distribution")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.configure_fm_alarm_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.log.logger.info")
    def test_execute_fm_02_alarm_rate_normal_flow(self, mock_logger_info, mock_sleep, mock_configure_fm_burst,
                                                  mock_create_profile_users, mock_calculate_alarm_load, *_):
        mock_create_profile_users.return_value = [Mock()]
        mock_calculate_alarm_load.return_value = 1, 2, 3, 4
        self.flow.execute_fm_02_alarm_rate_normal_flow()
        self.assertTrue(mock_logger_info.call_coubnt, 3)
        self.assertEqual(mock_calculate_alarm_load.call_count, 1)
        self.assertEqual(mock_create_profile_users.call_count, 1)
        self.assertTrue(mock_configure_fm_burst.call_count, 2)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_total_number_of_nodes_on_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_num_of_given_type_of_nodes_from_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.helper_methods")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.load_mgr.wait_for_setup_profile", side_effect=[False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.calculate_alarm_rate_distribution")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.configure_fm_alarm_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.log.logger.info")
    def test_execute_fm_02_alarm_rate_logs_exception(self, mock_logger_info, mock_sleep, mock_configure_fm_burst,
                                                     mock_create_profile_users, mock_calculate_alarm_load, *_):
        mock_create_profile_users.return_value = [Mock()]
        mock_calculate_alarm_load.return_value = 1, 2, 3, 4
        with patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.exchange_nodes") as mock_exchange_nodes:
            with patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.add_error_as_exception") as mock_add_error_as_exception:
                mock_exchange_nodes.side_effect = Exception
                self.flow.execute_fm_02_alarm_rate_normal_flow()
                self.assertTrue(mock_logger_info.call_coubnt, 3)
                self.assertEqual(mock_calculate_alarm_load.call_count, 1)
                self.assertEqual(mock_create_profile_users.call_count, 1)
                self.assertTrue(mock_configure_fm_burst.call_count, 2)
                self.assertTrue(mock_sleep.called)
                self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_total_number_of_nodes_on_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.get_num_of_given_type_of_nodes_from_deployment")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.helper_methods")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.load_mgr.wait_for_setup_profile", side_effect=[False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.configure_fm_alarm_burst")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.log.logger.info")
    def test_execute_fm_02_alarm_rate_distribution_exception(self, mock_logger_info, mock_sleep, mock_configure_fm_burst,
                                                             mock_create_profile_users, mock_calculate_alarm_load, *_):
        mock_create_profile_users.return_value = [Mock()]
        mock_calculate_alarm_load.return_value = 1, 2, 3, 4

        with patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.calculate_alarm_rate_distribution") as \
                mock_calculate_alarm_rate_distribution:
            with patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.add_error_as_exception") as \
                    mock_add_error_as_exception:
                mock_calculate_alarm_rate_distribution.side_effect = Exception
                self.flow.execute_fm_02_alarm_rate_normal_flow()
                self.assertTrue(mock_logger_info.call_coubnt, 3)
                self.assertEqual(mock_calculate_alarm_load.call_count, 1)
                self.assertEqual(mock_create_profile_users.call_count, 1)
                self.assertTrue(mock_configure_fm_burst.call_count, 2)
                self.assertTrue(mock_sleep.called)
                self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
