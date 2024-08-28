#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from websocket import WebSocketConnectionClosedException, WebSocketBadStatusException, WebSocketTimeoutException

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.nodecli_flows import nodecli_01_flow
from enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow import NodeCli01Flow
from enmutils_int.lib.workload import nodecli_01
from testslib import unit_test_utils


class NodeCli01UnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock(username="TEST_00_u0")
        unit_test_utils.setup()
        self.nodecli_01 = nodecli_01.NODECLI_01()
        self.flow = NodeCli01Flow()
        self.flow.NUM_USERS, self.flow.USER_ROLES = 2, ["SomeRole"]
        self.flow.SESSION_MULTIPLIER = 1
        self.flow.SCHEDULE_SLEEP = 900
        self.nodes_list = [Mock(), Mock()]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.execute_flow')
    def test_run__in_nodecli_01_is_successful(self, _):
        self.nodecli_01.run()

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.state')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.create_profile_users',
           return_value=["user", "user1"])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_node_poids',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.add_error_as_exception')
    def test_flow__continues_with_errors(self, mock_add_error, *_):
        self.flow.poids = []
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.state')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.create_profile_users',
           return_value=["user", "user1"])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_node_poids',
           return_value=(["123", "124"], ["Node", "Node1"]))
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.'
           'duplicate_poids_if_fewer_than_user_count')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.close_web_socket_connections')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.create_and_execute_threads')
    def test_execute_flow__success(self, mock_create_threads, mock_close, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_create_threads.call_count, 1)
        self.assertEqual(mock_close.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.close_web_socket_connections')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.state')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.create_profile_users',
           return_value=["user", "user1"])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.get_node_poids')
    def test_flow__uses_existing_poids(self, mock_get_node_poids, *_):
        self.flow.poids = ["123", "124"]
        self.flow.execute_flow()
        self.assertEqual(mock_get_node_poids.call_count, 0)

    def test_duplicate_poids_if_fewer_than_user_count__raises_enm_app_error(self):
        self.flow.poids = None
        self.assertRaises(EnmApplicationError, self.flow.duplicate_poids_if_fewer_than_user_count)

    def test_duplicate_poids_if_fewer_than_user_count__success(self):
        self.flow.poids = ["123", "124"]
        self.flow.users = ["user", "user1", "user2"]
        self.assertEqual(3, len(self.flow.duplicate_poids_if_fewer_than_user_count()))

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.get_poids', return_value=([], []))
    def test_get_node_poids__success(self, mock_get_poids):
        self.flow.profile_nodes, self.flow.completed_nodes = ["Node"], ["Node1"]
        self.flow.get_node_poids(self.user)
        mock_get_poids.assert_called_with(["Node"])

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.urlparse')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.copy')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.websocket_connection')
    def test_task_set_raises_websocket_timeout_exception(self, mock_create_connection, mock_error, *_):
        node = Mock()
        self.flow.poids = ["123"]
        worker_mock = (self.user, self.flow.poids, node)
        mock_create_connection.side_effect = WebSocketTimeoutException
        self.flow.task_set(worker_mock, self.flow)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.urlparse')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.copy')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.websocket_connection')
    def test_task_set_raises_websocket_bad_status_exception(self, mock_create_connection, mock_logger_debug, mock_error, *_):
        node = Mock()
        self.flow.poids = ["123"]
        worker_mock = (self.user, self.flow.poids, node)
        mock_create_connection.side_effect = WebSocketBadStatusException(message="abc %s %s", status_code="307")
        self.flow.task_set(worker_mock, self.flow)
        self.assertTrue(mock_error.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.urlparse')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.copy')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.websocket_connection')
    def test_task_set_raises_exception(self, mock_create_connection, mock_error, *_):
        node = Mock()
        self.flow.poids = ["123"]
        worker_mock = (self.user, self.flow.poids, node)
        mock_create_connection.side_effect = Exception
        self.flow.task_set(worker_mock, self.flow)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.urlparse')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.copy')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.websocket_connection')
    def test_task_set_success(self, mock_create_connection, mock_logger_debug, *_):
        node = Mock()
        self.flow.poids = ["123"]
        worker_mock = (self.user, self.flow.poids, node)
        mock_create_connection.return_value = Mock()
        self.flow.task_set(worker_mock, self.flow)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.urlparse')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.copy')
    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.websocket.create_connection')
    def test_create_connection_success(self, *_):
        self.flow.poids = ["123"]
        self.flow.websocket_connection(self.user, self.flow.poids)

    def test_close_web_socket_connections__closes_web_sockets(self):
        connection = Mock()
        nodecli_01_flow.WEB_SOCKET_CONNECTIONS = {"node": [True, connection]}
        self.flow.close_web_socket_connections()
        self.assertEqual(1, connection.close.call_count)

    @patch('enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow.NodeCli01Flow.add_error_as_exception')
    def test_close_web_socket_connections__adds_error_closing_socket_if_connection_opened_successfully(self,
                                                                                                       mock_add_error):
        connection = Mock()
        connection.close.side_effect = WebSocketConnectionClosedException("Failed.")
        nodecli_01_flow.WEB_SOCKET_CONNECTIONS = {"node": [True, connection], "node1": [False, connection]}
        self.flow.close_web_socket_connections()
        self.assertEqual(2, connection.close.call_count)
        self.assertEqual(1, mock_add_error.call_count)
        self.assertDictEqual({}, nodecli_01_flow.WEB_SOCKET_CONNECTIONS)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
