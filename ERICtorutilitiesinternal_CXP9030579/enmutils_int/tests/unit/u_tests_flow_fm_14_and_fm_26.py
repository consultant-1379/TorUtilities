#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock

from enmutils.lib.enm_node import ERBSNode
from enmutils_int.lib.profile_flows.fm_flows.fm_26_flow import Fm26
from testslib import unit_test_utils


class AlarmHistoryUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
        ]
        self.flow = Fm26()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "TEST1"
        self.flow.PIB_COMMAND = "some_command"
        self.flow.TIME_PERIOD_IN_MIN = 45
        self.flow.MAX_ALARMS = [20000, 50000]
        self.flow.safe_request = True
        self.good_response = Mock(rc=0, stdout="'Plan Status: Successful'")
        self.error_response = Mock(rc=5, stdout="Some Error")
        self.error_response2 = [Exception("Some Exception")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.decrease_max_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.get_alarm_hist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.increase_max_alarms")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.create_users')
    def test_execute_alarm_history_cli_capability_main_flow__success(self, mock_create_user, mock_keep_running,
                                                                     mock_sleep_until_time, mock_increase_max_alarms,
                                                                     mock_get_alarm_hist, mock_decrease_max_alarms):
        mock_keep_running.side_effect = [True, False]
        mock_get_alarm_hist.return_value = True
        self.flow.alarm_history_cli_capability_main_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep_until_time.called)
        self.assertTrue(mock_increase_max_alarms.called)
        self.assertTrue(mock_get_alarm_hist.called)
        self.assertTrue(mock_decrease_max_alarms.called)

    @patch("time.sleep")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.get_alarm_hist", side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.decrease_max_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.increase_max_alarms")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.create_users')
    def test_execute_alarm_history_cli_capability_main_flow__exception_raised(
            self, mock_create_user, mock_sleep_until_time, mock_increase_max_alarms, mock_decrease_max_alarms,
            mock_add_error_as_exception, *_):
        self.flow.alarm_history_cli_capability_main_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_sleep_until_time.called)
        self.assertTrue(mock_increase_max_alarms.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_decrease_max_alarms.called)

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.decrease_max_alarms", side_effect=[False, True])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.get_alarm_hist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.increase_max_alarms")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.create_users')
    def test_execute_alarm_history_cli_capability_main_flow__continues_with_errors(self, mock_create_user,
                                                                                   mock_keep_running,
                                                                                   mock_sleep_until_time,
                                                                                   mock_increase_max_alarms,
                                                                                   mock_get_alarm_hist,
                                                                                   *_):
        response = [False, True]
        mock_get_alarm_hist.side_effect = response + [response[1]]
        mock_increase_max_alarms.side_effect = response + [response[1], response[1]]
        mock_sleep_until_time.side_effect = response + [response[1], response[1], response[1]]
        mock_keep_running.side_effect = response + [response[1], response[1], response[1], response[1]]
        mock_create_user.side_effect = response + [response[1], response[1], response[1], response[1], response[1]]
        self.assertFalse(self.flow.alarm_history_cli_capability_main_flow())

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.decrease_max_alarms")
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.increase_max_alarms")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.create_users')
    def test_execute_alarm_history_cli_capability_main_flow__exception_raised_when_no_users(self, mock_create_user,
                                                                                            mock_add_error_as_exception,
                                                                                            mock_keep_running,
                                                                                            mock_sleep_until_time,
                                                                                            mock_increase_max_alarms,
                                                                                            mock_execute,
                                                                                            mock_decrease_max_alarms,
                                                                                            *_):
        mock_create_user.side_effect = self.error_response2
        mock_keep_running.side_effect = [True, False]
        output = ['>>alarm hist * --begin 2017-10-10T11:40:00',
                  u'presentSeverity\tNodeName\tspecificProblem\teventTime\tobjectOfReference\tproblemText\talarmState\talarmId\tprobableCause\teventType\trecordType',
                  u'CRITICAL\tnetsim_LTE03ERBS00037\tHeartbeat Failure\t2017-10-09T19:52:14\tSubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00037\tFailed to resolve Notification IRP\tACTIVE_UNACKNOWLEDGED\t-2\tLAN Error/Communication Error\tCommunications alarm\tHEARTBEAT_ALARM',
                  u'', u'Total number of alarms fetched for the given query is :1']
        response = Mock()
        response.get_output.return_value = output
        mock_execute.return_value = response

        self.flow.alarm_history_cli_capability_main_flow()
        self.assertTrue(mock_create_user.called)
        self.assertEqual(1, mock_add_error_as_exception.call_count)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep_until_time.called)
        self.assertFalse(mock_increase_max_alarms.called)
        self.assertFalse(mock_decrease_max_alarms.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.update_pib_parameter_on_enm")
    def test_increase_max_alarms__success(self, mock_update_pib_parameter_on_enm, mock_logger_debug):
        mock_update_pib_parameter_on_enm.return_value = True
        self.flow.increase_max_alarms()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.update_pib_parameter_on_enm")
    def test_increase_max_alarms__exception(self, mock_update_pib_parameter_on_enm, mock_logger_debug):
        mock_update_pib_parameter_on_enm.side_effect = Exception
        self.flow.increase_max_alarms()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.update_pib_parameter_on_enm")
    def test_decrease_max_alarms__success(self, mock_update_pib_parameter_on_enm, mock_logger_debug):
        mock_update_pib_parameter_on_enm.return_value = True
        self.flow.decrease_max_alarms()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.update_pib_parameter_on_enm")
    def test_decrease_max_alarms__exception(self, mock_update_pib_parameter_on_enm, mock_logger_debug):
        mock_update_pib_parameter_on_enm.side_effect = Exception
        self.flow.decrease_max_alarms()
        self.assertTrue(mock_logger_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
