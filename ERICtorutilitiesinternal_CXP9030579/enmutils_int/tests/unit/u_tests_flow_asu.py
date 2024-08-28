#!/usr/bin/env python
from datetime import datetime
import unittest2
from mock import Mock, PropertyMock, patch
from enmutils_int.lib.profile_flows.asu_flows.asu_flow import AsuFlow
from testslib import unit_test_utils


class AsuFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes_list = [Mock(), Mock()]
        self.flow = AsuFlow()
        self.flow.NAME = "ABC"
        self.flow.FILTERED_NODES_PER_HOST = 0
        self.flow.NUM_NODES = {}
        self.flow.NUM_USERS = 1
        self.flow.MAX_NODES = 1
        self.flow.SCHEDULED_DAYS = []
        self.flow.USER_ROLES = []
        self.flow.SKIP_SYNC_CHECK = True

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.get_schedule_time_strings',
           return_value=(["06:30:00"], [datetime(2020, 7, 27, 7, 0, 0)]))
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.get_timestamp_str')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.FlowAutomation')
    def test_execute_flow_asu_with_synced_nodes(self, mock_flow, mock_synced_nodes, mock_datetime, *_):
        mock_datetime.now.return_value = datetime(2020, 7, 27, 6, 30, 0)
        mock_synced_nodes.return_value = self.nodes_list
        self.flow.execute_flow()
        self.assertTrue(mock_flow.return_value.create_flow_automation.called)

    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.get_schedule_time_strings',
           return_value=(["06:30:00"], [datetime(2020, 7, 27, 6, 0, 0)]))
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.get_timestamp_str')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.AsuFlow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.asu_flows.asu_flow.FlowAutomation')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_execute_flow_asu_without_synced_nodes(self, mock_error, mock_flow, mock_synced_nodes, mock_datetime, *_):
        mock_datetime.now.return_value = datetime(2020, 7, 27, 6, 30, 0)
        mock_synced_nodes.return_value = []
        self.flow.execute_flow()
        self.assertFalse(mock_flow.return_value.create_flow_automation.called)
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
