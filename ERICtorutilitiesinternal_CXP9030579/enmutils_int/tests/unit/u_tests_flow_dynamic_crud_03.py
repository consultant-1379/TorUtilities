#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow import (DynamicCrud03Flow,
                                                                                    SINGLE_MO_ALL_ATTRIBUTES_URL,
                                                                                    MO_START, MO_END)
from testslib import unit_test_utils


class DynamicCrud03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()]
        self.flow = DynamicCrud03Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.REQ_COUNTS = {"REQ_1_2_3": 1}
        self.flow.NUMBER_OF_THREADS = 1
        self.flow.NUM_USERS = 1
        self.flow.MAX_NODES = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.prepare_data_for_req")
    def test_prepare_data__is_successful(self, mock_prepare_data_for_req):
        mock_prepare_data_for_req.return_value = [("REQ", "abc")]
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        self.assertEqual(self.flow.prepare_data(self.user, self.nodes, {"REQ": "abc"}, 1), [('REQ', 'abc')])
        self.assertEqual(mock_prepare_data_for_req.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_1_2_3(self,
                                                                mock_get_mo_data_req):
        self.flow.configure_mo_data("REQ_1_2_3", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_random_mo_data")
    def test_get_mo_data_req__is_successful_when_req_is_1_2_3(self, mock_get_random_mo_data):
        mock_get_random_mo_data.return_value = {"c": "d"}
        self.assertEqual(self.flow.get_mo_data_req("REQ_1_2_3", self.user, self.nodes),
                         {self.nodes[0].node_id: {"c": "d"}})
        self.assertEqual(mock_get_random_mo_data.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_random_mo_data")
    def test_get_mo_data_req__adds_exception_when_req_is_1_2_3_enm_execute_raises_exception(self,
                                                                                            mock_get_random_mo_data,
                                                                                            mock_add_error_as_exception):
        mock_get_random_mo_data.return_value = {"c": "d"}
        self.user.enm_execute.side_effect = Exception
        self.flow.get_mo_data_req("REQ_1_2_3", self.user, self.nodes)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_get_final_path_for_url__is_successful_for_req_1_2_3(self):
        self.assertEqual(self.flow.get_final_path_for_url("mo_path_req_1_2_3"),
                         SINGLE_MO_ALL_ATTRIBUTES_URL.format("mo_path_req_1_2_3"))

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.time.sleep", return_value=None)
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.flow_setup")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_update_delete_flow")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.prepare_data")
    def test_execute_flow__is_successful(self, mock_prepare_data, mock_create_update_delete_flow,
                                         mock_create_profile_users, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_prepare_data.return_value = [("REQ_1_2_3", "abc")]
        self.flow.execute_flow()
        self.assertEqual(mock_create_update_delete_flow.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_update_delete_flow")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.flow_setup",
        return_value=[])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_and_execute_threads")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.prepare_data")
    def test_execute_flow__adds_exception_when_no_mo_data(self, mock_prepare_data, mock_create_and_execute_threads,
                                                          mock_add_error_as_exception, *_):
        mock_prepare_data.return_value = []
        self.flow.execute_flow()
        self.assertEqual(mock_create_and_execute_threads.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.time.sleep", return_value=None)
    def test_reestablish_session__is_successful(self, _):
        self.flow.reestablish_session(self.user)
        self.assertEqual(self.user.open_session.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.time.sleep", return_value=None)
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.cleanup_existing_mos")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.partial")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.reestablish_session")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.create_and_execute_threads")
    def test_create_update_delete_flow__is_successful(self, mock_create_and_execute_threads, mock_reestablish_session,
                                                      *_):
        self.flow.create_update_delete_flow([('REQ', 'abc')], 1, self.user)
        self.assertEqual(mock_reestablish_session.call_count, 2)
        self.assertEqual(mock_create_and_execute_threads.call_count, 3)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.cleanup_existing_mos")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_filtered_nodes_per_host")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.reestablish_session")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.prepare_data")
    def test_flow_setup__is_successful(self, mock_prepare_data, mock_reestablish_session, *_):
        self.flow.flow_setup(self.user, 1, {"REQ_1": 1})
        self.assertEqual(mock_reestablish_session.call_count, 1)
        self.assertEqual(mock_prepare_data.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.delete_given_url")
    def test_remove_existing_mo__is_successful_when_response_has_status_code_200(self, mock_delete_given_url,
                                                                                 mock_debug, _):
        existing_mos = ["mo1", "mo2"]
        mock_delete_given_url.return_value.status_code = 200
        self.flow.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 removed successfully.")
        self.assertEqual(mock_delete_given_url.call_count, len(existing_mos))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.delete_given_url")
    def test_remove_existing_mo__is_successful_when_response_has_status_code_non_200(self, mock_delete_given_url,
                                                                                     mock_debug, _):
        existing_mos = ["mo1", "mo2"]
        mock_delete_given_url.return_value.status_code = 504
        self.flow.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 not removed.")
        self.assertEqual(mock_delete_given_url.call_count, len(existing_mos))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.delete_given_url")
    def test_remove_existing_mo__is_successful_when_response_doesnt_have_status_code(self, mock_delete_given_url,
                                                                                     mock_debug, _):
        existing_mos = ["mo1", "mo2"]
        mock_delete_given_url.return_value = Mock(spec="a")
        self.flow.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 not removed.")
        self.assertEqual(mock_delete_given_url.call_count, len(existing_mos))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.post_to_url_with_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    def test_task_set__is_successful(self, mock_get_final_path_for_url, mock_post_to_url_with_payload):
        self.flow.task_set((self.user, [("REQ_1", "mo_path_req_1")]), self.flow, self.user)
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_post_to_url_with_payload.call_count, MO_END - MO_START)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.put_to_url_with_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    def test_update_task_set__is_successful(self, mock_get_final_path_for_url, mock_put_to_url_with_payload):
        self.flow.update_task_set((self.user, [("REQ_1", "mo_path_req_1")]), self.flow, self.user)
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_put_to_url_with_payload.call_count, MO_END - MO_START)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.delete_given_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.get_final_path_for_url")
    def test_delete_task_set__is_successful(self, mock_get_final_path_for_url, mock_delete_given_url):
        self.flow.delete_task_set((self.user, [("REQ_1", "mo_path_req_1")]), self.flow, self.user)
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_delete_given_url.call_count, MO_END - MO_START)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
