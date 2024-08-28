#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow import NhmNbi06Flow
from enmutils_int.lib.workload.nhm_rest_nbi_06 import NHM_REST_NBI_06
from testslib import unit_test_utils


class NhmRestNbi06UnNitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock()]
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = NHM_REST_NBI_06()
        self.flow = NhmNbi06Flow()
        self.node_level_kpi = ['node_level_kpi_test']
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NHM_NBI_Administartor"]
        self.nodes = ['ERBS']
        self.allocated_nodes = [Mock()]
        self.fdn_values = ["test_Fdns"]
        self.nhm_rest_pre_defined_level = ['pre_defined_kpi_test']
        self.kpi_obj = [{'name': 'Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.execute_flow")
    def test_nhm_nbi_profile_nhm_nbi_06_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_06().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.sleep_until_day")
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.fdn_format')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.get_list_all_kpis')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.nhm_rest_pre_defined_kpi')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.kpi_execution_nhm_rest_pre_defined')
    def test_execute_flow__success(self, mock_kpi_execution, mock_node_level_kpi, mock_get_kpi_obj, mock_fdn_values,
                                   mock_keep_running, mock_create_user, *_):
        mock_create_user.return_value = self.user
        mock_keep_running.side_effect = [True, False]
        mock_fdn_values.return_value = self.fdn_values
        mock_get_kpi_obj.return_value = self.kpi_obj
        mock_node_level_kpi.return_value = self.node_level_kpi
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_execution.called)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.add_error_as_exception')
    def test_execute_flow__no_response(self, mock_add_error, mock_keep_running, mock_create_user, *_):
        mock_create_user.return_value = self.user
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow.NhmNbi06Flow.keep_running')
    def test_execute_flow__exception(self, mock_keep_running, mock_add_error, mock_create_user, *_):
        mock_create_user.return_value = self.user
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
