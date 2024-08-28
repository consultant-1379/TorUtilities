#!/usr/bin/env python

import unittest2
from flask import Flask
from mock import MagicMock, Mock, call, patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import log
from enmutils.lib.exceptions import NoNodesAvailable
from enmutils_int.lib import node_pool_mgr
import enmutils_int.lib.services.nodemanager as nodemanager
from testslib import unit_test_utils

app = Flask(__name__)

REMOVE_NODES_URL = "nodes/remove"
ADD_NODES_URL = "nodes/add"
LIST_NODES_URL = "nodes/list"
ALLOCATE_NODES_URL = "nodes/allocate"
DEALLOCATE_NODES_URL = "nodes/deallocate"
NODES_FILE = "/opt/ericcson/nssutils/etc/nodes/nodes"
SERVICES_DIRECTORY = '/home/enmutils/services'
SUCCESS_MESSAGE = '{"message": "", "success": true}'
CONTENT_TYPE = 'application/json'


class NodeManagerServiceUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def setup_nodes():
        nodes = []
        for i in xrange(3):
            node = Mock()
            node_attributes = {"node_id": "node{0}".format(i),
                               "profiles": ["PROFILE{0}".format(i), "PROFILE{0}".format(i + 100)],
                               "primary_type": "primary_type{0}".format(i),
                               "netsim": "netsim{0}".format(i),
                               "simulation": "simulation{0}".format(i),
                               "mim_version": "mim_version{0}".format(i),
                               "node_version": "node_version{0}".format(i),
                               "node_ip": "node_ip{0}".format(i),
                               "_is_exclusive": False}
            node_to_dict = {key: node_attributes[key] for key in node_attributes.keys() if "profiles" not in key}

            node.node_attributes = node_attributes
            node.to_dict.return_value = node_to_dict
            node.configure_mock(**node_attributes)
            node.extra_attribute = "extra_attribute{0}".format(i)

            nodes.append(node)
        return nodes

    @patch("enmutils_int.lib.services.nodemanager.convert_node_to_dictionary")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_list_nodes__is_successful(self, mock_response, mock_convert_node_to_dictionary):
        mock1, mock2 = Mock(), Mock()
        mock_convert_node_to_dictionary.side_effect = [mock1, mock2]
        node1, node2 = Mock(node_id="node1"), Mock(node_id="node2")
        node_pool_mgr.cached_nodes_list = [node1, node2]
        with app.test_request_context(LIST_NODES_URL, json={'profile': None, 'match_patterns': None,
                                                            'node_attributes': None, }):
            nodemanager.list_nodes()
        mock_response.assert_called_with(message={"node_data": [mock1, mock2],
                                                  'node_count_from_query': 2, 'total_node_count': 2})
        self.assertEqual([call(node1, None, profile_name=None), call(node2, None, profile_name=None)],
                         mock_convert_node_to_dictionary.mock_calls)

    @patch("enmutils_int.lib.services.nodemanager.log.logger")
    @patch("enmutils_int.lib.services.nodemanager.convert_node_to_dictionary")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_list_nodes__is_successful_if_profile_specified(
            self, mock_response, mock_convert_node_to_dictionary, mock_logger):
        mock_queue = MagicMock()
        mock_queue.__contains__.return_value = True
        nodemanager.PROFILE_ALLOCATION_QUEUE = mock_queue
        mock1, mock2 = Mock(), Mock()
        mock_convert_node_to_dictionary.side_effect = [mock1, mock2]
        node1 = Mock(node_id="node1", profiles=['PROFILE1', 'PROFILE2'])
        node2 = Mock(node_id="node2", profiles=['PROFILE2', 'PROFILE3'])
        node3 = Mock(node_id="node3", profiles=['PROFILE4', 'PROFILE5'])
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]
        with app.test_request_context(LIST_NODES_URL, json={'profile': "PROFILE2", 'match_patterns': None,
                                                            'node_attributes': ["node_id", "profiles"]}):
            nodemanager.list_nodes()
        mock_response.assert_called_with(
            message={'node_data': [mock1, mock2], 'node_count_from_query': 2, 'total_node_count': 3})
        self.assertEqual([call(node1, ["node_id", "profiles"], profile_name=u'PROFILE2'),
                          call(node2, ["node_id", "profiles"], profile_name=u'PROFILE2')],
                         mock_convert_node_to_dictionary.mock_calls)
        mock_queue.block_until_item_removed.assert_called_with("PROFILE2", mock_logger, max_time_to_wait=1800)

    @patch("enmutils_int.lib.services.nodemanager.convert_node_to_dictionary")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_list_nodes__is_successful_if_pattern_specified(self, mock_response, mock_convert_node_to_dictionary):
        mock1, mock2 = Mock(), Mock()
        mock_convert_node_to_dictionary.side_effect = [mock1, mock2]
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]
        with app.test_request_context(LIST_NODES_URL, json={'profile': None, 'match_patterns': "*ode2*,*ode1",
                                                            'node_attributes': ["node_id"]}):
            nodemanager.list_nodes()
        mock_response.assert_called_with(
            message={'node_data': [mock1, mock2], 'node_count_from_query': 2, 'total_node_count': 3})
        self.assertEqual([call(node1, ["node_id"], profile_name=None), call(node2, ["node_id"], profile_name=None)],
                         mock_convert_node_to_dictionary.mock_calls)

    @patch('enmutils_int.lib.services.nodemanager.log.logger')
    @patch("enmutils_int.lib.services.nodemanager.convert_node_to_dictionary")
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    def test_list_nodes__raises_exception_if_cannot_list_nodes(
            self, mock_abort_with_message, mock_convert_node_to_dictionary, mock_logger):
        exception = Exception("some_error")
        mock_convert_node_to_dictionary.side_effect = exception
        node_pool_mgr.cached_nodes_list = [Mock()]
        with app.test_request_context(LIST_NODES_URL, json={'profile': None, 'match_pattern': None}):
            nodemanager.list_nodes()
        mock_abort_with_message.assert_called_with("Could not locate node(s) in redis", mock_logger, 'nodemanager',
                                                   SERVICES_DIRECTORY, exception)

    @patch('enmutils_int.lib.services.nodemanager.create_and_start_background_scheduled_job')
    @patch('enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list')
    @patch('enmutils_int.lib.services.nodemanager.helper.retrieve_cell_information_and_apply_cell_type')
    @patch('enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes')
    def test_at_startup__success(self, mock_update_poid_attributes_on_pool_nodes, mock_apply, *_):
        nodemanager.at_startup()
        self.assertEqual(1, mock_update_poid_attributes_on_pool_nodes.call_count)
        self.assertEqual(1, mock_apply.call_count)

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 1))
    @patch("enmutils_int.lib.services.nodemanager.helper.update_total_node_count", return_value=40)
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.helper.retrieve_cell_information_and_apply_cell_type')
    @patch('enmutils_int.lib.services.nodemanager.get_json_response')
    @patch('enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes')
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.add', return_value=[["Node"], {}])
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_add_nodes__success(self, mock_abort_with_message, mock_populate,
                                mock_update_poid_attributes_on_pool_nodes, mock_get_json_response, *_):
        with app.test_request_context(ADD_NODES_URL, json=dict(file_name="nodes", node_range="1")):
            nodemanager.add_nodes()
        self.assertEqual(mock_abort_with_message.call_count, 0)
        self.assertEqual(mock_populate.call_count, 1)
        self.assertTrue(mock_update_poid_attributes_on_pool_nodes.called)
        mock_get_json_response.assert_called_with(
            message="Msg\nFailures occurred while trying to update nodes with POID info from ENM")

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 1))
    @patch("enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes", return_value=0)
    @patch('enmutils_int.lib.services.nodemanager.log.logger')
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.add')
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    def test_add_nodes__exception(self, mock_abort_with_message, mock_add, mock_logger,
                                  mock_update_poid_attributes_on_pool_nodes, _):
        exception = Exception("some_error")
        mock_add.side_effect = exception
        with app.test_request_context(ADD_NODES_URL, json=dict(file_name="nodes", node_range="1")):
            nodemanager.add_nodes()
        mock_abort_with_message.assert_called_with("Could not add nodes to the workload pool", mock_logger,
                                                   'nodemanager', SERVICES_DIRECTORY, exception)
        self.assertFalse(mock_update_poid_attributes_on_pool_nodes.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 1))
    @patch("enmutils_int.lib.services.nodemanager.helper.update_total_node_count", return_value=40)
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.add', return_value=[[], {"ALREADY_IN_POOL": "Node"}])
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch("enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes", return_value=0)
    @patch('enmutils_int.lib.services.nodemanager.get_json_response')
    @patch('enmutils_int.lib.services.nodemanager.print_failed_add_operation_summary', return_value="Msg")
    def test_add_nodes__calls_failed_summary_if_missing_nodes(self, mock_failed_add_summary, mock_get_response,
                                                              mock_update_poid_attributes_on_pool_nodes, *_):
        with app.test_request_context(ADD_NODES_URL, json=dict(file_name="nodes", node_range="1")):
            nodemanager.add_nodes()
        self.assertEqual(mock_failed_add_summary.call_count, 1)
        self.assertEqual(mock_get_response.call_count, 1)
        self.assertFalse(mock_update_poid_attributes_on_pool_nodes.called)

    @patch('enmutils_int.lib.services.nodemanager.remove_nodes_from_pool', return_value=[True, "Msg"])
    @patch('enmutils_int.lib.services.nodemanager.get_json_response')
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_remove_nodes__success(self, mock_abort_with_message, mock_get_json_response, mock_remove, *_):
        with app.test_request_context(REMOVE_NODES_URL, json=dict(file_name="all", node_range="None", force="false")):
            nodemanager.remove_nodes()
            self.assertEqual(mock_abort_with_message.call_count, 0)
            self.assertEqual(mock_get_json_response.call_count, 1)
            mock_remove.assert_called_with("all", None, False)

    @patch('enmutils_int.lib.services.nodemanager.log.logger')
    @patch('enmutils_int.lib.services.nodemanager.remove_nodes_from_pool')
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_remove_nodes__exception(self, mock_abort_with_message, mock_remove_nodes_from_pool, mock_logger):
        exception = Exception("some_error")
        mock_remove_nodes_from_pool.side_effect = exception
        with app.test_request_context(REMOVE_NODES_URL, json=dict(file_name="nodes", node_range="1", force="false")):
            nodemanager.remove_nodes()
        mock_abort_with_message.assert_called_with("Could not remove nodes from the workload pool", mock_logger,
                                                   'nodemanager', SERVICES_DIRECTORY, exception)

    @patch('enmutils_int.lib.services.nodemanager.remove_nodes_from_pool', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.nodemanager.get_json_response')
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_remove_nodes__exception_if_nodes_fail_to_remove(
            self, mock_abort_with_message, mock_get_response, mock_remove):
        with app.test_request_context(REMOVE_NODES_URL, json=dict(file_name="nodes", node_range="1", force="true")):
            nodemanager.remove_nodes()
        self.assertEqual(mock_abort_with_message.call_count, 1)
        self.assertEqual(mock_get_response.call_count, 0)
        mock_remove.assert_called_with("nodes", "1", True)

    @patch('enmutils_int.lib.services.nodemanager.get_json_response')
    @patch('enmutils_int.lib.services.nodemanager.helper.reset_nodes')
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_reset_nodes__success(self, mock_abort_with_message, *_):
        with app.test_request_context('/nodes/reset', json={'reset_network_values': True, 'no_ansi': True}):
            nodemanager.reset_nodes()
        self.assertEqual(mock_abort_with_message.call_count, 0)

    @patch('enmutils_int.lib.services.nodemanager.log.logger')
    @patch('enmutils_int.lib.services.nodemanager.helper.reset_nodes')
    @patch('enmutils_int.lib.services.nodemanager.abort_with_message')
    def test_reset_nodes__exception(self, mock_abort_with_message, mock_reset, mock_logger):
        exception = Exception("some_error")
        mock_reset.side_effect = exception
        with app.test_request_context('/nodes/reset', json={'reset_network_values': True, 'no_ansi': True}):
            nodemanager.reset_nodes()
        mock_abort_with_message.assert_called_with("Could not reset all nodes in the workload pool", mock_logger,
                                                   'nodemanager', SERVICES_DIRECTORY, exception)

    @patch("enmutils_int.lib.services.nodemanager.helper.perform_allocation_tasks")
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.mutexer.mutex")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_allocate_nodes__is_successful(
            self, mock_get_json_response, mock_mutex, mock_abort_with_message, mock_perform_allocation_tasks,):
        mock_queue = MagicMock()
        nodemanager.PROFILE_ALLOCATION_QUEUE = mock_queue
        with app.test_request_context(ALLOCATE_NODES_URL, json={'profile': 'profile1', 'nodes': None}):
            nodemanager.allocate_nodes()
        mock_get_json_response.assert_called_with(success=True)
        mock_mutex.assert_called_with("node-allocation", log_output=True)
        mock_perform_allocation_tasks.assert_called_with("profile1", None, profile_values=None, network_config=None)
        mock_queue.put_unique.assert_called_with("profile1")
        mock_queue.put_unique.get_item("profile1")
        self.assertFalse(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.perform_allocation_tasks",
           side_effect=NoNodesAvailable("no nodes found"))
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.mutexer.mutex")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_allocate_nodes__is_unsuccessful_if_no_nodes_found(
            self, mock_get_json_response, mock_mutex, mock_abort_with_message, mock_perform_allocation_tasks,):
        mock_queue = MagicMock()
        nodemanager.PROFILE_ALLOCATION_QUEUE = mock_queue
        with app.test_request_context(ALLOCATE_NODES_URL, json={'profile': 'profile1', 'nodes': None}):
            nodemanager.allocate_nodes()
        mock_get_json_response.assert_called_with(success=False, message="no nodes found")
        mock_mutex.assert_called_with("node-allocation", log_output=True)
        mock_perform_allocation_tasks.assert_called_with("profile1", None, profile_values=None, network_config=None)
        mock_queue.put_unique.assert_called_with("profile1")
        mock_queue.put_unique.get_item("profile1")
        self.assertFalse(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.perform_allocation_tasks",
           side_effect=Exception)
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.mutexer.mutex")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_allocate_nodes__is_unsuccessful_if_problem_encountered_during_allocation(
            self, mock_get_json_response, mock_mutex, mock_abort_with_message, mock_perform_allocation_tasks,):
        mock_queue = MagicMock()
        nodemanager.PROFILE_ALLOCATION_QUEUE = mock_queue
        with app.test_request_context(ALLOCATE_NODES_URL, json={'profile': 'profile1', 'nodes': None}):
            nodemanager.allocate_nodes()
        self.assertFalse(mock_get_json_response.called)
        mock_mutex.assert_called_with("node-allocation", log_output=True)
        mock_perform_allocation_tasks.assert_called_with("profile1", None, profile_values=None, network_config=None)
        mock_queue.put_unique.assert_called_with("profile1")
        mock_queue.put_unique.get_item("profile1")
        self.assertTrue(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_in_progress", return_value=None)
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_complete")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    @patch("enmutils_int.lib.services.nodemanager.helper.perform_deallocate_actions")
    def test_deallocate_nodes__is_successful(
            self, mock_perform_deallocate_actions, mock_get_json_response, mock_set_deallocation_complete,
            mock_abort_with_message, *_):
        with app.test_request_context(DEALLOCATE_NODES_URL, json={'profile': 'profile1', 'nodes': None}):
            nodemanager.deallocate_nodes()
        mock_get_json_response.assert_called_with(success=True)
        mock_perform_deallocate_actions.assert_called_with("profile1", None)
        self.assertTrue(mock_set_deallocation_complete.called)
        self.assertFalse(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_in_progress", return_value=None)
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_complete")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    @patch("enmutils_int.lib.services.nodemanager.helper.perform_deallocate_actions")
    def test_deallocate_nodes__is_unsuccessful_if_profile_name_not_specified(
            self, mock_perform_deallocate_actions, mock_get_json_response, mock_set_deallocation_complete,
            mock_abort_with_message, *_):
        with app.test_request_context(DEALLOCATE_NODES_URL, json={'profile': None, 'nodes': None}):
            nodemanager.deallocate_nodes()
        self.assertFalse(mock_get_json_response.called)
        self.assertFalse(mock_perform_deallocate_actions.called)
        self.assertTrue(mock_set_deallocation_complete.called)
        self.assertTrue(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_in_progress",
           return_value="deallocation in progress")
    @patch("enmutils_int.lib.services.nodemanager.helper.set_deallocation_complete")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    @patch("enmutils_int.lib.services.nodemanager.helper.perform_deallocate_actions")
    def test_deallocate_nodes__is_unsuccessful_if_cant_set_deallocation_in_progress(
            self, mock_perform_deallocate_actions, mock_get_json_response, mock_set_deallocation_complete, *_):
        with app.test_request_context(DEALLOCATE_NODES_URL, json={'profile': 'profile1', 'nodes': None}):
            result = nodemanager.deallocate_nodes()
        self.assertEqual(result, mock_get_json_response.return_value)
        mock_get_json_response.assert_called_with(success=False, message="deallocation in progress", rc=202)
        self.assertFalse(mock_perform_deallocate_actions.called)
        self.assertFalse(mock_set_deallocation_complete.called)

    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    def test_deallocate_nodes__raises_exception_if_no_profile_specified(
            self, mock_abort_with_message):
        with app.test_request_context(DEALLOCATE_NODES_URL, json={'profile': None, 'nodes': None}):
            nodemanager.deallocate_nodes()
        self.assertTrue(mock_abort_with_message.called)

    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch('enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list')
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_update_node_cache__is_successful(
            self, mock_get_json_response, mock_update_cache, mock_abort_with_message):
        with app.test_request_context('update_cache_on_request'):
            nodemanager.update_nodes_cache_on_request()
        self.assertFalse(mock_abort_with_message.called)
        mock_get_json_response.assert_called_with(message="Success")
        self.assertTrue(mock_update_cache.called)

    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch('enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list')
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_update_node_cache__calls_abort_if_error_occurs_while_updating(
            self, mock_get_json_response, mock_update_cache, mock_abort_with_message):
        error = Exception("error")
        mock_update_cache.side_effect = error
        with app.test_request_context('update_cache_on_request'):
            nodemanager.update_nodes_cache_on_request()
        mock_abort_with_message.assert_called_with("Failure occurred while updating nodes cache list", log.logger,
                                                   nodemanager.SERVICE_NAME, log.SERVICES_LOG_DIR, error)
        self.assertFalse(mock_get_json_response.called)

    def test_list_nodes_that_match_patterns__is_successful(self):
        nodes = self.setup_nodes()
        self.assertEqual([nodes[0], nodes[2]], nodemanager.list_nodes_that_match_patterns(nodes, "*de0*,node2"))

    def test_build_summary_message__add_nodes(self):
        result = nodemanager.build_summary_message("ADD", 1, 10, 40)
        expected = "\n\tNODE MANAGER SUMMARY\n\t--------------------\n\n\tNODES ADD: 1/10\n\tNODE POOL SIZE: 40\n"
        self.assertEqual(expected, result)

    def test_print_failed_remove_operation_summary__success(self):
        nodes = ["Node", "Node1"]
        expected = (
            "\n\tFAILED NODES\n\t------------\nNOTE: The list of nodes below could not be removed because they are not"
            " in the pool.\n{0}".format(",".join(nodes)))
        result = nodemanager.print_failed_remove_operation_summary(nodes)
        self.assertEqual(expected, result)

    @patch('enmutils_int.lib.services.nodemanager.helper.update_total_node_count', return_value=10)
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.print_failed_remove_operation_summary', return_value="Node")
    def test_update_remove_message__updates_missing(self, mock_summary, *_):
        message = nodemanager.update_remove_message([], ["Node"], ["Node"], "Still")
        self.assertEqual(1, mock_summary.call_count)
        self.assertEqual("MsgStillNode", message)

    @patch('enmutils_int.lib.services.nodemanager.helper.update_total_node_count', return_value=10)
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.print_failed_remove_operation_summary', return_value="Node")
    def test_update_remove_message__success(self, mock_summary, *_):
        message = nodemanager.update_remove_message(["Node"], [], [], "Still")
        self.assertEqual(0, mock_summary.call_count)
        self.assertEqual("Msg", message)

    @patch('enmutils_int.lib.services.nodemanager.helper.update_total_node_count')
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove_all', return_value=True)
    def test_remove_nodes_from_pool__removes_all(self, mock_remove_all, _):
        nodemanager.remove_nodes_from_pool("/opt/ericcson/nssutils/etc/nodes/all", "None", False)
        self.assertEqual(1, mock_remove_all.call_count)

    @patch('enmutils_int.lib.services.nodemanager.helper.update_total_node_count')
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove_all', return_value=False)
    def test_remove_nodes_from_pool__removes_all_still_running(self, mock_remove_all, _):
        message = nodemanager.remove_nodes_from_pool("/opt/ericcson/nssutils/etc/nodes/all", "None", False)
        self.assertEqual(1, mock_remove_all.call_count)
        self.assertEqual(message, "\nCould not remove all nodes from the workload pool as some profiles are still "
                                  "running.\nIf all profiles are stopped, execute ./workload reset and retry the "
                                  "remove command.")

    @patch("enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list")
    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(None, None))
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.update_remove_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove', return_value=[["Node"], [], []])
    def test_remove_nodes_from_pool__remove_all_nodes_from_file(
            self, mock_remove, mock_update_message, *_):
        nodemanager.remove_nodes_from_pool(NODES_FILE, "", True)
        mock_remove.assert_called_with(NODES_FILE, end=None, force=True, start=None)
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mock_update_message.call_count)

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 10))
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch("enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list")
    @patch('enmutils_int.lib.services.nodemanager.update_remove_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove', return_value=[["Node"], [], []])
    def test_remove_nodes_from_pool__remove_all_start_and_end_range_from_file(
            self, mock_remove, mock_update_message, mock_update_cached_nodes_list, *_):
        nodemanager.remove_nodes_from_pool(NODES_FILE, "1-10", True)
        mock_remove.assert_called_with(NODES_FILE, end=10, force=True, start=1)
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mock_update_message.call_count)
        self.assertTrue(mock_update_cached_nodes_list.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 10))
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch("enmutils_int.lib.services.nodemanager.helper.update_cached_nodes_list")
    @patch('enmutils_int.lib.services.nodemanager.update_remove_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove', return_value=[[], [], ["Node"]])
    def test_remove_nodes_from_pool__unable_to_remove_all_nodes(
            self, mock_remove, mock_update_message, mock_update_cached_nodes_list, *_):
        nodemanager.remove_nodes_from_pool(NODES_FILE, "1-10", True)
        mock_remove.assert_called_with(NODES_FILE, end=10, force=True, start=1)
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mock_update_message.call_count)
        self.assertFalse(mock_update_cached_nodes_list.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.determine_start_and_end_range", return_value=(1, 1))
    @patch('enmutils_int.lib.services.nodemanager.build_summary_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.update_remove_message', return_value="Msg")
    @patch('enmutils_int.lib.services.nodemanager.node_pool_mgr.remove', return_value=[["Node"], [], []])
    def test_remove_nodes_from_pool__remove_single_node_from_file(
            self, mock_remove, mock_update_message, *_):
        nodemanager.remove_nodes_from_pool(NODES_FILE, "1", True)
        mock_remove.assert_called_with(NODES_FILE, end=1, force=True, start=1)
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mock_update_message.call_count)

    def test_print_failed_summary_add_nodes(self):
        missing_nodes = {"NOT_ADDED": ["Node"], "NOT_SYNCED": ["Node1"],
                         "MISSING_PRIMARY_TYPE": ["Node2"], "ALREADY_IN_POOL": []}
        expected = ("\nNOTE: The list of nodes below were not added because they are not created on ENM.\n\nNode\n\n"
                    "NOTE: The list of nodes below were not added because they are not synced.\n\nNode1\n\n"
                    "NOTE: The list of nodes below were not added because they are not supported by the workload pool."
                    "\n\nNode2\n")
        result = nodemanager.print_failed_add_operation_summary(missing_nodes)
        self.assertEqual(expected, result)

    @patch("enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes", return_value=0)
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_update_poids_on_nodes__successful_if_update_ok_on_all_nodes(
            self, mock_get_json_response, mock_update_poid_attributes_on_pool_nodes):
        with app.test_request_context('get_deployment_info'):
            service_response = nodemanager.update_poids()

        self.assertEqual(mock_get_json_response.return_value, service_response)
        mock_get_json_response.assert_called_with(success=True, message="")
        self.assertTrue(mock_update_poid_attributes_on_pool_nodes.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes", return_value=5)
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_update_poids_on_nodes__successful_if_update_nok_on_all_nodes(
            self, mock_get_json_response, mock_update_poid_attributes_on_pool_nodes):
        with app.test_request_context('get_deployment_info'):
            service_response = nodemanager.update_poids()

        self.assertEqual(mock_get_json_response.return_value, service_response)
        mock_get_json_response.assert_called_with(success=False, message="Failed to update POID values on 5 nodes")
        self.assertTrue(mock_update_poid_attributes_on_pool_nodes.called)

    @patch("enmutils_int.lib.services.nodemanager.helper.update_poid_attributes_on_pool_nodes", side_effect=Exception)
    @patch("enmutils_int.lib.services.nodemanager.abort_with_message")
    @patch("enmutils_int.lib.services.nodemanager.get_json_response")
    def test_update_poids_on_nodes__returns_abort_if_error_occurs_updating_poids(
            self, mock_get_json_response, mock_abort_with_message, _):
        request_data = {"node1": "12345", "node2": "23456"}
        with app.test_request_context('get_deployment_info', json=request_data):
            nodemanager.update_poids()

        self.assertFalse(mock_get_json_response.called)
        self.assertTrue(mock_abort_with_message)

    @patch("enmutils_int.lib.services.nodemanager.mutexer.mutex")
    @patch("enmutils_int.lib.services.nodemanager.helper.convert_mos_to_dictionary", return_value="some_mos")
    def test_convert_node_to_dictionary__successful_when_attributes_are_required(self, *_):
        node = Mock(profiles=["PROFILE1", "PROFILE2"], node_name="node_1", subnetwork_str="some_subnetwork",
                    subnetwork_id="some_id", mim="some_mim", snmp_security_level="some_snmp_level", mos="some_mos")
        node.to_dict.return_value = {"node_id": "node1", "primary_type": "ERBS", "simulation": "sim1"}
        self.assertEqual(nodemanager.convert_node_to_dictionary(node, ["node_id", "profiles", "primary_type",
                                                                       "node_name"], profile_name="CMIMPORT_02"),
                         {"node_id": "node1", "primary_type": "ERBS", "profiles": ["PROFILE1", "PROFILE2"],
                          "node_name": "node_1"})

    @patch("enmutils_int.lib.services.nodemanager.helper.convert_mos_to_dictionary", return_value=[])
    def test_convert_node_to_dictionary__returns_full_node_if_no_attributes_specified(self, _):
        node = Mock(profiles=["PROFILE1", "PROFILE2"], node_name="node_1", subnetwork_str="some_subnetwork",
                    subnetwork_id="some_id", mim="some_mim", snmp_security_level="some_snmp_level", mos="some_mos",
                    available_to_profiles=set(), _is_exclusive=True, lte_cell_type="FDD", managed_element_type="ENodeB")
        node.to_dict.return_value = {"node_id": "node1", "primary_type": "ERBS", "simulation": "sim1"}
        self.assertEqual(nodemanager.convert_node_to_dictionary(node, None),
                         {"node_id": "node1", "primary_type": "ERBS", "simulation": "sim1",
                          "profiles": ["PROFILE1", "PROFILE2"], "node_name": "node_1",
                          "subnetwork_str": "some_subnetwork", "subnetwork_id": "some_id", "mos": {},
                          "mim": "some_mim", "snmp_security_level": "some_snmp_level", "managed_element_type": "ENodeB",
                          "available_to_profiles": [], "_is_exclusive": True, "lte_cell_type": "FDD"})

    @patch("enmutils_int.lib.services.nodemanager.helper.convert_mos_to_dictionary", return_value=[])
    def test_convert_node_to_dictionary__returns_full_node_if_all_specified(self, _):
        node = Mock(profiles=["PROFILE1", "PROFILE2"], node_name="node_1", subnetwork_str="some_subnetwork",
                    subnetwork_id="some_id", mim="some_mim", snmp_security_level="some_snmp_level", mos=[],
                    available_to_profiles=set(), _is_exclusive=True, lte_cell_type="FDD", managed_element_type="ENodeB")
        node.to_dict.return_value = {"node_id": "node1", "primary_type": "ERBS", "simulation": "sim1"}
        self.assertEqual(nodemanager.convert_node_to_dictionary(node, ["all"]),
                         {"node_id": "node1", "primary_type": "ERBS", "simulation": "sim1",
                          "profiles": ["PROFILE1", "PROFILE2"], "node_name": "node_1",
                          "subnetwork_str": "some_subnetwork", "subnetwork_id": "some_id", "mos": [],
                          "mim": "some_mim", "snmp_security_level": "some_snmp_level", "managed_element_type": "ENodeB",
                          "available_to_profiles": [], "_is_exclusive": True, "lte_cell_type": "FDD"})


if __name__ == "__main__":
    unittest2.main(verbosity=2)
