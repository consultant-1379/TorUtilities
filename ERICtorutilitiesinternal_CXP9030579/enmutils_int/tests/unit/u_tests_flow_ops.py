#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.ops_flows.ops_01_flow import Ops01Flow
from enmutils_int.lib.workload import ops_01
from mock import patch, Mock
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class OpsFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.ops_01 = ops_01.OPS_01()
        self.flow = Ops01Flow()
        self.flow.NUM_USERS = 2
        self.flow.SESSION_COUNT = 10
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.THREAD_QUEUE_TIMEOUT = 10 * 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.execute_flow')
    def test_run__in_ops_01_is_successful(self, mock_execute_flow):
        self.ops_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.keep_running')
    def test_execute_flow__is_successful(self, mock_keep_running, mock_sleep, mock_exchange, mock_user, mock_ops, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_user.return_value = [Mock(), Mock()]
        mock_ops.return_value.create_password_less_to_vm.return_value = True
        mock_ops.return_value.host_list = [Mock()]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_exchange.called)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_and_execute_threads',
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.keep_running')
    def test_ops_execute_flow_create_thread_throws_exception(self, mock_keep_running, mock_sleep, mock_user, mock_ops,
                                                             mock_error, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user.return_value = [Mock(), Mock()]
        mock_ops.return_value.host_list = []
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.log.logger.debug')
    def test_ops_execute_flow_taskset_success(self, mock_log, *_):
        user = Mock()
        user.name = "OPS_user"
        node = Mock()
        node.node_name = "123"
        worker_mock = (user, node, "34", generate_configurable_ip)
        self.flow.ops = Mock()
        self.flow.ops.host_list.return_value = [Mock(), Mock()]
        self.flow.ops.check_sessions_count.side_effect = None
        self.flow.ops.run_blade_runner_script_on_host.side_effect = None
        self.flow.task_set(worker_mock, self.flow)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.add_error_as_exception')
    def test_ops_execute_flow_taskset_script_and_session_count_throws_exception(self, mock_error, mock_log, *_):
        user = Mock()
        user.name = "OPS_user"
        node = Mock()
        node.node_name = "123"
        worker_mock = (user, node, "34", generate_configurable_ip)
        self.flow.ops = Mock()
        self.flow.ops.host_list.return_value = [Mock(), Mock()]
        self.flow.ops.check_sessions_count.side_effect = Exception
        self.flow.ops.run_blade_runner_script_on_host.side_effect = Exception
        self.flow.task_set(worker_mock, self.flow)
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_error.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.keep_running')
    def test_ops_execute_flow__taskset_throws_exception(self, mock_keep_running, mock_download_tls_certs, *_):
        mock_keep_running.side_effect = [False]
        self.flow.execute_flow()
        self.assertFalse(mock_download_tls_certs.called)

    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.create_workers', side_effect=[Exception])
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops')
    @patch('enmutils_int.lib.profile_flows.ops_flows.ops_01_flow.Ops01Flow.keep_running')
    def test_ops_execute_flow__exception(self, mock_keep_running, mock_ops, *_):
        mock_ops.return_value.create_password_less_to_vm.return_value = True
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()

    def test_split_session_count__returns_as_expected_for_low_session_count(self):
        self.flow.SESSION_COUNT = 2
        self.flow.MAX_SESSION_COUNT_PER_NODE = 35
        self.assertEqual(self.flow.split_session_count(4), [2, 2, 2, 2])

    def test_split_session_count__returns_as_expected_for_high_session_count(self):
        self.flow.SESSION_COUNT = 135
        self.flow.MAX_SESSION_COUNT_PER_NODE = 35
        self.assertEqual(self.flow.split_session_count(4), [34, 34, 34, 33])

    def test_create_workers__returns_as_expected(self):
        self.flow.SESSION_COUNT = 135
        self.flow.MAX_SESSION_COUNT_PER_NODE = 35
        nodes = ["node_" + str(i) for i in range(1, 17)]
        users = ["user" + str(i) for i in range(1, 5)]
        host_list = ["ops_" + str(i) for i in range(1, 5)]
        self.assertEqual(len(self.flow.create_workers(nodes, host_list, users)), 16)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
