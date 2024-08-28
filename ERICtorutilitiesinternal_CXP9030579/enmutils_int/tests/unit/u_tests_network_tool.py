#!/usr/bin/env python
import unittest2

from enmutils.lib.enm_user_2 import User
from enmutils_int.bin import network

from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class NetworkToolUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = User(username="network_unit_test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.bin.network._print_sync_status')
    def test_print_sync_status__returns_true_if_network_status_retrieved_ok(self, mock_print_status):
        self.assertTrue(network.print_network_sync_status(self.user, status=network.COMPLETE_SYNC_GROUPS))
        self.assertEqual(4, mock_print_status.call_count)

    @patch('enmutils_int.bin.network.log.logger.error')
    @patch('enmutils_int.bin.network._print_sync_status')
    def test_print_sync_status_returns__false_if_network_status_retrieved_is_blank(self, mock_print_status, mock_error):
        mock_print_status.side_effect = RuntimeError("Error")
        self.assertFalse(network.print_network_sync_status(self.user))
        mock_error.assert_called_with("Unable to retrieve the network sync status, error encountered: [Error].")

    @patch('enmutils_int.bin.network.log.logger.error')
    @patch('enmutils_int.bin.network._print_sync_status')
    def test_print_sync_status_returns__invalid_group(self, mock_print_status, mock_error):
        mock_print_status.side_effect = RuntimeError("Error")
        network.print_network_sync_status(self.user, status=["INVALID"])
        mock_error.assert_called_with("Invalid group arguments: INVALID")

    @patch('enmutils_int.bin.network.PmManagement.supervise')
    @patch('enmutils_int.bin.network.FmManagement.supervise')
    @patch('enmutils_int.bin.network.CmManagement.supervise')
    @patch("enmutils_int.bin.network._print_final_status")
    @patch("enmutils_int.bin.network._print_sync_status")
    @patch("enmutils_int.bin.network.timestamp.get_elapsed_time")
    def test_full_network_sync_returns_false_if_sync_fails(self, elapsed_time, sync_status_mock, *_):
        elapsed_time.return_value = 0.005
        sync_status_mock.side_effect = [(False, 10, 20), (False, 0, 20), (True, 9, 20)]
        network.WAIT_INTERVAL = 0.001
        network.TIMEOUT = 0.003
        self.assertFalse(network.sync_nodes(self.user, groups=["cm", "fm", "pm"]))

    @patch('enmutils_int.bin.network.log.logger.info')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.bin.network.PmManagement.get_status')
    @patch('enmutils_int.bin.network.FmManagement.get_status')
    @patch('enmutils_int.bin.network.CmManagement.get_status')
    def test_print_node_info_when_node_exists(self, cm, fm, pm, mock_execute, mock_log_info):
        cm.return_value = {'LTE01': 'SYNCHRONIZED'}
        fm.return_value = {'LTE01': 'IN_SERVICE'}
        pm.return_value = {'LTE01': 'true'}
        responses = []
        for resp in [[u'ossModelIdentity : 456.123'], [u'ipAddress : 123.123.456'],
                     [u'FDN NetworkElement=LTE01 : PmFunction']]:
            response = Mock()
            response.get_output.return_value = resp
            responses.append(response)
        mock_execute.side_effect = responses
        network.print_node_info("LTE01", self.user)
        self.assertEqual(7, mock_log_info.call_count)

    @patch('enmutils_int.bin.network.log.logger.warn')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.bin.network.PmManagement.get_status')
    @patch('enmutils_int.bin.network.FmManagement.get_status')
    @patch('enmutils_int.bin.network.CmManagement.get_status')
    def test_print_node_info_when_node_doesnt_exist(self, cm, fm, pm, mock_execute, mock_log_warn):
        cm.return_value, fm.return_value, pm.return_value = {}, {}, {}
        response = Mock()
        response.get_output.return_value = [u""]
        mock_execute.side_effect = [response, response, response]
        network.print_node_info("LTEERBS00001", self.user)
        self.assertEqual(1, mock_log_warn.call_count)

    @patch('enmutils_int.bin.network.enm_node_management.ShmManagement.get_status')
    @patch('enmutils_int.bin.network.PmManagement.get_status')
    @patch('enmutils_int.bin.network.FmManagement.get_status')
    @patch('enmutils_int.bin.network.CmManagement.get_status')
    def test_print_node_sync_status_when_node_exists(self, cm, fm, pm, shm):
        cm.return_value = {'LTE01': 'SYNCHRONIZED'}
        fm.return_value = {'LTE01': 'IN_SERVICE'}
        pm.return_value = {'LTE01': 'true'}
        shm.return_value = {'LTE01': 'true'}
        self.assertTrue(network.print_node_sync_status(self.user, "LTE01"))

    @patch('enmutils_int.bin.network.CmManagement.get_status')
    def test_print_node_sync_status_when_node_doesnt_exist(self, cm):
        cm.return_value = RuntimeError()
        self.assertFalse(network.print_node_sync_status(self.user, "LTE01"))

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_delete_network_mo_returns_true_if_valid_script_engine_response_is_given_from_delete_network_object(self, mock_enm_execute):
        enm_execute_response = Mock()
        enm_execute_response.get_output.return_value = ["0 nodes found"]
        mock_enm_execute.return_value = enm_execute_response
        self.assertTrue(network._delete_network_mo("SubNetwork", self.user))

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_delete_network_mo_returns_false_if_invalid_script_engine_response_is_given_from_delete_network_object(self, mock_enm_execute):
        enm_execute_response = Mock()
        enm_execute_response.get_output.return_value = ["ERROR 999 server issue"]
        enm_execute_response.command = "cmedit action * CmFunction deleteNrmDataFromEnm"
        mock_enm_execute.return_value = enm_execute_response
        self.assertFalse(network._delete_network_mo("deleteNrmDataFromEnm", self.user))

    @patch('enmutils_int.bin.network.log.logger.info')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_print_security_levels(self, mock_enm_execute, mock_info):
        response = Mock()
        response.get_output.return_value = ["netsim_LTE08ERBS00039 level 1 NA",
                                            "netsim_LTE08ERBS00040 level 1 NA",
                                            "Command Executed Successfully"]
        mock_enm_execute.return_value = response
        network.print_security_levels(self.user)
        self.assertEqual(mock_info.call_count, 4)

    @patch('enmutils_int.bin.network.log.logger.info')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_print_security_levels_show_nodes(self, mock_enm_execute, mock_info):
        response = Mock()
        response.get_output.return_value = ["netsim_LTE08ERBS00039level 1 NA",
                                            "netsim_LTE08ERBS00040 evel 1 NA",
                                            "Command Executed Successfully"]
        mock_enm_execute.return_value = response
        network.print_security_levels(self.user, show_nodes=True)
        self.assertEqual(mock_info.call_count, 6)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_print_security_levels_raises_runtime_error(self, mock_enm_execute):
        response = Mock()
        response.get_output.return_value = ["0 instance(s)"]
        mock_enm_execute.return_value = response
        self.assertRaises(RuntimeError, network.print_security_levels, self.user)

    @patch('enmutils_int.bin.network._get_sync_status_and_nodes', return_value=({"SYNCED": ["Node"]}, [], []))
    @patch('enmutils_int.bin.network._return_total_nodes_for_states', return_value=([], 1, 1))
    @patch('enmutils_int.bin.network.print_synced_node_status')
    def test_print_sync_status__not_nodes_and_not_unsynced(self, mock_print_synced, *_):
        network._print_sync_status(Mock(), "PM", ["State", "State1"], {"SYNCED": 0})
        self.assertEqual(1, mock_print_synced.call_count)

    @patch('enmutils_int.bin.network._get_sync_status_and_nodes', return_value=({"SYNCED": ["Node"]}, [], []))
    @patch('enmutils_int.bin.network._return_total_nodes_for_states', return_value=([], 1, 1))
    @patch('enmutils_int.bin.network.print_sync_unsynced_status')
    @patch('enmutils_int.bin.network.print_synced_node_status')
    def test_print_sync_status__print_nodes_required(self, mock_print_synced, mock_print_sync, *_):
        network._print_sync_status(Mock(), "PM", ["State", "State1"], {"SYNCED": 0}, nodes=True)
        self.assertEqual(0, mock_print_synced.call_count)
        self.assertEqual(1, mock_print_sync.call_count)

    @patch('enmutils_int.bin.network._get_sync_status_and_nodes', return_value=({}, [], []))
    @patch('enmutils_int.bin.network._return_total_nodes_for_states', return_value=([], 0, 0))
    @patch('enmutils_int.bin.network.log.logger.error')
    @patch('enmutils_int.bin.network.print_sync_unsynced_status')
    @patch('enmutils_int.bin.network.print_synced_node_status')
    def test_print_sync_status__no_node_information(self, mock_print_synced, mock_print_sync, mock_error, *_):
        network._print_sync_status(Mock(), "PM", ["State", "State1"], {"SYNCED": 0})
        self.assertEqual(0, mock_print_synced.call_count)
        self.assertEqual(0, mock_print_sync.call_count)
        mock_error.assert_called_with("Unable to retrieve Node sync information.\nPlease ensure the nodes are created "
                                      "on the deployment and the underlying ENM is in a healthy state.")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_synced_node_status__pm_true(self, mock_info):
        sync_state_count = {"SYNCED": 10}
        self.assertTrue(network.print_synced_node_status("pm", sync_state_count, 10, wait_state="SYNCED"))
        mock_info.assert_called_with("\x1b[96m    SYNCED             : 10/10\x1b[0m")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_synced_node_status__not_all_synced(self, mock_info):
        sync_state_count = {"SYNCED": 10}
        self.assertFalse(network.print_synced_node_status("fm", sync_state_count, 11, wait_state="SYNCED"))
        mock_info.assert_called_with("\x1b[96m    SYNCED             : 10/11\x1b[0m")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_sync_unsynced_status__pm_sync_type_not_synced(self, mock_info):
        network.print_sync_unsynced_status(False, "pm", ["Node1"], [])
        mock_info.assert_called_with("\x1b[95m\tDisabled:\n \t['Node1']\n\x1b[0m")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_sync_unsynced_status__pm_sync_type_unsynced(self, mock_info):
        network.print_sync_unsynced_status(True, "pm", ["Node1"], [])
        mock_info.assert_called_with("\x1b[95m\tDisabled:\n \t['Node1']\n\x1b[0m")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_sync_unsynced_status__sync_type_unsynced(self, mock_info):
        network.print_sync_unsynced_status(True, "fm", ["Node1"], [])
        mock_info.assert_called_with("\x1b[95m\tUnsynchronised:\n \t['Node1']\n\x1b[0m")

    @patch('enmutils_int.bin.network.log.logger.info')
    def test_print_sync_unsynced_status__sync_type_not_synced(self, mock_info):
        network.print_sync_unsynced_status(False, "fm", ["Node1"], [])
        mock_info.assert_called_with("\x1b[95m\tUnsynchronised:\n \t['Node1']\n\x1b[0m")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
