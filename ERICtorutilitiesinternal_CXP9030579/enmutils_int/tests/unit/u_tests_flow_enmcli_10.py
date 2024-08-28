#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow import ENMCLI10Flow
from enmutils.lib.exceptions import EnmApplicationError
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class ENMCLI10FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.node = Mock()
        self.node.node_id = "ABC"
        self.flow = ENMCLI10Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.execute_and_validate_response',
           side_effect=[Mock(), Mock(), Exception])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.ENMCLI10Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_debug, mock_enm_cli, mock_nodes, mock_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_nodes.side_effect = [self.node, self.node]
        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_exception.called)
        self.assertTrue(mock_enm_cli.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.execute_command_on_enm_cli')
    def test_execute_and_validate_response(self, mock_execute, mock_log):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN', u'', u'SUCCESS FDN', u'', u'', u'2 instance(s) updated']
        mock_execute.return_value = response
        self.flow.execute_and_validate_response(self.user, [self.node, self.node], 'manual')
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow.execute_command_on_enm_cli')
    def test_execute_and_validate_response_raises_enmapplication_error(self, mock_execute):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN', u'', u'SUCCESS FDN', u'', u'', u'1 instance(s) updated']
        mock_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.execute_and_validate_response, self.user, [self.node, self.node], 'manual')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
