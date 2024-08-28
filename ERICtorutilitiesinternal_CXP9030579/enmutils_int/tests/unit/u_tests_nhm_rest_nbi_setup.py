#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow import NhmRestNbiSetup
from enmutils_int.lib.workload.nhm_rest_nbi_setup import NHM_REST_NBI_SETUP
from testslib import unit_test_utils


class NhmRestNbiSetupUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

        self.mock_node = Mock()
        self.mock_node.primary_type = 'RadioNode'
        self.counters = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                         'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax', 'pmPagS1EdrxReceived']
        self.flow = NhmRestNbiSetup()
        self.flow.supported_node_types = ["RadioNode"]
        self.flow.USER_ROLES = ["NHM_NBI_Administrator"]
        self.flow.REPORTING_OBJECT_01 = {'RadioNode': 'ENodeBFunction'}
        self.flow.NUM_NODES = {'RadioNode': 2}
        self.flow.UNSUPPORTED_KPIS = ['test_kpi_2']
        self.flow.NUM_KPIS_01 = 5
        self.flow.UNSUPPORTED_TYPES_NODE_LEVEL_KPI = ['RNC']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.execute_flow")
    def test_nhm_rest_nbi_setup_execute_flow__successful(self, mock_flow):
        NHM_REST_NBI_SETUP().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state',
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiKpi')
    def test_execute_flow_success_with_new_kpis_added(self, mock_nhm_kpi, mock_get_nodes,
                                                      mock_create_profile_users, *_):
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_kpi_object.create.activate)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state',
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiKpi')
    def test_execute_flow__success_with_removed_kpis(self, mock_nhm_kpi, mock_get_nodes, mock_create_profile_users, *_):
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_kpi_object.create.activate)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup'
        '.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state",
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    def test_execute_flow_failure_no_nodes_verified_on_enm(self, mock_get_nodes, mock_log, *_):
        mock_get_nodes.return_value = None
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state",
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    def test_execute_flow_failure_with__no_nodes(self, mock_get_nodes, mock_log, *_):
        mock_get_nodes.return_value = [self.mock_node]
        self.mock_node.primary_type = 'RNC'
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.get_nodes_list_by_attribute')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state",
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    def test_execute_flow_failure_primary_type_in_unsupported(self, mock_get_nodes, mock_log, *_):
        mock_get_nodes.return_value = [self.mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state",
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.create_profile_users')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    def test_execute_flow_failure_exception_while_cleaning_the_system(self, mock_get_nodes, mock_log, mock_kpi, *_):
        mock_get_nodes.return_value = None
        mock_kpi.remove_kpis_by_pattern.side_effect = Exception()
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.state",
           new_callable=PropertyMock())
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup.'
        'create_profile_users')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup'
        '.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.log')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup'
        '.create_and_activate_node_level_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.get_nhm_nodes')
    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow.NhmRestNbiSetup'
        '.add_error_as_exception')
    def test_execute_flow_raises_exception(self, mock_add_error, mock_get_nodes, mock_create_activate, *_):
        mock_get_nodes.return_value = [self.mock_node]
        mock_create_activate.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
