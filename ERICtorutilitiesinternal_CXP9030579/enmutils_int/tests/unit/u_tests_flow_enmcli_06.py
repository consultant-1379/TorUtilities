#!/usr/bin/env python
import unittest2

from mock import patch, Mock

from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_06_flow import EnmCli06Flow


class EnmCli06FlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = EnmCli06Flow()
        self.flow.NUM_USERS = 1
        self.flow.NUM_COMMANDS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.SCHEDULED_TIMES_STRINGS = ["08:00:00"]
        self.flow.THREAD_QUEUE_TIMEOUT = 0

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.get_nodes_list_by_attribute",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.create_profile_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.chunks")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.create_and_execute_threads")
    def test_execute_flow_is_successful(self, mock_create_and_execute_threads,
                                        mock_chunks, *_):
        mock_chunks.return_value = [(Mock())]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.get_nodes_list_by_attribute",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.create_profile_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.chunks")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.create_and_execute_threads")
    def test_execute_flow_raises_environ_error(self, mock_create_and_execute_threads,
                                               mock_chunks, mock_add_error_as_exception, *_):
        mock_chunks.return_value = []
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_06_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.execute_command_on_enm_cli")
    def test_task_set_is_successful(self, mock_execute_command_on_enm_cli,
                                    mock_add_error_as_exception, mock_sleep):
        worker = [Mock(), [Mock()]]
        self.flow.task_set(worker, self.flow)
        self.assertTrue(mock_execute_command_on_enm_cli.called)
        self.assertTrue(mock_sleep.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_06_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.EnmCli06Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.enmcli_flows."
           "enmcli_06_flow.execute_command_on_enm_cli")
    def test_task_set_raises_exception(self, mock_execute_command_on_enm_cli,
                                       mock_add_error_as_exception, mock_sleep):
        worker = [Mock(), [Mock()]]
        mock_execute_command_on_enm_cli.side_effect = Exception("message")
        self.flow.task_set(worker, self.flow)
        self.assertTrue(mock_execute_command_on_enm_cli.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
