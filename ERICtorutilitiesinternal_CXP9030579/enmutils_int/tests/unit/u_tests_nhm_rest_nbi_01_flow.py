#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow import NhmNbi01Flow
from enmutils_int.lib.workload.nhm_rest_nbi_01 import NHM_REST_NBI_01
from testslib import unit_test_utils


class NhmRestNbi01UnNitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock()]
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = NHM_REST_NBI_01()
        self.flow = NhmNbi01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NHM_NBI_perator"]
        self.nodes = ['ERBS']
        self.fdn_values = ["test_Fdns"]
        self.node_level_kpi = ['Test_kpi']
        self.kpi_obj = [{'name': 'Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.execute_flow")
    def test_nhm_nbi_01_profile_nhm_nbi_01_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.fdn_format')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.get_list_all_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.nhm_rest_nbi_node_level_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.kpi_execution_nhm_rest_nbi')
    def test_execute_flow_01__success(self, mock_kpi_execution, mock_node_level_kpi, mock_get_kpi_obj, mock_fdn_values,
                                      mock_keep_running, mock_setup_nhm, *_):
        mock_setup_nhm.return_value = self.user, self.nodes
        mock_keep_running.side_effect = [True, False]
        mock_fdn_values.return_value = self.fdn_values
        mock_get_kpi_obj.return_value = self.kpi_obj
        mock_node_level_kpi.return_value = self.node_level_kpi
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_execution.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.add_error_as_exception')
    def test_execute_flow_01__no_response(self, mock_add_error, mock_sleep_until_time, mock_keep_running,
                                          mock_setup_nhm, *_):
        mock_setup_nhm.return_value = self.user, self.nodes
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep_until_time.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow.NhmNbi01Flow.keep_running')
    def test_execute_flow_01__exception(self, mock_keep_running, mock_setup_nhm, mock_add_error,
                                        mock_sleep_until_time, *_):
        mock_setup_nhm.return_value = Mock(stdout="error"), [Mock(username="test")]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep_until_time.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
