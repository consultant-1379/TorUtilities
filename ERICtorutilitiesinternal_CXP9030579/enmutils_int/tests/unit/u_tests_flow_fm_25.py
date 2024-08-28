#!/usr/bin/env python
import unittest2
from mock import patch, Mock, call

from enmutils.lib.enm_node import ERBSNode, MGWNode, SGSNNode, RadioNode
from enmutils_int.lib.profile_flows.fm_flows.fm_25_flow import Fm25
from testslib import unit_test_utils


class Fm25UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.erbs_nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', 'ip', 'F.1.101', '5783-904-386', '', 'netsim', 'netsim',
                     'netsim', 'netsim', primary_type='ERBS'),
        ]
        self.radio_nodes = [
            RadioNode('testNode1', primary_type='RadioNode')
        ]
        self.sgsn_nodes = [
            SGSNNode('testNode2', primary_type='SGSN-MME')
        ]
        self.mgw_nodes = [
            MGWNode('testNode3', primary_type='MGW')
        ]
        self.flow = Fm25()
        self.flow.NUM_USERS = 5
        self.flow.USER_ROLES = "TEST1"
        self.flow.SLEEP_TIME = 1
        self.nodes = {"ERBS": self.erbs_nodes,
                      "RadioNode": self.radio_nodes,
                      "SGSN-MME": self.sgsn_nodes,
                      "MGW": self.mgw_nodes}
        self.node_type = {"ERBS": False, "RadioNode": False, "SGSN-MME": False, "MGW": False}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.helper_methods."
           "generate_basic_dictionary_from_list_of_objects")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.process_thread_queue_errors')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.create_profile_users')
    def test_execute_flow_fm_25_success(self, mock_create_user, mock_keep_running,
                                        mock_thread_constructor, mock_process_thread_queue_errors, mock_nodes, *_):
        mock_create_user.return_value = [self.user] * self.flow.NUM_USERS
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = self.nodes
        with patch('enmutils_int.lib.profile_flows.fm_flows.'
                   'fm_25_flow.GenericFlow.exchange_nodes') as mock_exchange_nodes:
            self.flow.execute_flow_fm_25()
            self.assertTrue(mock_create_user.called)
            self.assertTrue(mock_keep_running.called)
            self.assertTrue(mock_exchange_nodes.called)
            self.assertEqual(5, mock_thread_constructor.call_count)
            self.assertEqual(5, mock_process_thread_queue_errors.call_count)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25._ui_tasks_for_netlog")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.helper_methods."
           "generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.create_profile_users')
    def test_execute_flow_fm_25__with_erbs_nodes_success(self, mock_create_user, mock_keep_running,
                                                         mock_thread_constructor, mock_nodes, mock_tasks, *_):
        mock_create_user.return_value = [self.user] * self.flow.NUM_USERS
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = {"ERBS": ["node1", "node2"]}
        with patch('enmutils_int.lib.profile_flows.fm_flows.'
                   'fm_25_flow.GenericFlow.exchange_nodes') as mock_exchange_nodes:
            self.flow.execute_flow_fm_25()
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_thread_constructor.call_count == 2)
            calls = [call(work_items=[mock_create_user.return_value[0]], num_workers=1,
                          func_ref=mock_tasks, task_join_timeout=None, task_wait_timeout=1,
                          args=[["node1"]]),
                     call(work_items=[mock_create_user.return_value[1]], num_workers=1,
                          func_ref=mock_tasks, task_join_timeout=None, task_wait_timeout=1,
                          args=[["node2"]])]
            mock_thread_constructor.assert_has_calls(calls)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.helper_methods."
           "generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.keep_running")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.create_profile_users")
    def test_execute_flow_fm_25_success_no_nodes(self, mock_create_user, mock_keep_running,
                                                 mock_thread_constructor, mock_process_thread_queue_errors, mock_nodes,
                                                 *_):
        mock_create_user.return_value = [self.user] * self.flow.NUM_USERS
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = []
        with patch('enmutils_int.lib.profile_flows.fm_flows.'
                   'fm_25_flow.GenericFlow.exchange_nodes') as mock_exchange_nodes:
            self.flow.execute_flow_fm_25()
            self.assertTrue(mock_create_user.called)
            self.assertTrue(mock_keep_running.called)
            self.assertTrue(mock_exchange_nodes.called)
            self.assertEqual(0, mock_thread_constructor.call_count)
            self.assertEqual(0, mock_process_thread_queue_errors.call_count)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.exchange_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.keep_running")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.create_profile_users")
    def test_execute_flow_fm_25_continues_with_errors(self, mock_create_user, mock_keep_running, mock_sleep_until_time,
                                                      mock_thread_constructor, mock_process_thread_queue_errors, *_):
        response = [False, True]
        mock_process_thread_queue_errors.side_effect = response + [response[1]]
        mock_thread_constructor.side_effect = response + [response[1], response[1]]
        mock_sleep_until_time.side_effect = response + [response[1], response[1], response[1]]
        mock_keep_running.side_effect = response + [response[1], response[1], response[1], response[1], response[1]]
        mock_create_user.side_effect = response + [response[1], response[1], response[1], response[1], response[1]]
        self.assertFalse(self.flow.execute_flow_fm_25())

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.collect_erbs_network_logs')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.cm_cli_home')
    def test_ui_tasks_for_netlog_erbs_nodes_success(self, mock_cm_cli_home, mock_logger_info,
                                                    mock_collect_erbs_network_logs):
        self.node_type = {"ERBS": True, "RadioNode": False, "SGSN": False, "MGW": False}
        self.flow._ui_tasks_for_netlog(self.user, self.erbs_nodes)
        self.assertTrue(mock_cm_cli_home.called)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_collect_erbs_network_logs.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.collect_eNodeB_network_logs')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.cm_cli_home')
    def test_ui_tasks_for_netlog_radionode_nodes_success(self, mock_cm_cli_home, mock_logger_info,
                                                         mock_collect_enodeb_network_logs):
        self.node_type = {"ERBS": False, "RadioNode": True, "SGSN": False, "MGW": False}
        self.flow._ui_tasks_for_netlog(self.user, self.radio_nodes)
        self.assertTrue(mock_cm_cli_home.called)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_collect_enodeb_network_logs.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.collect_sgsn_network_logs')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.cm_cli_home')
    def test_ui_tasks_for_netlog_sgsn_nodes_success(self, mock_cm_cli_home, mock_logger_info,
                                                    mock_collect_sgsn_network_logs):
        self.node_type = {"ERBS": False, "RadioNode": False, "SGSN": True, "MGW": False}
        self.flow._ui_tasks_for_netlog(self.user, self.sgsn_nodes)
        self.assertTrue(mock_cm_cli_home.called)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_collect_sgsn_network_logs.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.collect_mgw_network_logs')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.cm_cli_home')
    def test_ui_tasks_for_netlog_mgw_nodes_success(self, mock_cm_cli_home, mock_logger_info,
                                                   mock_collect_mgw_network_logs):
        self.node_type = {"ERBS": False, "RadioNode": False, "SGSN": False, "MGW": True}
        self.flow._ui_tasks_for_netlog(self.user, self.mgw_nodes)
        self.assertTrue(mock_cm_cli_home.called)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_collect_mgw_network_logs.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
