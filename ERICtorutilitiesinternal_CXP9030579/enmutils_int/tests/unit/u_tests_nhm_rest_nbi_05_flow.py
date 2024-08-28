#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import patch, Mock, PropertyMock
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.workload.nhm_rest_nbi_05 import NHM_REST_NBI_05
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow import NhmNbi05Flow


class NhmRestNbi05UnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

        self.mock_node = Mock()
        self.mock_node.primary_type = 'RadioNode'
        self.counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                         'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
        self.flow = NhmNbi05Flow()
        self.flow.supported_node_types = ["RadioNode"]
        self.flow.USER_ROLES = ["NHM_NBI_Administrator"]
        self.flow.REPORTING_OBJECT_01 = {'RadioNode': 'ENodeBFunction'}
        self.flow.NUM_NODES = {'RadioNode': 2}
        self.flow.UNSUPPORTED_KPIS = ['test_kpi_2']
        self.flow.NUM_KPIS_01 = 2
        self.flow.NUM_USERS = 5
        self.flow.UNSUPPORTED_TYPES_NODE_LEVEL_KPI = ['RNC']
        self.flow.SCHEDULED_DAYS = "TUESDAY"
        self.flow.SCHEDULED_TIMES_STRINGS = ["10:00:00"]
        self.kpi_obj = [{'name': 'NHM REST NBI 05 Govinda_testing', 'id': 'test_id'}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.execute_flow")
    def test_nhm_rest_nbi_05_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_05().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow._clean_system_nhm_rest_nbi')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.read_nhm_rest_nbi_05_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state',
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmRestNbiKpi')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_success_with_new_kpis_added(self, mock_keep_running, mock_nhm_kpi, mock_get_nodes,
                                                      mock_create_profile_users, mock_read_kpi, mock_clean, *_):
        mock_keep_running.side_effect = [True, False]
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_read_kpi.called)
        self.assertFalse(mock_clean.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state',
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmRestNbiKpi')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow__success_with_removed_kpis(self, mock_keep_running, mock_nhm_kpi, mock_get_nodes, mock_create_profile_users, mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_sleep.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow'
        '.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state",
           new_callable=PropertyMock())
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_failure_no_nodes_verified_on_enm(self, mock_keep_running, mock_get_nodes, mock_log, mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.return_value = None
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_sleep.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state",
           new_callable=PropertyMock())
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_failure_with__no_nodes(self, mock_keep_running, mock_get_nodes, mock_log, mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.return_value = [self.mock_node]
        self.mock_node.primary_type = 'RNC'
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_sleep.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state",
           new_callable=PropertyMock())
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_failure_primary_type_in_unsupported(self, mock_keep_running, mock_get_nodes, mock_log, mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state",
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.create_profile_users')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmRestNbiKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_failure_exception_while_cleaning_the_system(self, mock_keep_running, mock_get_nodes,
                                                                      mock_log, mock_kpi, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.return_value = None
        mock_kpi.remove_kpis_nhm_rest_nbi_05_by_pattern.side_effect = Exception()
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.state",
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.'
        'create_profile_users')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow'
        '.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmRestNbiKpi')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow'
        '.create_node_level_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.get_nhm_nodes')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow'
        '.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.keep_running")
    def test_execute_flow_raises_exception(self, mock_keep_running, mock_add_error, mock_get_nodes, mock_create_kpi, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_nodes.return_value = [self.mock_node]
        mock_create_kpi.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.log.logger.debug')
    def test_kpi_execution_nhm_rest_nbi_read_success_with_response(self, mock_logger_debug):
        user = Mock()
        response = Mock()
        response.ok = True
        user.get.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12}]
        self.flow.read_set_of_ten_kpi(user, node_level_kpi)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow.NhmNbi05Flow.'
           'add_error_as_exception')
    def test_kpi_execution_nhm_rest_nbi_read_with_no_response(self, mock_add_error):
        user = Mock()
        response = Mock()
        response.ok = False
        user.get.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12}]
        self.assertRaises(EnvironError, self.flow.read_set_of_ten_kpi, user, node_level_kpi)
        self.assertFalse(mock_add_error.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.get_list_all_kpis')
    def test_read_nhm_rest_nbi_05_kpi__is_successful(self, mock_get_kpi_obj):
        user = Mock()
        mock_get_kpi_obj.return_value = self.kpi_obj
        self.flow.read_nhm_rest_nbi_05_kpi(5 * [user])

if __name__ == "__main__":
    unittest2.main(verbosity=2)
