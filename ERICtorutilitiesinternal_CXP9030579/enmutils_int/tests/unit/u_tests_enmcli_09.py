#!/usr/bin/env python
import unittest2

from mock import patch, Mock, MagicMock
from testslib import unit_test_utils
from enmutils_int.lib.workload.enmcli_09 import ENMCLI_09


class Enmcli09UnitTest(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.nodes_list = [Mock(node_name='CUCP_1'), Mock(node_name='CUCP_2')]
        self.profile = ENMCLI_09()
        self.profile.NUM_USERS = 1
        self.profile.USER_ROLES = ['Cmedit_Administrator']
        self.profile.SCHEDULED_TIME_STRINGS = ['10:00:00']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.workload.enmcli_09.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.keep_running')
    @patch('enmutils_int.lib.workload.enmcli_09.log.logger.debug')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.create_profile_users')
    def test_run_enmcli_09__is_successful(self, mock_create_profile_users, mock_debug, mock_keep_running, mock_nodes, mock_enmcli, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_nodes.side_effect = [self.nodes_list, []]
        mock_response = MagicMock()
        mock_response.get_output.return_value = ['Some output', '2 instance(s)']
        mock_enmcli.return_value = mock_response
        self.profile.run()
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_enmcli.called)

    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.add_error_as_exception')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.keep_running')
    @patch('enmutils_int.lib.workload.enmcli_09.log.logger.debug')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.create_profile_users')
    def test_run_enmcli_09__raise_exception(self, mock_create_profile_users, mock_debug, mock_keep_running, mock_nodes, mock_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_nodes.side_effect = []
        self.profile.run()
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_exception.called)

    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.workload.enmcli_09.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.keep_running')
    @patch('enmutils_int.lib.workload.enmcli_09.log.logger.debug')
    @patch('enmutils_int.lib.workload.enmcli_09.ENMCLI_09.create_profile_users')
    def test_run_enmcli_09__raise_environerror(self, mock_create_profile_users, mock_debug, mock_keep_running, mock_nodes, mock_cli, *_):
        mock_keep_running.side_effect = [True, False]
        mock_nodes.side_effect = [self.nodes_list]
        mock_response = MagicMock()
        mock_response.get_output.return_value = ['Some output', '4 instance(s)']
        mock_cli.return_value = mock_response
        self.profile.run()
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_cli.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
