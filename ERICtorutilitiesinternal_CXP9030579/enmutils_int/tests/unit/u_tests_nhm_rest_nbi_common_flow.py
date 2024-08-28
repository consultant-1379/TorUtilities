#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow


class NhmRestNbiCommonFlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock()]
        self.NUM_KPIS_01 = 10
        self.nodes = unit_test_utils.get_nodes(2)
        self.flow = NhmRestNbiFlow()
        self.flow.NUM_OPERATORS = 1
        self.flow.OPERATOR_ROLE = ["Test_Operator"]
        self.flow.TOTAL_NODES = 1
        self.flow.NAME = 'NHM_REST_NBI_03'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_fdn_format__success(self, mock_logger_debug):
        node = Mock()
        setattr(node, 'node_id', 'test')
        self.flow.fdn_format([node])
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.random.sample',
           return_value=['kpi1'])
    def test_nhm_node_level_kpi__success(self, *_):
        all_kpis = [{'id': '111', 'name': 'NHM SETUP 0', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '1', 'name': 'NHM SETUP 1', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '2', 'name': 'NHM SETUP 2', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '3', 'name': 'NHM SETUP 3', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '4', 'name': 'NHM SETUP 4', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '5', 'name': 'NHM SETUP 5', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '6', 'name': 'NHM SETUP 6', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '7', 'name': 'NHM SETUP 7', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '88', 'name': 'NHM SETUP 8', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '18', 'name': 'NHM SETUP 9', 'active': True, 'reportingObject': ['ENodeBFunction']},
                    {'id': '114', 'name': 'NHM SETUP 10', 'active': True, 'reportingObject': ['ENodeBFunction']}]
        self.flow.nhm_node_level_kpi(all_kpis)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.random.sample',
           return_value=['kpi1'])
    def test_nhm_node_level_kpi_less_than_ten(self, *_):
        all_kpis = [{'id': '111', 'name': 'NHM SETUP 0', 'active': True, 'reportingObject': ['ENodeBFunction']}]
        self.assertRaises(EnmApplicationError, self.flow.nhm_node_level_kpi, all_kpis)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_kpi_execution__success_with_response(self, mock_logger_debug):
        operator_users = Mock()
        response = Mock()
        response.ok = True
        operator_users.post.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12, 'reportingObject': ['ENodeBFunction']}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi-values/v1/history/{id}"
        self.flow.kpi_execution(operator_users, node_level_kpi, fdn_values, kpi_value)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.'
           'add_error_as_exception')
    def test_kpi_execution__with_no_response(self, mock_add_error):
        operator_users = Mock()
        response = Mock()
        response.ok = False
        operator_users.post.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12, 'reportingObject': ['ENodeBFunction']}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi-values/v1/history/{id}"
        self.assertRaises(EnvironError, self.flow.kpi_execution, operator_users, node_level_kpi, fdn_values,
                          kpi_value)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow'
           '.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.create_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.wait_for_nhm_setup_profile")
    def test_setup_nhm_profile__success(self, mock_wait_for_setup_profile, mock_create_users, mock_allocated_nodes, *_):
        self.flow.NAME = 'NHM_REST_NBI_01'
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow'
           '.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.create_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.wait_for_nhm_setup_profile")
    def test_setup_nhm_profile__uses_setup_profile(self, mock_wait_for_setup_profile, mock_create_users,
                                                   mock_allocated_nodes, *_):
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow'
           '.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.create_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.wait_for_nhm_setup_profile")
    def test_setup_nhm_profile__uses_correct_num_nodes(self, mock_wait_for_setup_profile, mock_create_users,
                                                       mock_allocated_nodes, *_):
        self.flow.TOTAL_NODES = 1
        mock_allocated_nodes.return_value = self.nodes
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup_profile.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow'
           '.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.create_users')
    @patch("enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.wait_for_nhm_setup_profile")
    def test_setup_nhm_profile__total_nodes_less_than_verified(self, mock_get_allocated_nodes, mock_wait_for_setup, *_):
        mock_get_allocated_nodes.return_value = mock_get_allocated_nodes
        self.flow.setup_nhm_profile()
        self.assertTrue(mock_wait_for_setup.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_kpi_execution_nhm_rest_nbi__success_with_response(self, mock_logger_debug):
        operator_users = Mock()
        response = Mock()
        response.ok = True
        operator_users.post.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi-values/v1/history/{id}"
        self.flow.kpi_execution_nhm_rest_nbi(operator_users, node_level_kpi, fdn_values, kpi_value)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_kpi_execution_nhm_rest_nbi__success_with_no_response(self, mock_logger_debug):
        operator_users = Mock()
        response = Mock()
        response.ok = False
        operator_users.post.return_value = response
        node_level_kpi = [{'name': 'node_level_kpi_test', 'id': 12}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi-values/v1/history/{id}"
        self.assertRaises(EnvironError, self.flow.kpi_execution_nhm_rest_nbi, operator_users, node_level_kpi,
                          fdn_values, kpi_value)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_kpi_execution_nhm_rest_pre_defined__success_with_response(self, mock_logger_debug):
        user = Mock()
        response = Mock()
        response.ok = True
        user.put.return_value = response
        pre_defined_kpis = [{'name': 'node_level_kpi_test', 'id': 12}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi/v1/kpis/{id}"
        self.flow.kpi_execution_nhm_rest_pre_defined(user, fdn_values, pre_defined_kpis, kpi_value)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.'
           'add_error_as_exception')
    def test_kpi_execution_nhm_rest_nbi__with_no_response(self, mock_add_error):
        user = Mock()
        response = Mock()
        response.ok = False
        user.put.return_value = response
        pre_defined_kpis = [{'name': 'node_level_kpi_test', 'id': 12}]
        fdn_values = {"neNames": ["LTE40dg2ERBS00002", "LTE40dg2ERBS00001"]}
        kpi_value = "enm/kpi/v1/kpis/{id}"
        self.assertRaises(EnvironError, self.flow.kpi_execution_nhm_rest_pre_defined, user, fdn_values,
                          pre_defined_kpis,
                          kpi_value)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_nhm_rest_nbi_node_level_kpi(self, mock_logger_debug):
        self.flow.nhm_rest_nbi_node_level_kpi(
            [{u'name': 'NHM_SETUP_test', u'id': 'test'}, {u'name': 'test', u'id': 'test'}])
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.log.logger.debug')
    def test_nhm_rest_pre_defined_kpi(self, mock_logger_debug):
        self.flow.nhm_rest_pre_defined_kpi(
            [{u'createdBy': 'Ericsson', u'neTypes': 'RadioNode', u'active': False}, {u'createdBy': 'test', u'neTypes': 'test', u'active': True}])
        self.assertTrue(mock_logger_debug.called)

    def test_get_list_all_kpis__success_with_response(self):
        user = Mock()
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {'items': [{'name': 'NHM REST NBI Govinda_testing', 'id': 'test_id'}]}
        user.get.return_value = response
        self.flow.get_list_all_kpis(user)

    @patch(
        'enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow.NhmRestNbiFlow.add_error_as_exception')
    def test_get_list_all_kpis__success_with_no_response(self, mock_add_error):
        user = Mock()
        response = Mock()
        response.ok = False
        response.json.return_value = {'items': [{'name': 'NHM REST NBI Govinda_testing', 'id': 'test_id'}]}
        user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.get_list_all_kpis, user)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
