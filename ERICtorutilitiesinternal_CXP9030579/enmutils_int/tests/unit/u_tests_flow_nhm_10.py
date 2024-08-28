#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow import Nhm10


class Nhm10UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm10()
        self.user = ["A", "B"]
        self.nodes = [Mock(), Mock()]
        self.nodes[0].poid = "281474977292253"
        self.nodes[1].poid = "181474977292251"
        self.flow.TOTAL_NODES = 2
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']
        self.flow.NUM_ADMINS = 1
        self.flow.NUM_OPERATORS = 1
        self.flow.USER_ROLES = ["NHM_Administrator"]
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.SCHEDULE_SLEEP = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.NetworkSyncStatus')
    def test_create_widget_objects(self, mock_network_op_state, mock_network_sync_status, *_):
        self.flow.create_widget_objects(self.user, self.nodes)
        self.assertTrue(mock_network_op_state.called)
        self.assertTrue(mock_network_sync_status.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.create_widget_objects")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.ThreadQueue")
    def test_execute_flow_success(self, mock_thread_queue, mock_create_widget_objects, mock_logger, mock_sleep, *_):
        self.flow.TOTAL_NODES = 1
        mock_create_widget_objects.return_value = ['A', 'B']
        with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.setup_nhm_profile") as \
                mock_setup_nhm_profile:
            with patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.keep_running") as mock_keep_running:
                mock_setup_nhm_profile.return_value = self.user, self.nodes
                mock_keep_running.side_effect = [True, False]

                self.flow.execute_flow()

                self.assertEqual(mock_setup_nhm_profile.call_count, 1)
                self.assertTrue(mock_thread_queue.called)
                self.assertTrue(mock_keep_running.called)
                self.assertTrue(mock_sleep.called)
                self.assertTrue(mock_logger.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.create_widget_objects")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.setup_nhm_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.keep_running")
    def test_flow_continues_no_widgets_created(self, mock_keep_running, mock_setup_nhm_profile, mock_thread_queue,
                                               mock_create_widget_objects, mock_sleep, *_):
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
