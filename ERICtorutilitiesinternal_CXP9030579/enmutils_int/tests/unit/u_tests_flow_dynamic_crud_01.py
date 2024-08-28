#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow import (DynamicCrud01Flow,
                                                                                    SINGLE_MO_ALL_CHILD_URL,
                                                                                    SINGLE_MO_WITH_ATTR_URL,
                                                                                    SINGLE_NODE_ALL_ATTRIBUTES_WITH_MO_TYPE_URL,
                                                                                    REQ_4_5_6_ATTRS,
                                                                                    REQ_7_to_10_ATTRS)
from testslib import unit_test_utils


class DynamicCrud01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()]
        self.flow = DynamicCrud01Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.prepare_data_for_req")
    def test_prepare_data__is_successful(self, mock_prepare_data_for_req, _):
        mock_prepare_data_for_req.return_value = [("REQ", "abc")]
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        self.assertEqual(self.flow.prepare_data(self.user, self.nodes, {"REQ": "abc"}, 1), [('REQ', 'abc')] * 6)
        self.assertEqual(mock_prepare_data_for_req.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_1to6_and_mo_data_cells_not_present(self,
                                                                                             mock_get_mo_data_req, _):
        self.flow.configure_mo_data("REQ_4_5_6", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_1to6_and_mo_data_cells_present(self, mock_get_mo_data_req, _):
        self.flow.mo_data_cells = {"a": "b"}
        self.flow.configure_mo_data("REQ_4_5_6", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_7or9_and_mo_data_nodes_4g_present(self, mock_get_mo_data_req, _):
        self.flow.mo_data_nodes_4g = {"a": "b"}
        self.flow.configure_mo_data("REQ_7", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req")
    def test_configure_mo_data__is_successful_when_req_is_8or10_and_mo_data_nodes_5g_present(self,
                                                                                             mock_get_mo_data_req, _):
        self.flow.mo_data_nodes_5g = {"a": "b"}
        self.flow.configure_mo_data("REQ_10", self.user, self.nodes)
        self.assertEqual(mock_get_mo_data_req.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.log.logger.debug")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_7_to_10")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_based_on_cell_type")
    def test_get_mo_data_req__is_successful_when_req_is_1to6(self, mock_get_mo_data_req_based_on_cell_type,
                                                             mock_get_mo_data_req_7_to_10, _):
        mock_get_mo_data_req_based_on_cell_type.return_value = {"c": "d"}
        self.assertEqual(self.flow.get_mo_data_req("REQ_1_2_3", self.user, self.nodes), {"c": "d"})
        self.assertEqual(self.flow.mo_data_cells, {"c": "d"})
        self.assertEqual(mock_get_mo_data_req_based_on_cell_type.call_count, 1)
        self.assertEqual(mock_get_mo_data_req_7_to_10.call_count, 0)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_based_on_cell_type")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_7_to_10")
    def test_get_mo_data_req__is_successful_when_req_is_7or9(self, mock_get_mo_data_req_7_to_10,
                                                             mock_get_mo_data_req_based_on_cell_type):
        mock_get_mo_data_req_7_to_10.return_value = {"e": "f"}
        self.assertEqual(self.flow.get_mo_data_req("REQ_9", self.user, self.nodes), {"e": "f"})
        self.assertEqual(self.flow.mo_data_nodes_4g, {"e": "f"})
        self.assertEqual(mock_get_mo_data_req_based_on_cell_type.call_count, 0)
        self.assertEqual(mock_get_mo_data_req_7_to_10.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_7_to_10")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_based_on_cell_type")
    def test_get_mo_data_req__returns_empty_when_req_is_not_from_1to10(self, mock_get_mo_data_req_based_on_cell_type,
                                                                       mock_get_mo_data_req_7_to_10):
        self.assertEqual(self.flow.get_mo_data_req("REQ_11", self.user, self.nodes), {})
        self.assertEqual(mock_get_mo_data_req_based_on_cell_type.call_count, 0)
        self.assertEqual(mock_get_mo_data_req_7_to_10.call_count, 0)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_based_on_cell_type")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_mo_data_req_7_to_10")
    def test_get_mo_data_req__is_successful_when_req_is_8or10(self, mock_get_mo_data_req_7_to_10,
                                                              mock_get_mo_data_req_based_on_cell_type):
        mock_get_mo_data_req_7_to_10.return_value = {"e": "f"}
        self.assertEqual(self.flow.get_mo_data_req("REQ_8", self.user, self.nodes), {"e": "f"})
        self.assertEqual(self.flow.mo_data_nodes_5g, {"e": "f"})
        self.assertEqual(mock_get_mo_data_req_based_on_cell_type.call_count, 0)
        self.assertEqual(mock_get_mo_data_req_7_to_10.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_random_mo_data")
    def test_get_mo_data_req_7_to_10__is_successful(self, mock_get_random_mo_data):
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.assertEqual(self.flow.get_mo_data_req_7_to_10(self.user, self.nodes), {'LTE01dg2ERBS0001': 'mock_fdn'})
        self.assertEqual(self.user.enm_execute.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.add_error_as_exception")
    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.get_random_mo_data")
    def test_get_mo_data_req_7_to_10__adds_exception_when_enm_execute_raises_exception(self, mock_get_random_mo_data,
                                                                                       mock_add_error_as_exception):
        self.nodes[0].node_id = "LTE01dg2ERBS0001"
        mock_get_random_mo_data.return_value = "mock_fdn"
        self.user.enm_execute.side_effect = Exception
        self.flow.get_mo_data_req_7_to_10(self.user, self.nodes)
        self.assertEqual(self.user.enm_execute.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_get_final_path_for_url__is_successful_for_req_1_2_3(self):
        self.assertEqual(self.flow.get_final_path_for_url("REQ_1_2_3", "mo_path_req_1_2_3"),
                         SINGLE_MO_ALL_CHILD_URL.format("mo_path_req_1_2_3"))

    def test_get_final_path_for_url__is_successful_for_req_4_5_6_fdd(self):
        self.assertEqual(self.flow.get_final_path_for_url("REQ_4_5_6", "FDD_mo_path_req_4_5_6"),
                         SINGLE_MO_WITH_ATTR_URL.format("FDD_mo_path_req_4_5_6", REQ_4_5_6_ATTRS[0]))

    def test_get_final_path_for_url__is_successful_for_req_4_5_6_tdd(self):
        self.assertEqual(self.flow.get_final_path_for_url("REQ_4_5_6", "TDD_mo_path_req_4_5_6"),
                         SINGLE_MO_WITH_ATTR_URL.format("TDD_mo_path_req_4_5_6", REQ_4_5_6_ATTRS[1]))

    def test_get_final_path_for_url__is_successful_for_req_4_5_6_5g(self):
        self.assertEqual(self.flow.get_final_path_for_url("REQ_4_5_6", "NRCellDU_mo_path_req_4_5_6"),
                         SINGLE_MO_WITH_ATTR_URL.format("NRCellDU_mo_path_req_4_5_6", REQ_4_5_6_ATTRS[2]))

    def test_get_final_path_for_url__is_successful_for_req_7to9(self):
        req = "REQ_8"
        self.assertEqual(self.flow.get_final_path_for_url(req, "mo_path_req_8"),
                         SINGLE_NODE_ALL_ATTRIBUTES_WITH_MO_TYPE_URL.format("mo_path_req_8", REQ_7_to_10_ATTRS[req]))

    def test_get_final_path_for_url__is_successful_for_req_outside_1to10(self):
        req = "REQ_11"
        self.assertEqual(self.flow.get_final_path_for_url(req, "mo_path_req_10"),
                         "")

    def test_remove_existing_mo__returns_none(self):
        self.assertIsNone(self.flow.remove_existing_mo(self.user, []))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
