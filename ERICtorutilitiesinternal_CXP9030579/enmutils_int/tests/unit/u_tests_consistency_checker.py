#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.bin.consistency import (_validate_arguments, _display_available_nodes,
                                          _print_pool_consistency_results, _show_nodes, _retrieve_available_nodes)
from enmutils_int.lib.consistency_checker import ConsistencyChecker
from testslib import unit_test_utils


class ConsistencyLibUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.checker = ConsistencyChecker()
        self.enm_resp = [u"FDN : NetworkElement=netsim_LTE08ERBS00001", u"FDN : NetworkElement=netsim_LTE08ERBS00002",
                         u"FDN : NetworkElement=netsim_LTE08ERBS00003", u"FDN : NetworkElement=netsim_LTE08ERBS00004",
                         u"FDN : NetworkElement=netsim_LTE08ERBS00005", u"FDN : NetworkElement=netsim_LTE08ERBS00006",
                         u"FDN : NetworkElement=netsim_LTE08ERBS00007", u"FDN : NetworkElement=netsim_LTE08ERBS00008",
                         u"FDN : NetworkElement=netsim_LTE08ERBS00009", u"FDN : NetworkElement=netsim_LTE08ERBS000010"]

        self.enm_nodes = [Mock(node_id="netsim_LTE08ERBS00001", profiles=['Test1'], primary_type='ERBS'),
                          Mock(node_id="netsim_LTE08ERBS00002", profiles=['Test1'], primary_type='ERBS'),
                          Mock(node_id="netsim_LTE08ERBS00003", profiles=['Test1'], primary_type='ERBS'),
                          Mock(node_id="netsim_LTE08ERBS00004", profiles=[], primary_type='ERBS'),
                          Mock(node_id="netsim_LTE08ERBS00005", profiles=[], primary_type='ERBS'),
                          Mock(node_id="netsim_LTE08ERBS00006", profiles=['Test1', 'Test2'], primary_type='MGW'),
                          Mock(node_id="netsim_LTE08ERBS00007", profiles=['Test1'], primary_type='MGW'),
                          Mock(node_id="netsim_LTE08ERBS00008", profiles=[], primary_type='MGW'),
                          Mock(node_id="netsim_LTE08ERBS00009", profiles=[], primary_type='MGW'),
                          Mock(node_id="netsim_LTE08ERBS000010", profiles=[], primary_type='MGW')]

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_enm_nodes_list_raises_enm_application_error(self):
        self.user.enm_execute.return_value = None
        self.assertRaises(EnmApplicationError, self.checker.get_enm_nodes_list, self.user)

    def test_get_enm_nodes_list(self):
        response = Mock()
        response.get_output.return_value = self.enm_resp
        self.user.enm_execute_mock.return_value = response
        self.checker.get_enm_nodes_list(self.user)

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.get_enm_nodes_list')
    def test_filter_nodes_from_response(self, mock_get_enm_nodes_list):
        mock_get_enm_nodes_list.return_value = self.enm_resp
        self.assertEqual(10, len(self.checker.filter_enm_nodes_list()))

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.filter_enm_nodes_list')
    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_pool_is_consistent_with_enm_returns_nodes_not_on_enm(self, mock_get_pool, mock_filter_enm_nodes_list):
        mock_get_pool.return_value = self.enm_nodes
        mock_filter_enm_nodes_list.return_value = [node.node_id for node in self.enm_nodes[0:8]]
        for node in self.enm_nodes[8:]:
            self.assertIn(node.node_id, self.checker.pool_is_consistent_with_enm())
        self.assertEqual(2, len(self.checker.pool_is_consistent_with_enm()))

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.filter_enm_nodes_list')
    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_pool_is_consistent_with_enm_returns_zero_when_nodes_on_enm_and_empty_pool(self, mock_get_pool,
                                                                                       mock_filter_enm_nodes_list):
        mock_get_pool.return_value = []
        mock_filter_enm_nodes_list.return_value = [node.node_id for node in self.enm_nodes[0:8]]
        self.assertEqual(0, len(self.checker.pool_is_consistent_with_enm()))

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.filter_enm_nodes_list')
    @patch('enmutils_int.lib.consistency_checker.log.logger.debug')
    def test_pool_is_consistent_with_enm_catches_empty_set(self, mock_debug, *_):
        self.checker.pool_is_consistent_with_enm()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.filter_enm_nodes_list')
    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_pool_is_consistent_with_enm(self, mock_get_pool, mock_filter_enm_nodes_list):
        mock_get_pool.return_value = self.enm_nodes
        mock_filter_enm_nodes_list.return_value = [node.node_id for node in self.enm_nodes]
        self.assertTrue(len(self.checker.pool_is_consistent_with_enm()) is 0)

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.filter_enm_nodes_list')
    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_enm_is_consistent_with_pool(self, mock_get_pool, mock_filter_enm_nodes_list):
        mock_get_pool.return_value = self.enm_nodes
        mock_filter_enm_nodes_list.return_value = {node.node_id for node in self.enm_nodes[0:8]}
        self.assertTrue(len(self.checker.enm_is_consistent_with_pool()) is 0)

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_get_all_unused_nodes(self, mock_get_pool):
        mock_get_pool.return_value = self.enm_nodes
        self.assertEqual(5, len(self.checker.get_all_unused_nodes()))

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_get_all_unused_nodes_by_type(self, mock_get_pool):
        mock_get_pool.return_value = self.enm_nodes
        self.assertEqual(3, len(self.checker.get_all_unused_nodes(netype='MGW')))

    @patch('enmutils_int.lib.consistency_checker.ConsistencyChecker.all_nodes', new_callable=PropertyMock)
    def test_pool_dict__is_successful(self, mock_get_pool):
        mock_node_list = [Mock(node_id="netsim_LTE08ERBS00001", profiles=['Test1'], primary_type='ERBS')]
        mock_get_pool.return_value = mock_node_list
        self.assertEqual(self.checker.pool_dict, {'ERBS': mock_node_list})


class ConsistencyToolUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_validate_arguments__splits_node_types(self):
        arguments = {"NODE_TYPES": "ERBS,MGW"}
        self.assertListEqual(["ERBS", "MGW"], _validate_arguments(arguments=arguments))

    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_show_nodes__displays_nodes_missing_enm(self, mock_info):
        node, node1 = Mock(), Mock()
        node.node_id = "Node"
        node1.node_id = "Node1"
        _show_nodes([node, node1])
        mock_info.assert_called_with("['Node', 'Node1']")

    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_show_nodes__displays_nodes_missing_workload_pool(self, mock_info):
        node, node1 = Mock(), Mock()
        node.node_id = "Node"
        node1.node_id = "Node1"
        _show_nodes(set(["Node", "Node1"]))
        mock_info.assert_called_with("['Node', 'Node1']")

    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_show_nodes__cannot_determine_node_ids(self, mock_info):
        node, node1 = Mock(), Mock()
        node.node_id = "Node"
        node1.node_id = "Node1"
        _show_nodes(["Node", "Node1"])
        mock_info.assert_called_with("Could not determine node ids.")

    @patch('enmutils_int.bin.consistency.ConsistencyChecker.pool_is_consistent_with_enm', return_value=[])
    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_print_pool_consistency_results__pool_is_consistent(self, mock_info, _):
        _print_pool_consistency_results()
        mock_info.assert_called_with("Pool consistency check passed, no missing nodes on deployment.")

    @patch('enmutils_int.bin.consistency.ConsistencyChecker.pool_is_consistent_with_enm', return_value=["Node"])
    @patch('enmutils_int.bin.consistency._show_nodes')
    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_print_pool_consistency_results__show_nodes(self, mock_info, mock_show_nodes, _):
        _print_pool_consistency_results(show_nodes=True)
        mock_info.assert_called_with('The following nodes do not exist in ENM but are in the workload pool:\nNumber: 1')
        self.assertEqual(1, mock_show_nodes.call_count)

    @patch('enmutils_int.bin.consistency.ConsistencyChecker.enm_is_consistent_with_pool', return_value=["Node"])
    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_print_pool_consistency_results__enm_check(self, mock_info, _):
        _print_pool_consistency_results(enm=True)
        mock_info.assert_called_with('The following nodes do not exist in the workload pool but are available on '
                                     'ENM:\nNumber: 1')

    @patch('enmutils_int.bin.consistency.ConsistencyChecker.get_all_unused_nodes', side_effect=[["Node"]])
    def test_retrieve_available_nodes__success(self, mock_get_all):
        _retrieve_available_nodes()
        self.assertEqual(1, mock_get_all.call_count)

    @patch('enmutils_int.bin.consistency.ConsistencyChecker.get_all_unused_nodes', side_effect=[["Node"], []])
    def test_retrieve_available_nodes__node_types(self, mock_get_all):
        _retrieve_available_nodes(node_types=["ERBS", "MGW"])
        self.assertEqual(2, mock_get_all.call_count)

    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_display_available_nodes__success(self, mock_info):
        node = Mock()
        node.primary_type = "ERBS"
        _display_available_nodes([node])
        mock_info.assert_called_with("Total available ERBS nodes: 1")

    @patch('enmutils_int.bin.consistency._show_nodes')
    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_display_available_nodes__show_nodes(self, mock_info, mock_show_nodes):
        node = Mock()
        node.primary_type = "ERBS"
        _display_available_nodes([node], show_nodes=True)
        mock_info.assert_called_with("Total available ERBS nodes: 1")
        self.assertEqual(1, mock_show_nodes.call_count)

    @patch('enmutils_int.bin.consistency.log.logger.info')
    def test_display_available_nodes__no_nodes(self, mock_info):
        _display_available_nodes([])
        mock_info.assert_called_with("No available nodes discovered.")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
