#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from requests.exceptions import HTTPError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.netview_flows.netview_02_flow import Netview02Flow


class Netview02FlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = Netview02Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["NetworkViewer_Administrator"]
        self.flow.NUMBER_OF_NODES = 100
        self.flow.EXCLUDED_STRINGS = ["LTE", "MSC"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_plm_dynamic_content",
           return_value=["node1", "node2"])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_physical_links_on_nodes_by_rest_call")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._create_collection")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._get_poids")
    def test_execute_flow__success(
            self, mock_get_poids, mock_create_users, mock_add_error, mock_all_nodes_in_workload_pool, *_):
        node = Mock(node_id="node1", poid="12345")
        mock_all_nodes_in_workload_pool.return_value = [node]
        mock_create_users.return_value = [self.user]
        mock_get_poids.return_value = ["12345"]
        self.flow.execute_flow()

        self.assertFalse(mock_add_error.called)
        mock_get_poids.assert_called_with([node], ["node1", "node2"])

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_plm_dynamic_content",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_physical_links_on_nodes_by_rest_call")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._create_collection")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._get_poids")
    def test_execute_flow__add_error_while_getting_dynamic_content(
            self, mock_get_poids, mock_create_users, mock_add_error, mock_all_nodes_in_workload_pool, *_):
        node = Mock(node_id="node1", poid="12345")
        mock_all_nodes_in_workload_pool.return_value = [node]
        mock_create_users.return_value = [self.user]
        mock_get_poids.return_value = ["12345"]
        self.flow.execute_flow()

        self.assertTrue(mock_add_error.called)
        self.assertFalse(mock_get_poids.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_plm_dynamic_content")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_physical_links_on_nodes_by_rest_call",
           side_effect=HTTPError)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._create_collection")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._get_poids")
    def test_execute_flow__add_error_if_getting_physical_links_raises_httperror(
            self, mock_get_poids, mock_create_users, mock_add_error, mock_all_nodes_in_workload_pool, *_):
        node = Mock(node_id="node1", poid="12345")
        mock_all_nodes_in_workload_pool.return_value = [node]
        mock_create_users.return_value = [self.user]
        mock_get_poids.return_value = ["12345"]
        self.flow.execute_flow()

        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_get_poids.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_plm_dynamic_content")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.get_physical_links_on_nodes_by_rest_call",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._create_collection")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow._get_poids")
    def test_execute_flow__add_error_if_getting_physical_links_raises_other_error(
            self, mock_get_poids, mock_create_users, mock_add_error, mock_all_nodes_in_workload_pool, *_):
        node = Mock(node_id="node1", poid="12345")
        mock_all_nodes_in_workload_pool.return_value = [node]
        mock_create_users.return_value = [self.user]
        mock_get_poids.return_value = ["12345"]
        self.flow.execute_flow()

        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_get_poids.called)

    def test_create_collection_true(self):
        collection_obj = Mock()
        collection_obj.exists = True
        self.flow._create_collection(collection_obj, [])

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    def test_create_collection_false(self, mock_add_error_as_exception):
        collection_obj = Mock()
        collection_obj.exists = False
        collection_obj.create.side_effect = Exception
        self.flow._create_collection(collection_obj, [])

        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.filter_nodes_having_poid_set")
    def test_get_poids__successful(self, mock_filter_nodes_having_poid_set):
        node1 = Mock(node_id="node1", poid="12345")
        node2 = Mock(node_id="node2", poid="23456")
        node3 = Mock(node_id="node3", poid="")
        all_nodes = [node1, node2, node3]
        mock_filter_nodes_having_poid_set.return_value = [node1, node2]
        self.flow.NUMBER_OF_NODES = 2
        self.assertEqual(["12345", "23456"], self.flow._get_poids(all_nodes=all_nodes, node_ids=["node1", "node2"]))
        mock_filter_nodes_having_poid_set.assert_called_with([node1, node2])

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.Netview02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_02_flow.filter_nodes_having_poid_set")
    def test_get_poids__adds_error_if_not_all_poids_found(
            self, mock_filter_nodes_having_poid_set, mock_add_error_as_exception):
        node1 = Mock(node_id="node1", poid="12345")
        node2 = Mock(node_id="node2", poid="")
        node3 = Mock(node_id="node3", poid="34567")
        all_nodes = [node1, node2, node3]
        mock_filter_nodes_having_poid_set.return_value = [node1]
        self.flow.NUMBER_OF_NODES = 2
        self.assertEqual(["12345"], self.flow._get_poids(all_nodes=all_nodes, node_ids=["node1", "node2"]))
        mock_filter_nodes_having_poid_set.assert_called_with([node1, node2])
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
