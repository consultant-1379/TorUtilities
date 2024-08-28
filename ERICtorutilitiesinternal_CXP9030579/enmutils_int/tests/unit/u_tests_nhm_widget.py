#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nhm import KPI_BODY
from enmutils_int.lib.nhm_widget import (NhmWidget, NodesBreached, WorstPerforming,
                                         NetworkOperationalState, NetworkSyncStatus, MostProblematic, CellStatus)
from testslib import unit_test_utils

KPI_INFO = {u'name': u'Average_UE_PDCP_DL_Throughput', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'operands': [{u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'operands': [{u'operator': u'SUBTRACTION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'operands': None, u'value': 1000.0}]}]}], }]}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'Description'}
KPI_INFO_TEST = {u'name': u'unit_test_kpi', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'operands': [{u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'operands': [{u'operator': u'SUBTRACTION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'operands': None, u'value': 1000.0}]}]}], }]}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'Description'}

CURRENT_VIEW_URL_widget = "rest/ui/settings/networkhealthmonitor/dashboard"


class NhmWidgetUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser", workspace_id="1")

        nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim', 'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim', 'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]

        nodes[0].poid = "281474977292253"
        nodes[1].poid = "181474977292251"

        self.widget = NhmWidget(user=self.user, nodes=nodes)

        self.nodes_breached = NodesBreached(user=self.user, nodes=nodes)

        self.worst_performing = WorstPerforming(user=self.user, nodes=nodes)
        self.worst_performing.widget_kpi = KPI_INFO

        self.cell_status = CellStatus(user=self.user, nodes=nodes)
        self.cell_status_one_poid = CellStatus(user=self.user, nodes=[nodes[0]])
        self.cell_status_one_poid = CellStatus(user=self.user, nodes=[])

        self.most_problematic = MostProblematic(user=self.user, nodes=nodes)

        self.network_operational_state = NetworkOperationalState(user=self.user, nodes=nodes)

        self.network_sync_status = NetworkSyncStatus(user=self.user, nodes=nodes)

        self.worst_performing.created_configured = True
        self.cell_status.created_configured = True
        self.most_problematic.created_configured = True
        self.network_operational_state.created_configured = True
        self.network_sync_status.created_configured = True

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_configure_widget(self):
        self.assertRaises(NotImplementedError, self.widget.configure)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_create_widget_with_no_nodes_success(self, mock_log_logger_debug):
        widget = NhmWidget(user=self.user, nodes=[])
        self.assertRaises(NotImplementedError, widget.configure)
        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.create_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    def test_create_widget_with_no_network_scope(self, mock_get_network_element_scope, mock_create_network_element_scope):
        widget = NhmWidget(user=self.user, nodes=[])
        widget.network_scope = None

        self.assertRaises(NotImplementedError, widget.create)

        self.assertTrue(mock_get_network_element_scope.called)
        self.assertTrue(mock_create_network_element_scope.called)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._teardown')
    def test_teardown_success(self, mock_teardown):
        self.worst_performing.teardown()
        self.assertTrue(mock_teardown.called)

    def test_number_created_configured_widgets_true(self):
        widgets = [self.worst_performing, self.cell_status, self.most_problematic, self.network_operational_state,
                   self.network_sync_status]

        self.assertEqual(NhmWidget.number_created_configured_widgets(widgets), 5)

    def test_number_created_configured_widgets_error(self):
        widgets = [self.worst_performing, self.cell_status, self.most_problematic, self.network_operational_state,
                   self.network_sync_status]
        self.worst_performing.created_configured = False
        self.cell_status.created_configured = False
        self.most_problematic.created_configured = False
        self.network_operational_state.created_configured = False
        self.network_sync_status.created_configured = False

        self.assertEqual(NhmWidget.number_created_configured_widgets(widgets), 0)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NodesBreached.get_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi._get_kpi_body')
    def test_create_nodes_breached_widget_with_network_scope_success(self, mock_get_kpi_body, mock_get_available_kpis,
                                                                     mock_get_kpis, mock_get_widgets, _):
        mock_get_widgets.return_value = []
        mock_get_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                       'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                       'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_available_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                                 'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                                 'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_kpi_body.return_value = KPI_BODY

        self.nodes_breached.network_scope = "networkhealthmonitor:networkscope.1460459157.93.591000000"
        response = Mock(status_code=200, ok=True)
        self.user.put.return_value = response
        try:
            self.nodes_breached.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NodesBreached.get_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi._get_kpi_body')
    def test_create_nodes_breached_widget_raises_http_error(self, mock_get_kpi_body, mock_get_available_kpis,
                                                            mock_get_kpis, mock_get_widgets, _):
        # Get networkScope
        mock_get_widgets.return_value = []
        mock_get_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                       'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                       'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_available_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                                 'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                                 'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_kpi_body.return_value = KPI_BODY
        self.nodes_breached.network_scope = "networkhealthmonitor:networkscope.1460459157.93.591000000"
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.put.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached.create)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.create_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NodesBreached.get_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi._get_kpi_body')
    def test_create_nodes_breached_widget_with_no_network_scope_success(self, mock_get_kpi_body,
                                                                        mock_get_available_kpis,
                                                                        mock_get_kpis, mock_get_widgets,
                                                                        mock_create_network_scope, _):
        # Get networkScope
        mock_get_widgets.return_value = []
        self.nodes_breached.network_scope = None
        mock_create_network_scope.return_value = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        mock_get_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                       'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                       'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_available_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                                 'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                                 'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_kpi_body.return_value = KPI_BODY
        response = Mock(status_code=200, ok=True)
        self.user.put.return_value = response
        try:
            self.nodes_breached.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NodesBreached.get_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi._get_kpi_body')
    def test_create_nodes_breached_widget_with_network_scope_and_payload_success(self, mock_get_kpi_body,
                                                                                 mock_get_available_kpis,
                                                                                 mock_get_kpis, mock_get_widgets, _):
        # Get networkScope
        mock_get_widgets.return_value = [{u'id': u'dashboardSettings', u'value': u'{"type": "Dashboard", "layout": "one-column", "items":[[{"minimizeText": "Minimize", "maximizeText": "Maximize", "type": "TopWorstPerformers", "settings": true, "header": "Worst Performing Nodes By KPI", "maximizable": false, "closeText": "Close", "closable": true, "config": {"linkOptions": [], "appTitle": "Worst Performing Nodes By KPI", "kpiName": "Average_Cell_UL_PDCP_Throughput", "groupName": "networkhealthmonitor:networkscope.1508507314.38.403000000", "unit": "kbps", "smallerBetter": true, "thresholdValue": "78.0"}}]]}'}]
        mock_get_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                       'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                       'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_available_kpis.return_value = [{'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate',
                                                 'modelVersion': u'1.0.4', 'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
                                                 'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_kpi_body.return_value = KPI_BODY
        response = Mock(status_code=200, ok=True)
        self.user.put.return_value = response
        self.nodes_breached.network_scope = "networkhealthmonitor:networkscope.1460459157.93.591000000"
        try:
            self.nodes_breached.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NodesBreached.get_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi._get_kpi_body')
    def test_create_nodes_breached_widget_without_network_scope_success(self, mock_get_kpi_body,
                                                                        mock_get_available_kpis, mock_get_kpis,
                                                                        mock_get_widgets, _):
        mock_get_widgets.return_value = []
        mock_get_kpis.return_value = [
            {'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate', 'modelVersion': u'1.0.4',
             'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
             'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_available_kpis.return_value = [
            {'systemThreshold': 98.0, 'kpiName': 'Added_E-RAB_Establishment_Success_Rate', 'modelVersion': u'1.0.4',
             'smallerBetter': False, 'invalid': False, 'kpiUnit': 'PERCENTAGE',
             'measurementOn': ['EUtranCellTDD', 'EUtranCellFDD'], 'userThreshold': 98.0, 'active': True}]
        mock_get_kpi_body.return_value = KPI_BODY
        response = Mock(status_code=200, ok=True)
        self.nodes_breached.network_scope = "1460459157.93.591000000"
        self.user.put.return_value = response

        try:
            self.nodes_breached.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_nodes_breached_configured_no_kpis_raises_environ_error(self, mock_get_available_kpis):
        mock_get_available_kpis.return_value = []
        self.nodes_breached.kpis = None

        self.assertRaises(EnvironError, self.nodes_breached.configure)

    def test_get_network_element_scope_success(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{"id": "networkTopologySettings", "value": "{\"scopeId\":\"networkhealthmonitor:networkscope.1460459157.93.591000000\",\"selectedScopeId\":\"networkhealthmonitor:networkscope.1460459157.93.591000000\",\"selectedCount\":49,\"isShown\":true,\"totalCount\":50}"}]
        self.user.get.return_value = response
        try:
            self.nodes_breached.get_network_element_scope()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch("enmutils_int.lib.nhm_widget.log.logger.debug")
    def test_get_network_element_scope__value_dict_empty(self, mock_log, *_):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{"id": "networkTopologySettings",
                                       "value": "{\"\":\"networkhealthmonitor:networkscope.1460459157.93.591000000\",\"\":\"networkhealthmonitor:networkscope.1460459157.93.591000000\",\"selectedCount\":49,\"isShown\":true,\"totalCount\":50}"}]
        self.user.get.return_value = response
        self.nodes_breached.get_network_element_scope()
        mock_log.assert_called_with('User TestUser using network scope: None with [{\'id\': \'networkTopologySettings\','
                                    ' \'value\': \'{"":"networkhealthmonitor:networkscope.1460459157.93.591000000",""'
                                    ':"networkhealthmonitor:networkscope.1460459157.93.591000000","selectedCount":49,"'
                                    'isShown":true,"totalCount":50}\'}]')

    @patch("enmutils_int.lib.nhm_widget.log.logger.debug")
    def test_get_network_element_scope__json_return_empty(self, mock_log, *_):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = []
        self.user.get.return_value = response
        self.nodes_breached.get_network_element_scope()
        self.assertFalse(mock_log.called)

    def test_get_network_element_scope_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached.get_network_element_scope)

    def test_delete_widget_success(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {}
        self.user.put.return_value = response
        try:
            self.nodes_breached.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_delete_widget_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.put.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached.delete)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_set_selected_nodes_success(self, mock_log_logger_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{u'Success': u'true'}]
        self.user.post.return_value = response
        self.worst_performing._set_selected_nodes()
        self.assertTrue(mock_log_logger_debug.called)

    def test_set_selected_nodes_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.worst_performing._set_selected_nodes)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._set_selected_nodes')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._set_user_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    def test_create_network_element_scope_success(self, mock_get_network_element_scope,
                                                  mock__set_user_network_element_scope, mock__set_selected_nodes):
        response = Mock(status_code=200, ok=True)
        response.raise_for_status.side_effect = None
        self.user.post.return_value = response

        self.nodes_breached.create_network_element_scope()

        self.assertTrue(mock__set_selected_nodes.called)
        self.assertTrue(mock__set_user_network_element_scope.called)
        self.assertTrue(mock_get_network_element_scope.called)

    def test_create_network_element_scope_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response

        self.assertRaises(HTTPError, self.nodes_breached.create_network_element_scope)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_set_user_network_element_scope_success(self, mock_logger_debug):
        response = Mock(status_code=200, ok=True)
        self.user.put.return_value = response
        self.nodes_breached._set_user_network_element_scope()
        self.assertTrue(mock_logger_debug.called)

    def test_set_user_network_element_scope_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.put.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached._set_user_network_element_scope)

    @patch('enmutils_int.lib.nhm_widget.log.logger.info')
    def test_nodes_brached_get_kpis_success(self, mock_logger_info):
        self.nodes_breached.kpis = ['SomeValue']
        self.nodes_breached.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{u'Success': u'true'}]
        self.user.post.return_value = response
        self.nodes_breached.get_kpis()
        self.assertEqual(0, mock_logger_info.call_count)
        self.assertEqual(0, response.raise_for_status.call_count)

    def test_nodes_brached_get_kpis_raises_http_error(self):
        self.nodes_breached.kpis = ['SomeValue']
        self.nodes_breached.network_scope = 'test'
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached.get_kpis)

    def test_nodes_brached_get_kpis_not_ok(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {}
        self.user.post.return_value = response
        self.assertEqual(self.nodes_breached.get_kpis(), None)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_configure_network_sync_status(self, mock_log_logger_debug):

        self.network_sync_status.configure()

        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch('enmutils_int.lib.nhm_widget.MostProblematic._create_alarm_polling')
    def test_configure_most_problematic_success(self, mock_create_alarm_polling, mock_log_logger_debug):

        self.most_problematic.configure()

        self.assertTrue(mock_create_alarm_polling.called)
        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_configure_network_operational_state_success(self, mock_log_logger_debug):

        self.network_operational_state.configure()

        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch("enmutils_int.lib.nhm_widget.NhmKpi.get_kpi_info")
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_worst_performing_configuration_with_available_kpi_succss(self, mock_get_available_kpis, mock_kpi_info, mock_log_logger_debug):
        mock_get_available_kpis.return_value = [{u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput', u'modelVersion': None, u'userThreshold': 59.0}]
        mock_kpi_info.return_value = KPI_INFO

        self.worst_performing.configure()

        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch("enmutils_int.lib.nhm_widget.NhmKpi.get_kpi_info")
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_worst_performing_configuration_with_kpi_name_success(self, mock_get_available_kpis, mock_kpi_info, mock_log_logger_debug):
        mock_get_available_kpis.return_value = [{u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput', u'modelVersion': None, u'userThreshold': 59.0}]
        mock_kpi_info.return_value = KPI_INFO
        self.worst_performing.kpi_name = "Kpi name"

        self.worst_performing.configure()

        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_worst_performing_configuration_raises_environ_error(self, mock_get_available_kpis):

        mock_get_available_kpis.return_value = None

        self.assertRaises(EnvironError, self.worst_performing.configure)

    @patch('enmutils_int.lib.nhm_widget.WorstPerforming.configure')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi.get_all_kpi_names_active', return_value=[['Added_E-RAB_Establishment_Success_Rate'], ['Initial_E-RAB_Establishment_Success_Rate']])
    def test_get_kpi_with_results_successfully_returns_a_new_active_kpi(self, *_):
        self.worst_performing.kpi_name = 'Added_E-RAB_Establishment_Success_Rate'

        active_kpi = self.worst_performing.get_kpi_with_results()
        self.assertEqual(active_kpi, 'Initial_E-RAB_Establishment_Success_Rate')

    @patch('enmutils_int.lib.nhm_widget.WorstPerforming.configure')
    @patch('enmutils_int.lib.nhm_widget.NhmKpi.get_all_kpi_names_active', return_value=[['Initial_E-RAB_Establishment_Success_Rate']])
    def test_get_kpi_with_results_successfully_handles_unexpected_deleted_and_deactivated_kpis_from_enm_and_returns_a_new_active_kpi(self, *_):
        self.worst_performing.kpi_name = 'Added_E-RAB_Establishment_Success_Rate'

        active_kpi = self.worst_performing.get_kpi_with_results()
        self.assertEqual(active_kpi, 'Initial_E-RAB_Establishment_Success_Rate')

    @patch('enmutils_int.lib.nhm_widget.NhmKpi.get_all_kpi_names_active', return_value=[['Added_E-RAB_Establishment_Success_Rate']])
    def test_get_kpi_with_results_raises_environ_error_when_there_are_no_usuable_active_kpis_left_on_enm(self, *_):
        self.worst_performing.kpi_name = 'Added_E-RAB_Establishment_Success_Rate'
        self.worst_performing.kpi_with_no_results = ['Added_E-RAB_Establishment_Success_Rate']

        self.assertRaises(EnvironError, self.worst_performing.get_kpi_with_results)

    @patch('enmutils_int.lib.nhm_widget.NhmKpi.get_all_kpi_names_active', return_value=[])
    def test_get_kpi_with_results_no_kpis_raises_environ_error_when_there_are_no_active_kpis_on_enm(self, *_):
        self.worst_performing.kpi_name = 'kpi_test_name'
        self.worst_performing.kpi_with_no_results = []

        self.assertRaises(EnvironError, self.worst_performing.get_kpi_with_results)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch("enmutils_int.lib.nhm_widget.NhmKpi.get_kpi_info")
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_cell_status_configuration_ok_multiple_kpi_success(self, mock_get_available_kpis, mock_get_kpi_info, mock_log_logger_debug):
        mock_get_available_kpis.return_value = [{u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput',
                                                 u'modelVersion': None, u'userThreshold': 59.0},
                                                {u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput',
                                                 u'modelVersion': None, u'userThreshold': 59.0}]
        mock_get_kpi_info.return_value = KPI_INFO

        self.cell_status.configure()

        self.assertTrue(mock_log_logger_debug.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch("enmutils_int.lib.nhm_widget.NhmKpi.get_kpi_info")
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_cell_status_configuration_one_kpi_success(self, mock_get_available_kpis, mock_get_kpi_info, mock_log_logger_debug):
        mock_get_available_kpis.return_value = [
            {u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput', u'modelVersion': None,
             u'userThreshold': 59.0}]
        mock_get_kpi_info.return_value = KPI_INFO

        self.cell_status.configure()

        self.assertTrue(mock_log_logger_debug.called)
        self.assertTrue(mock_get_kpi_info.called)
        self.assertTrue(mock_get_available_kpis.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch("enmutils_int.lib.nhm_widget.NhmKpi.get_kpi_info")
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_cell_status_configuration_no_kpi_present(self, mock_get_available_kpis, mock_get_kpi_info, mock_log_logger_debug):
        mock_get_available_kpis.return_value = [
            {u'systemThreshold': 59.0, u'kpiName': u'Total_UL_PDCP_Cell_Throughput', u'modelVersion': None,
             u'userThreshold': 59.0}]
        self.cell_status.kpi_present = None
        mock_get_kpi_info.return_value = KPI_INFO

        self.cell_status.configure()

        self.assertTrue(mock_log_logger_debug.called)
        self.assertFalse(mock_get_kpi_info.called)
        self.assertFalse(mock_get_available_kpis.called)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_available_kpis')
    def test_cell_status_configuration_raises_environ_error(self, mock_get_available_kpis):
        mock_get_available_kpis.return_value = None

        self.assertRaises(EnvironError, self.cell_status.configure)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._remove_network_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.delete')
    def test_teardonw_success(self, mock_delete, mock_remove_network_scope):

        self.worst_performing._teardown()

        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_remove_network_scope.called)

    @patch('enmutils_int.lib.nhm_widget.NhmWidget._remove_network_scope')
    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.delete')
    def test_teardonw_raises_exception(self, mock_delete, mock_log_logger_debug, mock_remove_network_scope):
        mock_delete.side_effect = Exception

        self.worst_performing._teardown()

        self.assertTrue(mock_delete.called)
        self.assertEqual(mock_log_logger_debug.call_count, 2)
        self.assertTrue(mock_remove_network_scope.called)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_create_alarm_polling_success(self, mock_log_logger_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{u'Success': u'true'}]
        self.user.post.return_value = response
        self.most_problematic._create_alarm_polling()

        self.assertTrue(mock_log_logger_debug.called)

    def test_create_alarm_polling_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response

        self.assertRaises(HTTPError, self.most_problematic._create_alarm_polling)

    def test_get_widgets_success(self):
        data = [{u'Success': u'true'}]
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{u'Success': u'true'}]
        self.user.get.return_value = response
        self.assertTrue(self.worst_performing._get_widgets() == data)

    def test_get_widgets__raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.worst_performing._get_widgets)

    @patch('enmutils_int.lib.nhm_widget.log.logger.debug')
    def test_remove_network_scope_success(self, mock_log_logger_debug):
        self.nodes_breached.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        response = Mock(status_code=200, ok=True)
        response.json.return_value = [{u'Success': u'true'}]
        self.user.put.return_value = response
        self.nodes_breached._remove_network_scope()

        self.assertTrue(mock_log_logger_debug.called)

    def test_remove_network_scope_raises_http_error(self):
        self.nodes_breached.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.put.return_value = response
        self.assertRaises(HTTPError, self.nodes_breached._remove_network_scope)

    @patch('enmutils_int.lib.nhm_widget.json')
    @patch('enmutils_int.lib.nhm_widget.ast')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.configure')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.create_network_element_scope')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget._get_widgets')
    @patch('enmutils_int.lib.nhm_widget.NhmWidget.get_network_element_scope')
    def test_create_response_is_not_200(self, mock_get_scope, mock_items, *_):
        mock_response = Mock()
        mock_response.status_code = 777
        mock_items.return_value = None
        mock_get_scope.return_value = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        user = Mock()
        user.put.return_value = mock_response
        mock_node = Mock()
        mock_node.poid = 9999999999999
        widget = NhmWidget(user, [mock_node])
        widget.CREATE_PAYLOAD = {"maximizeText": "Maximize", "minimizeText": "Minimize",
                                 "config": {"selectedKpis": [], "groupName": "", "appTitle": "Nodes Breached per KPI"},
                                 "settings": True, "header": "Nodes Breached per KPI", "maximizable": False,
                                 "closeText": "Close",
                                 "closable": True, "type": "KpiBreachWidget"}

        widget.create()
        self.assertTrue(mock_response.raise_for_status.called)

    def test_widget_get_kpis_calls_raise_for_status(self):
        mock_user = Mock()
        mock_response = Mock()
        mock_node = Mock()
        mock_node.poid = 9999999999999
        mock_response.status_code = 247420
        mock_user.post.return_value = mock_response
        widget = NhmWidget(nodes=[mock_node], user=mock_user)
        widget.get_kpi_names()

        self.assertTrue(mock_response.raise_for_status.called)

    def test_widget_get_kpis(self):
        mock_user = Mock()
        mock_response = Mock()
        mock_node = Mock()
        mock_node.poid = 9999999999999
        mock_response.status_code = 200
        mock_response.json.return_value = [[0, 1, 2, 3, 4, 5]]
        mock_user.post.return_value = mock_response
        widget = NhmWidget(nodes=[mock_node], user=mock_user)
        widget.get_kpi_names()

        self.assertFalse(mock_response.raise_for_status.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
