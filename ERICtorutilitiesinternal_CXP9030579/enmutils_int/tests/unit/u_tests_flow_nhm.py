#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.nhm_widget import NetworkOperationalState
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile


class NhmFlowProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = NhmFlowProfile()
        self.users = [Mock(), Mock(), Mock(), Mock(), Mock()]
        self.nodes = unit_test_utils.get_nodes(2)
        for node in self.nodes:
            node.poid = 999999999999
        self.nodes_widget = NetworkOperationalState(user=self.users[0], nodes=self.nodes)
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']
        self.flow.NUM_KPIS = 2
        self.flow.TOTAL_NODES = 2
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.NUM_OPERATORS = 5
        self.flow.SCHEDULE_SLEEP = 2
        self.flow.WIDGETS = ["NodesBreached", "WorstPerforming", "MostProblematic", "NetworkOperationalState",
                             "NetworkSyncStatus"]
        self.widgets = ["NodesBreached", "WorstPerforming", "MostProblematic", "NetworkOperationalState",
                        "NetworkSyncStatus"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmWidget.create')
    def test_create_widgets_taskset_is_successful(self, mock_widget_create, *_):
        self.flow.create_widgets_taskset(self.nodes_widget)
        self.assertTrue(mock_widget_create.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmWidget.number_created_configured_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.process_thread_queue_errors')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmWidget.create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.ThreadQueue')
    def test_create_and_configure_widgets_is_successful(self, mock_thread_queue, mock_create_widgets_taskset,
                                                        mock_process_tq_errors, mock_num_created_configured, mock_sleep,
                                                        mock_add_error, *_):
        mock_num_created_configured.side_effect = [0, 1]
        self.flow.create_and_configure_widgets(["NodesBreached"])
        mock_thread_queue.execute.assert_called()
        mock_thread_queue.assert_any_calls(self.widgets, func_ref=mock_create_widgets_taskset, num_workers=5)
        mock_process_tq_errors.assert_any_calls(last_error_only=True)
        self.assertEqual(mock_num_created_configured.call_count, 2)
        self.assertFalse(mock_add_error.called)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmWidget.number_created_configured_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.process_thread_queue_errors')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmWidget.create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.ThreadQueue')
    def test_create_and_configure_widgets_adds_error_after_max_attempts(self, mock_thread_queue,
                                                                        mock_create_widgets_taskset,
                                                                        mock_process_tq_errors,
                                                                        mock_num_created_configured, mock_sleep,
                                                                        mock_add_error, *_):
        mock_num_created_configured.side_effect = [0, 0, 0, 1]
        self.flow.create_and_configure_widgets(["NodesBreached"])
        mock_thread_queue.execute.assert_called()
        mock_thread_queue.assert_any_calls(self.widgets, func_ref=mock_create_widgets_taskset, num_workers=5)
        mock_process_tq_errors.assert_any_calls(last_error_only=True)
        self.assertEqual(mock_num_created_configured.call_count, 4)
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.wait_for_nhm_setup_profile')
    def test_setup_nhm_profile(self, mock_wait_for_setup_profile, mock_create_users, mock_allocated_nodes, *_):
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.wait_for_nhm_setup_profile')
    def test_setup_nhm_profile_uses_correct_num_nodes(self, mock_wait_for_setup_profile, mock_create_users,
                                                      mock_allocated_nodes, *_):
        self.flow.TOTAL_NODES = 1
        mock_allocated_nodes.return_value = self.nodes
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.get_allocated_nodes")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.wait_for_nhm_setup_profile')
    def test_setup_nhm_profile_success(self, mock_wait_for_setup, *_):
        self.flow.setup_nhm_profile()

        self.assertTrue(mock_wait_for_setup.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.create_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.wait_for_nhm_setup_profile')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.NhmFlowProfile.get_allocated_nodes")
    def test_setup_nhm_profile_total_nodes_less_than_verified(self, mock_get_allocated_nodes, mock_wait_for_setup, *_):
        mock_get_allocated_nodes.return_value = mock_get_allocated_nodes
        self.flow.setup_nhm_profile()

        self.assertTrue(mock_wait_for_setup.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
