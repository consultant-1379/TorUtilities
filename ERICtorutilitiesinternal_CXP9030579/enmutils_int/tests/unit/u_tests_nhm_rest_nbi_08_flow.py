#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow import NhmRestNbi08Flow
from enmutils_int.lib.workload.nhm_rest_nbi_08 import NHM_REST_NBI_08
from testslib import unit_test_utils


class NhmRestnbi08FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = [Mock(username="TestUser")]
        self.profile = NHM_REST_NBI_08()
        self.flow = NhmRestNbi08Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NHM_NBI_Operator"]
        self.flow.SCHEDULED_TIMES = []
        self.nodes = unit_test_utils.setup_test_node_objects(5, primary_type="ESC")
        self.kpi_obj = [{'name': 'NHM REST NBI Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.execute_flow")
    def test_nhm_rest_nbi_profile_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_08().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.execute_flow")
    def test_nhm_rest_nbi_profile_nhm_nbi_08_execute_flow__successful(self, mock_execute_flow):
        self.profile.execute_flow()
        mock_execute_flow.assert_called()

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.random.sample', return_value=['kpi', 'kpi1'])
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.calculation_metrics')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep_until_time',
           return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep',
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.get_list_all_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.'
           'create_profile_users')
    def test_execute_flow_success(self, mock_user, mock_get_kpi_obj, *_):
        mock_user.return_value = self.user
        mock_get_kpi_obj.return_value = self.kpi_obj
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.random.sample',
           return_value=[])
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.calculation_metrics')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep_until_time',
           return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep',
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.add_error_as_exception')
    def test_execute_flow__error(self, mock_add_error, mock_user, *_):
        mock_user.return_value = self.user
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.random.sample',
           return_value=[])
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.calculation_metrics')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep_until_time',
           return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.sleep',
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.keep_running",
           side_effect=[True, False])
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.get_list_all_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.NhmRestNbi08Flow.'
           'create_profile_users')
    def test_execute_no_kpi(self, mock_user, mock_get_kpi_obj, *_):
        mock_user.return_value = self.user
        mock_get_kpi_obj.return_value = self.kpi_obj
        self.flow.execute_flow()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.log.logger.debug")
    def test_calculation_metrics__success(self, mock_logger_debug):
        response = Mock()
        user = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {u'lastRopTimeRangeStart': u'2023-10-11 06:30:00',
                                      u'recommendedKpiInstances': 300000,
                                      u'lastRopTimeRangeEnd': u'2023-10-11 06:45:00', u'kpiInstancesLastRop': 7049}
        user.get.return_value = response
        self.flow.calculation_metrics(user)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow.log.logger.debug")
    def test_calculation_metrics__failure(self, mock_logger_debug):
        response = Mock()
        user = Mock()
        response.ok = True
        response.status_code = 500
        user.get.return_value = response
        self.flow.calculation_metrics(user)
        self.assertTrue(mock_logger_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
