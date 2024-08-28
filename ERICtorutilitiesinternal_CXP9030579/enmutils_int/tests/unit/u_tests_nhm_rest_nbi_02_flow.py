import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow import NhmNbi02Flow
from enmutils_int.lib.workload.nhm_rest_nbi_02 import NHM_REST_NBI_02
from testslib import unit_test_utils


class NhmRestNbi02UnNitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock()]
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = NHM_REST_NBI_02()
        self.flow = NhmNbi02Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NHM_NBI_perator"]
        self.nodes = ['ERBS']
        self.fdn_values = ["test_Fdns"]
        self.node_level_kpi = ['node_level_kpi_test']
        self.kpi_obj = [{'name': 'NHM REST NBI Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.execute_flow")
    def test_nhm_nbi_profile_nhm_nbi_02_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_02().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.sleep_until_time')
    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.fdn_format')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.get_list_all_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.nhm_rest_nbi_node_level_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.kpi_execution_nhm_rest_nbi')
    def test_execute_flow__success(self, mock_kpi_execution, mock_node_level_kpi, mock_get_kpi_obj, mock_fdn_values,
                                   mock_keep_running, mock_setup_nhm, *_):
        mock_setup_nhm.return_value = self.user, self.nodes
        mock_keep_running.side_effect = [True, False]
        mock_fdn_values.return_value = self.fdn_values
        mock_get_kpi_obj.return_value = self.kpi_obj
        mock_node_level_kpi.return_value = self.node_level_kpi
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_execution.called)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.add_error_as_exception')
    def test_execute_flow__no_response(self, mock_add_error, mock_sleep_until_time, mock_keep_running, mock_setup_nhm,
                                       *_):
        mock_setup_nhm.return_value = self.user, self.nodes
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep_until_time.call_count, 1)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.setup_nhm_profile')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow.NhmNbi02Flow.keep_running')
    def test_execute_flow__exception(self, mock_keep_running, mock_setup_nhm, mock_add_error,
                                     mock_sleep_until_time, *_):
        mock_setup_nhm.return_value = Mock(stdout="error"), [Mock(username="test")]
        response = Mock(stdout="error")
        response.ok = False
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep_until_time.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
