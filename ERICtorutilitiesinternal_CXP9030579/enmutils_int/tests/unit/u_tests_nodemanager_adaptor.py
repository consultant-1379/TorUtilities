#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import NoNodesAvailable
from enmutils.lib.enm_node import BaseNodeLite
from enmutils_int.lib.services import nodemanager_adaptor
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class NodeManagerAdaptorUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values')
    def test_add_nodes__success(self, mock_sanitize, mock_send_request, _):
        nodemanager_adaptor.add_nodes({"IDENTIFIER": "nodes", "RANGE": None})
        mock_send_request.assert_called_with("POST", nodemanager_adaptor.ADD_NODES_URL,
                                             json_data={'file_name': 'nodes', 'node_range': 'None'})
        self.assertEqual(1, mock_sanitize.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values')
    def test_add_nodes__success_with_range(self, mock_sanitize, mock_send_request, _):
        nodemanager_adaptor.add_nodes({"IDENTIFIER": "nodes", "RANGE": "1-10"})
        mock_send_request.assert_called_with("POST", nodemanager_adaptor.ADD_NODES_URL,
                                             json_data={'file_name': 'nodes', 'node_range': '1-10'})
        self.assertEqual(1, mock_sanitize.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values', side_effect=ValueError("Args failed"))
    @patch('enmutils_int.lib.services.nodemanager_adaptor.log.logger.info')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    def test_add_nodes__logs_failed_validation(self, mock_send_request, mock_info, *_):
        nodemanager_adaptor.add_nodes({"IDENTIFIER": "nodes", "RANGE": "1-10"})
        self.assertEqual(0, mock_send_request.call_count)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values')
    def test_remove_nodes__success(self, mock_sanitize, mock_send_request, _):
        nodemanager_adaptor.remove_nodes({"IDENTIFIER": "nodes", "RANGE": "1-10", "force": False})
        mock_send_request.assert_called_with("POST", nodemanager_adaptor.REMOVE_NODES_URL,
                                             json_data={'file_name': 'nodes', 'node_range': '1-10', 'force': 'false'})
        self.assertEqual(1, mock_sanitize.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values')
    def test_remove_nodes__calls_remove_all_if_no_identifier(self, mock_sanitize, mock_send_request, _):
        nodemanager_adaptor.remove_nodes({"IDENTIFIER": None, "RANGE": None, "force": True})
        mock_send_request.assert_called_with("POST", nodemanager_adaptor.REMOVE_NODES_URL,
                                             json_data={'file_name': 'all', 'node_range': 'None', 'force': 'true'})
        self.assertEqual(1, mock_sanitize.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.sanitize_values', side_effect=ValueError("Args failed"))
    @patch('enmutils_int.lib.services.nodemanager_adaptor.log.logger.info')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    def test_remove_nodes__logs_failed_validation(self, mock_send_request, mock_info, *_):
        nodemanager_adaptor.remove_nodes({"IDENTIFIER": "nodes", "RANGE": "1-10", "force": False})
        self.assertEqual(0, mock_send_request.call_count)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service')
    def test_reset_nodes__success(self, mock_send_request, mock_print):
        nodemanager_adaptor.reset_nodes()
        mock_send_request.assert_called_with("POST", nodemanager_adaptor.RESET_NODES_URL,
                                             json_data={'no_ansi': False, 'reset_network_values': False})
        self.assertEqual(1, mock_print.call_count)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.log.logger")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_update_poids__is_successful(
            self, mock_send_request_to_service, mock_validate_response, mock_logger):
        nodemanager_adaptor.update_poids()
        mock_send_request_to_service.assert_called_with("POST", "nodes/update_poids")
        mock_validate_response.assert_called_with(mock_send_request_to_service.return_value)

    @ParameterizedTestCase.parameterize(
        ("arguments", "values"),
        [
            ([None], [None]),
            (["IDENTIFIER"], [[]]),
            (["IDENTIFIER"], [{}]),
            (["IDENTIFIER"], [()]),
            (["IDENTIFIER", "RANGE"], ["nodes", "1,2"]),
            (["IDENTIFIER", "RANGE"], ["nodes", "first"]),
            (["IDENTIFIER", "RANGE"], ["nodes", "1-2-3"])
        ]
    )
    def test_sanitize_values__raises_value_error_if_invalid_argument_value(self, arguments, values):
        arg_dict = {}
        for arg, val in zip(arguments, values):
            arg_dict.update({arg: val})
        self.assertRaises(ValueError, nodemanager_adaptor.sanitize_values, arg_dict)

    @ParameterizedTestCase.parameterize(
        ("arguments", "values"),
        [
            (["IDENTIFIER", "RANGE"], ["nodes", None]),
            (["IDENTIFIER", "RANGE"], ["nodes", "1"]),
            (["IDENTIFIER", "RANGE"], ["nodes", "1-10"]),
            (["IDENTIFIER", "RANGE"], ["all", None]),
            (["IDENTIFIER", "RANGE"], ["all", "1-10"]),
        ]
    )
    def test_sanitize_values__success(self, arguments, values):
        arg_dict = {}
        for arg, val in zip(arguments, values):
            arg_dict.update({arg: val})
        nodemanager_adaptor.sanitize_values(arg_dict)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_adaptor.send_request_to_service")
    def test_send_request_to_service__success(self, mock_send_request):
        nodemanager_adaptor.send_request_to_service("POST", "nodes/add", {"file_name": "nodes", "node_range": None})
        mock_send_request.assert_called_with("POST", "nodes/add", nodemanager_adaptor.SERVICE_NAME, retry=False,
                                             json_data={"file_name": "nodes", "node_range": None})

    @patch('time.sleep', return_value=None)
    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_adaptor.send_request_to_service")
    def test_send_request_to_service__resends_request_if_status_code_202_received(
            self, mock_send_request_to_service, _):
        mock_send_request_to_service.side_effect = [Mock(status_code=202), Mock(status_code=200)]
        nodemanager_adaptor.send_request_to_service("POST", "nodes/add", {"file_name": "nodes", "node_range": None})
        self.assertEqual(2, mock_send_request_to_service.call_count)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_nodes_preference_check__is_successful(self, mock_send_request_to_service):
        node1 = {"node_id": "LTE04dg2ERBS00009"}
        node2 = {"node_id": "LTE04dg2ERBS00008"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"node_data": [node1, node2]}}
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual(True, nodemanager_adaptor.nodes_preference_check())
        mock_send_request_to_service.assert_called_with(
            nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.LIST_NODES_URL,
            json_data={'profile': None, 'node_attributes': ["node_id"], 'match_patterns': None})

    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_nodes_preference_check__is_failure(self, mock_send_request_to_service):
        node1 = {"node_id": "blah1"}
        node2 = {"node_id": "blah2"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"node_data": [node1, node2]}}
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual(False, nodemanager_adaptor.nodes_preference_check())
        mock_send_request_to_service.assert_called_with(
            nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.LIST_NODES_URL,
            json_data={'profile': None, 'node_attributes': ["node_id"], 'match_patterns': None})

    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_nodes_preference_check__is_response_failure(self, mock_send_request_to_service):
        mock_response = Mock()
        mock_response.ok = False
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual(False, nodemanager_adaptor.nodes_preference_check())
        mock_send_request_to_service.assert_called_with(
            nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.LIST_NODES_URL,
            json_data={'profile': None, 'node_attributes': ["node_id"], 'match_patterns': None})

    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_received_data_to_nodes")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_list_nodes__is_successful(self, mock_send_request_to_service, mock_convert_received_data_to_nodes):
        node1 = {"node1": "blah1"}
        node2 = {"node2": "blah2"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"node_data": [node1, node2], "total_node_count": 3, "node_count_from_query": 2}}
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual((3, 2, mock_convert_received_data_to_nodes.return_value), nodemanager_adaptor.list_nodes())
        mock_send_request_to_service.assert_called_with(
            nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.LIST_NODES_URL,
            json_data={'profile': None, 'node_attributes': ["node_id"], 'match_patterns': None})
        mock_convert_received_data_to_nodes.assert_called_with([node1, node2])

    @patch("enmutils_int.lib.services.nodemanager_adaptor.list_nodes")
    def test_get_list_of_nodes_from_service__is_successful(self, mock_list_nodes):
        nodes = [Mock()]
        mock_list_nodes.return_value = (3, 2, nodes)
        self.assertEqual(nodes, nodemanager_adaptor.get_list_of_nodes_from_service("blah"))
        mock_list_nodes.assert_called_with("blah", None, None, False)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_received_data_to_nodes")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_list_nodes__is_successful_if_json_response_specified(
            self, mock_send_request_to_service, mock_convert_received_data_to_nodes):
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {"node_data": {"blah": "blah1"}, "total_node_count": 3, "node_count_from_query": 2}}
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual((3, 2, {"blah": "blah1"}),
                         nodemanager_adaptor.list_nodes(node_attributes=["node_id", "simulation"], json_response=True))
        mock_send_request_to_service.assert_called_with(
            nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.LIST_NODES_URL,
            json_data={'profile': None, 'node_attributes': ["node_id", "simulation"],
                       'match_patterns': None})
        self.assertFalse(mock_convert_received_data_to_nodes.called)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_received_data_to_nodes")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_list_nodes__return_no_nodes_if_bad_response_from_service(self, mock_send_request_to_service, _):
        mock_response = Mock()
        mock_response.ok = 0
        mock_send_request_to_service.return_value = mock_response
        self.assertEqual([], nodemanager_adaptor.list_nodes()[2])

    @patch('enmutils_int.lib.services.nodemanager_adaptor.get_profile_attributes_and_values')
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_erbs_node_pop_node__is_successful(self, mock_send_request_to_service, _):
        nodemanager_adaptor.MAX_NODES_COUNT_PER_REQUEST = 4
        profile = Mock(NAME="TEST_01")
        nodes = Mock()
        nodemanager_adaptor.erbs_node_pop(profile, nodes)
        self.assertFalse(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={'profile': 'TEST_01', 'nodes': None, 'profile_values': {}, 'network_config': None}) in
            mock_send_request_to_service.mock_calls)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.get_profile_attributes_and_values', return_value={})
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.get_list_of_nodes_from_service")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.erbs_node_pop")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.nodes_preference_check")
    def test_allocate_node__is_successful_ha(self, mock_pref, *_):
        nodemanager_adaptor.MAX_NODES_COUNT_PER_REQUEST = 4
        profile = Mock(NAME="HA_01")
        mock_pref.return_value = True
        nodemanager_adaptor.allocate_nodes(profile)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.get_profile_attributes_and_values', return_value={})
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_allocate_node__is_successful(self, mock_list, mock_send_request_to_service, _):
        nodemanager_adaptor.MAX_NODES_COUNT_PER_REQUEST = 4
        profile = Mock(NAME="TEST_01")
        nodemanager_adaptor.allocate_nodes(profile)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={'profile': 'TEST_01', 'nodes': None, 'profile_values': {}, 'network_config': None}) in
            mock_send_request_to_service.mock_calls)
        self.assertEqual(1, mock_list.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.get_profile_attributes_and_values', return_value={})
    @patch("enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_allocate_node__is_successful_if_nodes_specified(self, mock_list, mock_send_request_to_service, *_):
        nodemanager_adaptor.MAX_NODES_COUNT_PER_REQUEST = 4
        profile = Mock(NAME="TEST_01")
        nodes = [Mock(node_id="node{0}".format(i + 1)) for i in xrange(10)]
        nodemanager_adaptor.allocate_nodes(profile, nodes=nodes)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node1,node2,node3,node4"}) in
            mock_send_request_to_service.mock_calls)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node5,node6,node7,node8"}) in
            mock_send_request_to_service.mock_calls)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node9,node10"}) in mock_send_request_to_service.mock_calls)

        nodemanager_adaptor.allocate_nodes(profile)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": None, 'profile_values': {},
                            'network_config': None}) in mock_send_request_to_service.mock_calls)
        self.assertTrue(call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                             json_data={"profile": "TEST_01", "nodes": None, 'profile_values': {},
                                        'network_config': None}) in mock_send_request_to_service.mock_calls)
        self.assertEqual(2, mock_list.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.get_prop', return_value='40k')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.get_profile_attributes_and_values', return_value={})
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_allocate_node__raises_nonodesavailable(self, mock_send_request_to_service, *_):
        profile = Mock(NAME="TEST_01")
        mock_send_request_to_service.return_value.json.return_value = {
            "success": False, "message": "Could not allocate some node type"}
        self.assertRaises(NoNodesAvailable, nodemanager_adaptor.allocate_nodes, profile)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.ALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": None, 'profile_values': {}, 'network_config': "40k"}) in
            mock_send_request_to_service.mock_calls)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_deallocate_node__is_successful(self, mock_send_request_to_service, _):
        profile = Mock(NAME="TEST_01")
        nodemanager_adaptor.deallocate_nodes(profile)
        mock_send_request_to_service.assert_called_with(nodemanager_adaptor.POST_METHOD,
                                                        nodemanager_adaptor.DEALLOCATE_NODES_URL,
                                                        json_data={"profile": "TEST_01", "nodes": None})

    @patch("enmutils_int.lib.services.nodemanager_adaptor.print_service_operation_message")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_deallocate_node__is_successful_if_unused_nodes_specified(self, mock_send_request_to_service, *_):
        nodemanager_adaptor.MAX_NODES_COUNT_PER_REQUEST = 4
        profile = Mock(NAME="TEST_01")
        nodes = [Mock(node_id="node{0}".format(i + 1)) for i in xrange(10)]
        nodemanager_adaptor.deallocate_nodes(profile, unused_nodes=nodes)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.DEALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node1,node2,node3,node4"}) in
            mock_send_request_to_service.mock_calls)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.DEALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node5,node6,node7,node8"}) in
            mock_send_request_to_service.mock_calls)
        self.assertTrue(
            call(nodemanager_adaptor.POST_METHOD, nodemanager_adaptor.DEALLOCATE_NODES_URL,
                 json_data={"profile": "TEST_01", "nodes": "node9,node10"}) in mock_send_request_to_service.mock_calls)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_adaptor.validate_response")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.send_request_to_service")
    def test_update_node_cache__sends_request(self, mock_send_request_to_service, mock_validate_response):
        nodemanager_adaptor.update_nodes_cache_on_request()
        mock_validate_response.assert_called_with(mock_send_request_to_service.return_value)
        mock_send_request_to_service.assert_called_with(nodemanager_adaptor.GET_METHOD, nodemanager_adaptor.UPDATE_NODES_CACHE)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.allocate_nodes")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.deallocate_nodes")
    def test_exchange_nodes__is_successful(self, mock_allocate_nodes, mock_deallocate_nodes):
        profile = Mock(NAME="TEST_01")
        nodemanager_adaptor.exchange_nodes(profile)
        mock_allocate_nodes.assert_called_with(profile)
        mock_deallocate_nodes.assert_called_with(profile)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_registry.can_service_be_used", return_value=True)
    def test_can_service_be_used__is_successful_for_profile(self, mock_can_service_be_used):
        profile = Mock(priority=1)
        self.assertTrue(nodemanager_adaptor.can_service_be_used(profile))
        mock_can_service_be_used.assert_called_with("nodemanager", 1)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.service_registry.can_service_be_used", return_value=True)
    def test_can_service_be_used__is_successful_for_tools(self, mock_can_service_be_used):
        self.assertTrue(nodemanager_adaptor.can_service_be_used())
        mock_can_service_be_used.assert_called_with("nodemanager", None)

    def test_convert_received_data_to_nodes__success(self):
        node1_data = {"node_id": "node1", "node_ip": "some_ip_address1", "simulation": "sim1"}
        nodes = nodemanager_adaptor.convert_received_data_to_nodes([node1_data])

        self.assertEqual(nodes[0].__dict__, node1_data)
        self.assertTrue(isinstance(nodes[0], BaseNodeLite))
        self.assertEqual(len(nodes), 1)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.tuple_str_keys")
    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_dictionary_to_mos")
    def test_convert_received_data_to_nodes__converts_mos(self, mock_convert, mock_tuple):
        node1_data = {"node_id": "node1", "node_ip": "some_ip_address1", "simulation": "sim1", "mos": {"mo": 1}}
        nodemanager_adaptor.convert_received_data_to_nodes([node1_data])
        self.assertEqual(1, mock_convert.call_count)
        self.assertEqual(1, mock_tuple.call_count)
        mock_convert.assert_called_with({'mo': 1})
        mock_tuple.assert_called_with({"mo": 1})

    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_dict_to_users")
    def test_convert_dictionary_to_mos__not_a_dict(self, mock_convert):
        nodemanager_adaptor.convert_dictionary_to_mos([])
        self.assertEqual(0, mock_convert.call_count)

    @patch("enmutils_int.lib.services.nodemanager_adaptor.EnmMo.__init__", return_value=None)
    @patch("enmutils_int.lib.services.nodemanager_adaptor.convert_dict_to_users")
    def test_convert_dictionary_to_mos__converts(self, mock_convert, _):
        key = "key"
        test_dict = {key: {key: {key: {key: [{'mo_id': 1}]}}}}
        nodemanager_adaptor.convert_dictionary_to_mos(test_dict)
        self.assertEqual(1, mock_convert.call_count)
        mock_convert.assert_called_with({'mo_id': 1})

    def test_convert_dict_to_users__user(self):
        test_dict = {'user': {'username': "Test", 'password': 'Test'}}
        result = nodemanager_adaptor.convert_dict_to_users(test_dict)
        self.assertTrue(getattr(result.get('user'), 'get_apache_url_from_service', False))

    def test_convert_dict_to_users__no_user(self):
        test_dict = {'user': None}
        result = nodemanager_adaptor.convert_dict_to_users(test_dict)
        self.assertDictEqual(test_dict, result)

    def test_tuple_str_keys__success(self):
        tuple_dict = {"A|||1": {"B||1": {"C|||1": ["mo"]}}}
        nodemanager_adaptor.tuple_str_keys(tuple_dict)
        self.assertDictEqual({('A', '1'): {"B||1": {('C', '1'): ['mo']}}}, tuple_dict)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.__init__', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.get_profiles_values',
           return_value={"Key": "Value"})
    def test_get_profile_attributes_and_values__success(self, mock_get, _):
        profile_name = 'CMEVENTS_NBI_01'
        result = nodemanager_adaptor.get_profile_attributes_and_values(profile_name)
        mock_get.assert_called_with('cmevents_nbi', profile_name)
        self.assertDictEqual({'Key': 'Value'}, result)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.__init__', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.get_profiles_values',
           return_value=None)
    def test_get_profile_attributes_and_values__no_values(self, mock_get, _):
        profile_name = 'CMEVENTS_NBI_01'
        result = nodemanager_adaptor.get_profile_attributes_and_values(profile_name)
        mock_get.assert_called_with('cmevents_nbi', profile_name)
        self.assertDictEqual({}, result)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.__init__', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.load_custom_config_values', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.get_profiles_values',
           return_value={"Key": "Value"})
    def test_get_profile_attributes_and_values__load_config_no_entry(self, mock_get, mock_load, *_):
        profile_name = 'CMEVENTS_NBI_01'
        result = nodemanager_adaptor.get_profile_attributes_and_values(profile_name)
        mock_get.assert_called_with('cmevents_nbi', profile_name)
        self.assertDictEqual({"Key": "Value"}, result)
        self.assertEqual(1, mock_load.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.__init__', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.load_custom_config_values')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.InputData.get_profiles_values',
           return_value={"Key": "Value"})
    def test_get_profile_attributes_and_values__load_config_custom_values(self, mock_get, mock_load, *_):
        mock_module = Mock()
        mock_module.CMEVENTS_NBI_01 = {'Key': "Value2"}
        mock_load.return_value = mock_module
        profile_name = 'CMEVENTS_NBI_01'
        result = nodemanager_adaptor.get_profile_attributes_and_values(profile_name)
        mock_get.assert_called_with('cmevents_nbi', profile_name)
        self.assertDictEqual({"Key": "Value2"}, result)
        self.assertEqual(1, mock_load.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.get_prop', return_value="path")
    @patch('enmutils_int.lib.services.nodemanager_adaptor.imp.load_source')
    def test_load_custom_config_values__success(self, mock_load, _):
        nodemanager_adaptor.load_custom_config_values()
        self.assertEqual(1, mock_load.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.get_prop', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_adaptor.imp.load_source')
    def test_load_custom_config_values__no_file_path(self, mock_load, _):
        nodemanager_adaptor.load_custom_config_values()
        self.assertEqual(0, mock_load.call_count)

    @patch('enmutils_int.lib.services.nodemanager_adaptor.config.get_prop', return_value="path")
    @patch('enmutils_int.lib.services.nodemanager_adaptor.log.logger.debug')
    @patch('enmutils_int.lib.services.nodemanager_adaptor.imp.load_source', side_effect=Exception("Error"))
    def test_load_custom_config_values__logs_exception(self, mock_load, mock_debug, _):
        nodemanager_adaptor.load_custom_config_values()
        self.assertEqual(1, mock_load.call_count)
        mock_debug.assert_called_with("Unable to load configuration file, error encountered: Error.")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
