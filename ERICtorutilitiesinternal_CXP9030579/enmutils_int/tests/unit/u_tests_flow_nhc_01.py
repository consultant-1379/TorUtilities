#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import patch, Mock
from enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow import Nhc01
from enmutils.lib.enm_node import ERBSNode as erbs


class NHC01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = Nhc01()
        self.nodes = [erbs(node_id='LTEdg2ERBS00001', primary_type='ERBS'),
                      erbs(node_id='LTEdg2ERBS00002', primary_type='ERBS'),
                      erbs(node_id='MGw01', primary_type='MGW'), erbs(node_id='MGw02', primary_type='MGW')]
        self.nodes_dict = {'ERBS': ['LTEdg2ERBS00001', 'LTEdg2ERBS00002'], 'MGW': ['MGw01', 'MGw02']}
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "Nhc_Operator"
        self.flow.NHC_SLEEP = 120
        self.flow.START_TIME = "20:00:00"
        self.flow.STOP_TIME = "06:00:00"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.state")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.NHCCmds")
    def test_execute_nhc_01_flow_is_successful(self, mock_nhc_cmds, mock_create_users, mock_nodes, mock_nodes_dict,
                                               *_):
        self.flow.SCHEDULED_TIMES = []
        mock_create_users.return_value = [self.user]
        mock_nodes.return_value = self.nodes
        mock_nodes_dict.return_value = self.nodes_dict
        self.flow.execute_nhc_01_flow()
        mock_nodes_dict.assert_called_with(self.nodes, "primary_type")
        self.assertTrue(mock_nhc_cmds.return_value.execute.call_count, 2)
        self.assertEqual(len(self.flow.SCHEDULED_TIMES), 5)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.state")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.NHCCmds")
    def test_execute_nhc_01_flow_add_error_as_exception(self, mock_nhc_cmds, mock_create_users, mock_nodes,
                                                        mock_nodes_dict, mock_add_error_as_exception, *_):
        self.flow.SCHEDULED_TIMES = []
        mock_create_users.return_value = [self.user]
        mock_nhc_cmds.return_value.execute.side_effect = [Exception, None]
        mock_nodes.return_value = self.nodes
        mock_nodes_dict.return_value = self.nodes_dict
        self.flow.execute_nhc_01_flow()
        mock_nodes_dict.assert_called_with(self.nodes, "primary_type")
        self.assertEqual(len(self.flow.SCHEDULED_TIMES), 5)
        self.assertTrue(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
