#!/usr/bin/env python
import json

import unittest2
from enmscripting.exceptions import TimeoutException
from mock import patch, Mock
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nhm import (CREATED_BY_DEFAULT, KPI_BODY, sleep_until_profile_persisted,
                                  wait_for_nhm_setup_profile, get_nhm_nodes, get_kpi,
                                  check_is_kpi_usable_and_assign_to_node_type, NhmKpi,
                                  get_counters_if_enodeb, transport_counters, ROUTER_COUNTERS)
from enmutils_int.lib.profile_flows.nhm_flows.nhm_09_flow import Nhm09
from testslib import unit_test_utils

URL = 'http://localhost/'
KPI_INFO = {u'name': u'Average_UE_PDCP_DL_Throughput', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'operands': [{u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'operands': [{u'operator': u'SUBTRACTION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'operands': None, u'value': 1000.0}]}]}], }]}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'Description'}
KPI_INFO_TEST = {u'name': u'unit_test_kpi', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'operands': [{u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'operands': [{u'operator': u'SUBTRACTION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'operands': None, u'value': 1000.0}]}]}], }]}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'Description'}


class NhmKpiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.NODE_IP_1 = unit_test_utils.generate_configurable_ip()
        self.NODE_IP_2 = unit_test_utils.generate_configurable_ip()
        self.nodes = [
            Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00001', node_ip=self.NODE_IP_1, mim_version='F.1.101',
                 model_identity='5783-904-386', primary_type='ERBS'),
            Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00002', node_ip=self.NODE_IP_2, mim_version='F.1.101',
                 model_identity='5783-904-386', primary_type='ERBS')
        ]
        self.profile = Nhm09()
        self.kpi = NhmKpi(user=self.user, name="unit_test_kpi", nodes=self.nodes, reporting_objects=["EUtranCellFDD"],
                          created_by=self.user.username, active="false")

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_kpi_info_success(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        NhmKpi.get_kpi_info(self.user)
        self.assertTrue(self.user.get.called)

    def test_get_kpi_info_raises_http_error(self):
        response = Mock()
        response.status_code = 305
        self.user.get.return_value = response
        NhmKpi.get_kpi_info(self.user)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.annotate_fdn_poid_return_node_objects')
    def test_get_nhm_nodes_success(self, mock_return_node_objects, *_):
        nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        mock_return_node_objects.return_value = nodes
        get_nhm_nodes(self.profile, self.user, nodes)

        self.assertTrue(mock_return_node_objects.called)
        self.assertEqual(mock_return_node_objects.return_value, nodes)

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.annotate_fdn_poid_return_node_objects')
    def test_get_nhm_nodes_error_no_nodes(self, mock_return_node_objects, mock_log_logger_debug, *_):
        nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        mock_return_node_objects.side_effect = [[], nodes]
        get_nhm_nodes(self.profile, self.user, nodes)

        self.assertEqual(mock_return_node_objects.call_count, 2)
        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_09_flow.Nhm09.add_error_as_exception')
    @patch('enmutils_int.lib.nhm.annotate_fdn_poid_return_node_objects')
    def test_get_nhm_nodes_http_error(self, mock_return_node_objects, mock_add_error_as_exception, mock_time_sleep, *_):
        profile = Nhm09()
        nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        mock_return_node_objects.side_effect = [HTTPError, nodes]

        get_nhm_nodes(profile, self.user, nodes)

        self.assertEqual(mock_return_node_objects.call_count, 2)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_09_flow.Nhm09.add_error_as_exception')
    @patch('enmutils_int.lib.nhm.annotate_fdn_poid_return_node_objects')
    def test_get_nhm_nodes_timeout_error(self, mock_return_node_objects, mock_add_error_as_exception, mock_time_sleep):
        profile = Nhm09()
        nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        mock_return_node_objects.side_effect = [TimeoutException, nodes]
        get_nhm_nodes(profile, self.user, nodes)
        self.assertEqual(mock_return_node_objects.call_count, 2)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch("enmutils_int.lib.nhm.time.sleep")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    @patch('enmutils_int.lib.nhm.NhmKpi.get_kpis_created_by')
    def test_clean_down_system_kpis_success(self, mock_get_kpis_created_by, mock_deactivate,
                                            mock_time_sleep, mock_update, mock_logger_debug,):
        response = Mock()
        response.status_code = 200
        response.json.return_value = ['Total_UL_PDCP_Cell_Throughput', 'Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation',
                                      'E-RAB_Retainability_Session_Time_Normalized_Loss_Rate', 'Total_DL_PDCP_Cell_Throughput']
        self.user.post.return_value = response
        mock_get_kpis_created_by.return_value = CREATED_BY_DEFAULT
        mock_deactivate.return_value = response
        mock_time_sleep.return_value = response
        mock_update.return_value = response
        NhmKpi.clean_down_system_kpis(self.user)
        self.assertEqual(4, mock_get_kpis_created_by.call_count)
        self.assertEqual(4, mock_deactivate.call_count)
        self.assertTrue(mock_time_sleep.called)
        self.assertTrue(mock_logger_debug.called)
        self.assertTrue(self.user.post.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch("enmutils_int.lib.nhm.time.sleep")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    @patch('enmutils_int.lib.nhm.NhmKpi.get_kpis_created_by')
    def test_clean_down_system_kpis_no_default_kpi(self, mock_get_kpis_created_by, mock_deactivate, mock_time_sleep,
                                                   mock_update, mock_logger_debug):
        response = Mock()
        response.status_code = 200
        response.json.return_value = ['Total_UL_PDCP_Cell_Throughput', 'Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation',
                                      'E-RAB_Retainability_Session_Time_Normalized_Loss_Rate', 'Total_DL_PDCP_Cell_Throughput']
        self.user.post.return_value = response
        mock_get_kpis_created_by.return_value = self.user.username
        NhmKpi.clean_down_system_kpis(self.user)
        self.assertEqual(4, mock_get_kpis_created_by.call_count)
        self.assertFalse(mock_deactivate.called)
        self.assertFalse(mock_time_sleep.called)
        self.assertFalse(mock_update.called)
        self.assertEqual(4, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch("enmutils_int.lib.nhm.time.sleep")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    @patch('enmutils_int.lib.nhm.NhmKpi.get_kpis_created_by')
    def test_clean_down_system_kpis_deactivate_error(self, mock_get_kpis_created_by, mock_deactivate, mock_time_sleep,
                                                     mock_update):
        response = Mock()
        response.status_code = 200
        response.json.return_value = ['Total_UL_PDCP_Cell_Throughput',
                                      'Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation',
                                      'E-RAB_Retainability_Session_Time_Normalized_Loss_Rate',
                                      'Total_DL_PDCP_Cell_Throughput']
        self.user.post.return_value = response
        mock_get_kpis_created_by.return_value = CREATED_BY_DEFAULT
        mock_deactivate.side_effect = Exception
        NhmKpi.clean_down_system_kpis(self.user)
        self.assertEqual(4, mock_get_kpis_created_by.call_count)
        self.assertTrue(mock_time_sleep.called)
        self.assertEqual(4, mock_deactivate.call_count)
        self.assertEqual(4, mock_update.call_count)

    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch("enmutils_int.lib.nhm.time.sleep")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    @patch('enmutils_int.lib.nhm.NhmKpi.get_kpis_created_by')
    def test_clean_down_system_kpis_update_error(self, mock_get_kpis_created_by, mock_deactivate, mock_time_sleep,
                                                 mock_update):
        response = Mock()
        response.status_code = 205
        response.json.return_value = ['Total_UL_PDCP_Cell_Throughput',
                                      'Average_UL_PDCP_UE_Throughput_For_Carrier_Aggregation',
                                      'E-RAB_Retainability_Session_Time_Normalized_Loss_Rate',
                                      'Total_DL_PDCP_Cell_Throughput']
        self.user.post.return_value = response
        mock_get_kpis_created_by.return_value = CREATED_BY_DEFAULT
        mock_update.side_effect = Exception
        NhmKpi.clean_down_system_kpis(self.user)
        self.assertEqual(4, mock_get_kpis_created_by.call_count)
        self.assertTrue(mock_time_sleep.called)
        self.assertEqual(4, mock_deactivate.call_count)
        self.assertEqual(4, mock_update.call_count)

    def test_get_kpi_body_success(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        self.kpi._get_kpi_body()
        self.assertTrue(self.user.get.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_kpi_body_raises_http_error(self, mock_raise_for_status):
        response = Mock()
        response.status_code = 404
        self.user.get.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.kpi._get_kpi_body()
        self.assertTrue(mock_raise_for_status.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_exclude_success(self, _):
        response = Mock()
        self.user.post.return_value = response
        returned = [[["A", "B"]]]
        response.json.return_value = [[["A", "B"], [["C", "D"]]]]
        self.kpi.get_all_kpi_names_active(self.user, exclude='NHM_03')
        self.assertTrue(self.user.post.called)
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user, exclude='NHM_03'), returned)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_if_condition_success(self, *_):
        response = Mock()
        response.json.return_value = [[["A", "B"], [["C", "D"]]]]
        self.user.post.return_value = response
        returned = [[['A', 'B']]]
        self.kpi.get_all_kpi_names_active(self.user, exclude='NHM_03')
        self.assertTrue(self.user.post.called)
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user, exclude='NHM_03'), returned)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_else_condition_success(self, mock_raise_for_status):
        response = Mock()
        response.json.return_value = [[["A", "B"], ["C", "D"]]]
        returned = [[['A', 'B']]]
        self.user.post.return_value = response
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user), returned)
        self.assertTrue(mock_raise_for_status.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_if_kpi1_is_null(self, mock_raise_for_status):
        response = Mock()
        response.json.return_value = [[["A", "B"], []]]
        returned = []
        self.user.post.return_value = response
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user), returned)
        self.assertTrue(mock_raise_for_status.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_if_exclude_in_kpi(self, *_):
        response = Mock()
        response.json.return_value = [[u'NHM_03 Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        self.user.post.return_value = response
        returned = []
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user, exclude='NHM_03'), returned)
        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_all_kpi_names_active_if_exclude_not_in_kpi(self, *_):
        response = Mock()
        response.json.return_value = [[['A', 'B'], ['C', 'D']]]
        self.user.post.return_value = response
        returned = [[['A', 'B']]]
        self.assertEqual(self.kpi.get_all_kpi_names_active(self.user, exclude="['E', 'F']"), returned)
        self.assertTrue(self.user.post.called)

    def test_get_all_kpi_names_active_raises_environ_error(self):
        response = Mock()
        response.json.return_value = []
        self.mock_user.post.return_value = response
        self.assertRaises(EnvironError, self.kpi.get_all_kpi_names_active, self.mock_user)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._get_kpi")
    def test_get_kpi_by_name_success(self, mock_get_kpi, mock_log_logger_debug):
        mock_get_kpi.return_value = KPI_BODY

        self.kpi.get_kpi_by_name(self.user, "kpi name")

        self.assertTrue(self.kpi.get_kpi_by_name(self.user, "kpi name") == KPI_BODY)
        self.assertTrue(mock_log_logger_debug.called)

    def test_get_all_kpi_names_success(self):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        NhmKpi.get_all_kpi_names(self.user)
        self.assertTrue(self.user.post.called)

    def test_get_all_kpi_names_exclude_success(self):
        response = Mock()
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        returned = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI']]
        self.user.post.return_value = response
        self.assertEqual(self.kpi.get_all_kpi_names(self.user, exclude='NHM_03'), returned)
        self.assertTrue(self.user.post.called)

    def test_get_all_kpi_names_if_exclude_not_in_kpi(self):
        response = Mock()
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        returned = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        self.user.post.return_value = response
        self.assertEqual(self.kpi.get_all_kpi_names(self.user, exclude='FM'), returned)
        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    def test_get_kpis_created_by_success(self, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        returned = u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'
        self.user.post.return_value = response
        self.assertEqual(self.kpi.get_kpis_created_by(self.user), returned)
        self.assertTrue(self.user.post.called)

    def test_get_kpis_created_by_response_failed(self):
        response = Mock()
        response.status_code = 300
        self.user.post.return_value = response
        NhmKpi.get_kpis_created_by(self.user)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.nhm.raise_for_status")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    def test_get_kpis_created_by__empty_response(self, mock_log, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = []
        self.user.post.return_value = response
        NhmKpi.get_kpis_created_by(self.user)
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.nhm.NhmKpi._create_kpi_equation")
    def test_create_node_level_body_success(self, mock_kpi_equation):
        self.kpi.name = "NHM_01_1017-16230557_KPI_3"
        self.kpi.counters = ['pmPagS1Received', 'pmRrcConnBrEnbMax', 'pmRimReportErr', 'pmMoFootprintMax']
        self.kpi.threshold_domain = "GREATER_THAN"
        self.kpi.threshold_value = 219
        self.kpi.node_types = ['ERBS', 'RadioNode']
        mock_kpi_equation.return_value = {"operator": "MULTIPLICATION",
                                          "operands": [{"operator": "MULTIPLICATION",
                                                        "operands": [{"counterRef": "pmPagS1Received"},
                                                                     {"counterRef": "pmRrcConnBrEnbMax"},
                                                                     {"counterRef": "pmRimReportErr"},
                                                                     {"counterRef": "pmMoFootprintMax"}]}]}
        self.assertEqual(self.kpi._create_node_level_body(), KPI_BODY)

    @patch("enmutils_int.lib.nhm.NhmKpi._create_kpi_equation")
    def test_create_cell_level_body_success(self, mock_kpi_equation):
        self.kpi.name = "NHM_01_1017-16230557_KPI_3"
        self.kpi.counters = ['pmPagS1Received', 'pmRrcConnBrEnbMax', 'pmRimReportErr', 'pmMoFootprintMax']
        self.kpi.threshold_domain = "GREATER_THAN"
        self.kpi.threshold_value = 219
        self.kpi.node_types = ['ERBS', 'RadioNode', 'MSRBS_V1', 'RNC']
        mock_kpi_equation.return_value = {"operator": "MULTIPLICATION",
                                          "operands": [{"operator": "MULTIPLICATION",
                                                        "operands": [{"counterRef": "pmPagS1Received"},
                                                                     {"counterRef": "pmRrcConnBrEnbMax"},
                                                                     {"counterRef": "pmRimReportErr"},
                                                                     {"counterRef": "pmMoFootprintMax"}]}]}
        self.assertEqual(self.kpi._create_cell_level_body(), KPI_BODY)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_kpi_equation")
    def test_create_cell_level_body_wrong_node_type_success(self, mock_kpi_equation, mock_log_logger_debug):
        self.kpi.name = "NHM_01_1017-16230557_KPI_3"
        self.kpi.counters = ['pmPagS1Received', 'pmRrcConnBrEnbMax', 'pmRimReportErr', 'pmMoFootprintMax']
        self.kpi.threshold_domain = "GREATER_THAN"
        self.kpi.threshold_value = 219
        self.kpi.node_types = ['wrong_node_typeERBS', 'RadioNode', 'MSRBS_V1']
        mock_kpi_equation.return_value = {"operator": "MULTIPLICATION",
                                          "operands": [{"operator": "MULTIPLICATION",
                                                        "operands": [{"counterRef": "pmPagS1Received"},
                                                                     {"counterRef": "pmRrcConnBrEnbMax"},
                                                                     {"counterRef": "pmRimReportErr"},
                                                                     {"counterRef": "pmMoFootprintMax"}]}]}
        self.assertEqual(self.kpi._create_cell_level_body(), KPI_BODY)
        self.assertTrue(mock_log_logger_debug.called)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._get_kpi_body")
    def test_kpi_create_success_created_by_success(self, mock_get_kpi_body, mock_logger_debug, mock_user_post):
        response = Mock()
        mock_user_post.return_value = response
        response.status_code = 200
        self.kpi.created_by = 'Ericsson'
        self.kpi.node_poids = ['11']
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.create()
        self.assertTrue(mock_get_kpi_body.called)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_cell_level_body")
    def test_kpi_create_success_created_by_not_success(self, mock_create_cell_level_body, mock_logger_debug, mock_user_post):
        response = Mock()
        mock_user_post.return_value = response
        response.status_code = 200
        self.kpi.created_by = 'jira'
        self.kpi.node_poids = ['11']
        mock_create_cell_level_body.return_value = KPI_BODY
        self.kpi.create()
        self.assertTrue(mock_create_cell_level_body.called)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.nhm.json.dumps")
    @patch("enmutils_int.lib.nhm.NhmKpi._create_cell_level_body")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    def test_kpi_create_success_node_no_poids_success(self, mock_log_logger_debug, mock_create_cell_level_body, *_):
        response = Mock()
        response.status_code = 201
        self.user.post.return_value = response
        self.kpi.node_poids = ['11']
        self.kpi.create()
        self.assertTrue(mock_create_cell_level_body.called)
        self.assertTrue(mock_log_logger_debug.called)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_nhm_12_kpi_payload")
    def test_kpi_create_self_name_success(self, mock_create_nhm_12_kpi_payload, mock_log_logger_debug):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        self.kpi.name = "NHM12001"
        self.kpi.node_poids = ['11']
        mock_create_nhm_12_kpi_payload.return_value = {'name': 'NHM_01_1018-13035768_KPI_6', 'allNeTypes': ['RadioNode', 'ERBS'], 'lastModifiedBy': '', 'kpiModel': {'categorySet': ['CATEGORY'], 'version': '1.0.0', 'kpiFormulaList': [{'formulaTypeInfoList': [{'neType': 'RadioNode', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}, {'neType': 'ERBS', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}], 'computation': {'abstractFormulaOperand': {'varName': 'theRO', 'iterationSet': {'var': {'name': 'INPUT'}, 'setVariables': []}, 'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'}, 'operands': [{'operator': 'SUBTRACTION', 'operands': [{'on': 'theRO', 'piName': 'pmPagS1EdrxReceived'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersMax'}, {'on': 'theRO', 'piName': 'pmMoFootprintMax'}, {'on': 'theRO', 'piName': 'pmPagS1Received'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersLicense'}, {'on': 'theRO', 'piName': 'pmPagS1Discarded'}, {'on': 'theRO', 'piName': 'pmRimReportErr'}, {'on': 'theRO', 'piName': 'pmRrcConnBrEnbMax'}]}]}]}, 'preComputation': {}}, 'neTypes': ['RadioNode', 'ERBS']}], 'createdBy': '', 'createdDate': '', 'namespace': 'MULTI', 'modelCreationType': 'USER_CREATED', 'unit': 'MS'}, 'lastModifiedTime': '', 'kpiActivation': {'active': False, 'threshold': {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 133}, 'poidList': [u'281474999339008'], 'nodeCount': 1}}
        self.kpi.create()
        self.assertTrue(mock_create_nhm_12_kpi_payload.called)
        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_router_node_kpi_body")
    def test_kpi_create_self_node_types_success(self, mock_create_router_node_kpi_body, mock_log_logger_debug):

        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        self.kpi.name = "NHM01"
        self.kpi.node_types = ["Router6672", "Router6675"]
        self.kpi.node_poids = ['11']
        mock_create_router_node_kpi_body.return_value = {'name': 'NHM_01_1018-13035768_KPI_6', 'allNeTypes': ['RadioNode', 'ERBS'], 'lastModifiedBy': '', 'kpiModel': {'categorySet': ['CATEGORY'], 'version': '1.0.0', 'kpiFormulaList': [{'formulaTypeInfoList': [{'neType': 'RadioNode', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}, {'neType': 'ERBS', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}], 'computation': {'abstractFormulaOperand': {'varName': 'theRO', 'iterationSet': {'var': {'name': 'INPUT'}, 'setVariables': []}, 'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'}, 'operands': [{'operator': 'SUBTRACTION', 'operands': [{'on': 'theRO', 'piName': 'pmPagS1EdrxReceived'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersMax'}, {'on': 'theRO', 'piName': 'pmMoFootprintMax'}, {'on': 'theRO', 'piName': 'pmPagS1Received'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersLicense'}, {'on': 'theRO', 'piName': 'pmPagS1Discarded'}, {'on': 'theRO', 'piName': 'pmRimReportErr'}, {'on': 'theRO', 'piName': 'pmRrcConnBrEnbMax'}]}]}]}, 'preComputation': {}}, 'neTypes': ['RadioNode', 'ERBS']}], 'createdBy': '', 'createdDate': '', 'namespace': 'MULTI', 'modelCreationType': 'USER_CREATED', 'unit': 'MS'}, 'lastModifiedTime': '', 'kpiActivation': {'active': False, 'threshold': {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 133}, 'poidList': [u'281474999339008'], 'nodeCount': 1}}
        self.kpi.create()
        self.assertTrue(mock_create_router_node_kpi_body.called)
        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm.log.logger.info')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_router_node_kpi_body")
    def test_kpi_create_self_node_types_fail(self, mock_create_router_node_kpi_body, mock_log_logger_info):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        self.kpi.name = "NHM01"
        self.kpi.node_types = ["Router6672", "Router6675"]
        self.kpi.node_poids = []
        mock_create_router_node_kpi_body.return_value = {'name': 'NHM_01_1018-13035768_KPI_6', 'allNeTypes': ['RadioNode', 'ERBS'], 'lastModifiedBy': '', 'kpiModel': {'categorySet': ['CATEGORY'], 'version': '1.0.0', 'kpiFormulaList': [{'formulaTypeInfoList': [{'neType': 'RadioNode', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}, {'neType': 'ERBS', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}], 'computation': {'abstractFormulaOperand': {'varName': 'theRO', 'iterationSet': {'var': {'name': 'INPUT'}, 'setVariables': []}, 'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'}, 'operands': [{'operator': 'SUBTRACTION', 'operands': [{'on': 'theRO', 'piName': 'pmPagS1EdrxReceived'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersMax'}, {'on': 'theRO', 'piName': 'pmMoFootprintMax'}, {'on': 'theRO', 'piName': 'pmPagS1Received'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersLicense'}, {'on': 'theRO', 'piName': 'pmPagS1Discarded'}, {'on': 'theRO', 'piName': 'pmRimReportErr'}, {'on': 'theRO', 'piName': 'pmRrcConnBrEnbMax'}]}]}]}, 'preComputation': {}}, 'neTypes': ['RadioNode', 'ERBS']}], 'createdBy': '', 'createdDate': '', 'namespace': 'MULTI', 'modelCreationType': 'USER_CREATED', 'unit': 'MS'}, 'lastModifiedTime': '', 'kpiActivation': {'active': False, 'threshold': {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 133}, 'poidList': [u'281474999339008'], 'nodeCount': 1}}
        self.kpi.create()
        self.assertTrue(mock_create_router_node_kpi_body.called)
        self.assertTrue(mock_log_logger_info.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_cell_level_body")
    def test_kpi_create_cell_success(self, mock_create_cell_level_body, mock_logger_debug):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 201
        self.kpi.created_by = self.user.username
        self.kpi.reporting_objects = ['EUtranCellFDD', 'EUtranCellTDD']
        self.kpi.node_poids = ['11']
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        mock_create_cell_level_body.return_value = KPI_BODY
        self.kpi.create()
        self.assertTrue(response.raise_for_status.called)
        self.assertTrue(mock_create_cell_level_body.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_node_level_body")
    def test_kpi_create_success_node_success(self, mock_create_node_level_body, mock_logger_debug):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        self.kpi.created_by = self.user.username
        self.kpi.reporting_objects[0] = 'ENodeBFunction'
        self.kpi.node_poids = ['11']
        mock_create_node_level_body.return_value = {'name': 'NHM_01_1018-13035768_KPI_6', 'allNeTypes': ['RadioNode', 'ERBS'], 'lastModifiedBy': '', 'kpiModel': {'categorySet': ['CATEGORY'], 'version': '1.0.0', 'kpiFormulaList': [{'formulaTypeInfoList': [{'neType': 'RadioNode', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}, {'neType': 'ERBS', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}], 'computation': {'abstractFormulaOperand': {'varName': 'theRO', 'iterationSet': {'var': {'name': 'INPUT'}, 'setVariables': []}, 'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'}, 'operands': [{'operator': 'SUBTRACTION', 'operands': [{'on': 'theRO', 'piName': 'pmPagS1EdrxReceived'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersMax'}, {'on': 'theRO', 'piName': 'pmMoFootprintMax'}, {'on': 'theRO', 'piName': 'pmPagS1Received'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersLicense'}, {'on': 'theRO', 'piName': 'pmPagS1Discarded'}, {'on': 'theRO', 'piName': 'pmRimReportErr'}, {'on': 'theRO', 'piName': 'pmRrcConnBrEnbMax'}]}]}]}, 'preComputation': {}}, 'neTypes': ['RadioNode', 'ERBS']}], 'createdBy': '', 'createdDate': '', 'namespace': 'MULTI', 'modelCreationType': 'USER_CREATED', 'unit': 'MS'}, 'lastModifiedTime': '', 'kpiActivation': {'active': False, 'threshold': {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 133}, 'poidList': [u'281474999339008'], 'nodeCount': 1}}
        self.kpi.create()
        self.assertTrue(mock_create_node_level_body.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi._create_node_level_body")
    def test_kpi_raise_http_error(self, mock_create_node_level_body, *_):
        response = Mock()
        response.raise_for_status.side_effect = [HTTPError, HTTPError, HTTPError, HTTPError]
        response.status_code = 405
        self.user.post.side_effect = [response, response, response, response]
        self.kpi.created_by = self.user.username
        self.kpi.reporting_objects[0] = 'ENodeBFunction'
        self.kpi.node_poids = ['11']
        mock_create_node_level_body.return_value = {'name': 'NHM_01_1018-13035768_KPI_6', 'allNeTypes': ['RadioNode', 'ERBS'], 'lastModifiedBy': '', 'kpiModel': {'categorySet': ['CATEGORY'], 'version': '1.0.0', 'kpiFormulaList': [{'formulaTypeInfoList': [{'neType': 'RadioNode', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}, {'neType': 'ERBS', 'reportingObjectType': 'ENodeBFunction', 'inputData': {'inputScope': 'OBJECTS_FOR_TARGET', 'inputResourceMap': {'INPUT': [{'ns': 'UNKNOWN', 'name': 'ENodeBFunction'}]}}}], 'computation': {'abstractFormulaOperand': {'varName': 'theRO', 'iterationSet': {'var': {'name': 'INPUT'}, 'setVariables': []}, 'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'}, 'operands': [{'operator': 'SUBTRACTION', 'operands': [{'on': 'theRO', 'piName': 'pmPagS1EdrxReceived'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersMax'}, {'on': 'theRO', 'piName': 'pmMoFootprintMax'}, {'on': 'theRO', 'piName': 'pmPagS1Received'}, {'on': 'theRO', 'piName': 'pmLicConnectedUsersLicense'}, {'on': 'theRO', 'piName': 'pmPagS1Discarded'}, {'on': 'theRO', 'piName': 'pmRimReportErr'}, {'on': 'theRO', 'piName': 'pmRrcConnBrEnbMax'}]}]}]}, 'preComputation': {}}, 'neTypes': ['RadioNode', 'ERBS']}], 'createdBy': '', 'createdDate': '', 'namespace': 'MULTI', 'modelCreationType': 'USER_CREATED', 'unit': 'MS'}, 'lastModifiedTime': '', 'kpiActivation': {'active': False, 'threshold': {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 133}, 'poidList': [u'281474999339008'], 'nodeCount': 1}}
        self.assertRaises(HTTPError, self.kpi.create)

    @patch("enmutils_int.lib.nhm.NhmKpi._get_kpi")
    def test_get_kpi_public_success(self, mock_get_kpi):
        kpi_info = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                     {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                     ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        mock_get_kpi.return_value = kpi_info
        self.assertEqual(self.kpi.get_kpi(self.user), kpi_info)

    def test_get_kpi_success(self):
        response = Mock()
        response.status_code = 205
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0},
                                       ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator',
                                       '20171017162049745']]
        returned = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                     {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                     ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        self.user.post.return_value = response
        self.assertEqual(NhmKpi._get_kpi(self.user), returned)

    def test_get_kpi_name_success(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0},
                                       ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator',
                                       '20171017162049745']]
        returned = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                     {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                     ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        self.user.post.return_value = response
        self.assertEqual(NhmKpi._get_kpi(self.user, name='Ericsson'), returned)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update__success(self, mock_get_kpi_body, mock_log_logger_debug):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        KPI_BODY["kpiActivation"]["threshold"] = {'thresholdDomain': None}
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(threshold_value=100)
        self.assertEqual(mock_log_logger_debug.call_count, 2)
        self.assertEqual(0, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update__remove_all_nodes_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug):
        response = Mock()
        response.status_code = 201
        self.user.post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(remove_all_nodes=True)
        self.assertEqual(mock_log_logger_debug.call_count, 2)
        data = {'url': 'kpi-specification-rest-api-war/kpi/edit/',
                'headers': {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json'},
                'data': '{"kpiModel": {"kpiFormulaList": [{"formulaTypeInfoList": [{"neType": "ERBS", '
                        '"reportingObjectType": "ENodeBFunction", "inputData": {"inputScope": "OBJECTS_FOR_TARGET", '
                        '"inputResourceMap": {"INPUT": [{"ns": "UNKNOWN", "name": "ENodeBFunction"}]}}}, '
                        '{"neType": "RadioNode", "reportingObjectType": "ENodeBFunction", "inputData": '
                        '{"inputScope": "OBJECTS_FOR_TARGET", "inputResourceMap": {"INPUT": [{"ns": "UNKNOWN", '
                        '"name": "ENodeBFunction"}]}}}], "computation": {"abstractFormulaOperand": {"operator": '
                        '"MULTIPLICATION", "operands": [{"operator": "MULTIPLICATION", "operands": [{"counterRef": '
                        '"pmPagS1Received"}, {"counterRef": "pmRrcConnBrEnbMax"}, {"counterRef": "pmRimReportErr"}, '
                        '{"counterRef": "pmMoFootprintMax"}]}]}, "preComputation": {}}, "neTypes": '
                        '["ERBS", "RadioNode"]}], "unit": "NUMBER_OF_COUNTS"}, "allNeTypes": ["ERBS", '
                        '"RadioNode"], "name": "NHM_01_1017-16230557_KPI_3", "kpiActivation": {"poidList": [], '
                        '"nodeCount": 0, "threshold": {}, '
                        '"autoUpdateKpiScope": false, "queries": [], "active": "false"}}'}
        self.assertDictEqual(self.user.post.call_args[1], data)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_remove_nodes_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 201
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(remove_nodes=["1234567"])
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_add_nodes_and_active_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 201
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        KPI_BODY["kpiActivation"]["active"] = True
        self.kpi.update(add_nodes=["1234567"])
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_add_nodes_and_not_active_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug,
                                                             mock_user_post):
        response = Mock()
        response.status_code = 201
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        KPI_BODY["kpiActivation"]["active"] = False
        self.kpi.update(add_nodes=["1234567"])
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_threshold_domain_value_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 201
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(threshold_domain="GREATER_THAN", threshold_value=100)
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_threshold_domain_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 200
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(threshold_domain="GREATER_THAN")
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_not_threshold_domain_value_kpi_success(self, mock_get_kpi_body, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 200
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update(threshold_value=100, threshold_domain="GREATER_THAN")
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._create_kpi_equation')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_formula_kpi_success(self, mock_get_kpi_body, mock_create_kpi_equation, mock_log_logger_debug, mock_user_post):
        response = Mock()
        response.status_code = 201
        mock_user_post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        mock_create_kpi_equation.return_value = {"operator": "MULTIPLICATION",
                                                 "operands": [{"operator": "MULTIPLICATION",
                                                               "operands": [{"counterRef": "pmPagS1Received"},
                                                                            {"counterRef": "pmRrcConnBrEnbMax"},
                                                                            {"counterRef": "pmRimReportErr"},
                                                                            {"counterRef": "pmMoFootprintMax"}]}]}
        self.kpi.update(replace_formula=True)
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_kpi_update_success(self, mock_get_kpi_body, mock_log_logger_debug):
        response = Mock()
        response.status_code = 201
        self.user.post.return_value = response
        mock_get_kpi_body.return_value = KPI_BODY
        self.kpi.update()
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.NhmKpi._get_kpi_body')
    def test_update_raises_http_error(self, mock_get_kpi_body, *_):
        response = Mock()
        self.user.post.return_value = response
        response.raise_for_status.side_effect = HTTPError
        mock_get_kpi_body.return_value = KPI_BODY
        self.assertRaises(HTTPError, self.kpi.update, threshold_domain="GREATER_THAN", threshold_value=20000)

    def test_kpi_activate_success_for_else(self):
        response = Mock()
        response.status_code = 200
        self.user.put.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_kpi_activate_success_for_if(self):
        self.user.username = "NHM_13_0821-08385549_u0"
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("enmutils_int.lib.nhm.time.sleep")
    def test_kpi_activate_raises_http_error(self, *_):
        response = Mock()
        self.user.put.return_value = response
        try:
            self.kpi.activate()
        except Exception as e:
            raise HTTPError("Raised Http error: {}".format(str(e)))

    def test_kpi_deactivate_success(self):
        response = Mock(status_code=200)
        self.user.put.return_value = response
        try:
            self.kpi.deactivate()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("enmutils_int.lib.nhm.time.sleep")
    def test_kpi_deactivate_raises_http_error(self, *_):
        response = Mock()
        self.user.put.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.deactivate)

    def test_delete_kpi_success(self):
        response = Mock()
        response.status_code = 200
        self.user.delete_request.return_value = response
        try:
            self.kpi.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("enmutils.lib.enm_user_2.User.delete_request")
    @patch('enmutils_int.lib.nhm.log.logger.info')
    def test_delete_kpi_default_kpi_success(self, mock_log_logger_info, mock_user_delete_request):
        response = Mock()
        mock_user_delete_request.return_value = response
        self.kpi.created_by = CREATED_BY_DEFAULT
        try:
            self.kpi.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))
        self.assertTrue(mock_log_logger_info.called)

    def test_delete_kpi_exception(self):
        response = Mock()
        self.user.delete_request.return_value = response
        self.kpi.delete()
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.nhm.time.sleep")
    def test_delete_raises_http_error(self, *_):
        response = Mock()
        response.status_code = 305
        self.user.delete_request.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.delete)

    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    @patch("enmutils_int.lib.nhm.NhmKpi.delete")
    def test_remove_kpis_by_pattern_new_success(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        self.user.post.return_value = response
        NhmKpi.remove_kpis_by_pattern_new(user=self.user, pattern='NHM')
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    @patch("enmutils_int.lib.nhm.NhmKpi.delete")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_remove_kpis_by_pattern_new_deactivate_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        self.user.post.return_value = response
        mock_deactivate.side_effect = Exception
        self.kpi.remove_kpis_by_pattern_new(pattern='NHM', user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    @patch("enmutils_int.lib.nhm.NhmKpi.delete")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_remove_kpis_by_pattern_new_delete_exception(self, mock_delete, mock_deactivate):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [[u'Average_DL_UE_PDCP_DRB_Latency_per_QCI'], [u'NHM_03 kpi']]
        self.user.post.return_value = response
        mock_delete.side_effect = Exception
        self.kpi.remove_kpis_by_pattern_new(pattern='NHM', user=self.user)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_deactivate.called)

    def test_remove_kpis_by_pattern_new_http_error(self):
        response = Mock()
        response.status_code = 305
        self.user.post.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.kpi.remove_kpis_by_pattern_new, pattern='NHM', user=self.user)

    def test_create_kpi_equation_logic(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_create_kpi_equation_division(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        self.kpi.operators = ['DIVISION']
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_create_kpi_equation_division__counter_greater_than_2(self):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual", "pmHwUtilDl", "pmHwUtilUl"]
        self.kpi.operators = ['DIVISION']
        try:
            kpi_equation = self.kpi._create_kpi_equation()
            json.dumps(kpi_equation)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("random.sample")
    def test_create_kpi_equation__not_division(self, mock_sample):
        self.kpi.counters = ["pmHwUtilDl", "pmHwUtilUl", "pmLic5MHzSectorCarrierActual", "pmLic5Plus5MHzScFddActual"]
        self.kpi.operators = ['MULTIPLICATION']
        self.kpi._create_kpi_equation()
        self.assertFalse(mock_sample.called)

    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_kpi_teardown_ericsson_success(self, mock_deactivate, mock_update):
        self.kpi.created_by = CREATED_BY_DEFAULT
        self.kpi._teardown()
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_update.called)

    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_kpi_teardown_ericsson_exception(self, mock_deactivate):
        self.kpi.created_by = CREATED_BY_DEFAULT
        mock_deactivate.side_effect = Exception
        self.assertRaises(self.kpi._teardown)

    @patch("enmutils_int.lib.nhm.NhmKpi.delete")
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_kpi_teardown_user_success(self, mock_deactivate, mock_delete):
        self.kpi.created_by = "nhm_user"
        self.kpi._teardown()
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)

    @patch("enmutils_int.lib.nhm.NhmKpi.delete")
    @patch("enmutils_int.lib.nhm.NhmKpi.update")
    @patch('enmutils_int.lib.nhm.log.logger.debug')
    @patch("enmutils_int.lib.nhm.NhmKpi.deactivate")
    def test_kpi_teardown_user_deactivate_exception(self, mock_deactivate, mock_log_logger_debug, mock_update,
                                                    mock_delete):
        self.kpi.created_by = "nhm_user"
        mock_deactivate.side_effect = Exception
        self.kpi._teardown()
        self.assertTrue(mock_delete.called)
        self.assertFalse(mock_update.called)
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch("enmutils_int.lib.nhm.get_counters_if_enodeb")
    def test_get_counters_specified_by_nhm(self, mock_get_counters_if_enodeb):
        mock_get_counters_if_enodeb.return_value = ['pmPagS1Received', 'pmPagS1Discarded']
        return_value_cell = ['pmRrcConnEstabAtt', 'pmRrcConnEstabAttMod', 'pmRrcConnReestAtt', 'pmRrcConnEstabSuccMod',
                             'pmRrcConnEstabSuccMos', 'pmRrcConnEstabSucc', 'pmRrcConnReestSucc', 'pmRrcConnReestAttHo',
                             'pmErabEstabAttInit', 'pmRrcConnReestSuccHo']
        rnc_return_value = ['pmNoFailedRrcConnectReqCsHw', 'pmTotNoRrcConnectReqCs', 'pmTotNoRrcConnectReqPs',
                            'pmNoFailedRrcConnectReqPsHw', 'pmTotNoRrcConnReqHsFach', 'pmTotNoRrcConnectSetup',
                            'pmTotNoRrcConnectReqSuccess', 'pmTotNoRrcConnectReqSms',
                            'pmNoRabEstablishAttemptPacketStream', 'pmNoRabEstAttPsHoCsfb']
        return_value_node_router = ['queue3_drop_red_bytes', 'queue4_tx_yellow_bytes', 'queue6_drop_total_packets',
                                    'queue0_drop_green_bytes', 'policing_class6_violate_drop_octets', 'ipv6_inpackets',
                                    'policing_class1_conform_octets', 'policing_class1_exceed_octets',
                                    'policing_class4_conform_octets', 'policing_class3_exceed_packets']
        return_value_global = ['free_user_mem', 'average_user_mem', 'load5min', 'peak_user_mem', 'load15min', 'cpu5sec',
                               'cpu1min', 'load1min', 'total_user_mem', 'peakcpu5min', 'cpu5min']

        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object='ENodeBFunction',
                                                               ne_type='MSRBS_V1') ==
                        mock_get_counters_if_enodeb.return_value)
        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object=['EUtranCellFDD'],
                                                               ne_type='ERBS') == return_value_cell)
        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object=['EUtranCell'],
                                                               ne_type='ERBS') == [])
        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object=['UtranCell'],
                                                               ne_type='RNC') == rnc_return_value)
        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object='dot1q-history',
                                                               ne_type='Router6672') == return_value_node_router)
        self.assertTrue(self.kpi.get_counters_specified_by_nhm(reporting_object='global',
                                                               ne_type='Router6675') == return_value_global)

    def test_get_counters_if_enodeb(self):
        return_value_node_ERBS = ['pmPagS1Received', 'pmPagS1Discarded', 'pmRimReportErr', 'pmLicConnectedUsersLicense',
                                  'pmRrcConnBrEnbMax', 'pmMoFootprintMax', 'pmLicConnectedUsersMax',
                                  'pmPagS1EdrxReceived']
        return_value_node_MSRBS_V1 = ['pmPagS1Received', 'pmPagS1Discarded']
        self.assertTrue(get_counters_if_enodeb(ne_type='ERBS') == return_value_node_ERBS)
        self.assertTrue(get_counters_if_enodeb(ne_type='MSRBS_V1') == return_value_node_MSRBS_V1)
        self.assertTrue(get_counters_if_enodeb(ne_type='other type') == [])

    def test_transport_counters(self):
        return_value_global = ['free_user_mem', 'average_user_mem', 'load5min', 'peak_user_mem', 'load15min', 'cpu5sec',
                               'cpu1min', 'load1min', 'total_user_mem', 'peakcpu5min', 'cpu5min']
        return_value_tdm1001 = ['epochtime', 'severelyErroredSecondsHC', 'backgroundBlockErrorsHC',
                                'erroredBlocksHC', 'erroredSecondsHC', 'unavailableTimeHC']
        return_value_ces_pw = ['outpackets', 'inpackets', 'epochtime', 'inoctets', 'outoctets',
                               'missingPackets']
        self.assertTrue(transport_counters(reporting_object='global') == return_value_global)
        self.assertTrue(transport_counters(reporting_object='tdm1001-pdh-history') == return_value_tdm1001)
        self.assertTrue(transport_counters(reporting_object='ces-pw-history') == return_value_ces_pw)
        self.assertTrue(transport_counters(reporting_object='EUtranCellFDD') == [])

    def test_g_node_types_returns_true_if_all_supported(self):
        response = Mock()
        response.json.return_value = [
            [u'unit_test_kpi', False, u'PERCENTAGE', {u'thresholdDomain': None, u'thresholdValue': None},
             [u'ERBS', u'RadioNode'], [u'EUtranCellTDD', u'EUtranCellFDD'], 0, u'Ericsson',
             u'NHM_0120-14563305_u0', u'20180220145639575']]
        self.mock_user.post.return_value = response

        self.assertTrue(self.kpi.check_supported_node_types(self.mock_user, self.kpi.name, ['ERBS', 'RadioNode']))

    def test_check_supported_node_types_returns_false_if_erbs_not_in_ne_types(self):
        response = Mock()
        response.json.return_value = [
            [u'unit_test_kpi', False, u'PERCENTAGE', {u'thresholdDomain': None, u'thresholdValue': None},
             [u'RBS', u'RadioNode'], [u'EUtranCellTDD', u'EUtranCellFDD'], 0, u'Ericsson',
             u'NHM_0120-14563305_u0', u'20180220145639575']]
        self.mock_user.post.return_value = response
        self.assertFalse(self.kpi.check_supported_node_types(self.mock_user, self.kpi.name, ['ERBS', 'RadioNode']))

    def test_check_supported_node_types_returns_true_if_more_than_erbs_radio_nodes_in_ne_types(self):
        response = Mock()
        response.json.return_value = [
            [u'unit_test_kpi', False, u'PERCENTAGE', {u'thresholdDomain': None, u'thresholdValue': None},
             [u'ERBS', u'RadioNode', u'RBS', u'RNC'], [u'EUtranCellTDD', u'EUtranCellFDD'], 0, u'Ericsson',
             u'NHM_0120-14563305_u0', u'20180220145639575']]
        self.mock_user.post.return_value = response
        self.assertTrue(self.kpi.check_supported_node_types(self.mock_user, self.kpi.name, ['ERBS', 'RadioNode']))

    def test_check_reporting_object_returns_true_if_any_or_all_of_the_reporting_objects_match(self):
        response = Mock()
        response.json.return_value = [
            [u'unit_test_kpi', False, u'PERCENTAGE', {u'thresholdDomain': None, u'thresholdValue': None},
             [u'ERBS', u'RadioNode'], [u'EUtranCellTDD', u'EUtranCellFDD'], 0, u'Ericsson',
             u'NHM_0120-14563305_u0', u'20180220145639575']]
        self.mock_user.post.return_value = response
        self.assertTrue(self.kpi.check_reporting_object(self.mock_user, self.kpi.name,
                                                        profile_reporting_objects=['EUtranCellTDD', 'EUtranCellFDD']))

    def test_check_reporting_object_returns_false_if_reporting_objects_do_not_match(self):
        response = Mock()
        response.json.return_value = [
            [u'unit_test_kpi', False, u'PERCENTAGE', {u'thresholdDomain': None, u'thresholdValue': None},
             [u'ERBS', u'RadioNode'], [u'IP_interface'], 0, u'Ericsson',
             u'NHM_0120-14563305_u0', u'20180220145639575']]
        self.mock_user.post.return_value = response
        self.assertFalse(self.kpi.check_reporting_object(self.mock_user, self.kpi.name,
                                                         profile_reporting_objects=['EUtranCellTDD', 'EUtranCellFDD']))

    @patch('enmutils_int.lib.nhm.log.logger')
    def test_create_nhm_12_payload_body(self, mock_log):
        user = Mock()
        response = Mock()
        response.status_code = 999
        user.post.return_value = response
        kpi = NhmKpi(user=user, name="NHM12_test_kpi", nodes=[], reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, active="false")
        kpi.node_poids = ['123', '456']
        kpi.create()

        self.assertTrue(mock_log.debug.called)
        self.assertFalse(mock_log.info.called)

    @patch('enmutils_int.lib.nhm.NhmKpi._create_router_node_kpi_body',
           return_value={"kpiActivation": {"poidList": None}})
    def test_create_nhm_router_body__success(self, mock_create_router_body):
        user = Mock()
        response = Mock()
        response.status_code = 999
        user.post.return_value = response
        kpi = NhmKpi(user=user, name="NHM", node_types=['Router6672'],
                     created_by=self.user.username, active="false")
        kpi.node_poids = ['123', '456']
        kpi.create()
        self.assertEqual(1, mock_create_router_body.call_count)

    @patch('enmutils_int.lib.nhm.log.logger')
    def test_create_nhm_12_payload_body_bad_request(self, mock_log):
        user = Mock()
        response = Mock()
        response.status_code = 200
        user.post.return_value = response
        kpi = NhmKpi(user=user, name="NHM12_test_kpi", nodes=[], reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, active="false")
        kpi.node_poids = ['123', '456']
        kpi.create()
        self.assertTrue(mock_log.debug.called)
        self.assertFalse(mock_log.info.called)

    @patch('enmutils_int.lib.nhm.log.logger')
    def test_create_nhm_14_payload_body(self, mock_log):
        user = Mock()
        response = Mock()
        response.status_code = 999
        user.post.return_value = response
        kpi = NhmKpi(user=user, name="NHM_14_0123-13270495_KPI_01", nodes=[], reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, counters=['queue3_drop_red_bytes', 'queue4_tx_yellow_bytes'],
                     active="false")
        kpi.node_poids = ['123', '456']
        kpi.create()

        self.assertTrue(mock_log.debug.called)
        self.assertFalse(mock_log.info.called)


class NhmUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_nhm_get_kpi_success(self):
        response = Mock()
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0},
                                       ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator',
                                       '20171017162049745']]
        returned = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                     {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                     ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        self.user.post.return_value = response
        self.assertEqual(get_kpi(self.user), returned)

    def test_nhm_get_kpi_success_with_name_specified(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0},
                                       ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator',
                                       '20171017162049745']]
        returned = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                     {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                     ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        self.user.post.return_value = response
        self.assertEqual(get_kpi(self.user, 'Total_UL_PDCP_Cell_Throughput'), returned)

    def test_nhm_get_kpi_raises_http_error(self):
        response = Mock()
        response.status_code = 305
        self.user.post.return_value = response
        get_kpi(self.user)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.nhm.time.sleep")
    def test_nhm_get_kpi_retry(self, *_):
        response = Mock()
        response.status_code = 305
        self.user.post.return_value = response
        response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, get_kpi, user=self.user)

    def test_check_is_kpi_usable_and_assign_to_node_type(self):
        response = Mock()
        response.status_code = 200
        kpi_name = 'Total_UL_PDCP_Cell_Throughput'
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0}, ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator', '20171017162049745']]
        self.user.post.return_value = response
        result = check_is_kpi_usable_and_assign_to_node_type(self.user, kpi_name, {'ERBS': []}, ['ERBS'],
                                                             {'ERBS': ['EUtrancellFDD']}, unsupported_kpis=[])
        self.assertTrue(result == {'ERBS': []})

    def test_check_is_kpi_usable_and_assign_to_node_type_kpi_is_unsupported(self):
        response = Mock()
        response.status_code = 200
        kpi_name = 'Total_UL_PDCP_Cell_Throughput'
        response.json.return_value = [['Total_UL_PDCP_Cell_Throughput', False, u'MEGA_BITS_PER_SECOND',
                                       {'thresholdDomain': 'GREATER_THAN', 'thresholdValue': 59.0},
                                       ['ERBS', 'RadioNode'],
                                       ['EUtranCellTDD', 'EUtranCellFDD'], 0, 'Ericsson', 'administrator',
                                       '20171017162049745']]
        self.user.post.return_value = response
        result = check_is_kpi_usable_and_assign_to_node_type(self.user, kpi_name, {'ERBS': []}, ['ERBS'],
                                                             {'ERBS': ['EUtrancellFDD']},
                                                             unsupported_kpis=[['Total_UL_PDCP_Cell_Throughput']])
        self.assertTrue(result == {'ERBS': []})

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_sleep_until_profile_persited(self, mock_persistence, mock_time_sleep):
        side_effects = [False for _ in range(17)]
        side_effects.append(True)
        mock_persistence.has_key.side_effect = side_effects
        sleep_until_profile_persisted("NHM_SETUP")
        self.assertTrue(mock_persistence.has_key.called)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.nhm.log.logger')
    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile_if_not_persistence(self, mock_persistence, *_):
        mock_persistence.has_key.side_effect = [False, True]
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        mock_persistence.get.side_effect = [mock_profile_with_flag, mock_profile_with_flag]
        wait_for_nhm_setup_profile()

    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.log.logger')
    @patch('enmutils_int.lib.nhm.sleep_until_profile_persisted')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile__sleep_until_profile_persisted(self, mock_persistence, mock_profile_persisted,
                                                                       *_):
        mock_persistence.has_key.side_effect = [False, True]
        mock_profile_with_flag = Mock(FLAG="COMPLETED")
        mock_profile_with_out_flag = Mock(FLAG="RUNNING")
        mock_persistence.get.side_effect = [mock_profile_with_out_flag] * 18 + [False] + [mock_profile_with_flag]
        wait_for_nhm_setup_profile()
        self.assertTrue(mock_profile_persisted.called)

    @patch('enmutils_int.lib.nhm.log.logger')
    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile_start_with_flag_completed(self, mock_persistence, *_):
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        mock_persistence.get.side_effect = [mock_profile_with_flag, mock_profile_with_flag]
        wait_for_nhm_setup_profile()

    @patch('enmutils_int.lib.nhm.log.logger')
    @patch('enmutils_int.lib.nhm.time.sleep')
    @patch('enmutils_int.lib.nhm.persistence')
    def test_wait_for_nhm_setup_profile_starts_and_wait_for_the_flag(self, mock_persistence, *_):
        mock_profile_with_flag = Mock()
        mock_profile_with_flag.FLAG = "COMPLETED"
        side_effects = [Mock() for _ in range(17)]
        side_effects.append(mock_profile_with_flag)
        mock_persistence.get.side_effect = side_effects
        wait_for_nhm_setup_profile()

    @patch('enmutils_int.lib.nhm.NhmKpi._create_router_equation')
    def test_create_router_node_kpi_body__only_select_applicable_counters(self, mock_create_equation):
        reporting_objects = ROUTER_COUNTERS.keys()[:2]
        kpi = NhmKpi(user=self.user, name="NHM01", node_types=['Router6672'], created_by="TEST",
                     active="false", reporting_objects=reporting_objects)
        kpi._create_router_node_kpi_body()
        self.assertEqual(2, mock_create_equation.call_count)

    def test_create_router_equation__success(self):
        counters = ["counter1"]
        kpi = NhmKpi(user=self.user, name="NHM12_test_kpi", nodes=[], reporting_objects=["EUtranCellFDD"],
                     created_by=self.user.username, active="false")
        result = kpi._create_router_equation(counters)
        returned = {'varName': 'theRO',
                    'iterationSet': {'var': {'name': 'INPUT'}},
                    'operands': [{'reportingInstructions': {'reportingObjectIdSource': 'theRO'},
                                  'operands': [{'operator': 'MULTIPLICATION',
                                                'operands': [{'on': 'theRO', 'piName': "counter1"},
                                                             {'on': 'theRO', 'piName': "counter1"}]}]}],
                    'setVariables': []}
        self.assertEquals(result, returned)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
