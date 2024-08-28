import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow import (DynamicCrud05Flow, EUTRANETWORK_CMD,
                                                                                    SINGLE_MO_ALL_ATTRIBUTES_URL,
                                                                                    ADD_OPERATION, REMOVE_OPERATION)
from testslib import unit_test_utils


class DynamicCrud05FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()]
        self.profile = DynamicCrud05Flow()
        self.profile.USER_ROLES = 'ADMINISTRATOR'
        self.profile.NUM_USERS = 1
        self.profile.REQ_COUNTS = {}
        self.profile.NUMBER_OF_THREADS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.enm_user_2.User.open_session")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow'
           '.create_profile_users')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.reestablish_session")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow"
           ".sleep_until_next_scheduled_iteration")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.add_remove_obj')
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.flow_setup')
    def test_execute_flow__is_success(self, mock_flow_setup, *_):
        mock_flow_setup.return_value = [(1, "MO")]
        self.profile.execute_flow()
        self.assertEqual(mock_flow_setup.call_count, 1)

    @patch("enmutils.lib.enm_user_2.User.open_session")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow'
           '.create_profile_users')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.reestablish_session")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow"
           ".sleep_until_next_scheduled_iteration")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.add_remove_obj')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.flow_setup')
    def test_execute_flow__adds_exception_when_no_mo_data(self, mock_flow_setup, mock_add_error_as_exception, *_):
        mock_flow_setup.return_value = []
        self.profile.execute_flow()
        self.assertEqual(mock_flow_setup.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_nodes_list_by_attribute")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_filtered_nodes_per_host")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.cleanup_existing_mos")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.prepare_data")
    def test_flow_setup__success(self, mock_prepare_data, mock_cleanup_existing_mos, *_):
        mock_prepare_data.return_value = [(1, 'MO')]
        self.assertEqual(self.profile.flow_setup(self.user, {"PATCH": 1}, 1), [(1, 'MO')])
        self.assertEqual(mock_prepare_data.call_count, 1)
        self.assertEqual(mock_cleanup_existing_mos.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_filtered_nodes_per_host")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.cleanup_existing_mos")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.prepare_data")
    def test_flow_setup__adds_exception_when_no_filtered_nodes(self, mock_prepare_data, mock_cleanup_existing_mos,
                                                               mock_get_filtered_nodes_per_host,
                                                               mock_add_error_as_exception, *_):
        mock_get_filtered_nodes_per_host.return_value = []
        self.profile.flow_setup(self.user, {}, 1)
        self.assertEqual(mock_prepare_data.call_count, 0)
        self.assertEqual(mock_cleanup_existing_mos.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.patch_with_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_final_path_for_url")
    def test_remove_existing_mo__is_successful_when_response_has_status_code_200(self, mock_get_final_path_for_url,
                                                                                 mock_patch_with_payload, mock_debug):
        existing_mos = ["mo1", "mo2"]
        mock_patch_with_payload.return_value.status_code = 200
        self.profile.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 removed successfully.")
        self.assertEqual(mock_get_final_path_for_url.call_count, len(existing_mos))
        self.assertEqual(mock_patch_with_payload.call_count, len(existing_mos))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.patch_with_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_final_path_for_url")
    def test_remove_existing_mo__is_successful_when_response_has_status_code_non_200(self, mock_get_final_path_for_url,
                                                                                     mock_patch_with_payload,
                                                                                     mock_debug):
        existing_mos = ["mo1", "mo2"]
        mock_patch_with_payload.return_value.status_code = 504
        self.profile.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 not removed.")
        self.assertEqual(mock_get_final_path_for_url.call_count, len(existing_mos))
        self.assertEqual(mock_patch_with_payload.call_count, len(existing_mos))

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.patch_with_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_final_path_for_url")
    def test_remove_existing_mo__is_successful_when_response_doesnt_have_status_code(self, mock_get_final_path_for_url,
                                                                                     mock_patch_with_payload,
                                                                                     mock_debug):
        existing_mos = ["mo1", "mo2"]
        mock_patch_with_payload.return_value = Mock(spec="a")
        self.profile.remove_existing_mo(self.user, existing_mos)
        self.assertEqual(mock_debug.call_args[0][0], "MO mo2 not removed.")
        self.assertEqual(mock_get_final_path_for_url.call_count, len(existing_mos))
        self.assertEqual(mock_patch_with_payload.call_count, len(existing_mos))

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.network_flows.network_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.time.sleep', return_value=0)
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.create_and_execute_threads")
    def test_add_remove_obj(self, mock_create_and_execute_threads, *_):
        self.profile.add_remove_obj(self.user, [], 1)
        self.assertEqual(mock_create_and_execute_threads.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug')
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.prepare_data_for_req_obj")
    def test_prepare_data__is_successful(self, mock_prepare_data_for_req_obj, mock_log):
        mock_prepare_data_for_req_obj.return_value = [(1, "MO")]
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        self.assertEqual(self.profile.prepare_data(self.user, self.nodes, {"PATCH": 1}, 1), [(1, 'MO')])
        self.assertEqual(mock_prepare_data_for_req_obj.call_count, 1)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.configure_mo_data")
    def test_prepare_data_for_req_obj__is_successful(self, mock_configure_mo_data, mock_log):
        mock_configure_mo_data.return_value = {"LTEdg2ERBS001": "FDN/MO"}
        self.nodes = ["LTE01dg2ERBS0001", "LTE01dg2ERBS0002", "LTE01dg2ERBS0003"]
        self.assertEqual(self.profile.prepare_data_for_req_obj("PATCH", self.user, self.nodes, {"PATCH": 1}),
                         [(1, "FDN/MO")])
        self.assertEqual(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful(self, mock_get_mo_data_req, _):
        self.profile.configure_mo_data("PATCH", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_random_mo_data")
    def test_get_mo_data_req__is_successful(self, mock_get_random_mo_data, _):
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "MO/FDN"
        self.assertEqual(self.profile.get_mo_data_req("PATCH", self.user, self.nodes), {'LTE01dg2ERBS0001': 'MO/FDN'})
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertIn(EUTRANETWORK_CMD, self.user.enm_execute.call_args[0][0])

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_random_mo_data")
    def test_get_mo_data_req__adds_exception_when_enm_execute_raises_exception(self, mock_get_random_mo_data,
                                                                               mock_add_error_as_exception, *_):
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "MO/FDN"
        self.user.enm_execute.side_effect = Exception
        self.profile.get_mo_data_req("PATCH", self.user, self.nodes)
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_get_final_path_for_url__is_successful(self):
        self.assertEqual(self.profile.get_final_path_for_url("MO_PATH"), SINGLE_MO_ALL_ATTRIBUTES_URL.format("MO_PATH"))

    def test_generate_mo_payload__add_operation_success(self):
        self.assertEqual(ADD_OPERATION, self.profile.generate_mo_payload(self.profile, 1, "add")[0]["op"])

    def test_generate_mo_payload__remove_operation_success(self):
        self.assertEqual(REMOVE_OPERATION, self.profile.generate_mo_payload(self.profile, 1, "remove")[0]["op"])

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.generate_mo_payload")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.get_final_path_for_url")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.patch_with_payload")
    def test_task_set__is_successful(self, mock_patch_with_payload, mock_get_final_path_for_url,
                                     mock_generate_mo_payload):
        self.profile.task_set((1, "MO"), self.profile, self.user, "add")
        self.assertEqual(mock_get_final_path_for_url.call_count, 1)
        self.assertEqual(mock_generate_mo_payload.call_count, 1)
        self.assertEqual(mock_patch_with_payload.call_count, 1)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
