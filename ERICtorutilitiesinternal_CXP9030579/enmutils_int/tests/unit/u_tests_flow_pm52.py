#!/usr/bin/env python

from datetime import datetime

import unittest2
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.pm_flows import pm52profile
from enmutils_int.lib.workload import pm_52
from mock import patch, PropertyMock, Mock, call
from testslib import unit_test_utils

USER = Mock()


class Pm52ProfileUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(spec_set=User(username="test"))
        self.pm_52 = pm_52.PM_52()
        self.profile = pm52profile.Pm52Profile()
        self.profile.NAME = "PM_52"
        self.profile.USER_ROLES = ['Cmedit_Administrator', 'PM_Operator']
        self.profile.NODES_TO_FIND = {'RadioNode': 2}
        self.profile.SCHEDULED_TIMES_STRINGS = ["08:00:00", "12:00:00"]

        self.radionode1 = Mock(node_id="radionode1", primary_type="RadioNode", netsim="netsim2")
        self.radionode2 = Mock(node_id="radionode2", primary_type="RadioNode", netsim="netsim3")
        self.radionode3 = Mock(node_id="radionode3", primary_type="RadioNode", netsim="netsim4")
        self.radionode4 = Mock(node_id="radionode4", primary_type="RadioNode", netsim="netsim3")

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def get_nodes(node_type, number_of_nodes):
        return [Mock(primary_type=node_type)] * number_of_nodes

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_profile_users", return_value=[USER])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.keep_running",
           side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.start_ulsa_uplink_measurement")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.perform_teardown_actions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_profile_nodes")
    def test_execute_flow__is_successful(
            self, mock_filter_profile_nodes, mock_perform_teardown_actions,
            mock_partial, mock_create_and_execute_threads, start_ulsa_uplink_measurement, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            selected_nodes = [Mock()]
            mock_filter_profile_nodes.return_value = selected_nodes
            self.profile.execute_flow()
            mock_partial.assert_called_with(mock_perform_teardown_actions, USER, selected_nodes, self.profile)
            mock_create_and_execute_threads.assert_called_with(
                selected_nodes, len(selected_nodes), func_ref=start_ulsa_uplink_measurement, args=[USER])
            self.assertEqual(mock_partial.call_count, 1)
            self.assertEqual(mock_create_and_execute_threads.call_count, 2)
            mock_check_and_remove_old_ulsas_in_enm.assert_called_with(USER, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_profile_users", return_value=[USER])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_and_remove_old_ulsas_in_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_profile_nodes")
    def test_execute_flow__add_error_to_profile_if_no_nodes_selected(
            self, mock_filter_profile_nodes, mock_keep_running, mock_add_error_as_exception,
            mock_check_and_remove_old_ulsas_in_enm, *_):
        mock_filter_profile_nodes.return_value = []
        self.profile.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertFalse(mock_keep_running.called)
        self.assertFalse(mock_check_and_remove_old_ulsas_in_enm.called)

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_profile_users", return_value=[USER])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.keep_running",
           side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.start_ulsa_uplink_measurement")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.perform_teardown_actions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_profile_nodes")
    def test_execute_flow__add_error_if_check_and_remove_old_ulsas_in_enm_raises_enm_application_error(
            self, mock_filter_profile_nodes, mock_perform_teardown_actions,
            mock_partial, mock_create_and_execute_threads, start_ulsa_uplink_measurement, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            with patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile."
                       "Pm52Profile.add_error_as_exception") as mock_add_error:
                selected_nodes = [Mock()]
                mock_filter_profile_nodes.return_value = selected_nodes
                mock_check_and_remove_old_ulsas_in_enm.side_effect = EnmApplicationError("ENM command execution "
                                                                                         "unsuccessful")
                self.profile.execute_flow()
                mock_partial.assert_called_with(mock_perform_teardown_actions, USER, selected_nodes, self.profile)
                mock_create_and_execute_threads.assert_called_with(
                    selected_nodes, len(selected_nodes), func_ref=start_ulsa_uplink_measurement, args=[USER])
                self.assertEqual(mock_partial.call_count, 1)
                self.assertEqual(mock_create_and_execute_threads.call_count, 2)
                self.assertTrue(mock_check_and_remove_old_ulsas_in_enm.called)
                self.assertTrue(call(mock_check_and_remove_old_ulsas_in_enm.side_effect in mock_add_error.mock_calls))

    # select_nodes_to_use test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_list_from_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_nodes_info_with_ulsa_mos")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_enm_network_element_sync_states")
    def test_select_nodes_to_use__returns_nodes_successfully(self, mock_get_enm_network_element_sync_states,
                                                             mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                             mock_update_nodes_info_with_ulsa_mos, *_):

        radionode_nodes = self.get_nodes("RadioNode", 4)
        allocated_nodes = radionode_nodes

        enm_node_sync_states = {radionode_nodes[0].node_id: "SYNCHRONIZED",
                                radionode_nodes[1].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[2].node_id: "SYNCHRONIZED",
                                radionode_nodes[3].node_id: "UNSYNCHRONIZED"}
        mock_get_enm_network_element_sync_states.return_value = enm_node_sync_states

        radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                "rfport": "rfport_mo3"}}
        mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos]
        selected_nodes_with_rfport = {"RadioNode": radionode_nodes_that_contain_rfport_mos}
        radionode_nodes_with_ulsa_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                      "rfport": "rfport_mo3",
                                                                      "ulsa_mo_list": ["ulsa_mo2"]}}
        nodes_with_ulsa_mos = {"RadioNode": radionode_nodes_with_ulsa_mos}
        mock_update_nodes_info_with_ulsa_mos.return_value = nodes_with_ulsa_mos

        self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
        mock_update_nodes_info_with_ulsa_mos.assert_called_with(self.user, selected_nodes_with_rfport)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_list_from_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "update_nodes_info_with_ulsa_mos")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_enm_network_element_sync_states")
    def test_select_nodes_to_use__returns_none_if_no_synced_nodes(self, mock_get_enm_network_element_sync_states,
                                                                  mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                                  mock_update_nodes_info_with_ulsa_mos,
                                                                  mock_add_error_as_exception, *_):
        radionode_nodes = self.get_nodes("RadioNode", 4)
        allocated_nodes = radionode_nodes

        enm_node_sync_states = {radionode_nodes[0].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[1].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[2].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[3].node_id: "UNSYNCHRONIZED"}
        mock_get_enm_network_element_sync_states.return_value = enm_node_sync_states

        radionode_nodes_that_contain_rfport_mos = {}
        mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos]

        self.assertEqual({}, self.profile.select_nodes_to_use(self.user, allocated_nodes))
        self.assertFalse(mock_update_nodes_info_with_ulsa_mos.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    # select_nodes_from_pool_that_contain_rfport_mo test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_select_nodes_from_pool_that_contain_rfport_mo__returns_nodes_if_rfport_list_no_empty(
            self, mock_add_error_as_exception):
        path2 = "Equipment=1,FieldReplaceableUnit=1"

        radionode1_rfport1 = ("ManagedElement={0},{1},RfPort=1".format(self.radionode1.node_id, path2))
        radionode2_rfport2 = ("ManagedElement={0},{1},RfPort=2".format(self.radionode2.node_id, path2))
        radionode1_rfport3 = ("ManagedElement={0},{1},RfPort=1".format(self.radionode3.node_id, path2))

        radio_rfports = [radionode1_rfport1, radionode2_rfport2, radionode1_rfport3]
        rfport_fdn_list = radio_rfports

        actual_output = self.profile.select_nodes_from_pool_that_contain_rfport_mo(
            "RadioNode", [self.radionode1, self.radionode2, self.radionode3], rfport_fdn_list)
        expected_output = {self.radionode1.node_id: {"node": self.radionode1,
                                                     "node_rfport_fdn_list": [radionode1_rfport1]},
                           self.radionode2.node_id: {"node": self.radionode2,
                                                     "node_rfport_fdn_list": [radionode2_rfport2]}}
        self.assertEqual(actual_output, expected_output)

        self.assertEqual(mock_add_error_as_exception.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_select_nodes_from_pool_that_contain_rfport_mo__adds_error_if_rfport_list_empty(
            self, mock_add_error_as_exception):
        nodes = [self.radionode1, self.radionode3, self.radionode4]
        self.assertEqual({}, self.profile.select_nodes_from_pool_that_contain_rfport_mo("RadioNode", nodes, []))
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    # initialize_profile_prerequisites test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__is_successful(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__returns_none_if_no_nodes_in_node_list(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = []
        self.assertEqual(self.profile.initialize_profile_prerequisites(), None)
        self.assertFalse(mock_create_users.called)
        self.assertFalse(mock_select_nodes_to_use.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_cannot_create_user(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_create_users.side_effect = Exception
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertFalse(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_select_nodes_to_use_throws_exception(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_select_nodes_to_use.side_effect = Exception
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_select_nodes_to_use_throws_keyerror(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_select_nodes_to_use.side_effect = KeyError
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    # get_rfport_fdn_list_from_enm test cases
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep', return_value=0)
    def test_get_rfport_fdn_list_from_enm__is_successful(self, _):
        self.user.enm_execute.return_value.get_output.return_value = ["FDN : rfport_fdn1",
                                                                      "FDN : rfport_fdn2",
                                                                      "2 instance(s) found"]
        actual_output = pm52profile.get_rfport_fdn_list_from_enm(self.user)
        self.assertEqual(["rfport_fdn1", "rfport_fdn2"], actual_output)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep', return_value=0)
    def test_get_rfport_fdn_list_from_enm__raises_enmapplicationerror_if_enm_doesnt_return_instance_count(self, _):
        self.user.enm_execute.return_value.get_output.return_value = ["blah"]
        self.assertRaises(EnmApplicationError, pm52profile.get_rfport_fdn_list_from_enm, self.user)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep', return_value=0)
    def test_get_rfport_fdn_list_from_enm__retries_when_errored(self, mock_sleep):
        self.user.enm_execute.return_value.get_output.return_value = ["Error", "Error", "Error"]
        self.assertRaises(EnmApplicationError, pm52profile.get_rfport_fdn_list_from_enm, self.user)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep', return_value=0)
    def test_get_rfport_fdn_list_from_enm__raises_environerror_if_no_instance_count_returned_from_enm(self, _):
        self.user.enm_execute.return_value.get_output.return_value = ["0 instance(s) found"]
        self.assertRaises(EnvironError, pm52profile.get_rfport_fdn_list_from_enm, self.user)

    # get_fdn_of_ulsa_parent test cases
    def test_get_fdn_of_ulsa_parent__is_successful(self):
        erbs_nodes = self.get_nodes("ERBS", 1)
        self.user.enm_execute.return_value.get_output.return_value = ["FDN : blah", "0 instance(s) found"]
        self.assertEqual("blah", pm52profile.get_fdn_of_ulsa_parent(self.user, erbs_nodes[0]))

    def test_get_fdn_of_ulsa_parent__raises_enmapplication_error_if_exception_occurs_with_enm_execute(self):
        radionode_nodes = self.get_nodes("RadioNode", 1)
        self.user.enm_execute.side_effect = Exception()
        self.assertRaises(EnmApplicationError, pm52profile.get_fdn_of_ulsa_parent, self.user, radionode_nodes[0])

    def test_get_fdn_of_ulsa_parent__raises_enmapplication_error_if_no_ulsa_parent_mo_found(self):
        erbs_nodes = self.get_nodes("ERBS", 1)
        self.user.enm_execute.return_value.get_output.return_value = ["0 instance(s) found"]
        self.assertRaises(EnmApplicationError, pm52profile.get_fdn_of_ulsa_parent, self.user, erbs_nodes[0])

    # create_ulsa_mo_objects test cases
    def test_create_ulsa_mo_objects__is_successful(self):
        radionodes_nodes = self.get_nodes("ERBS", 1)

        self.user.enm_execute.return_value.get_output.return_value = ["1 instance(s) created"]
        pm52profile.create_ulsa_mo_objects(self.user, radionodes_nodes[0], "fdn_ulsa_parent", ["ulsa1", "ulsa2"])

    def test_create_ulsa_mo_objects__raises_enmapplication_error_if_exception_occurs_with_enm_execute(self):
        radionodes_nodes = self.get_nodes("ERBS", 1)
        self.user.enm_execute.side_effect = Exception()
        self.assertRaises(EnmApplicationError, pm52profile.create_ulsa_mo_objects, self.user, radionodes_nodes[0],
                          "fdn_ulsa_parent", ["ulsa1", "ulsa2"])

    def test_create_ulsa_mo_objects__raises_enmapplication_error_if_mo_was_not_created(self):
        radionodes_nodes = self.get_nodes("ERBS", 1)

        self.user.enm_execute.return_value.get_output.return_value = ["0 instance(s) updated"]
        self.assertRaises(EnmApplicationError, pm52profile.create_ulsa_mo_objects, self.user, radionodes_nodes[0],
                          "fdn_ulsa_parent", ["ulsa1", "ulsa2"])

    # get_current_list_of_ulsa_mos_for_node test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.raise_for_status")
    def test_get_current_list_of_ulsa_mos_for_node_via_rest_call__is_successful(self, _):
        erbs_nodes = self.get_nodes("ERBS", 1)

        ulsa_mo_path = ("SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,"
                        "NodeManagementFunction=1,UlSpectrumAnalyzer")

        json_data = {
            "1": {
                "attributes": {
                    "UlSpectrumAnalyzerId": "1",
                    "info": "UNDEFINED",
                    "samplingType": "SNAPSHOT_SAMPLING",
                    "targetRfPort": "",
                    "ulSpectrumSamplingStatus": "UNKNOWN"
                },
                "fdn": "{0}=1".format(ulsa_mo_path)
            },
            "PM_52_ULSA_0": {
                "attributes": {
                    "UlSpectrumAnalyzerId": "PM_52_ULSA_0",
                    "info": "UNDEFINED",
                    "samplingType": "SNAPSHOT_SAMPLING",
                    "targetRfPort": "",
                    "ulSpectrumSamplingStatus": "UNKNOWN"
                },
                "fdn": "{0}=PM_52_ULSA_0".format(ulsa_mo_path)
            },
            "PM_52_ULSA_1": {
                "attributes": {
                    "UlSpectrumAnalyzerId": "PM_52_ULSA_1",
                    "info": "UNDEFINED",
                    "samplingType": "SNAPSHOT_SAMPLING",
                    "targetRfPort": "",
                    "ulSpectrumSamplingStatus": "UNKNOWN"
                },
                "fdn": "{0}=PM_52_ULSA_1".format(ulsa_mo_path)
            },
            "PM_52_ULSA_2": {
                "attributes": {
                    "UlSpectrumAnalyzerId": "PM_52_ULSA_2",
                    "info": "UNDEFINED",
                    "samplingType": "SNAPSHOT_SAMPLING",
                    "targetRfPort": "",
                    "ulSpectrumSamplingStatus": "UNKNOWN"
                },
                "fdn": "{0}=PM_52_ULSA_2".format(ulsa_mo_path)
            }
        }
        response = Mock()
        response.json.return_value = json_data

        self.user.get.return_value = response
        expected_ulsa_mo_list = ["{0}=1".format(ulsa_mo_path), "{0}=PM_52_ULSA_1".format(ulsa_mo_path),
                                 "{0}=PM_52_ULSA_1".format(ulsa_mo_path), "{0}=PM_52_ULSA_2".format(ulsa_mo_path)]

        actual_output = pm52profile.get_current_list_of_ulsa_mos_for_node(self.user, erbs_nodes[0])
        self.assertEqual(expected_ulsa_mo_list.sort(), actual_output.sort())

    def test_get_current_list_of_ulsa_mos_for_node__returns_empty_list_if_no_ulsa_mo_found(self):
        response = Mock()
        response.json.return_value = {
            "1": {
                "attributes": {
                    "UlSpectrumAnalyzerId": "1",
                    "info": "UNDEFINED",
                    "samplingType": "SNAPSHOT_SAMPLING",
                    "targetRfPort": "",
                    "ulSpectrumSamplingStatus": "UNKNOWN"
                },
                "FDN": "blah"
            },
        }
        self.user.get.return_value = response
        erbs = self.get_nodes("ERBS", 1)
        actual_output = pm52profile.get_current_list_of_ulsa_mos_for_node(self.user, erbs[0])
        self.assertEqual([], actual_output)

    # test_extract_rfport_ldn_from_fdn__is_successful test cases
    def test_extract_rfport_ldn_from_fdn__is_successful(self):
        rfport_fdn = "blah1,ManagedElement=1,blah2"
        self.assertEqual("ManagedElement=1,blah2", pm52profile.extract_rfport_ldn_from_fdn(rfport_fdn))

    def test_extract_rfport_ldn_from_fdn__raises_environerror_if_fdn_doesnt_contain_managedelement(self):
        self.assertRaises(EnvironError, pm52profile.extract_rfport_ldn_from_fdn, "blah")

    # select_nodes test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_rfport_for_node")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.generate_basic_dictionary_from_list_of_objects")
    def test_select_nodes__successful(
            self, mock_generate_basic_dictionary_from_list_of_objects, mock_get_rfport_for_node,
            mock_add_error_as_exception):
        synced_nodes = [Mock()] * 4

        mock_generate_basic_dictionary_from_list_of_objects.return_value = {"RadioNode": [self.radionode1,
                                                                                          self.radionode2,
                                                                                          self.radionode3,
                                                                                          self.radionode4]}

        mock_get_rfport_for_node.side_effect = ["radionode1_rfport", "radionode2_rfport", "radionode3_rfport"]

        rfport_fdn_list, ulsa_fdn_list = Mock(), Mock()

        expected_selected_nodes = [(self.radionode1.node_id, "radionode1_rfport"),
                                   (self.radionode2.node_id, "radionode2_rfport")]

        selected_nodes = self.profile.select_nodes(synced_nodes, rfport_fdn_list, ulsa_fdn_list)
        self.assertEqual(selected_nodes, expected_selected_nodes)
        self.assertTrue(call(self.radionode1, [], rfport_fdn_list, ulsa_fdn_list) in
                        mock_get_rfport_for_node.mock_calls)
        self.assertTrue(call(self.radionode2, ["netsim2"], rfport_fdn_list, ulsa_fdn_list) in
                        mock_get_rfport_for_node.mock_calls)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_rfport_for_node")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.generate_basic_dictionary_from_list_of_objects")
    def test_select_nodes__adds_error_to_profile_if_not_all_required_nodes_selected_as_rfport_not_listed(
            self, mock_generate_basic_dictionary_from_list_of_objects, mock_get_rfport_for_node,
            mock_add_error_as_exception):
        self.profile.NODES_TO_FIND = {'RadioNode': 6}

        synced_nodes = [Mock()] * 4

        mock_generate_basic_dictionary_from_list_of_objects.return_value = {"RadioNode": [self.radionode1,
                                                                                          self.radionode2,
                                                                                          self.radionode3,
                                                                                          self.radionode4]}

        mock_get_rfport_for_node.side_effect = ["radionode1_rfport", None, "radionode2_rfport", None]

        rfport_fdn_list, ulsa_fdn_list = Mock(), Mock()

        expected_selected_nodes = [(self.radionode1.node_id, "radionode1_rfport"),
                                   (self.radionode3.node_id, "radionode2_rfport")]
        selected_nodes = self.profile.select_nodes(synced_nodes, rfport_fdn_list, ulsa_fdn_list)
        self.assertEqual(selected_nodes, expected_selected_nodes)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    # get_rfport_for_node test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_node_existed_in_used_netsims")
    def test_get_rfport_for_node__successfull(self, mock_check_node_existed_in_used_netsims):
        radionode_rfport = "SubNetwork=1,ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort={1}"

        radionode1_rfport1 = radionode_rfport.format(self.radionode1.node_id, 1)
        radionode2_rfport1 = radionode_rfport.format(self.radionode2.node_id, 1)
        radionode2_rfport2 = radionode_rfport.format(self.radionode2.node_id, 2)
        radionode3_rfport1 = radionode_rfport.format(self.radionode3.node_id, 3)
        radionode4_rfport1 = radionode_rfport.format(self.radionode4.node_id, 4)

        radionode_ulsa = "SubNetwork=1,ManagedElement={0},NodeSupport=1,UlSpectrumAnalyzer=1"

        radionode1_ulsa = radionode_ulsa.format(self.radionode1.node_id)
        radionode2_ulsa = radionode_ulsa.format(self.radionode2.node_id)
        radionode3_ulsa = radionode_ulsa.format(self.radionode3.node_id)
        radionode4_ulsa = radionode_ulsa.format(self.radionode4.node_id)

        rfport_fdn_list = [radionode1_rfport1, radionode2_rfport1, radionode2_rfport2, radionode3_rfport1,
                           radionode4_rfport1]
        ulsa_fdn_list = [radionode1_ulsa, radionode2_ulsa, radionode3_ulsa, radionode4_ulsa]
        mock_check_node_existed_in_used_netsims.return_value = True

        self.assertEqual(self.profile.get_rfport_for_node(self.radionode2, [], rfport_fdn_list, ulsa_fdn_list),
                         radionode2_rfport1)
        mock_check_node_existed_in_used_netsims.assert_called_with(self.radionode2, [])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_node_existed_in_used_netsims")
    def test_get_rfport_for_node__returns_none_if_two_nodes_are_used_from_same_netsim_box(
            self, mock_check_node_existed_in_used_netsims):
        mock_check_node_existed_in_used_netsims.return_value = False
        used_netsims = ["netsim3", "netsim3"]
        self.assertIsNone(self.profile.get_rfport_for_node(self.radionode2, used_netsims, Mock(), Mock()))
        mock_check_node_existed_in_used_netsims.assert_called_with(self.radionode2, used_netsims)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_node_existed_in_used_netsims")
    def test_get_rfport_for_node__returns_none_if_node_not_found_in_rfport_fdn_list(
            self, mock_check_node_existed_in_used_netsims):
        mock_check_node_existed_in_used_netsims.return_value = True
        self.assertIsNone(self.profile.get_rfport_for_node(self.radionode2, [], [], Mock()))
        mock_check_node_existed_in_used_netsims.assert_called_with(self.radionode2, [])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_node_existed_in_used_netsims")
    def test_get_rfport_for_node__returns_none_if_node_not_found_in_ulsa_fdn_list(
            self, mock_check_node_existed_in_used_netsims):
        radionode_rfport = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,"
                            "DeviceGroup=1,RfPort={1}")
        rfport_fdn_list = [radionode_rfport.format(self.radionode3.node_id, 1)]
        mock_check_node_existed_in_used_netsims.return_value = True
        self.assertIsNone(self.profile.get_rfport_for_node(self.radionode3, [], rfport_fdn_list, []))
        mock_check_node_existed_in_used_netsims.assert_called_with(self.radionode3, [])

    # filter_profile_nodes test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "get_unused_nodes_and_deallocate_from_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_filter_profile_nodes__is_successful(
            self, mock_add_exception, mock_get_nodes_list_by_attribute, mock_select_nodes,
            mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes, mock_filter_synced_pm_enabled_nodes,
            mock_deallocate_unused_nodes):

        allocated_nodes = [self.radionode1, self.radionode2]
        rfport_fdn_list = ["rfport1", "rfport2"]
        ulsa_fdn_list = ["ulsa1", "ulsa2"]
        synced_nodes = allocated_nodes[:2]

        mock_get_nodes_list_by_attribute.return_value = allocated_nodes
        mock_filter_synced_pm_enabled_nodes.return_value = synced_nodes
        mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.return_value = (rfport_fdn_list, ulsa_fdn_list)
        mock_select_nodes.return_value = [("node1", "rfport1"), ("node2", "rfport2")]

        self.profile.filter_profile_nodes(USER)

        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "netsim", "primary_type",
                                                                             "profiles"])
        self.assertTrue(call(USER, synced_nodes) in
                        mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.mock_calls)
        mock_select_nodes.assert_called_with(mock_filter_synced_pm_enabled_nodes.return_value, rfport_fdn_list,
                                             ulsa_fdn_list)
        mock_filter_synced_pm_enabled_nodes.assert_called_with(allocated_nodes, USER)
        self.assertTrue(mock_deallocate_unused_nodes.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "get_unused_nodes_and_deallocate_from_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_filter_profile_nodes__is_successful_and_nodes_deallocated(
            self, mock_add_exception, mock_get_nodes_list_by_attribute, mock_select_nodes,
            mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes, mock_filter_synced_pm_enabled_nodes,
            mock_deallocate_unused_nodes):
        allocated_nodes = [self.radionode1, self.radionode4]
        rfport_fdn_list = ["rfport1", "rfport2"]
        ulsa_fdn_list = ["ulsa1", "ulsa2"]
        synced_nodes = [self.radionode4]

        mock_get_nodes_list_by_attribute.return_value = allocated_nodes
        mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.return_value = (rfport_fdn_list, ulsa_fdn_list)
        mock_filter_synced_pm_enabled_nodes.return_value = synced_nodes
        mock_select_nodes.return_value = [("node1", "rfport1")]

        self.profile.filter_profile_nodes(USER)

        self.assertTrue(call(USER, synced_nodes) in
                        mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.mock_calls)
        mock_select_nodes.assert_called_with(synced_nodes, rfport_fdn_list, ulsa_fdn_list)
        mock_filter_synced_pm_enabled_nodes.assert_called_with(allocated_nodes, USER)
        mock_deallocate_unused_nodes.assert_called_with(allocated_nodes, mock_select_nodes.return_value)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "get_unused_nodes_and_deallocate_from_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_filter_profile_nodes__adds_error_to_profile_error_occurs_during_selection(
            self, mock_add_exception, mock_filter_synced_pm_enabled_nodes, *_):
        mock_filter_synced_pm_enabled_nodes.side_effect = EnvironError("Synced nodes are not available")
        self.profile.filter_profile_nodes(USER)
        self.assertTrue(call(mock_filter_synced_pm_enabled_nodes.side_effect in mock_add_exception.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "get_unused_nodes_and_deallocate_from_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_filter_profile_nodes__is_successful_if_no_nodes_allocated(
            self, mock_add_exception, mock_get_nodes_list_by_attribute, mock_select_nodes,
            mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes, mock_filter_synced_pm_enabled_nodes,
            mock_deallocate_unused_nodes):
        mock_get_nodes_list_by_attribute.return_value = []

        self.profile.filter_profile_nodes(USER)

        self.assertFalse(mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.called)
        self.assertFalse(mock_select_nodes.called)
        self.assertFalse(mock_filter_synced_pm_enabled_nodes.called)
        self.assertFalse(mock_deallocate_unused_nodes.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "get_unused_nodes_and_deallocate_from_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.filter_synced_pm_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.select_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    def test_filter_profile_nodes__raises_env_error_if_pm_function_not_enabled_on_nodes(
            self, mock_add_exception, mock_get_nodes_list_by_attribute, mock_select_nodes,
            mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes, mock_filter_synced_pm_enabled_nodes,
            mock_deallocate_unused_nodes):
        allocated_nodes = [self.radionode4, self.radionode1]
        mock_get_nodes_list_by_attribute.return_value = allocated_nodes
        mock_filter_synced_pm_enabled_nodes.side_effect = EnvironError("PM is not enabled on any nodes allocated"
                                                                       " to the profile")
        self.profile.filter_profile_nodes(USER)
        mock_filter_synced_pm_enabled_nodes.assert_called_with(allocated_nodes, USER)
        self.assertTrue(mock_filter_synced_pm_enabled_nodes.called)
        self.assertFalse(mock_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes.called)
        self.assertFalse(mock_select_nodes.called)
        self.assertFalse(mock_deallocate_unused_nodes.called)
        self.assertTrue(call(mock_filter_synced_pm_enabled_nodes.side_effect in mock_add_exception.mock_calls))

    # get_unused_nodes_and_deallocate_from_profile test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    def test_get_unused_nodes_and_deallocate_from_profile__is_successful(self,
                                                                         mock_update_profile_persistence_nodes_list,
                                                                         mock_debug_log):
        self.profile.get_unused_nodes_and_deallocate_from_profile([self.radionode2, self.radionode3],
                                                                  [("node1", "rfport1")])
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    def test_get_unused_nodes_and_deallocate_from_profile__if_unused_nodes_not_found(
            self, mock_update_profile_persistence_nodes_list, mock_debug_log):
        self.profile.get_unused_nodes_and_deallocate_from_profile([self.radionode2], [("radionode2", "rfport1")])
        self.assertFalse(mock_update_profile_persistence_nodes_list.called)
        self.assertFalse(mock_debug_log.called)

    # filter_synced_pm_enabled_nodes test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_sync_and_remove")
    def test_filter_synced_pm_enabled_nodes__is_successful(self, mock_check_sync_and_remove,
                                                           mock_get_pm_function_enabled_nodes):
        allocated_nodes = [self.radionode3, self.radionode4, self.radionode1, self.radionode2]
        mock_check_sync_and_remove.return_value = (allocated_nodes[:3], [self.radionode2])
        mock_get_pm_function_enabled_nodes.return_value = (allocated_nodes[:2], [self.radionode1])
        self.profile.filter_synced_pm_enabled_nodes(allocated_nodes, self.user)
        mock_check_sync_and_remove.assert_called_with(allocated_nodes, self.user)
        mock_get_pm_function_enabled_nodes.assert_called_with(mock_check_sync_and_remove.return_value[0], self.user)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_sync_and_remove")
    def test_filter_synced_pm_enabled_nodes__raises_env_error_if_synced_nodes_not_found(
            self, mock_check_sync_and_remove, mock_get_pm_function_enabled_nodes):
        allocated_nodes = [self.radionode4, self.radionode3, self.radionode1, self.radionode2]
        mock_check_sync_and_remove.return_value = (allocated_nodes[:3], [self.radionode2])
        mock_get_pm_function_enabled_nodes.return_value = ([], mock_check_sync_and_remove.return_value[0])
        self.assertRaises(EnvironError, self.profile.filter_synced_pm_enabled_nodes, allocated_nodes, self.user)
        mock_check_sync_and_remove.assert_called_with(allocated_nodes, self.user)
        mock_get_pm_function_enabled_nodes.assert_called_with(mock_check_sync_and_remove.return_value[0], self.user)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.check_sync_and_remove")
    def test_filter_synced_pm_enabled_nodes__raises_env_error_if_pm_enabled_nodes_not_found(
            self, mock_check_sync_and_remove, mock_get_pm_function_enabled_nodes):
        allocated_nodes = [self.radionode3, self.radionode4, self.radionode1, self.radionode2]
        mock_check_sync_and_remove.return_value = ([], allocated_nodes)
        self.assertRaises(EnvironError, self.profile.filter_synced_pm_enabled_nodes, allocated_nodes, self.user)
        mock_check_sync_and_remove.assert_called_with(allocated_nodes, self.user)
        self.assertFalse(mock_get_pm_function_enabled_nodes.called)

    # start_ulsa_uplink_measurement test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.json.dumps")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.raise_for_status")
    def test_start_ulsa_uplink_measurement__is_successful(
            self, mock_raise_for_status, mock_dumps):

        response = Mock()
        response.content = '{"filepath":"","triggeredat":"Tue, 28 Aug 2018 11:09:21 +0100"}'
        USER.post.return_value = response

        json_data = {"nodeId": "node1",
                     "ulsaMoName": "0",
                     "ulsaStartCenterFrequencyParameter": 678175,
                     "ulsaStartDisplayedBandwidthParameter": 100,
                     "ulsaStartPortParameter": "rfport1",
                     "ulsaStartResolutionBandwidthParameter": 100,
                     "ulsaStartSamplingIntervalParameter": 2,
                     "ulsaStartSamplingTimeoutParameter": 21600,
                     "ulsaStartSamplingTypeParameter": "CONTINUOUS_SAMPLING"}

        pm52profile.start_ulsa_uplink_measurement(("node1", "rfport1"), USER)

        self.assertEqual(mock_raise_for_status.call_count, 1)
        USER.post.assert_called_with("pmul-service/rest/command/start", data=mock_dumps.return_value,
                                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        mock_dumps.assert_called_with(json_data)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.raise_for_status")
    def test_start_ulsa_uplink_measurement__raises_error_if_response_from_enm_is_unexpected(
            self, mock_raise_for_status):
        response = Mock()
        response.content = 'some_content'
        USER.post.return_value = response

        self.assertRaises(EnmApplicationError, pm52profile.start_ulsa_uplink_measurement, ("node1", "rfport1"), USER)
        self.assertEqual(mock_raise_for_status.call_count, 1)

    # stop_ulsa_uplink_measurement test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_stop_ulsa_uplink_measurement__is_successful(self, mock_debug):

        response = Mock(ok=True)
        response.json.return_value = {"jobState": "STOPPED"}
        USER.put.return_value = response

        pm52profile.stop_ulsa_uplink_measurement(("node1", "rfport1"), USER)
        USER.put.assert_called_with("pmul-service/rest/command/stop/node/node1/ulsa/0/port/rfport1/"
                                    "samplingType/CONTINUOUS")
        message = "Sampling stopped on node node1 (i.e. jobState==STOPPED in response when job is stopped)"
        self.assertTrue(call(message) in mock_debug.mock_calls)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_stop_ulsa_uplink_measurement__is_successful_if_response_from_enm_is_unexpected(self, mock_debug):
        response = Mock(ok=True)
        response.json.return_value = {"jobState": "ERROR"}
        USER.put.return_value = response

        pm52profile.stop_ulsa_uplink_measurement(("node1", "rfport1"), USER)
        message = "Sampling not stopped on node node1 (i.e. jobState==STOPPED in response when job is stopped)"
        self.assertTrue(call(message) in mock_debug.mock_calls)

    # perform_teardown_actions test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.stop_ulsa_uplink_measurement")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.create_and_execute_threads")
    def test_perform_teardown_actions__is_successful(
            self, mock_create_and_execute_threads, mock_stop_ulsa_uplink_measurement):
        selected_nodes = [Mock(), Mock()]

        pm52profile.perform_teardown_actions(USER, selected_nodes, self.profile)

        mock_create_and_execute_threads.assert_called_with(selected_nodes, len(selected_nodes),
                                                           func_ref=mock_stop_ulsa_uplink_measurement,
                                                           args=[USER])

    # delete_ulsa_mo_objects test cases
    def test_delete_ulsa_mos_created_by_profile__is_successful(self):
        self.user.enm_execute.return_value.get_output.return_value = ["1 instance(s) deleted"]
        pm52profile.delete_ulsa_mo_objects(self.user, "ulsa_fdn")

    def test_delete_ulsa_mos_created_by_profile__raises_enmapplicationerror_if_enm_execute_fails(self):
        self.user.enm_execute.return_value.get_output.side_effect = Exception()
        self.assertRaises(EnmApplicationError, pm52profile.delete_ulsa_mo_objects, self.user, "ulsa_fdn")

    def test_delete_ulsa_mos_created_by_profile__raises_enmapplicationerror_if_delete_fails(self):
        self.user.enm_execute.return_value.get_output.return_value = ["Unsuccessful"]
        self.assertRaises(EnmApplicationError, pm52profile.delete_ulsa_mo_objects, self.user, "ulsa_fdn")

    # update_nodes_info_with_ulsa_mos test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_current_list_of_ulsa_mos_for_node")
    def test_update_nodes_info_with_ulsa_mos__returns_correct_data_if_no_extra_mos_need_to_be_created(
            self, mock_get_current_list_of_ulsa_mos_for_node, *_):

        erbs_node = {"node": Mock(primary_type="ERBS"), "rfport_ldn": "rfport_ldn_blah"}
        erbs_node_ulsa_mo_list = ["ulsa_mo_1a", "ulsa_mo_1b", "ulsa_mo_1c", "ulsa_mo_1d"]
        radionode_node = {"node": Mock(primary_type="RadioNode"), "rfport_ldn": "rfport_ldn_blah"}
        radionode_node_ulsa_mo_list = ["ulsa_mo_blah"]
        nodes = {"ERBS": {"erbs1": erbs_node}, "RadioNode": {"radionode1": radionode_node}}

        mock_get_current_list_of_ulsa_mos_for_node.side_effect = [erbs_node_ulsa_mo_list,
                                                                  radionode_node_ulsa_mo_list]
        output_data = self.profile.update_nodes_info_with_ulsa_mos(self.user, nodes)

        erbs_node["ulsa_mo_list"] = erbs_node_ulsa_mo_list
        radionode_node["ulsa_mo_list"] = radionode_node_ulsa_mo_list
        updated_nodes = {"ERBS": {"erbs1": erbs_node}, "RadioNode": {"radionode1": radionode_node}}
        self.assertEqual(output_data, updated_nodes)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.create_ulsa_mo_objects")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_fdn_of_ulsa_parent")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_current_list_of_ulsa_mos_for_node")
    def test_update_nodes_info_with_ulsa_mos__returns_correct_data_if_extra_mos_need_to_be_created(
            self, mock_get_current_list_of_ulsa_mos_for_node, *_):

        erbs_node = {"node": Mock(primary_type="ERBS"), "rfport_ldn": "rfport_ldn_blah"}
        erbs_node_ulsa_mo_list_initially = ["ulsa_mo_1a"]
        erbs_node_ulsa_mo_list_after_mos_created = ["ulsa_mo_1a", "ulsa_mo_1b", "ulsa_mo_1c", "ulsa_mo_1d"]

        radionode_node = {"node": Mock(primary_type="RadioNode"), "rfport_ldn": "rfport_ldn_blah"}
        radionode_node_ulsa_mo_list = ["ulsa_mo_blah"]

        nodes = {"ERBS": {"erbs1": erbs_node}, "RadioNode": {"radionode1": radionode_node}}

        mock_get_current_list_of_ulsa_mos_for_node.side_effect = [erbs_node_ulsa_mo_list_initially,
                                                                  erbs_node_ulsa_mo_list_after_mos_created,
                                                                  radionode_node_ulsa_mo_list]
        output_data = self.profile.update_nodes_info_with_ulsa_mos(self.user, nodes)

        erbs_node["ulsa_mo_list"] = erbs_node_ulsa_mo_list_after_mos_created
        radionode_node["ulsa_mo_list"] = radionode_node_ulsa_mo_list
        updated_nodes = {"ERBS": {"erbs1": erbs_node}, "RadioNode": {"radionode1": radionode_node}}
        self.assertEqual(output_data, updated_nodes)

    # wait_until_first_scheduled_time test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.datetime.datetime")
    def test_wait_until_first_scheduled_time__wont_call_sleep_if_profile_starts_before_first_scheduled_time(
            self, mock_datetime, mock_time_sleep):
        mock_datetime.now.return_value = datetime.now().replace(hour=06, minute=0, second=0, microsecond=0)

        ulsa_sampling_start_time = datetime.strptime(self.profile.SCHEDULED_TIMES_STRINGS[0], "%H:%M:%S")
        mock_datetime.strptime.return_value = ulsa_sampling_start_time

        self.profile.wait_until_first_scheduled_time()
        self.assertFalse(mock_time_sleep.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.datetime.datetime")
    def test_wait_until_first_scheduled_time__will_sleep_extra_time_if_profile_starts_after_first_scheduled_time(
            self, mock_datetime, mock_time_sleep, _):
        start_hour = 22
        time_now = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)

        mock_datetime.now.return_value = time_now
        start_time = datetime.strptime(self.profile.SCHEDULED_TIMES_STRINGS[0], "%H:%M:%S")
        mock_datetime.strptime.return_value = start_time

        time_gap = 30
        first_scheduled_time = int(self.profile.SCHEDULED_TIMES_STRINGS[0].split(":")[0])
        time_in_sec_until_first_scheduled_time = (24 + first_scheduled_time - start_hour) * 60 * 60

        self.profile.wait_until_first_scheduled_time()
        mock_time_sleep.assert_called_with(time_in_sec_until_first_scheduled_time - time_gap)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_list_from_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_nodes_info_with_ulsa_mos")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_enm_network_element_sync_states")
    def test_deallocate_unused_nodes_and_update_profile_persistence(self, mock_get_enm_network_element_sync_states,
                                                                    mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                                    mock_update_nodes_info_with_ulsa_mos,
                                                                    mock_update_profile_persistence_nodes_list, *_):
        radionode_nodes = self.get_nodes("RadioNode", 4)
        allocated_nodes = radionode_nodes

        enm_node_sync_states = {radionode_nodes[0].node_id: "SYNCHRONIZED",
                                radionode_nodes[1].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[2].node_id: "SYNCHRONIZED",
                                radionode_nodes[3].node_id: "UNSYNCHRONIZED"}
        mock_get_enm_network_element_sync_states.return_value = enm_node_sync_states
        radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                "rfport": "rfport_mo3"}}
        mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos]
        selected_nodes_with_rfport = {"RadioNode": radionode_nodes_that_contain_rfport_mos}

        radionode_nodes_with_ulsa_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                      "rfport": "rfport_mo3",
                                                                      "ulsa_mo_list": ["ulsa_mo2"]}}
        nodes_with_ulsa_mos = {"RadioNode": radionode_nodes_with_ulsa_mos}
        mock_update_nodes_info_with_ulsa_mos.return_value = nodes_with_ulsa_mos

        self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
        mock_update_nodes_info_with_ulsa_mos.assert_called_with(self.user, selected_nodes_with_rfport)
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_list_from_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_nodes_info_with_ulsa_mos")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_enm_network_element_sync_states")
    def test_deallocate_unused_nodes_if_sync_nodes_only(
            self, mock_get_enm_network_element_sync_states, mock_select_nodes_from_pool_that_contain_rfport_mo,
            mock_update_nodes_info_with_ulsa_mos, mock_update_profile_persistence_nodes_list, *_):
        radionode_nodes = self.get_nodes("RadioNode", 4)
        allocated_nodes = radionode_nodes

        enm_node_sync_states = {radionode_nodes[0].node_id: "SYNCHRONIZED",
                                radionode_nodes[1].node_id: "SYNCHRONIZED",
                                radionode_nodes[2].node_id: "SYNCHRONIZED",
                                radionode_nodes[3].node_id: "SYNCHRONIZED"}
        mock_get_enm_network_element_sync_states.return_value = enm_node_sync_states

        radionode_nodes_that_contain_rfport_mos = {
            radionode_nodes[0].node_id: {"node": radionode_nodes[0], "rfport": "rfport_mo3"},
            radionode_nodes[1].node_id: {"node": radionode_nodes[1], "rfport": "rfport_mo4"}}
        mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos]
        selected_nodes_with_rfport = {"RadioNode": radionode_nodes_that_contain_rfport_mos}

        radionode_nodes_with_ulsa_mos = {
            radionode_nodes[0].node_id: {"node": radionode_nodes[0], "rfport": "rfport_mo3",
                                         "ulsa_mo_list": ["ulsa_mo3"]},
            radionode_nodes[1].node_id: {"node": radionode_nodes[1], "rfport": "rfport_mo4",
                                         "ulsa_mo_list": ["ulsa_mo4"]}}
        nodes_with_ulsa_mos = {"RadioNode": radionode_nodes_with_ulsa_mos}
        mock_update_nodes_info_with_ulsa_mos.return_value = nodes_with_ulsa_mos
        self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
        mock_update_nodes_info_with_ulsa_mos.assert_called_with(self.user, selected_nodes_with_rfport)
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_rfport_fdn_list_from_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.update_nodes_info_with_ulsa_mos")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_enm_network_element_sync_states")
    def test_deallocate_unused_nodes_if_no_synced_nodes(self, mock_get_enm_network_element_sync_states,
                                                        mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                        mock_update_nodes_info_with_ulsa_mos,
                                                        mock_add_error_as_exception,
                                                        mock_update_profile_persistence_nodes_list, _):
        radionode_nodes = self.get_nodes("RadioNode", 4)
        allocated_nodes = radionode_nodes

        enm_node_sync_states = {radionode_nodes[1].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[2].node_id: "UNSYNCHRONIZED",
                                radionode_nodes[3].node_id: "UNSYNCHRONIZED"}
        mock_get_enm_network_element_sync_states.return_value = enm_node_sync_states

        radionode_nodes_that_contain_rfport_mos = {}
        mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos]
        self.assertEqual({}, self.profile.select_nodes_to_use(self.user, allocated_nodes))
        self.assertFalse(mock_update_nodes_info_with_ulsa_mos.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)

    # check_and_remove_old_ulsas_in_enm test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.delete_ulsa_mo_objects")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_ulsas_from_enm_based_on_profile_name")
    def test_check_and_remove_old_ulsas_in_enm__is_successful(self, mock_get_ulsas, mock_delete_ulsa, mock_add_error,
                                                              mock_debug_log):
        mock_get_ulsas.return_value = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_0',
                                       u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_1',
                                       u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_2']
        pm52profile.check_and_remove_old_ulsas_in_enm(USER, self.profile)
        self.assertEqual(3, mock_delete_ulsa.call_count)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.delete_ulsa_mo_objects")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_ulsas_from_enm_based_on_profile_name")
    def test_check_and_remove_old_ulsas_in_enm__add_error_if_delete_ulsa_mo_objects_raises_error(
            self, mock_get_ulsas, mock_delete_ulsa, mock_add_error, mock_debug_log):
        mock_get_ulsas.return_value = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_0',
                                       u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_1',
                                       u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_2']
        mock_delete_ulsa.side_effect = [EnmApplicationError("ENM command execution unsuccessful"),
                                        "1 instance(s) deleted", "1 instance(s) deleted"]
        pm52profile.check_and_remove_old_ulsas_in_enm(USER, self.profile)
        self.assertEqual(3, mock_delete_ulsa.call_count)
        self.assertTrue(call(EnmApplicationError("ENM command execution unsuccessful") in mock_add_error.mock_calls))
        self.assertTrue(mock_debug_log.called)

    # get_ulsas_from_enm_based_on_profile_name test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_get_ulsas_from_enm_based_on_profile_name__is_successful(self, mock_debug_log):
        USER.enm_execute.return_value.get_output.return_value = [
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_3',
            u'', u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_1',
            u'', u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_2',
            u'', u'', u'3 instance(s)']
        actual_output = pm52profile.get_ulsas_from_enm_based_on_profile_name(USER, self.profile.NAME)
        expected_output = [
            u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_3',
            u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_1',
            u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_2']
        self.assertEqual(expected_output, actual_output)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_get_ulsas_from_enm_based_on_profile_name__raises_enmapplicationerror_if_enm_doesnt_return_instance_count(
            self, mock_debug_log):
        USER.enm_execute.return_value.get_output.return_value = ['something is wrong']
        self.assertRaises(EnmApplicationError, pm52profile.get_ulsas_from_enm_based_on_profile_name, USER,
                          self.profile.NAME)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_get_ulsas_from_enm_based_on_profile_name__raises_enmapplicationerror_if_return_error(self, mock_debug_log):
        USER.enm_execute.return_value.get_output.side_effect = Exception("something is wrong")
        self.assertRaises(EnmApplicationError, pm52profile.get_ulsas_from_enm_based_on_profile_name, USER,
                          self.profile.NAME)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_get_ulsas_from_enm_based_on_profile_name__if_matched_fdns_not_found(self, mock_debug_log):
        USER.enm_execute.return_value.get_output.return_value = [
            'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00003,ManagedElement=1,NodeManagementFunction=1,UlSpectrumAnalyzer=PM_52_ULSA_3',
            u'', u'1 instance(s)']
        self.assertEqual([], pm52profile.get_ulsas_from_enm_based_on_profile_name(USER, self.profile.NAME))
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    def test_get_ulsas_from_enm_based_on_profile_name__if_fdns_not_found_in_enm(self, mock_debug_log):
        USER.enm_execute.return_value.get_output.return_value = [u'0 instance(s)']
        self.assertEqual([], pm52profile.get_ulsas_from_enm_based_on_profile_name(USER, self.profile.NAME))
        self.assertEqual(mock_debug_log.call_count, 2)

    # check_node_existed_in_used_netsims test cases
    def test_check_node_existed_in_used_netsims__is_successful(self):
        used_netsims = [self.radionode4.netsim]
        self.assertEqual(True, pm52profile.check_node_existed_in_used_netsims(self.radionode4, used_netsims))

    def test_check_node_existed_in_used_netsims__if_two_nodes_used_from_same_netsim_box(self):
        used_netsims = [self.radionode4.netsim, self.radionode2.netsim]
        self.assertEqual(False, pm52profile.check_node_existed_in_used_netsims(self.radionode2, used_netsims))

    def test_check_node_existed_in_used_netsims__if_used_netsims_list_empty(self):
        self.assertEqual(True, pm52profile.check_node_existed_in_used_netsims(self.radionode2, []))

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile.execute_flow')
    def test_run__in_pm_52_is_successful(self, mock_flow):
        self.pm_52.run()
        self.assertTrue(mock_flow.called)

    # get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_fdn_list_from_enm")
    def test_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes__is_successful(self, mock_get_fdn_list_from_enm,
                                                                                  mock_debug_log):

        allocated_nodes = [self.radionode1, self.radionode2]
        rfport_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode1,Equipment=1,'
                           u'FieldReplaceableUnit=1,RfPort=1',
                           u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode2,'
                           u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        ulsa_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode1,NodeSupport=1,'
                         u'UlSpectrumAnalyzer=1',
                         u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode2,'
                         u'NodeSupport=1,UlSpectrumAnalyzer=1']
        synced_nodes = allocated_nodes[:2]
        mock_get_fdn_list_from_enm.side_effect = [rfport_fdn_list, ulsa_fdn_list]
        self.assertEqual((rfport_fdn_list, ulsa_fdn_list),
                         pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes(USER, synced_nodes))
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(call(USER, "RfPort") in mock_get_fdn_list_from_enm.mock_calls)
        self.assertTrue(call(USER, "UlSpectrumAnalyzer") in mock_get_fdn_list_from_enm.mock_calls)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm52profile.get_fdn_list_from_enm")
    def test_get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes__if_node_id_not_existed(self,
                                                                                           mock_get_fdn_list_from_enm,
                                                                                           mock_debug_log):

        allocated_nodes = [self.radionode3, self.radionode1]
        rfport_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode3,Equipment=1,'
                           u'FieldReplaceableUnit=1,RfPort=1',
                           u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode2,'
                           u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        ulsa_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode3,NodeSupport=1,'
                         u'UlSpectrumAnalyzer=1',
                         u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode2,'
                         u'NodeSupport=1,UlSpectrumAnalyzer=1']
        synced_nodes = allocated_nodes[:2]
        mock_get_fdn_list_from_enm.side_effect = [rfport_fdn_list, ulsa_fdn_list]
        excepted_output = ([u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode3,'
                            u'Equipment=1,FieldReplaceableUnit=1,RfPort=1'],
                           [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=radionode3,'
                            u'NodeSupport=1,UlSpectrumAnalyzer=1'])
        self.assertEqual(excepted_output,
                         pm52profile.get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes(USER, synced_nodes))
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(call(USER, "RfPort") in mock_get_fdn_list_from_enm.mock_calls)
        self.assertTrue(call(USER, "UlSpectrumAnalyzer") in mock_get_fdn_list_from_enm.mock_calls)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
