#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow import (DynamicCrud04Flow,
                                                                                    SINGLE_MO_ALL_ATTRIBUTES_URL)
from testslib import unit_test_utils


class DynamicCrud04FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()]
        self.flow = DynamicCrud04Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.REQ_COUNTS = {"REQ_1_2_3": 1}
        self.flow.NUMBER_OF_THREADS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.prepare_data_for_req")
    def test_prepare_data__is_successful(self, mock_prepare_data_for_req):
        mock_prepare_data_for_req.return_value = [("REQ", "abc")]
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        self.assertEqual(self.flow.prepare_data(self.user, self.nodes, {"REQ": "abc"}, 1), [('REQ', 'abc')])
        self.assertEqual(mock_prepare_data_for_req.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_1_2_3(self,
                                                                mock_get_mo_data_req):
        self.flow.configure_mo_data("REQ_1_2_3", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_mo_data_req_based_on_cell_type")
    def test_get_mo_data_req__is_successful_when_req_is_1_2_3(self, mock_get_mo_data_req_based_on_cell_type):
        mock_get_mo_data_req_based_on_cell_type.return_value = {"c": "d"}
        self.assertEqual(self.flow.get_mo_data_req("REQ_1_2_3", self.user, self.nodes), {"c": "d"})
        self.assertEqual(mock_get_mo_data_req_based_on_cell_type.call_count, 1)

    def test_get_final_path_for_url__is_successful_for_req_1_2_3(self):
        self.assertEqual(self.flow.get_final_path_for_url("REQ_1_2_3", "mo_path_req_1_2_3"),
                         SINGLE_MO_ALL_ATTRIBUTES_URL.format("mo_path_req_1_2_3"))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.reestablish_session")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.create_and_execute_threads")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.prepare_data")
    def test_execute_flow__is_successful(self, mock_prepare_data, mock_create_and_execute_threads,
                                         mock_create_profile_users, mock_reestablish_session, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_prepare_data.return_value = [("REQ_7", "abc")]
        self.flow.execute_flow()
        self.assertEqual(mock_reestablish_session.call_count, 1)
        self.assertEqual(mock_create_and_execute_threads.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.reestablish_session")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.create_and_execute_threads")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.prepare_data")
    def test_execute_flow__adds_exception_when_no_mo_data(self, mock_prepare_data, mock_create_and_execute_threads,
                                                          mock_add_error_as_exception, *_):
        mock_prepare_data.return_value = []
        self.flow.execute_flow()
        self.assertEqual(mock_create_and_execute_threads.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_given_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.get_final_path_for_url")
    def test_task_set__is_successful(self, mock_get_final_path_for_url, mock_get_given_url):
        self.flow.task_set([["REQ_1", "mo_path_req_1"]], self.flow, self.user)
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_get_given_url.call_count, 1)

    def test_remove_existing_mo__returns_none(self):
        self.assertIsNone(self.flow.remove_existing_mo(self.user, []))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
