#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow import Nhm13Flow, CREATED_BY_DEFAULT
from mock import patch, Mock, call
from testslib import unit_test_utils


class Nhm13UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm13Flow()
        self.user = Mock()
        self.user.username = "User_u0"
        self.flow.ADMIN_ROLE = ["NHM_Administrator"]
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.NUM_ADMINS = 1
        self.flow.NUM_OPERATORS = 1
        self.flow.SCHEDULE_SLEEP = 2
        self.flow.REQUIRED_NODES = 10

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.NhmKpi')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.filter_nodes_having_poid_set")
    def test_activate_kpi__successful(self, mock_filter_nodes_having_poid_set, mock_nhm_kpi):
        kpi_list = ['Downlink_Latency', 'Abnormal_Releases_ENB', 'Average_DL_UE_Latency']
        node1 = Mock(primary_type='ERBS', node_id='123', poid="123456")
        node2 = Mock(primary_type='ERBS', node_id='234', poid="234567")
        mock_filter_nodes_having_poid_set.return_value = [node1, node2]
        user = Mock()

        self.flow.activate_kpi(user, kpi_list, [node1, node2])
        self.assertTrue(mock_nhm_kpi.called)
        self.assertTrue(call(name='Downlink_Latency', nodes=[node1, node2], user=user, po_ids=['123456', '234567'],
                             created_by=CREATED_BY_DEFAULT) in mock_nhm_kpi.mock_calls)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.NhmKpi')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.filter_nodes_having_poid_set")
    def test_activate_kpi__adds_error_if_activation_fails(
            self, mock_filter_nodes_having_poid_set, mock_nhm_kpi, mock_add_error_as_exception):
        kpi_list = ['Downlink_Latency', 'Abnormal_Releases_ENB', 'Average_DL_UE_Latency']
        node1 = Mock(primary_type='ERBS', node_id='123', poid="123456")
        node2 = Mock(primary_type='ERBS', node_id='234', poid="234567")
        mock_filter_nodes_having_poid_set.return_value = [node1, node2]
        user = Mock()
        mock_nhm_kpi.return_value.activate.side_effect = Exception

        self.flow.activate_kpi(user, kpi_list, [node1, node2])
        self.assertTrue(mock_nhm_kpi.called)
        self.assertTrue(call(name='Downlink_Latency', nodes=[node1, node2], user=user, po_ids=['123456', '234567'],
                             created_by=CREATED_BY_DEFAULT) in mock_nhm_kpi.mock_calls)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.log.logger.info")
    def test_expected_count__successful(self, mock_logger_info):
        used_nodes = ['A', 'B']
        self.flow.NUMBER_OF_CELLS = 3
        self.flow.NUMBER_OF_KPIS = 4
        self.flow.expected_count(used_nodes)
        self.assertTrue(mock_logger_info.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.activate_kpi')
    def test_nodes_to_be_used__successful(self, mock_activate_kpi, mock_logger_debug):
        self.flow.RECOMMENDED_KPIS = ['Downlink_Latency', 'Abnormal_Releases_ENB', 'Average_DL_UE_Latency']
        used_nodes = ['A', 'B']
        users = ['User_u0', 'User_u1']
        self.flow.nodes_to_be_used(used_nodes, users)
        self.assertTrue(mock_logger_debug.called)
        self.assertTrue(mock_activate_kpi.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.nodes_to_be_used", return_value=Mock())
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.expected_count")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.'
           'Nhm13Flow.deallocate_unused_nodes_and_update_profile_persistence', return_value=Mock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.get_nodes_with_required_number_of_cells',
           return_value=['A', 'B'])
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.create_profile_users')
    def test_execute_flow__successful(self, mock_create_profile_users, mock_activate_kpi, mock_expected_count, *_):
        mock_create_profile_users.return_value = [self.user, self.user]
        self.flow.TOTAL_NODES = 1
        self.flow.NUMBER_OF_CELLS = 3

        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_activate_kpi.called)
        self.assertTrue(mock_expected_count.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.keep_running")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.get_nodes_with_required_number_of_cells')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.create_profile_users')
    def test_execute_flow__handles_get_nodes_with_required_number_of_cells_exception(
            self, mock_create_profile_users, mock_get_nodes, mock_add_error, mock_keep_running, *_):
        mock_create_profile_users.return_value = [self.user, self.user]
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.side_effect = Exception
        self.flow.RECOMMENDED_KPIS = ['Downlink_Latency', 'Abnormal_Releases_ENB', 'Average_DL_UE_Latency']
        self.flow.TOTAL_NODES = 1
        self.flow.NUMBER_OF_CELLS = 3

        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
