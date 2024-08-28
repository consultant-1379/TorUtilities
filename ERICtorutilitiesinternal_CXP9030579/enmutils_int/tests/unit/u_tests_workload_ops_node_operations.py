#!/usr/bin/env python
import unittest2
from mock import patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils_int.lib import workload_ops_node_operations
from testslib import unit_test_utils


class WorkloadOpsNodeOperationsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._validate')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._execute_operation')
    def test_execute__calls_execute_operation(self, mock_execute_operation, mock_validate, _):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.execute()
        self.assertEqual(1, mock_execute_operation.call_count)
        self.assertEqual(1, mock_validate.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.set_file_path_and_numeric_range')
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation.set_file_path_and_numeric_range')
    def test_validate(self, mock_remove_range, mock_add_range, _):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op.nodes_file_path = "/tmp/test"
        remove_op._validate()
        self.assertEqual("all", remove_op.nodes_file_path)
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op._validate()
        self.assertEqual(0, mock_remove_range.call_count)
        self.assertEqual(1, mock_add_range.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.remove_all', side_effect=[False, True])
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.remove_nodes')
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils.lib.log.logger.error')
    def test_execute_operation_remove_all__uses_legacy(self, mock_error, mock_update_total, mock_service, *_):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op.nodes_file_path = "all"
        remove_op._execute_operation()
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(0, mock_update_total.call_count)
        remove_op._execute_operation()
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(2, mock_update_total.call_count)
        self.assertEqual(0, mock_service.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation.get_parsed_file_location',
           return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.remove_nodes')
    def test_execute_operation_remove_all__uses_service(self, mock_service, *_):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op.nodes_file_path = "all"
        remove_op._execute_operation()
        self.assertEqual(1, mock_service.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.remove', return_value=(["Node"], [], ["Node1"]))
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation.calculate_num_items', return_value=2)
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation._print_add_removed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.logger.error')
    def test_execute_operation_remove_allocated(self, mock_error, mock_print_failed, *_):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op._execute_operation()
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(0, mock_print_failed.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.remove', return_value=(["Node"], ["Node1"], []))
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation.calculate_num_items', return_value=2)
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation._print_add_removed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.logger.error')
    def test_execute_operation_remove_failed(self, mock_error, mock_print_failed, *_):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op._execute_operation()
        self.assertEqual(0, mock_error.call_count)
        self.assertEqual(1, mock_print_failed.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.RemoveNodesOperation.get_parsed_file_location',
           return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.os.path.join', return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.config.get_nodes_data_dir')
    @patch('enmutils_int.lib.workload_ops_node_operations.arguments.get_numeric_range', return_value=(1, 2))
    @patch('enmutils_int.lib.workload_ops_node_operations.filesystem.does_file_exist')
    def test_set_file_path_and_numeric_range(self, mock_does_file_exist, mock_get_range, *_):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all", "RANGE": "1-2"})
        remove_op.set_file_path_and_numeric_range()
        mock_does_file_exist.assert_called_with("path")
        mock_get_range.assert_called_with(remove_op.nodes_range)

    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.get_parsed_file_location',
           return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.os.path.join', return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.config.get_nodes_data_dir')
    @patch('enmutils_int.lib.workload_ops_node_operations.arguments.get_numeric_range')
    @patch('enmutils_int.lib.workload_ops_node_operations.filesystem.does_file_exist')
    def test_set_file_path_and_numeric_range_no_range(self, mock_does_file_exist, mock_get_range, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.set_file_path_and_numeric_range()
        mock_does_file_exist.assert_called_with("path")
        self.assertEqual(0, mock_get_range.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.get_parsed_file_location',
           return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.os.path.join', return_value="path")
    @patch('enmutils_int.lib.workload_ops_node_operations.config.get_nodes_data_dir')
    @patch('enmutils_int.lib.workload_ops_node_operations.filesystem.does_file_exist', return_value=False)
    def test_set_file_path_and_numeric_range_raises_runtime_error(self, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all", "RANGE": "1-2"})
        self.assertRaises(RuntimeError, add_op.set_file_path_and_numeric_range)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.filesystem.does_file_exist', side_effect=[True, False])
    def test_get_parsed_file_location__returns_enmutils_if_file_not_available_in_nssutils(self, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all", "RANGE": "1-2"})
        self.assertIn("enmutils", add_op.get_parsed_file_location())

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.filesystem.does_file_exist', side_effect=[True, True])
    def test_get_parsed_file_location__returns_nssutils_if_file_available_in_nssutils(self, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all", "RANGE": "1-2"})
        self.assertIn("nssutils", add_op.get_parsed_file_location())

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    def test_calculate_num_items(self, _):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        self.assertEqual(add_op.calculate_num_items(["Node"] * 4, ["Node"] * 4), 8)
        add_op.range_end = 10
        add_op.range_start = 1
        self.assertEqual(add_op.calculate_num_items(["Node"] * 4, ["Node"] * 4), 10)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.log.cyan_text')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.purple_text')
    def test_print_add_removed_summary(self, mock_purple, mock_cyan, _):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op.deleted = ["Node1", "Node2"]
        remove_op.total_nodes = 2
        remove_op._print_add_removed_summary(10)
        mock_purple.assert_called_with("\nNODE MANAGER SUMMARY\n--------------------\n")
        mock_cyan.assert_called_with("  NODES REMOVED: 2/10\n  NODE POOL SIZE: 2\n")

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.log.cyan_text')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.purple_text')
    def test_print_add_removed_summary_add_nodes(self, mock_purple, mock_cyan, _):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.added = ["Node1"]
        add_op.deleted = ["Node1", "Node2"]
        add_op.total_nodes = 1
        add_op._print_add_removed_summary(10, action="ADDED")
        mock_purple.assert_called_with("\nNODE MANAGER SUMMARY\n--------------------\n")
        mock_cyan.assert_called_with("  NODES ADDED: 1/10\n  NODE POOL SIZE: 1\n")

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.log.logger.warn')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.purple_text')
    def test_print_failed_summary(self, mock_purple, mock_warn, _):
        remove_op = workload_ops_node_operations.RemoveNodesOperation({"IDENTIFIER": "all"})
        remove_op.missing = ["Node", "Node1"]
        remove_op._print_failed_summary()
        mock_purple.assert_called_with("FAILED NODES\n------------")
        mock_warn.assert_called_with("\nNOTE: The list of nodes below could not be removed because they are not in the "
                                     "pool.\nNode,Node1")

    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.update_nodes_with_poid_info')
    @patch("enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.__init__", return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.add',
           return_value=(["Node"], {"Error": []}))
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.calculate_num_items', return_value=1)
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.add_nodes')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_add_removed_summary')
    def test_execute_operation__in_add_op_uses_legacy(self, mock_print_add_removed_summary, mock_print_failed_summary,
                                                      mock_service, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.added = []
        add_op.not_added = []
        add_op.missing_nodes = {}
        add_op.nodes_file_path = "some_path"
        add_op.range_start = 1
        add_op.range_end = 2
        add_op.validate = True
        add_op.can_service_be_used = False
        add_op._execute_operation()
        mock_print_add_removed_summary.assert_called_with(1, action="ADDED")
        self.assertEqual(0, mock_print_failed_summary.call_count)
        self.assertEqual(0, mock_service.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.get_parsed_file_location',
           return_value="path")
    @patch("enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.__init__", return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.add_nodes')
    def test_execute_operation__in_add_op_uses_service(self, mock_service, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.can_service_be_used = True
        add_op.nodes_range = "some_range"
        add_op._execute_operation()
        self.assertEqual(1, mock_service.call_count)

    @patch("enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.__init__", return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.add',
           return_value=(["Node"], {"Error": ["Node1"]}))
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.calculate_num_items', return_value=2)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_add_removed_summary')
    def test_execute_operation__in_add_op_failed_nodes(
            self, mock_print_add_removed_summary, mock_print_failed_summary, mock_update_nodes_with_poid_info, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.can_service_be_used = False
        add_op.added = []
        add_op.not_added = []
        add_op.missing_nodes = {}
        add_op.nodes_file_path = "some_path"
        add_op.range_start = 1
        add_op.range_end = 2
        add_op.validate = True
        add_op._execute_operation()
        mock_print_add_removed_summary.assert_called_with(2, action="ADDED")
        self.assertEqual(1, mock_print_failed_summary.call_count)
        self.assertTrue(mock_update_nodes_with_poid_info.called)

    @patch("enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.__init__", return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.add',
           return_value=(["Node"], {"Error": ["Node1"]}))
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.calculate_num_items', return_value=2)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.log.logger.info')
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.update_nodes_with_poid_info',
           side_effect=Exception("some error"))
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_add_removed_summary')
    def test_execute_operation__in_add_op_failed_to_update_poids(
            self, mock_print_add_removed_summary, mock_print_failed_summary, mock_update_nodes_with_poid_info,
            mock_info, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.can_service_be_used = False
        add_op.added = []
        add_op.not_added = []
        add_op.missing_nodes = {}
        add_op.nodes_file_path = "some_path"
        add_op.range_start = 1
        add_op.range_end = 2
        add_op.validate = True
        add_op._execute_operation()
        mock_print_add_removed_summary.assert_called_with(2, action="ADDED")
        self.assertEqual(1, mock_print_failed_summary.call_count)
        self.assertTrue(mock_update_nodes_with_poid_info.called)
        mock_info.assert_called_with("some error")

    @patch("enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.__init__", return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.node_pool_mgr.add',
           return_value=([], {"Error": ["Node1"]}))
    @patch('enmutils_int.lib.workload_ops_node_operations.update_total_node_count')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation.calculate_num_items', return_value=2)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops_node_operations.GenericFlow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_failed_summary')
    @patch('enmutils_int.lib.workload_ops_node_operations.AddNodesOperation._print_add_removed_summary')
    def test_execute_operation__in_add_op_no_nodes_added(
            self, mock_print_add_removed_summary, mock_print_failed_summary, mock_update_nodes_with_poid_info, *_):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.can_service_be_used = False
        add_op.added = []
        add_op.not_added = []
        add_op.missing_nodes = {}
        add_op.nodes_file_path = "some_path"
        add_op.range_start = 1
        add_op.range_end = 2
        add_op.validate = True
        add_op._execute_operation()
        mock_print_add_removed_summary.assert_called_with(2, action="ADDED")
        self.assertEqual(1, mock_print_failed_summary.call_count)
        self.assertFalse(mock_update_nodes_with_poid_info.called)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.log.logger.warn')
    @patch('enmutils_int.lib.workload_ops_node_operations.log.purple_text')
    def test_print_failed_summary_add_nodes(self, mock_purple, mock_warn, _):
        add_op = workload_ops_node_operations.AddNodesOperation({"IDENTIFIER": "all"})
        add_op.missing_nodes = {"NOT_ADDED": ["Node"], "NOT_SYNCED": ["Node1"],
                                "MISSING_PRIMARY_TYPE": ["Node2"], "ALREADY_IN_POOL": []}
        add_op._print_failed_summary()
        mock_purple.assert_any_call("\nNOTE: The list of nodes below were not added because they are not created on "
                                    "ENM.\n")
        mock_purple.assert_any_call("\nNOTE: The list of nodes below were not added because they are not synced.\n")
        mock_purple.assert_any_call("\nNOTE: The list of nodes below were not added because they are not supported by "
                                    "the workload pool.\n")
        self.assertEqual(3, mock_warn.call_count)

    @patch("enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used", return_value=False)
    def test_get_workload_operations__has_function_print_failed_summary(self, _):
        op = workload_ops_node_operations.get_workload_operations("add", {"IDENTIFIER": "all"})
        self.assertTrue(hasattr(op, "_print_failed_summary"))

    @patch("enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used", return_value=False)
    def test_get_workload_operations__raises_key_error(self, _):
        self.assertRaises(KeyError, workload_ops_node_operations.get_workload_operations, "not_an_operation", {})


class ResetNodesUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops_node_operations.reset_nodes')
    def test_workload_reset__prints_node_error_info_when_error_on_node(self, mock_reset, _):
        workload_ops_node_operations.ResetNodesOperation({"--network-values": False, "--no-ansi": False}).execute()
        self.assertEqual(1, mock_reset.call_count)

    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops_node_operations.nodemanager_adaptor.reset_nodes')
    def test_workload_reset__uses_node_manager_service(self, mock_reset, _):
        workload_ops_node_operations.ResetNodesOperation({"--network-values": True, "--no-ansi": True}).execute()
        self.assertEqual(1, mock_reset.call_count)
        mock_reset.assert_called_with(reset_network_values=True, no_ansi=True)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
