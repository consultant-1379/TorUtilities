#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow import NhmRestNbi07Flow
from enmutils_int.lib.workload.nhm_rest_nbi_07 import NHM_REST_NBI_07
from testslib import unit_test_utils


class NhmRestnbi07FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="TestUser")
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = NHM_REST_NBI_07()
        self.flow = NhmRestNbi07Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NHM_NBI_Operator"]
        self.flow.SCHEDULED_TIMES = []
        self.nodes = unit_test_utils.setup_test_node_objects(5, primary_type="ESC")
        self.kpi_obj = [{'name': 'Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.execute_flow")
    def test_nhm_rest_nbi_profile_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_07().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.execute_flow")
    def test_nhm_rest_nbi_profile_nhm_nbi_07_execute_flow__successful(self, mock_execute_flow):
        self.profile.execute_flow()
        mock_execute_flow.assert_called()

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.sleep',
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.get_list_all_kpis')
    def test_execute_flow_success(self, mock_list_all_kpis, mock_setup_nhm, mock_keep_running, *_):
        mock_setup_nhm.return_value = ["NHM_NBI_Operator"]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_list_all_kpis.called)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow.NhmRestNbi07Flow.create_profile_users')
    def test_execute_flow__exception(self, mock_setup_nhm, mock_keep_running, mock_add_error,
                                     mock_sleep_until_time, *_):
        mock_setup_nhm.return_value = ["NHM_NBI_Operator"]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep_until_time.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
