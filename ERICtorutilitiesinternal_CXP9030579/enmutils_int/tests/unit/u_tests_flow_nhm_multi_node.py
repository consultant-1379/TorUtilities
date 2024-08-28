#!/usr/bin/env python
import unittest2
from mock import patch

from enmutils.lib.enm_user_2 import User
from enmutils_int.lib.nhm_widget import NetworkOperationalState, CellStatus
from enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow import NhmMultiNodeFlow
from testslib import unit_test_utils


class NhmMultiNodeFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = NhmMultiNodeFlow()
        self.users = [User(username='nhm_test_operator'), User(username='nhm_test_admin')]
        self.nodes = unit_test_utils.get_nodes(2)
        for node in self.nodes:
            node.poid = 9999999999999
        self.nodes_widget = NetworkOperationalState(user=self.users[0], nodes=self.nodes)
        self.flow.ADMIN_ROLE = ["NHM_Administrator"]
        self.flow.NUM_ADMINS = 1
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.NUM_OPERATORS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.call_widget_flow')
    def test_taskset_is_successful(self, mock_call_widget_flow, mock_debug):
        self.flow.taskset(self.nodes_widget)
        self.assertTrue(mock_call_widget_flow.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.call_widget_flow')
    def test_taskset_is_successful_with_cell_status_widget(self, mock_call_widget_flow):
        cell_status_widget = CellStatus(user=self.users[0], nodes=self.nodes)
        self.flow.taskset(cell_status_widget)
        self.assertEqual(cell_status_widget.ne_type, 'ERBS')
        self.assertTrue(mock_call_widget_flow.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.NhmMultiNodeFlow.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.NhmMultiNodeFlow.setup_nhm_profile')
    def test_setup_is_successful(self, mock_setup_profile, mock_create_users):
        mock_setup_profile.return_value = self.users, self.nodes
        self.flow.setup()
        self.assertTrue(mock_setup_profile.called)
        self.assertTrue(mock_create_users.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.NhmMultiNodeFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.NhmMultiNodeFlow.process_thread_queue_errors')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow.NhmMultiNodeFlow.keep_running')
    def test_execute_05_06_flow_is_successful(self, mock_keep_running, mock_thread_queue, mock_process_tq_errors,
                                              mock_sleep):
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_multi_node_flow([self.nodes_widget])
        mock_thread_queue.execute.assert_called()
        self.assertTrue(mock_process_tq_errors.called)
        self.assertTrue(mock_sleep.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
