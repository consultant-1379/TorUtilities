#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from enmutils.lib.exceptions import NetworkTopologyError
from enmutils_int.lib.topology_browser import (go_to_topology_browser_home,
                                               step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd,
                                               update_random_attribute_on_eutrancellfdd_or_eutrancelltdd,
                                               navigate_topology_browser_app_help, update_random_attribute_on_nrcelldu,
                                               step_through_topology_browser_node_tree_to_nrcelldu,
                                               update_random_attribute_on_nrcellcu,
                                               step_through_topology_browser_node_tree_to_nrcellcu)
from testslib import unit_test_utils


class TopologyBrowserUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_go_to_topology_browser_home_is_successful(self, _):
        response = self.user.get.return_value
        go_to_topology_browser_home(self.user)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcelldu_with_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS',
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement',
                                                                          u'poId': 281474988390922,
                                                                          u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBDUFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBDUFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NRCellDU',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBDUFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertEqual(step_through_topology_browser_node_tree_to_nrcelldu(self.user, "1", "1"), response3)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcelldu_without_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 0, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBDUFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'RadioNode', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}

        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NRCellDU',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NRCellDU',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response2]
        self.assertEqual(step_through_topology_browser_node_tree_to_nrcelldu(self.user, "1", "1"), response2)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcelldu_with_no_gnbdu_function_raises_network_topology_error(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS', u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement', u'poId': 281474988390922, u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_nrcelldu, self.user, "1", "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcelldu_with_no_necelldu_raises_network_topology_error(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS', u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement', u'poId': 281474988390922, u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}],
                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBDUFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBDUFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_nrcelldu, self.user, "1", "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcellcu_with_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS',
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement',
                                                                          u'poId': 281474988390922,
                                                                          u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS',
                                     u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBCUCPFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBCUCPFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NRCellCU',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBCUCPFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertEqual(step_through_topology_browser_node_tree_to_nrcellcu(self.user, "1", "1"), response3)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcellcu_without_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 0, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBCUCPFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'RadioNode',
                                     u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}

        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NRCellCU',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NRCellCU',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response2]
        self.assertEqual(step_through_topology_browser_node_tree_to_nrcellcu(self.user, "1", "1"), response2)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcellcu_with_no_gnbdu_function_raises_network_topology_error(
            self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS',
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement',
                                                                          u'poId': 281474988390922,
                                                                          u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS',
                                     u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_nrcellcu, self.user, "1",
                          "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_nrcellcu_with_no_necelldu_raises_network_topology_error(self,
                                                                                                                _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS',
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement',
                                                                          u'poId': 281474988390922,
                                                                          u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS',
                                     u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}],
                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'GNBDUFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'GNBDUFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_nrcellcu, self.user, "1",
                          "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_nrcelldu_is_successful(self, mock_choice, *_):
        nrelldu_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=NR99gNodeBRadio00034,ManagedElement=1,GNBDUFunction=1,NRCellDU=NR99gNodeBRadio00034-2',
                              u'attributes': [{u'datatype': None, u'value': False, u'key': u'dl256QamEnabled'},
                                              {u'datatype': None, u'value': False, u'key': u'bfrEnabled'}],
                              u'poId': 281474988668320}
        mock_choice.return_value = 'dl256QamEnabled'
        expected_result = {u'datatype': None, u'value': False, u'key': u'dl256QamEnabled'}
        self.assertEqual(update_random_attribute_on_nrcelldu(nrelldu_attributes, self.user), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_nrcelldu_undo_dl256QamEnabled_is_successful(self, mock_choice, *_):
        nrcelldu_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=NR99gNodeBRadio00034,ManagedElement=1,GNBDUFunction=1,NRCellDU=NR99gNodeBRadio00034-2',
                               u'attributes': [{u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'},
                                               {u'datatype': None, u'value': True, u'key': u'bfrEnabled'}],
                               u'poId': 281474988668320}
        mock_choice.return_value = 'dl256QamEnabled'
        attribute_default = {u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'}
        expected_result = attribute_default
        self.assertEqual(update_random_attribute_on_nrcelldu(nrcelldu_attributes, self.user,
                                                             attribute_default=attribute_default,
                                                             action="UNDO"), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_nrcellcu_is_successful(self, mock_choice, *_):
        nrcellcu_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=NR99gNodeBRadio00034,ManagedElement=1,GNBDUFunction=1,NRCellDU=NR99gNodeBRadio00034-2',
                               u'attributes': [{u'datatype': None, u'value': False, u'key': u'hiPrioDetEnabled'},
                                               {u'datatype': None, u'value': False, u'key': u'mcpcPCellEnabled'}],
                               u'poId': 281474988668320}
        mock_choice.return_value = 'hiPrioDetEnabled'
        expected_result = {u'datatype': None, u'value': False, u'key': u'hiPrioDetEnabled'}
        self.assertEqual(update_random_attribute_on_nrcellcu(nrcellcu_attributes, self.user), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_nrcellcu_undo_hiPrioDetEnabled_is_successful(self, mock_choice, *_):
        nrcellcu_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=NR99gNodeBRadio00034,ManagedElement=1,GNBDUFunction=1,NRCellDU=NR99gNodeBRadio00034-2',
                               u'attributes': [{u'datatype': None, u'value': True, u'key': u'hiPrioDetEnabled'},
                                               {u'datatype': None, u'value': True, u'key': u'mcpcPCellEnabled'}],
                               u'poId': 281474988668320}
        mock_choice.return_value = 'hiPrioDetEnabled'
        attribute_default = {u'datatype': None, u'value': True, u'key': u'hiPrioDetEnabled'}
        expected_result = attribute_default
        self.assertEqual(update_random_attribute_on_nrcellcu(nrcellcu_attributes, self.user,
                                                             attribute_default=attribute_default,
                                                             action="UNDO"), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd_with_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS',
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement',
                                                                          u'poId': 281474988390922,
                                                                          u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ENodeBFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'ENodeBFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'EUtranCellFDD',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'ENodeBFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertEqual(step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd(self.user, "1", "1"), response3)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd_without_managed_element_is_successful(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 0, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ENodeBFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'RadioNode', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}

        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'EUtranCellFDD',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'EUtranCellFDD',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response2]
        self.assertEqual(step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd(self.user, "1", "1"), response2)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd_with_no_enodeb_function_raises_network_topology_error(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS', u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement', u'poId': 281474988390922, u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}]}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd, self.user, "1", "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd_with_no_eutrancell_fdd_raises_network_topology_error(self, _):
        response1 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'1', u'neType': u'ERBS', u'syncStatus': u'',
                                                                          u'moType': u'ManagedElement', u'poId': 281474988390922, u'id': u'281474988390922'}],
                                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}],
                     u'moName': u'netsim_LTE02ERBS00021', u'neType': u'ERBS', u'syncStatus': u'SYNCHRONIZED',
                     u'moType': u'MeContext', u'poId': 281474987596605, u'id': u'281474987596605'}
        response2 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'ENodeBFunction',
                                                                          u'poId': 281474988695266,
                                                                          u'id': u'281474988695266'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'ENodeBFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}

        response3 = {u'treeNodes': [{u'noOfChildrens': 1, u'childrens': [{u'noOfChildrens': 1, u'childrens': None,
                                                                          u'moName': u'5', u'neType': None,
                                                                          u'syncStatus': u'',
                                                                          u'moType': u'NodeManagementFunction',
                                                                          u'poId': 281474988695267,
                                                                          u'id': u'281474988695267'}], u'moName': u'1',
                                     u'neType': None, u'syncStatus': u'', u'moType': u'NodeManagementFunction',
                                     u'poId': 281474988390951, u'id': u'281474988390951'}]}
        self.user.get.return_value.json.side_effect = [response1, response2, response3]
        self.assertRaises(NetworkTopologyError, step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd, self.user, "1", "1")

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_eutrancellfdd_or_eutrancelltdd_is_successful(self, mock_choice, *_):
        eutrancell_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00010-3',
                                 u'attributes': [{u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'},
                                                 {u'datatype': None, u'value': [{u'datatype': None, u'value': -1, u'key': u'posCellBearing'},
                                                                                {u'datatype': None, u'value': -1, u'key': u'posCellOpeningAngle'},
                                                                                {u'datatype': None, u'value': 0, u'key': u'posCellRadius'}], u'key': u'eutranCellCoverage'}],
                                 u'poId': 281474988668320}
        mock_choice.return_value = 'dl256QamEnabled'
        expected_result = {u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'}
        self.assertEqual(update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, self.user), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_eutrancellfdd_or_eutrancelltdd_undo_eutranCellCoverage_is_successful(self, mock_choice, *_):
        eutrancell_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00010-3',
                                 u'attributes': [{u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'},
                                                 {u'datatype': None, u'value': [{u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellBearing'},
                                                                                {u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellOpeningAngle'},
                                                                                {u'datatype': 'INTEGER', u'value': 0, u'key': u'posCellRadius'}], u'key': u'eutranCellCoverage'}],
                                 u'poId': 281474988668320}
        mock_choice.return_value = 'eutranCellCoverage'
        attribute_default = {u'datatype': None, u'value': [{u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellBearing'},
                                                           {u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellOpeningAngle'},
                                                           {u'datatype': 'INTEGER', u'value': 0, u'key': u'posCellRadius'}], u'key': u'eutranCellCoverage'}
        expected_result = attribute_default
        self.assertEqual(update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, self.user, attribute_default=attribute_default, action="UNDO"), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_eutrancellfdd_or_eutrancelltdd_undo_eutranCellCoverage_datatpye_none_is_successful(self, mock_choice, *_):
        eutrancell_attributes = {
            u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00010-3',
            u'attributes': [{u'datatype': None, u'value': True, u'key': u'dl256QamEnabled'},
                            {u'datatype': None,
                             u'value': [{u'datatype': None, u'value': -1, u'key': u'posCellBearing'},
                                        {u'datatype': None, u'value': -1, u'key': u'posCellOpeningAngle'},
                                        {u'datatype': None, u'value': 0, u'key': u'posCellRadius'}],
                             u'key': u'eutranCellCoverage'}],
            u'poId': 281474988668320}
        mock_choice.return_value = 'eutranCellCoverage'
        attribute_default = {u'datatype': None, u'key': u'eutranCellCoverage',
                             u'value': [{u'datatype': None, u'key': u'posCellBearing', u'value': -1},
                                        {u'datatype': None, u'key': u'posCellOpeningAngle', u'value': -1},
                                        {u'datatype': None, u'key': u'posCellRadius', u'value': 0}]}
        # When datatype is None for Children of eutranCellCoverage, attribute_default is internally being modified
        # expected_result is the initial value of attribute_default before modification
        expected_result = {u'datatype': None, u'key': u'eutranCellCoverage',
                           u'value': [{u'datatype': None, u'key': u'posCellBearing', u'value': -1},
                                      {u'datatype': None, u'key': u'posCellOpeningAngle', u'value': -1},
                                      {u'datatype': None, u'key': u'posCellRadius', u'value': 0}]}
        self.assertEqual(update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, self.user,
                                                                                   attribute_default=attribute_default,
                                                                                   action="UNDO"), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    @patch("enmutils_int.lib.topology_browser.log")
    @patch("enmutils_int.lib.topology_browser.choice")
    def test_update_random_attribute_on_eutrancellfdd_or_eutrancelltdd_undo_dl256QamEnabled_is_successful(self, mock_choice, *_):
        eutrancell_attributes = {u'fdn': u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00010,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00010-3',
                                 u'attributes': [{u'datatype': None, u'value': False, u'key': u'dl256QamEnabled'},
                                                 {u'datatype': None, u'value': [{u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellBearing'},
                                                                                {u'datatype': 'INTEGER', u'value': -1, u'key': u'posCellOpeningAngle'},
                                                                                {u'datatype': 'INTEGER', u'value': 0, u'key': u'posCellRadius'}], u'key': u'eutranCellCoverage'}],
                                 u'poId': 281474988668320}
        mock_choice.return_value = 'dl256QamEnabled'
        attribute_default = {u'datatype': None, u'value': False, u'key': u'dl256QamEnabled'}
        expected_result = attribute_default
        self.assertEqual(update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, self.user,
                                                                                   attribute_default=attribute_default,
                                                                                   action="UNDO"), expected_result)

    @patch('enmutils_int.lib.topology_browser.time.sleep', return_value=0)
    def test_navigate_topology_browser_app_help_is_successful(self, _):
        navigate_topology_browser_app_help(self.user)
        response = self.user.get.return_value
        self.user.get.assert_any_call("/#help/app/topologybrowser", verify=False)
        self.user.get.assert_any_call("/#help/app/topologybrowser/concept/faq", verify=False)
        self.user.get.assert_any_call("#help/app/topologybrowser/concept/tutorials/tutorial02", verify=False)
        self.user.get.assert_called_with("#help/app/topologybrowser/concept/tutorials/tutorial03", verify=False)
        self.assertTrue(response.raise_for_status.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
