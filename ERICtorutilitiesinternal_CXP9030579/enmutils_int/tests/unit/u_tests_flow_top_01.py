#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock
from requests import HTTPError
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.load_node import ERBSLoadNode
from enmutils_int.lib.profile_flows.top_flows.top_01_flow import TOP01Flow, execute_user_tasks
from enmutils_int.lib.workload.top_01 import TOP_01


class TOP01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.user.username = "TestTopUser_u0"
        self.flow = TOP01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.node1 = ERBSLoadNode(id='LTE02ERBS00040', simulation='LTE-120', model_identity='1-2-34',
                                  node_id='netsim_LTE02ERBS00040', poid=281474987596639,
                                  subnetwork='SubNetwork=ERBS-SUBNW-1')
        self.nodes_list = [self.node1]
        self.num_of_subnetworks = 2
        self.flow.THREAD_QUEUE_TIMEOUT = 0.1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.execute_flow")
    def test_top01_profile_execute_flow__successful(self, mock_flow):
        TOP_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    def test_task_set__is_successful(self, mock_add_error_as_exception, *_):
        user_to_node_info_list = [self.user, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852', 'GNodeB']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    def test_task_set__is_successful_when_user_index_is_0(self, mock_navigate, *_):
        user_to_node_info_list = [self.user, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852', 'GNodeB']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertTrue(mock_navigate.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    def test_task_set__is_successful_when_user_index_greater_than_0(self, mock_navigate, *_):
        user2 = Mock()
        user2.username = "TestTopUser_u1"
        user_to_node_info_list = [user2, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852', 'GNodeB']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertTrue(mock_navigate.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    def test_task_set_is_successful_manage_element_type_equal_to_GNodeB(self, mock_add_error_as_exception, *_):
        user_to_node_info_list = [self.user, ['NR01gNodeBRadio00001', 281474987596639, u'281474979898852', 'GNodeB']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    def test_task_set_is_successful_manage_element_type_equal_to_ENodeB(self, mock_navigate, *_):
        user2 = Mock()
        user2.username = "TestTopUser_u1"
        user_to_node_info_list = [user2, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852', 'ENodeB']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertTrue(mock_navigate.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch(
        'enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcellcu')
    @patch(
        'enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcellcu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    def test_task_set_is_successful_manage_element_type_not_equal_to_GNodeB_or_ENodeB(self, mock_navigate, *_):
        user3 = Mock()
        user3.username = "TestTopUser_u1"
        user_to_node_info_list = [user3, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852', 'CRAN']]
        self.flow.task_set(user_to_node_info_list, self.num_of_subnetworks)
        self.assertTrue(mock_navigate.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.update_nodes_with_subnet_poids')
    def test_get_subnetwork_poid_per_node__is_successful(self, mock_update_nodes, *_):
        node2 = ERBSLoadNode(id='LTE02ERBS00050', simulation='LTE-120', model_identity='1-2-34',
                             # pylint: disable=attribute-defined-outside-init
                             node_id='netsim_LTE02ERBS00050', poid=281474987596699,
                             subnetwork='SubNetwork=ERBS-SUBNW-1')
        self.nodes_list = [self.node1, node2]
        subnetworks = {u'2042102': u'NETSimW', u'2042103': u'ERBS-SUBNW-1'}
        self.user.get.return_value.json.return_value = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [
            {u'noOfChildrens': 1, u'childrens': None, u'moName': u'netsim_LTE02ERBS00040', u'neType': u'ERBS',
             u'syncStatus': u'SYNCHRONIZED', u'moType': u'MeContext', u'poId': 281474987596639,
             u'id': u'281474987596639'}]}]}
        nodes_with_subnet_poids = ['netsim_LTE02ERBS00040', 281474987596639, u'2042103']
        mock_update_nodes.return_value = [nodes_with_subnet_poids]
        result = self.flow.get_subnetwork_poid_per_node(self.user, self.nodes_list, subnetworks)
        expected_result = ([nodes_with_subnet_poids], 2)
        self.assertEqual(result, expected_result)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    def test_get_subnetwork_poid_per_node__raises_http_error(self, mock_add_error_as_exception, *_):
        subnetwork_poids_names = {u'2042103': u'NETSimW'}
        self.user.get.return_value.raise_for_status.side_effect = HTTPError
        self.flow.get_subnetwork_poid_per_node(self.user, self.nodes_list, subnetwork_poids_names)
        self.assertTrue(mock_add_error_as_exception.called)

    def test_get_subnetwork_poid_per_node__raises_enm_application_error(self):
        subnetwork_poids_names = {u'2042103': u'NETSimW'}
        self.user.is_session_established.return_value = False
        self.assertRaises(EnmApplicationError, self.flow.get_subnetwork_poid_per_node, self.user, self.nodes_list,
                          subnetwork_poids_names)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.get_pos_by_poids')
    def test_get_subnetwork_poids_and_names__is_successful(self, mock_get_pos_by_poids):
        search = {"objects": [{"id": "14102", "type": "SubNetwork", "targetTypeAttribute": None}]}
        mock_get_pos_by_poids.return_value.json.return_value = [{"moName": "NETSimW", "poId": "14102"}]
        self.assertEqual(self.flow.get_subnetwork_poids_and_names(self.user, search), {u'14102': u'NETSimW'})

    def test_update_nodes_with_subnet_poids__is_successful(self):
        node = self.node1
        subnetwork_poids_names = {u'2042102': u'NETSimW', u'2042103': u'ERBS-SUBNW-1'}
        node_name_poids = {u'netsim_LTE02ERBS00040': 281474987596639}
        nodes_with_subnet_poids = []
        self.flow.update_nodes_with_subnet_poids(node, subnetwork_poids_names, node_name_poids,
                                                 nodes_with_subnet_poids)

    def test_update_nodes_with_subnet_poids__logs_not_found_when_not_present_in_subnetwork_poids_names(self):
        node = self.node1
        subnetwork_poids_names = {u'2042102': u'NETSimW'}
        node_name_poids = {u'netsim_LTE02ERBS00040': 281474987596639}
        nodes_with_subnet_poids = []
        self.flow.update_nodes_with_subnet_poids(node, subnetwork_poids_names, node_name_poids,
                                                 nodes_with_subnet_poids)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.'
           'update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.'
           'step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poids_and_names')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poid_per_node')
    def test_execute_flow_is_successful(self, mock_get_subnetwork_poid_per_node, mock_get_subnetwork_poids_and_names,
                                        mock_add_error_as_exception, mock_nodes_list,
                                        mock_create_users, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = self.nodes_list
        mock_create_users.return_value = [self.user]
        mock_get_subnetwork_poids_and_names.side_effect = [{u'2042103': u'NETSimW'}, {u'2042102': u'ERBS-SUBNW-1'}]
        nodes_with_subnet_poids = ['netsim_LTE02ERBS00040', 281474987596639, u'2042103']
        mock_get_subnetwork_poid_per_node.return_value = ([nodes_with_subnet_poids], 2)
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.flow.execute_flow()
            self.assertTrue(mock_exchange_nodes.called)
            self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    def test_execute_flow_raises_http_error_due_to_search(self, mock_add_error_as_exception,
                                                          mock_nodes_list, mock_create_users,
                                                          mock_search_execute, mock_exchange_nodes,
                                                          mock_log, *_):
        mock_nodes_list.return_value = [self.node1, self.node1]
        mock_create_users.return_value = [self.user]
        mock_search_execute.side_effect = HTTPError
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.flow.execute_flow()
            self.assertFalse(mock_exchange_nodes.called)
            self.assertTrue(mock_add_error_as_exception.called)
            mock_log.logger.debug.assert_called_with('Issue encountered in setting up pre-requisites. Please restart the'
                                                     ' profile when the environment is stable.')

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poids_and_names')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poid_per_node')
    def test_execute_flow_raises_error_due_to_user_node_mismatch(self, mock_get_subnetwork_poid_per_node, mock_get_subnetwork_poids_and_names,
                                                                 mock_add_error_as_exception, mock_nodes_list,
                                                                 mock_create_users, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = [self.node1, self.node1]
        mock_create_users.return_value = [self.user]
        mock_get_subnetwork_poids_and_names.side_effect = [{u'2042103': u'NETSimW'}, {u'2042102': u'ERBS-SUBNW-1'}]
        nodes_with_subnet_poids = ['netsim_LTE02ERBS00040', 281474987596639, u'2042103']
        mock_get_subnetwork_poid_per_node.return_value = ([nodes_with_subnet_poids] * 2, 2)
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.flow.execute_flow()
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poids_and_names',
           side_effect=[{u'2042103': u'NETSimW'}, {u'2042102': u'ERBS-SUBNW-1'}])
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poid_per_node')
    def test_execute_flow__getsubnet_poid_raises_error(self, mock_get_subnetwork_poid_per_node,
                                                       mock_add_error_as_exception, mock_nodes_list,
                                                       mock_create_users, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = [self.node1, self.node1]
        mock_create_users.return_value = [self.user]
        mock_get_subnetwork_poid_per_node.side_effect = EnmApplicationError
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.flow.execute_flow()
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poid_per_node')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poids_and_names')
    def test_execute_flow__raises_EnvironError_when_no_nodes(self, mock_get_subnetwork_poids_and_names,
                                                             mock_add_error_as_exception, mock_nodes_list,
                                                             mock_create_users, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = []
        mock_create_users.return_value = [self.user]
        mock_get_subnetwork_poids_and_names.side_effect = [{u'2042103': u'NETSimW'}, {u'2042102': u'ERBS-SUBNW-1'}]
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.assertRaises(EnvironError, self.flow.execute_flow())
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.log')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_nrcelldu')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.update_random_attribute_on_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.navigate_topology_browser_app_help')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.Search.execute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poids_and_names')
    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.get_subnetwork_poid_per_node')
    def test_execute_flow_raises_error_due_to_no_nodes_with_subnet_poids(self, mock_get_subnetwork_poid_per_node,
                                                                         mock_get_subnetwork_poids_and_names,
                                                                         mock_add_error_as_exception, mock_nodes_list,
                                                                         mock_create_users, mock_exchange_nodes, *_):
        mock_nodes_list.return_value = [self.node1, self.node1]
        mock_create_users.return_value = [self.user]
        mock_get_subnetwork_poids_and_names.side_effect = [{u'2042103': u'NETSimW'}, {u'2042102': u'ERBS-SUBNW-1'}]
        mock_get_subnetwork_poid_per_node.return_value = ([], 2)
        with patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.keep_running', side_effect=[True, False]):
            self.flow.execute_flow()
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.top_flows.top_01_flow.TOP01Flow.create_and_execute_threads')
    def test_execute_user_tasks(self, mock_threads):
        user_to_node_info_list = [self.user, ['netsim_LTE02ERBS00040', 281474987596639, u'281474979898852']]
        execute_user_tasks(self.flow, user_to_node_info_list, self.flow.NUM_USERS, self.num_of_subnetworks,
                           self.flow.THREAD_QUEUE_TIMEOUT)
        self.assertTrue(mock_threads.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
