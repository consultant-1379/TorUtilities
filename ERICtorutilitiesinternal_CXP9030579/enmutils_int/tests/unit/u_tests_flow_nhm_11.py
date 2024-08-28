#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow import Nhm11


class Nhm11UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm11()
        self.user = ["A", "B"]
        self.nodes = [Mock(), Mock()]
        self.flow.NUMBER_OF_KPIS = 4
        self.flow.WIDGETS = ["NodesBreached", "MostProblematic", "NetworkOperationalState", "NetworkSyncStatus"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.random')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkSyncStatus')
    def test_create_widget_objects_nodes_breached(self, mock_network_sync_status, mock_network_op_state,
                                                  mock_nodes_breached, mock_most_problematic, mock_random):
        mock_random.choice.return_value = "NodesBreached"
        self.flow.create_widget_objects(self.user, Mock(), self.nodes)
        self.assertFalse(mock_network_sync_status.called)
        self.assertFalse(mock_network_op_state.called)
        self.assertTrue(mock_nodes_breached.called)
        self.assertFalse(mock_most_problematic.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.random')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkSyncStatus')
    def test_create_widget_objects_most_problematic(self, mock_network_sync_status, mock_network_op_state,
                                                    mock_nodes_breached, mock_most_problematic, mock_random):
        mock_random.choice.return_value = "MostProblematic"
        self.flow.create_widget_objects(self.user, Mock(), self.nodes)
        self.assertFalse(mock_network_sync_status.called)
        self.assertFalse(mock_network_op_state.called)
        self.assertFalse(mock_nodes_breached.called)
        self.assertTrue(mock_most_problematic.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.random')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkSyncStatus')
    def test_create_widget_objects_network_op_state(self, mock_network_sync_status, mock_network_op_state,
                                                    mock_nodes_breached, mock_most_problematic, mock_random):
        mock_random.choice.return_value = "NetworkOperationalState"
        self.flow.create_widget_objects(self.user, Mock(), self.nodes)
        self.assertFalse(mock_network_sync_status.called)
        self.assertTrue(mock_network_op_state.called)
        self.assertFalse(mock_nodes_breached.called)
        self.assertFalse(mock_most_problematic.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.random')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.MostProblematic')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.NetworkSyncStatus')
    def test_create_widget_objects_network_sync_status(self, mock_network_sync_status, mock_network_op_state,
                                                       mock_nodes_breached, mock_most_problematic, mock_random):
        mock_random.choice.return_value = "NetworkSyncStatus"
        self.flow.create_widget_objects(self.user, Mock(), self.nodes)
        self.assertTrue(mock_network_sync_status.called)
        self.assertFalse(mock_network_op_state.called)
        self.assertFalse(mock_nodes_breached.called)
        self.assertFalse(mock_most_problematic.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.setup_nhm_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.create_widget_objects")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.keep_running")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.ThreadQueue")
    def test_execute_flow(self, mock_thread_queue, mock_keep_running, mock_create_widget_objects,
                          mock_setup_nhm_profile, mock_sleep, *_):
        mock_setup_nhm_profile.return_value = self.user, self.nodes
        mock_create_widget_objects.return_value = [[Mock()], [Mock()], [Mock()]]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_setup_nhm_profile.call_count, 1)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_thread_queue.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.create_widget_objects")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.setup_nhm_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.keep_running")
    def test_flow_continues_no_widgets_created(self, mock_keep_running, mock_setup_nhm_profile, mock_thread_queue,
                                               mock_create_widget_objects, mock_sleep):
        mock_create_widget_objects.return_value = []
        mock_setup_nhm_profile.return_value = self.user, self.nodes
        mock_keep_running.side_effect = [True, False]

        self.flow.execute_flow()

        self.assertEqual(mock_setup_nhm_profile.call_count, 1)
        self.assertTrue(mock_thread_queue.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_keep_running.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
