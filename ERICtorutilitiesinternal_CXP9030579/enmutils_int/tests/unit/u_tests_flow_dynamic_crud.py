#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow import (DynamicCrudFlow, REQ_1_2_3_CELLS_CMD,
                                                                                 EnvironWarning)
from testslib import unit_test_utils


class DynamicCrudFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()]
        self.flow = DynamicCrudFlow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.REQ_COUNTS = {}
        self.flow.NUMBER_OF_THREADS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_given_url__is_successful(self):
        self.flow.get_given_url(self.user, "abc")
        self.assertEqual(self.user.get.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    def test_get_given_url__adds_exception_when_get_raises_exception(self, mock_add_error_as_exception):
        self.user.get.side_effect = Exception
        self.flow.get_given_url(self.user, "abc")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_patch_with_payload__is_successful(self):
        self.flow.patch_with_payload(self.user, "url", [])
        self.assertEqual(self.user.patch.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    def test_patch_with_payload__adds_exception_when_patch_raises_exception(self, mock_add_error_as_exception):
        self.user.patch.side_effect = Exception
        self.flow.patch_with_payload(self.user, "url", [])
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_post_to_url_with_payload__is_successful(self):
        self.flow.post_to_url_with_payload(self.user, "url", "abc")
        self.assertEqual(self.user.post.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    def test_post_to_url_with_payload__adds_exception_when_post_raises_exception(self, mock_add_error_as_exception):
        self.user.post.side_effect = Exception
        self.flow.post_to_url_with_payload(self.user, "url", "abc")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_put_to_url_with_payload__is_successful(self):
        self.flow.put_to_url_with_payload(self.user, "url", "abc")
        self.assertEqual(self.user.put.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    def test_put_to_url_with_payload__adds_exception_when_put_raises_exception(self, mock_add_error_as_exception):
        self.user.put.side_effect = Exception
        self.flow.put_to_url_with_payload(self.user, "url", "abc")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_delete_given_url__is_successful(self):
        self.flow.delete_given_url(self.user, "abc")
        self.assertEqual(self.user.delete_request.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    def test_delete_given_url_adds_exception_when_delete_raises_exception(self, mock_add_error_as_exception):
        self.user.delete_request.side_effect = Exception
        self.flow.delete_given_url(self.user, "abc")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.time.sleep", return_value=None)
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.reestablish_session")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.create_and_execute_threads")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.prepare_data")
    def test_execute_flow__is_successful(self, mock_prepare_data, mock_create_and_execute_threads,
                                         mock_create_profile_users, mock_reestablish_session, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_prepare_data.return_value = [("REQ_7", "abc")]
        self.flow.execute_flow()
        self.assertEqual(mock_reestablish_session.call_count, 1)
        self.assertEqual(mock_create_and_execute_threads.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.reestablish_session")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.time.sleep", return_value=None)
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.exchange_nodes")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.sleep_until_next_scheduled_iteration")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.keep_running",
        side_effect=[True, False])
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.create_profile_users")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.create_and_execute_threads")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.prepare_data")
    def test_execute_flow__adds_exception_when_no_mo_data(self, mock_prepare_data, mock_create_and_execute_threads,
                                                          mock_add_error_as_exception, *_):
        mock_prepare_data.return_value = []
        self.flow.execute_flow()
        self.assertEqual(mock_create_and_execute_threads.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_remove_existing_mo__raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.flow.remove_existing_mo(self.user, [])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.remove_existing_mo")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.check_existing_mo")
    def test_cleanup_existing_mos__calls_remove_existing_mo_if_there_are_existing_mos(self, mock_check_existing_mo,
                                                                                      mock_remove_existing_mo):
        mock_check_existing_mo.return_value = ["mo"]
        self.flow.cleanup_existing_mos(self.user)
        self.assertEqual(mock_remove_existing_mo.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.remove_existing_mo")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.check_existing_mo")
    def test_cleanup_existing_mos__doesnt_call_remove_existing_mo_if_there_are_no_existing_mos(self,
                                                                                               mock_check_existing_mo,
                                                                                               mock_remove_existing_mo):
        mock_check_existing_mo.return_value = []
        self.flow.cleanup_existing_mos(self.user)
        self.assertEqual(mock_remove_existing_mo.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.log.logger.debug')
    def test_check_existing_mo__returns_mo_list(self, mock_log):
        response = Mock()
        response.get_output.return_value = ["FDN : managed_element,mo", "abc"]
        self.user.enm_execute.return_value = response
        self.assertEqual(self.flow.check_existing_mo(self.user), ["managed_element/mo"])
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.log.logger.debug')
    def test_check_existing_mo__returns_empty_list(self, mock_log):
        response = Mock()
        response.get_output.return_value = ["managed_element,mo", "abc"]
        self.user.enm_execute.return_value = response
        self.assertEqual(self.flow.check_existing_mo(self.user), [])
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertEqual(mock_log.call_count, 2)

    def test_prepare_data__raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.flow.prepare_data(self.user, [], {}, 1)

    def test_configure_mo_data__raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.flow.configure_mo_data("", self.user, [])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.configure_mo_data")
    def test_prepare_data_for_req__is_successful(self, mock_configure_mo_data):
        mock_configure_mo_data.return_value = {"LTEdg2ERBS001": "me/fdn"}
        self.assertEqual(self.flow.prepare_data_for_req("REQ_9", self.user, self.nodes, {"REQ_9": 1}, 2),
                         [('REQ_9', 'me/fdn')])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.configure_mo_data")
    def test_prepare_data_for_req__is_successful_when_randomize_mo_data_is_false(self, mock_configure_mo_data):
        mock_configure_mo_data.return_value = {"node_id": "me/fdn"}
        self.assertEqual(self.flow.prepare_data_for_req("REQ_1_2_3", self.user, self.nodes, {"REQ_1_2_3": 1}, 2, False),
                         ['me/fdn'])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.configure_mo_data")
    def test_prepare_data_for_req__adds_exception_when_configure_mo_data_returns_empty_dict(self,
                                                                                            mock_configure_mo_data):
        mock_configure_mo_data.return_value = {}
        self.assertEqual(self.flow.prepare_data_for_req("REQ_7", self.user, self.nodes, {"REQ_7": 1}, 1), [])

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.random.choice")
    def test_get_random_mo_data__is_successful(self, mock_choice):
        response = Mock()
        response.get_output.return_value = ["FDN : mock_managed_element,mock_fdn", "abc"]
        mock_choice.return_value = "FDN : mock_managed_element,mock_fdn"
        self.assertEqual(self.flow.get_random_mo_data(response, []), "mock_managed_element/mock_fdn")

    def test_get_random_mo_data__raises_environ_warning_when_no_matching_fdns(self):
        response = Mock()
        response.get_output.return_value = []
        with self.assertRaises(EnvironWarning):
            self.flow.get_random_mo_data(response, [])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrudFlow.get_random_mo_data")
    def test_get_mo_data_req_based_on_cell_type__is_successful_when_lte_cell_type_is_tdd(self, mock_get_random_mo_data):
        self.nodes[0].lte_cell_type = "TDD"
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.assertEqual(self.flow.get_mo_data_req_based_on_cell_type(self.user, self.nodes),
                         {'LTE01dg2ERBS0001': 'mock_fdn'})
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertIn(REQ_1_2_3_CELLS_CMD[0], self.user.enm_execute.call_args[0][0])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrudFlow.get_random_mo_data")
    def test_get_mo_data_req_based_on_cell_type__is_successful_when_lte_cell_type_is_fdd(self, mock_get_random_mo_data):
        self.nodes[0].lte_cell_type = "FDD"
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.assertEqual(self.flow.get_mo_data_req_based_on_cell_type(self.user, self.nodes),
                         {'LTE01dg2ERBS0001': 'mock_fdn'})
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertIn(REQ_1_2_3_CELLS_CMD[1], self.user.enm_execute.call_args[0][0])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrudFlow.get_random_mo_data")
    def test_get_mo_data_req_based_on_cell_type__is_successful_when_lte_cell_type_is_not_tdd_or_fdd(self,
                                                                                                    mock_get_random_mo_data):
        self.nodes[0].node_id = "NR01gNodeBRadio00001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.assertEqual(self.flow.get_mo_data_req_based_on_cell_type(self.user, self.nodes),
                         {'NR01gNodeBRadio00001': 'mock_fdn'})
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertIn(REQ_1_2_3_CELLS_CMD[2], self.user.enm_execute.call_args[0][0])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrudFlow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrudFlow.get_random_mo_data")
    def test_get_mo_data_req_based_on_cell_type__adds_exception_when_enm_execute_raises_exception(self,
                                                                                                  mock_get_random_mo_data,
                                                                                                  mock_add_error_as_exception):
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.user.enm_execute.side_effect = Exception
        self.flow.get_mo_data_req_based_on_cell_type(self.user, self.nodes)
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_get_final_path_for_url__raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.flow.get_final_path_for_url("", "")

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.get_given_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.DynamicCrudFlow.get_final_path_for_url")
    def test_task_set__is_successful(self, mock_get_final_path_for_url, mock_get_given_url):
        self.flow.task_set(("REQ_8", "mo_path_req_8"), self.flow, self.user)
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_get_given_url.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
