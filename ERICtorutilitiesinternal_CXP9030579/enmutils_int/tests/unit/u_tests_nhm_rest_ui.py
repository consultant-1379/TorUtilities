#!/usr/bin/env python
import time

import responses
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode
from enmutils_int.lib.nhm_widget import (NodesBreached, WorstPerforming, MostProblematic, NetworkOperationalState,
                                         NetworkSyncStatus, CellStatus)
from enmutils_int.lib.nhm_ui import (get_nhm_kpi_home, poll_alarm_widget, _nodes_breached_home,
                                     _common_kpi_loading_endpoints, _network_status_landing_page,
                                     _nodes_breached_node_view, _worst_performing_landing_page,
                                     network_operational_state_flow, _cell_status_page, _nodemonitor_poid,
                                     worst_performing_flow, nhm_widget_flows, call_widget_flow, nodes_breached_flow,
                                     cell_status_flow, nhm_landing_page_flow, _worst_performing_node_page,
                                     create_widgets_taskset, _multi_node_health_monitor_page,
                                     _nodes_breached_node_view_perform_main_request)

URL = 'http://test.com'

KPI_INFO = {u'name': u'Average_UE_PDCP_DL_Throughput', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'operands': [{u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'operands': [{u'operator': u'SUBTRACTION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'operands': [{u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'operands': None, u'value': 1000.0}]}]}], }]}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'Description'}


class NHMRestUiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.nodes[0].poid = "281474977292253"
        self.nodes[1].poid = "181474977292251"

        self.nodes_breached = NodesBreached(user=self.user, nodes=self.nodes)
        self.nodes_breached.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        self.nodes_breached.widget_kpi = 'Average_UE_PDCP_DL_Throughput'

        self.worst_performing = WorstPerforming(user=self.user, nodes=self.nodes)
        self.worst_performing.widget_kpi = KPI_INFO
        self.worst_performing.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        self.worst_performing.widget_kpi = {'name': 'Average_UE_PDCP_DL_Throughput'}
        self.worst_performing.kpi_name = 'Average_UE_PDCP_DL_Throughput'

        self.cell_status_one_poid = CellStatus(user=self.user, nodes=[self.nodes[0]])
        self.cell_status = CellStatus(nodes=self.nodes, user=self.user)
        self.cell_status.network_scope = 'networkhealthmonitor:networkscope.1460459157.93.591000000'
        self.cell_status.poid = "281474977292253"
        self.cell_status.widget_kpi = {'name': 'Circuit-Switched_CS_Speech_Accessibility_Failure'}

        self.most_problematic = MostProblematic(user=self.user, nodes=self.nodes)
        self.most_problematic.polling_id = '1'

        self.network_operational_state = NetworkOperationalState(user=self.user, nodes=self.nodes)

        self.network_sync_status = NetworkSyncStatus(user=self.user, nodes=self.nodes)

        self.worst_performing.created_configured = True
        self.cell_status.created_configured = True
        self.most_problematic.created_configured = True
        self.network_operational_state.created_configured = True
        self.network_sync_status.created_configured = True
        self.widgets = [self.nodes_breached, self.worst_performing, self.cell_status, self.most_problematic,
                        self.network_operational_state, self.network_sync_status]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_get_nhm_kpi_home_success(self, mock_log_logger_debug):
        response = Mock(status_code=200, ok=True)
        self.user.get.return_value = response
        get_nhm_kpi_home(user=self.user)
        self.assertTrue(mock_log_logger_debug.called)

    def test_get_nhm_kpi_home_raise_for_status(self):
        response = Mock(status_code=400, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, get_nhm_kpi_home, user=self.user)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_poll_alarm_widget_success(self, mock_log_logger_debug):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'Success': u'true'}
        self.user.post.return_value = response
        poll_alarm_widget(self.user, '1')
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    @responses.activate
    def test_nodes_breached_home_success(self, mock_nhm_landing_page_flow):
        responses.add(responses.GET, URL + "/oss/nhm/networkscope?scopeId={scope_id}".
                      format(scope_id='networkhealthmonitor:networkscope.1460459157.93.591000000'),
                      json={},
                      status=200,
                      match_querystring=True,
                      content_type='application/json')

        _nodes_breached_home(self.nodes_breached)

        self.assertTrue(mock_nhm_landing_page_flow.called)

    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    @responses.activate
    def test_nodes_breached_home__no_network_scope(self, mock_nhm_landing_page_flow):
        self.nodes_breached.network_scope = None

        _nodes_breached_home(self.nodes_breached)
        self.assertTrue(mock_nhm_landing_page_flow.called)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @patch('enmutils_int.lib.nhm_ui.NodesBreached.get_kpis')
    def test_nodes_breached_node_view_no_kpi_nodes_success(self, mock_get_kpis, mock_log_logger_debug):
        response = Mock()
        response.json.return_value = [{u'kpiName': u'Total_UL_PDCP_Cell_Throughput', u'numberOfNodes': u'N/A',
                                       u'indexValue': None, u'breachedKpiGroupName': None,
                                       u'kpiUnit': u'MEGA_BITS_PER_SECOND',
                                       u'measurementOn': [u'EUtranCellTDD', u'EUtranCellFDD'], u'indexLabel': None,
                                       u'thresholdValue': u'N/A', u'poIDs': []}]
        mock_get_kpis.return_value = response
        response = Mock(status_code=200, ok=True)
        self.user.post.return_value = response
        _nodes_breached_node_view(self.nodes_breached, '1')

        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui._nodes_breached_node_view_perform_main_request')
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @patch('enmutils_int.lib.nhm_ui.NodesBreached.get_kpis')
    def test_nodes_breached_node_view_no_kpis_return_value_success(self, mock_get_kpis, mock_log_logger_debug, _):
        mock_get_kpis.return_value = None
        response = Mock(status_code=200, ok=True)
        self.user.post.return_value = response
        _nodes_breached_node_view(self.nodes_breached, '1')
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @responses.activate
    def test_nodes_breached_node_view_no_network_scope_success(self, mock_log_logger_debug):
        self.nodes_breached.network_scope = None

        _nodes_breached_node_view(self.nodes_breached, '1')
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @patch('enmutils_int.lib.nhm_ui._multi_node_health_monitor_page')
    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    def test_network_operational_state_flow_success(self, mock_nhm_landing_page_flow, mock_node_health_monitor_page, mock_log_logger_debug):
        data = [{u'neType': u'ERBS', u'counts': [{u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_DISABLED', u'name': u'DISABLED'}, {u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_MIXED', u'name': u'MIXED'}, {u'count': 40, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_ENABLED', u'name': u'ENABLED'}, {u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_NA', u'name': u'NA'}], u'neCount': 40, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL', u'technologyDomain': u'LTE'}]
        response = Mock(status_code=200, ok=True)
        response.json.return_value = data
        self.user.post.return_value = response
        network_operational_state_flow(widget=self.worst_performing, scope=str(time.time()).replace(".", ""))

        self.assertTrue(mock_nhm_landing_page_flow.called)
        self.assertTrue(mock_node_health_monitor_page.called)
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_network_operational_state_flow__empty_response(self, mock_log, _):
        data = []
        response = Mock(status_code=200, ok=True)
        response.json.return_value = data
        self.user.post.return_value = response
        network_operational_state_flow(widget=self.worst_performing, scope=str(time.time()).replace(".", ""))
        self.assertEqual(mock_log.call_count, 1)
        mock_log.assert_called_with("Starting Network Operational State flow")

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @patch('enmutils_int.lib.nhm_ui._multi_node_health_monitor_page')
    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    def test_network_operational_state_flow_response_http_error(self, mock_nhm_landing_page_flow,
                                                                mock_node_health_monitor_page, mock_log_logger_debug):
        data = [{u'neType': u'ERBS', u'counts': [{u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_DISABLED', u'name': u'DISABLED'}, {u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_MIXED', u'name': u'MIXED'}, {u'count': 40, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_ENABLED', u'name': u'ENABLED'}, {u'count': 0, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL_NA', u'name': u'NA'}], u'neCount': 40, u'scopeId': u'networkhealthmonitor:networkscope.1512472364.69.680000000_ERBS_EPS_OPERATIONAL', u'technologyDomain': u'LTE'}]
        response = Mock(status_code=500, ok=False)
        response.json.return_value = data
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response
        self.assertRaises(HTTPError, network_operational_state_flow, widget=self.worst_performing,
                          scope=str(time.time()).replace(".", ""))

        self.assertTrue(mock_nhm_landing_page_flow.called)
        self.assertFalse(mock_node_health_monitor_page.called)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @patch('requests.models.Response.raise_for_status')
    @patch('enmutils_int.lib.nhm_ui._multi_node_health_monitor_page')
    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    @responses.activate
    def test_network_operational_state_flow_response_no_network_scope(self, mock_nhm_landing_page_flow,
                                                                      mock_node_health_monitor_page,
                                                                      mock_raise_for_status,
                                                                      mock_log_logger_debug):
        self.worst_performing.network_scope = None
        network_operational_state_flow(widget=self.worst_performing, scope=str(time.time()).replace(".", ""))

        self.assertTrue(mock_nhm_landing_page_flow.called)
        self.assertFalse(mock_node_health_monitor_page.called)
        self.assertFalse(mock_raise_for_status.called)
        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch('enmutils_int.lib.nhm_ui._worst_performing_node_page')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_landing_page')
    @responses.activate
    def test_worst_performing_flow_success(self, mock_worst_performing_landing_page,
                                           mock_worst_performing_node_page):
        response = Mock()
        response.return_value = [
            {u'neType': u'ERBS', u'poID': 281474977228574, u'name': u'ieatnetsimv7004-17_LTE31ERBS00068', u'rank': 1,
             u'kpiValue': 0.0},
            {u'neType': u'ERBS', u'poID': 281474977241057, u'name': u'ieatnetsimv7004-17_LTE31ERBS00017', u'rank': 1,
             u'kpiValue': 0.0}]
        response.status_code = 200
        mock_worst_performing_landing_page.return_value = response

        worst_performing_flow(self.worst_performing)

        self.assertTrue(mock_worst_performing_landing_page.called)
        self.assertTrue(mock_worst_performing_node_page.called)

    @patch('enmutils_int.lib.nhm_ui.log.logger')
    @patch('enmutils_int.lib.nhm_ui.WorstPerforming.get_kpi_with_results')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_node_page')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_landing_page')
    @responses.activate
    def test_worst_performing_flow_http_error(self, mock_worst_performing_landing_page, mock_worst_performing_node_page,
                                              mock_get_kpi_with_results, mock_logger):
        response = Mock()
        response.return_value = []
        response.json.return_value = []
        response.status_code = 200
        mock_worst_performing_landing_page.return_value = response
        mock_get_kpi_with_results.return_value = "new kpi name"

        worst_performing_flow(self.worst_performing)

        self.assertTrue(mock_worst_performing_landing_page.called)
        self.assertTrue(mock_get_kpi_with_results.called)
        self.assertTrue(mock_logger.info.called)
        self.assertFalse(mock_worst_performing_node_page.called)

    @patch('enmutils_int.lib.nhm_ui.log.logger')
    @patch('enmutils_int.lib.nhm_ui.WorstPerforming.get_kpi_with_results')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_node_page')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_landing_page')
    @responses.activate
    def test_worst_performing_flow_no_response(self, mock_worst_performing_landing_page, mock_worst_performing_node_page,
                                               mock_get_kpi_with_results, mock_logger):
        response = None
        mock_worst_performing_landing_page.return_value = response
        mock_get_kpi_with_results.return_value = "new kpi name"

        worst_performing_flow(self.worst_performing)

        self.assertTrue(mock_worst_performing_landing_page.called)
        self.assertTrue(mock_logger.debug.called)
        self.assertFalse(mock_get_kpi_with_results.called)
        self.assertFalse(mock_worst_performing_node_page.called)

    @patch("enmutils.lib.shell.Response.json")
    @patch('enmutils_int.lib.nhm_ui.WorstPerforming.get_kpi_with_results')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_node_page')
    @patch('enmutils_int.lib.nhm_ui._worst_performing_landing_page')
    @responses.activate
    def test_worst_performing_flow_raise_for_status(self, mock_worst_performing_landing_page, mock_worst_performing_node_page,
                                                    mock_get_kpi_with_results, mock_response_json):
        response = Mock(return_value=[], status_code=500)
        response.json.return_value = []
        mock_worst_performing_landing_page.return_value = response
        mock_get_kpi_with_results.return_value = "new kpi name"

        mock_response_json.return_value = {}

        worst_performing_flow(self.worst_performing)

        self.assertTrue(mock_worst_performing_landing_page.called)
        self.assertFalse(mock_get_kpi_with_results.called)
        self.assertFalse(mock_worst_performing_node_page.called)

    def test_worst_performing_landing_page_no_kpi_index_success(self):
        response = Mock(status_code=200, ok=True)
        self.user.get.return_value = response
        _worst_performing_landing_page(self.worst_performing)
        self.assertEqual(0, response.raise_for_status.call_count)

    def test_worst_performing_landing_page_with_kpi_index_success(self):
        self.worst_performing.kpi_name = "Average_DRB_Latency"
        self.worst_performing.widget_kpi = {'name': 'Average_DRB_Latency'}
        response = Mock(status_code=200, ok=True)
        self.user.get.return_value = response
        _worst_performing_landing_page(self.worst_performing)
        self.assertEqual(0, response.raise_for_status.call_count)

    def test_worst_performing_landing_page_with_no_network_scope(self):
        self.worst_performing.widget_kpi = ""
        response = Mock(status_code=200, ok=True)
        self.user.get.return_value = response
        _worst_performing_landing_page(self.worst_performing)
        self.assertEqual(0, response.raise_for_status.call_count)

    def test_worst_performing_landing_page_with_kpi_index_raises_http_error(self):
        self.worst_performing.kpi_name = "Highest Average"
        self.worst_performing.widget_kpi = {'name': 'Highest Average'}
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, _worst_performing_landing_page, self.worst_performing)
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.nhm_ui.nhm_landing_page_flow')
    @responses.activate
    def test_network_status_landing_page_success(self, mock_nhm_landing_page_flow):
        responses.add(responses.GET,
                      URL + "/oss/nhm/kpi/cellstatus/{poid}?kpi={kpi_name}".format(poid=self.nodes[0].poid,
                                                                                   kpi_name='Average_UE_PDCP_DL_Throughput'),
                      json={},
                      status=200,
                      match_querystring=True,
                      content_type='application/json')

        responses.add(responses.POST, URL + "/network-status-rest-service/networkstatus/stateCount/{0}"
                      .format(self.nodes_breached.network_scope),
                      json={},
                      status=200,
                      content_type='application/json')
        _network_status_landing_page(self.nodes_breached)

        self.assertTrue(mock_nhm_landing_page_flow.called)

    def test_nodemonitor_poid_success(self):
        response = Mock(status_code=200, ok=True)
        self.user.get.return_value = response
        _nodemonitor_poid(widget=self.cell_status)
        self.assertEqual(0, response.raise_for_status.call_count)

    def test_nodemonitor_poid_raises_http_error(self):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, _nodemonitor_poid, widget=self.cell_status)
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.NhmWidget.create')
    @responses.activate
    def test_create_widgets_taskset_success(self, mock_nhmwidget_create, mock_time_sleep):
        create_widgets_taskset(self.widgets)

        self.assertEqual(mock_nhmwidget_create.call_count, len(self.widgets))
        self.assertEqual(mock_time_sleep.call_count, len(self.widgets) + 1)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.cell_status_flow')
    @patch('enmutils_int.lib.nhm_ui.poll_alarm_widget')
    @patch('enmutils_int.lib.nhm_ui.worst_performing_flow')
    @patch('enmutils_int.lib.nhm_ui.network_operational_state_flow')
    @patch('enmutils_int.lib.nhm_ui.nodes_breached_flow')
    @responses.activate
    def test_nhm_widget_flows_success(self, mock_nodes_breached_flow, mock_network_operational_state_flow,
                                      mock_worst_performing_flow, mock_poll_alarm_widget, mock_cell_status_flow, *_):
        nhm_widget_flows(self.widgets, len(self.widgets))

        self.assertTrue(mock_nodes_breached_flow.called)
        self.assertTrue(mock_network_operational_state_flow.called)
        self.assertTrue(mock_worst_performing_flow.called)
        self.assertTrue(mock_poll_alarm_widget.called)
        self.assertTrue(mock_cell_status_flow.called)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    def test_nhm_widget_flows__retry_on_type_error(self, _):
        self.assertRaises(TypeError, nhm_widget_flows, 2)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.randint', side_effect=TypeError)
    def test_call_widget_flow__retry_on_type_error(self, *_):
        self.assertRaises(TypeError, call_widget_flow, self.widgets[0])

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.cell_status_flow')
    @patch('enmutils_int.lib.nhm_ui.poll_alarm_widget')
    @patch('enmutils_int.lib.nhm_ui.worst_performing_flow')
    @patch('enmutils_int.lib.nhm_ui.network_operational_state_flow')
    @patch('enmutils_int.lib.nhm_ui.nodes_breached_flow')
    @responses.activate
    def test_call_widget_flow__success(self, mock_nodes_breached_flow, mock_network_operational_state_flow,
                                       mock_worst_performing_flow, mock_poll_alarm_widget, mock_cell_status_flow, *_):
        for widget in self.widgets:
            call_widget_flow(widget)

        self.assertEqual(1, mock_nodes_breached_flow.call_count)
        self.assertEqual(1, mock_network_operational_state_flow.call_count)
        self.assertEqual(1, mock_worst_performing_flow.call_count)
        self.assertEqual(1, mock_poll_alarm_widget.call_count)
        self.assertEqual(1, mock_cell_status_flow.call_count)

    @patch('enmutils_int.lib.nhm_ui._nodes_breached_home')
    @patch('enmutils_int.lib.nhm_ui._nodes_breached_node_view')
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @responses.activate
    def test_nodes_breached_flow_success(self, mock_log_logger_debug, mock_nodes_breached_node_view, mock_nodes_breached_home):
        nodes_breached_flow(self.widgets[0], '111')

        self.assertTrue(mock_log_logger_debug.called)
        self.assertTrue(mock_nodes_breached_node_view.called)
        self.assertTrue(mock_nodes_breached_home)

    @patch('enmutils_int.lib.nhm_ui._cell_status_page')
    @patch('enmutils_int.lib.nhm_ui._multi_node_health_monitor_page')
    @patch('enmutils_int.lib.nhm_ui._network_status_landing_page')
    @responses.activate
    def test_cell_status_flow_success(self, mock_network_status_landing_page, mock_multi_node_health_monitor_page,
                                      mock_cell_status_page):
        cell_status_flow(self.widgets[0])

        self.assertTrue(mock_network_status_landing_page.called)
        self.assertTrue(mock_multi_node_health_monitor_page.called)
        self.assertTrue(mock_cell_status_page.called)

    def test_nhm_landing_page_flow_sucess(self):
        data = [{u'Success': u'true'}]
        response = Mock(status_code=200, ok=True)
        response.json.return_value = data
        self.user.get.return_value = response
        nhm_landing_page_flow(self.user)

    @patch('enmutils_int.lib.nhm_ui._common_kpi_loading_endpoints')
    @patch('enmutils_int.lib.nhm_ui._nodemonitor_poid')
    @responses.activate
    def test_worst_performing_node_page(self, mock_nodemonitor_poid, mock_comon_kpi_loading_endpoints):
        response = Mock()
        response.json.return_value = [
            {u'neType': u'ERBS', u'poID': 281474977228574, u'name': u'ieatnetsimv7004-17_LTE31ERBS00068', u'rank': 1,
             u'kpiValue': 0.0},
            {u'neType': u'ERBS', u'poID': 281474977241057, u'name': u'ieatnetsimv7004-17_LTE31ERBS00017', u'rank': 1,
             u'kpiValue': 0.0}]
        responses.add(responses.POST, URL + "/network-status-rest-service/networkstatus/state/{scope_id}".format(scope_id=self.worst_performing.network_scope),
                      json={},
                      status=200,
                      content_type='application/json')
        _worst_performing_node_page(self.worst_performing, response)
        self.assertTrue(mock_nodemonitor_poid.called)
        self.assertTrue(mock_comon_kpi_loading_endpoints.called)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    @responses.activate
    def test_multi_node_health_monitor_page__no_network_scope(self, mock_log_logger_debug, *_):
        self.cell_status.network_scope = ''

        _multi_node_health_monitor_page(self.cell_status)

        mock_log_logger_debug.assert_called_with("No network scope found for this widget")

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_multi_node_health_monitor_page__success(self, mock_log_logger_debug, *_):
        mock_widget = Mock()
        mock_widget.network_scope = 'network_scope.23412423423.2434000420'
        mock_widget.poids = [4234234200420]
        mock_widget.get_kpi_names.return_value = ["some kpi"]
        mock_widget.user = Mock()

        _multi_node_health_monitor_page(mock_widget)

        self.assertEqual(mock_log_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_multi_node_health_monitor_page__when_no_kpi(self, mock_log_logger_debug, *_):
        mock_widget = Mock()
        mock_widget.network_scope = 'network_scope.23412423423.2434000420'
        mock_widget.poids = [4234234200420]
        mock_widget.get_kpi_names.return_value = []
        mock_widget.user = Mock()

        _multi_node_health_monitor_page(mock_widget)

        self.assertEqual(mock_log_logger_debug.call_count, 2)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_multi_node_health_monitor_page__retries_on_http_error(self, *_):
        mock_widget = Mock()
        mock_widget.network_scope = 'network_scope.23412423423.2434000420'
        mock_widget.get_kpi_names.side_effect = [HTTPError, "some kpi"]
        mock_widget.poids = [4234234200420]

        self.assertRaises(HTTPError, _multi_node_health_monitor_page(mock_widget))
        self.assertEqual(2, mock_widget.get_kpi_names.call_count)

    @patch('enmutils_int.lib.nhm_ui._common_kpi_loading_endpoints')
    @patch('enmutils_int.lib.nhm_ui._nodemonitor_poid')
    def test_cell_status_page_success(self, mock_nodemonitor_poid, mock_common_kpi_loading_endpoints):
        mock_widget = Mock(widget_kpi=self.cell_status.widget_kpi)
        mock_user = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_user.get.return_value = mock_response
        mock_user.post.return_value = mock_response
        mock_widget.user = mock_user
        _cell_status_page(widget=mock_widget)

        self.assertTrue(mock_common_kpi_loading_endpoints.called)
        self.assertTrue(mock_nodemonitor_poid.called)
        self.assertFalse(mock_response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui._common_kpi_loading_endpoints')
    @patch('enmutils_int.lib.nhm_ui._nodemonitor_poid')
    def test_cell_status_page_raise_get_http_error(self, mock_nodemonitor_poid, mock_common_kpi_loading_endpoints):
        mock_widget = Mock(widget_kpi=self.cell_status.widget_kpi)
        mock_user = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_user.get.return_value = mock_response
        mock_widget.user = mock_user

        _cell_status_page(widget=mock_widget)

        self.assertTrue(mock_common_kpi_loading_endpoints.called)
        self.assertTrue(mock_nodemonitor_poid.called)
        self.assertTrue(mock_response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui._common_kpi_loading_endpoints')
    @patch('enmutils_int.lib.nhm_ui._nodemonitor_poid')
    def test_cell_status_page_raise_post_http_error(self, mock_nodemonitor_poid, mock_common_kpi_loading_endpoints):
        mock_widget = Mock(widget_kpi=self.cell_status.widget_kpi)
        mock_user = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_user.post.return_value = mock_response
        mock_widget.user = mock_user

        _cell_status_page(widget=mock_widget)

        self.assertTrue(mock_common_kpi_loading_endpoints.called)
        self.assertTrue(mock_nodemonitor_poid.called)
        self.assertTrue(mock_response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_nodes_breached_node_view_perform_main_request__succes(self, *_):
        kpis = [{"numberOfNodes": 5, "kpiName": "some kpi", "measurementOn": "Nodes", "kpiUnit": "some unit"}]
        mock_kpis = Mock()
        mock_kpis.json.return_value = kpis
        mock_widget = Mock()
        mock_widget.network_scope = "some_network_scope"
        mock_widget.node_poids = [423423423000420]
        mock_widget.user = Mock()
        mock_widget.get_kpi_names.return_value = kpis
        mock_network_scope_response = Mock()
        mock_network_scope_response.status_code = 200
        mock_random_scope_id = "scope.4242342.423000420"
        _nodes_breached_node_view_perform_main_request(mock_kpis, mock_widget, mock_random_scope_id,
                                                       mock_network_scope_response)

        self.assertFalse(mock_network_scope_response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui.time.sleep', return_value=0)
    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_nodes_breached_node_view_perform_main_request__http_error(self, *_):
        kpis = [{"numberOfNodes": 5, "kpiName": "some kpi", "measurementOn": "Nodes", "kpiUnit": "some unit"}]
        mock_kpis = Mock()
        mock_kpis.json.return_value = kpis
        mock_widget = Mock()
        mock_widget.network_scope = "some_network_scope"
        mock_widget.node_poids = [423423423000420]
        mock_widget.user = Mock()
        mock_widget.get_kpi_names.return_value = kpis
        mock_network_scope_response = Mock()
        mock_network_scope_response.status_code = 500
        mock_random_scope_id = "scope.4242342.423000420"
        _nodes_breached_node_view_perform_main_request(mock_kpis, mock_widget, mock_random_scope_id,
                                                       mock_network_scope_response)

        self.assertTrue(mock_network_scope_response.raise_for_status.called)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_common_kpi_loading_endpoints__success(self, mock_debug):
        user = Mock()
        widget = Mock(widget_kpi={'name': "Widget"}, headers_dict={}, network_scope=0.001, user=user)
        _common_kpi_loading_endpoints(widget, '1234')
        self.assertEqual(0, mock_debug.call_count)
        self.assertEqual(2, user.post.call_count)
        self.assertEqual(1, user.get.call_count)

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_common_kpi_loading_endpoints__no_widget_name(self, mock_debug):
        user = Mock()
        widget = Mock(widget_kpi={"key": "value"}, headers_dict={}, network_scope=0.001, user=user)
        _common_kpi_loading_endpoints(widget, '1234')
        self.assertEqual(0, user.post.call_count)
        self.assertEqual(0, user.get.call_count)
        mock_debug.assert_called_with("No KPI found to load the info into the widget: {0}".format(widget))

    @patch('enmutils_int.lib.nhm_ui.log.logger.debug')
    def test_common_kpi_loading_endpoints__no_widget_kpi(self, mock_debug):
        user = Mock()
        widget = Mock(widget_kpi={}, headers_dict={}, network_scope=0.001, user=user)
        self.assertEqual(0, user.post.call_count)
        self.assertEqual(0, user.get.call_count)
        _common_kpi_loading_endpoints(widget, "1235")
        mock_debug.assert_called_with("WARNING: Wrong values found: widget: {0}, poid: 1235, widget.widget_kpi: "
                                      "{1}".format(widget, widget.widget_kpi))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
