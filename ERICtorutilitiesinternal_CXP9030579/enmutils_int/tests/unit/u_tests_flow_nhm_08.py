#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils

from enmutils.lib.enm_node import ERBSNode
from enmutils_int.lib.nhm_widget import MostProblematic, CellStatus
from enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow import Nhm08, create_widgets_taskset, taskset


class Nhm08UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm08()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', 'some_ip_1', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', 'some_ip_2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.nodes[0].poid = "281474977292253"
        self.nodes[1].poid = "181474977292251"
        self.flow.TOTAL_NODES = 2
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']
        self.flow.NUM_ADMINS = 1
        self.flow.NUM_OPERATORS = 1
        self.flow.NUM_USERS = 2
        self.flow.ADMIN_ROLE = ["NHM_Administrator"]
        self.flow.OPERATOR_ROLE = ["NHM_Operator"]
        self.flow.SCHEDULE_SLEEP = 2
        self.flow.widget_cell = CellStatus(user=self.user, nodes=self.nodes)
        self.flow.widget_cell.widget_kpi = {u'name': u'Average_UE_PDCP_DL_Throughput', u'kpiActivation': {u'active': True, u'threshold': {u'thresholdDomain': None, u'thresholdValue': None}, u'poidList': [281474977614391], u'nodeCount': 1}, u'lastModifiedBy': u'NHM_01_1018-13010228_u0', u'kpiModel': {u'kpiFormulaList': [{u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'ERBS', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellFDD'}]}}, {u'neType': u'RadioNode', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellFDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellFDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'replacements': None, u'operands': [{u'replacements': None, u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'replacements': None, u'operands': [{u'operator': u'SUBTRACTION', u'replacements': None, u'operands': [{u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'replacements': None, u'operands': [{u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'replacements': None, u'operands': None, u'value': 1000.0}]}]}], u'setVariables': None}], u'iterationSet': {u'indices': None, u'var': {u'index': None, u'replacements': None, u'name': u'INPUT', u'operands': None, u'key': None, u'extract': None}, u'pmCounter': None}, u'setVariables': []}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}, {u'formulaTypeInfoList': [{u'neType': u'MSRBS_V1', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'MSRBS_V1_eNodeBFunction', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'ERBS', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'ERBS_NODE_MODEL', u'name': u'EUtranCellTDD'}]}}, {u'neType': u'RadioNode', u'reportingObjectNs': None, u'neVersion': None, u'reportingObjectType': u'EUtranCellTDD', u'inputData': {u'inputScope': u'OBJECTS_FOR_TARGET', u'inputResourceMap': {u'INPUT': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}, u'computationInput': [{u'ns': u'Lrat', u'name': u'EUtranCellTDD'}]}}], u'computation': {u'abstractFormulaOperand': {u'varName': u'theRO', u'replacements': None, u'operands': [{u'replacements': None, u'reportingInstructions': {u'reportingObjectIdSource': u'theRO', u'customKvPairMap': None}, u'operands': [{u'operator': u'DIVISION', u'replacements': None, u'operands': [{u'operator': u'SUBTRACTION', u'replacements': None, u'operands': [{u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrb', u'counterRef': u'pmPdcpVolDlDrb', u'extract': None}, {u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmPdcpVolDlDrbLastTTI', u'counterRef': u'pmPdcpVolDlDrbLastTTI', u'extract': None}]}, {u'operator': u'DIVISION', u'replacements': None, u'operands': [{u'index': None, u'replacements': None, u'operands': None, u'on': u'theRO', u'piName': u'pmUeThpTimeDl', u'counterRef': u'pmUeThpTimeDl', u'extract': None}, {u'replacements': None, u'operands': None, u'value': 1000.0}]}]}], u'setVariables': None}], u'iterationSet': {u'indices': None, u'var': {u'index': None, u'replacements': None, u'name': u'INPUT', u'operands': None, u'key': None, u'extract': None}, u'pmCounter': None}, u'setVariables': []}, u'preComputation': None}, u'neTypes': [u'ERBS', u'MSRBS_V1', u'RadioNode']}], u'namespace': u'global', u'categorySet': [u'Integrity'], u'version': None, u'createdBy': u'Ericsson', u'createdDate': u'20170330000000', u'modelCreationType': u'DESIGNED', u'unit': u'KILO_BITS_PER_SECOND'}, u'lastModifiedTime': u'20171018130422231', u'allNeTypes': [u'MSRBS_V1', u'ERBS', u'RadioNode'], u'description': u'While eMBMS traffic does not directly impact the DL throughput metrics which cover non-eMBMS traffic, there may be some interaction / impact as the eMBMS traffic may cause fewer available PRB and extra scheduling delay for the non-eMBMS traffic and result in a consequential reduction in average throughput. The reduction in throughput will be approximately in the ratio of pmPrbAvailDlMbms / pmPrbAvailDl.'}
        self.flow.widget_cell.node_poids[0] = self.nodes[0].poid
        self.flow.widget_cell.node_poids[1] = self.nodes[1].poid
        self.flow.widget_cell.poid = "0"

        self.flow.widget_most = MostProblematic(user=self.user, nodes=self.nodes)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.NhmWidget.create")
    def test_create_widgets_taskset(self, mock_create, mock_sleep):

        create_widgets_taskset([self.flow.widget_cell, self.flow.widget_most], self.flow)

        self.assertTrue(mock_create.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.time.sleep')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.NhmWidget.create")
    def test_create_widgets_taskset_raises_exception(self, mock_create, mock_sleep, mock_add_error_as_exception):

        mock_create.side_effect = Exception
        create_widgets_taskset([self.flow.widget_cell, self.flow.widget_most], self.flow)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.wait_for_nhm_setup_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.sleep_until_profile_persisted")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.nhm_widget_flows')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.nhm_landing_page_flow')
    def test_taskset_cell_status(self, mock_nhm_landing_page_flow, mock_nhm_widget_flows, *_):

        taskset([self.flow.widget_most, self.flow.widget_cell], self.flow)

        self.assertTrue(mock_nhm_landing_page_flow.called)
        self.assertTrue(mock_nhm_widget_flows.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.wait_for_nhm_setup_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.nhm_widget_flows')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.nhm_landing_page_flow')
    def test_taskset_cell_status_raises_exception(self, mock_nhm_landing_page_flow, mock_nhm_widget_flows,
                                                  mock_add_error_as_exception, *_):

        mock_nhm_landing_page_flow.side_effect = Exception
        taskset([self.flow.widget_cell, self.flow.widget_most], self.flow)

        self.assertTrue(mock_add_error_as_exception.called)
        self.assertFalse(mock_nhm_widget_flows.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.wait_for_nhm_setup_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.create_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.NhmWidget.number_created_configured_widgets",
           return_value=1)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.state")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.process_thread_queue_errors",
           return_value=1)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.log.logger.debug")
    def test_flow_continues_with_errors(self, mock_debug, mock_get_allocated_nodes, *_):
        self.flow.TOTAL_NODES = 1
        self.flow.NAME = "NHM_08"
        mock_get_allocated_nodes.return_value = [Mock(poid=123), Mock(poid=456)]
        self.flow.execute_flow()
        mock_debug.assert_called_with("NHM_08 has encountered 1 thread queue exceptions. Please see log errors for "
                                      "more details")

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.wait_for_nhm_setup_profile")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.create_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.state")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.NhmWidget.number_created_configured_widgets")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.get_allocated_nodes")
    def test_flow_no_continues_with_errors(self, mock_get_allocated_nodes, mock_created_widgets, *_):
        mock_created_widgets.side_effect = [0, 1]
        self.flow.TOTAL_NODES = 1
        self.flow.NAME = "NHM_08"
        mock_get_allocated_nodes.return_value = [Mock(poid=123)]
        self.flow.execute_flow()
        self.assertEqual(2, mock_created_widgets.call_count)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.time.sleep", return_value=0.1)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.NhmWidget.number_created_configured_widgets')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.ThreadQueue.execute")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.get_allocated_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.create_users')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.wait_for_nhm_setup_profile")
    def test_flow_continues_no_widgets_created(self, mock_wait_for_setup_profile, mock_create_users,
                                               mock_allocated_nodes, mock_thread_queue,
                                               mock_created_configured_widgets, *_):
        mock_allocated_nodes.return_value = self.nodes
        mock_create_users.return_value = [self.user]
        mock_created_configured_widgets.side_effect = [0, 0, 1, 1]

        self.flow.execute_flow()

        self.assertEqual(mock_wait_for_setup_profile.call_count, 1)
        self.assertTrue(mock_created_configured_widgets.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_allocated_nodes.called)
        self.assertTrue(mock_thread_queue.called)
        self.assertEqual(mock_thread_queue.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
