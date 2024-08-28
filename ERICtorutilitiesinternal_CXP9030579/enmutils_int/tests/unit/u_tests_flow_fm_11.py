#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.profile_flows.fm_flows.fm_11_flow import Fm11
from testslib import unit_test_utils


class Fm11UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.flow = Fm11()
        self.flow.NUM_USERS = 2
        self.flow.USER_ROLES = "TEST1"
        self.flow.SCHEDULE_SLEEP = 2
        self.time_span = 60 * 25
        self.error_response = [Exception("Some exception")]
        self.error_response1 = [ScriptEngineResponseValidationError("Some other exception", "")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.timedelta")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11_success(self, mock_create_user, mock_keep_running, mock_logger_debug, *_):
        mock_user = Mock()
        command_response = Mock()
        mock_user.enm_execute.return_value = command_response
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_11()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11_continues_with_errors(self, mock_create_user, mock_keep_running, mock_logger_debug, *_):
        mock_create_user.return_value = [self.user]
        response = [False, True]
        mock_logger_debug.side_effect = response
        mock_keep_running.side_effect = response + [response[1]]
        self.assertFalse(self.flow.execute_flow_fm_11())

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.timedelta")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11_throws_exception(self, mock_create_user, mock_keep_running,
                                                 mock_add_error_as_exception, *_):

        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.user.enm_execute.side_effect = self.error_response
        self.flow.execute_flow_fm_11()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.state")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11_raises_ScriptEngineResponseValidationError(self, mock_create_user, *_):
        mock_create_user.return_value = [self.user]
        command_response = Mock()
        command_response.get_output.return_value = ["Invalid value"]
        self.user.enm_execute.return_value = command_response
        self.assertRaises(ScriptEngineResponseValidationError, self.flow.execute_flow_fm_11)

    @patch('time.sleep')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.timedelta")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11_alarm_count_greater_than_10k(self, mock_create_user, mock_keep_running,
                                                             mock_logger_debug, *_):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        output = ["Please narrow down the criteria"]
        command_response = Mock()
        command_response.get_output.return_value = output
        self.user.enm_execute.return_value = command_response
        self.flow.execute_flow_fm_11()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('time.sleep')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.timedelta")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.create_users')
    def test_execute_flow_fm_11__string_not_in_line_break(self, mock_create_user, mock_keep_running, mock_info, *_):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        output = [""]
        command_response = Mock()
        command_response.get_output.return_value = output
        self.user.enm_execute.return_value = command_response
        self.flow.execute_flow_fm_11()
        self.assertEqual(mock_info.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
