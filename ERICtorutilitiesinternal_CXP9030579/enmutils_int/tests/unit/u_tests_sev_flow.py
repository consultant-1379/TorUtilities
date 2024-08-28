#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError
from enmutils_int.lib.profile_flows.sev_flows.sev_flow import SEV01Flow
from enmutils_int.lib.profile_flows.sev_flows.sev_flow import SEV02Flow
from enmutils_int.lib.workload.sev_01 import SEV_01
from enmutils_int.lib.workload.sev_02 import SEV_02

from testslib import unit_test_utils


class SEV01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="TestUser")
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = SEV_01()
        self.flow = SEV01Flow()
        self.flow.NUM_USERS = 5
        self.flow.USER_ROLES = ["SEV_Administartor", "SEV_Operator"]
        self.nodes = unit_test_utils.setup_test_node_objects(5, primary_type="ESC")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.execute_flow")
    def test_sev_profile_sev_01_execute_flow__successful(self, mock_flow):
        SEV_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.create_users', return_value=5)
    def test_execute_flow__success(self, mock_create_user, mock_keep_running, mock_nodes_list, mock_threads,
                                   mock_exchange_nodes, mock_sleep):
        users = [self.user for _ in xrange(5)]
        mock_nodes_list.return_value = self.nodes
        mock_create_user.return_value = users
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_threads.called)
        self.assertTrue(mock_exchange_nodes.called)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.create_users', return_value=5)
    def test_execute_flow__no_nodes(self, mock_create_user, mock_keep_running, mock_nodes_list,
                                    mock_add_error, mock_sleep):
        users = [self.user for _ in xrange(5)]
        mock_nodes_list.return_value = []
        mock_create_user.return_value = users
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.create_users', return_value=5)
    def test_execute_flow__exception(self, mock_create_users, mock_keep_running, mock_nodes_list,
                                     mock_add_error, mock_sleep):
        mock_nodes_list.return_value = Mock(stdout="error")
        mock_create_users.return_value = [Mock(username="test")]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.log.logger.debug')
    def test_task_set__success(self, mock_logger_debug, *_):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"node": {"name": "Transport111ERS-SN-ESC37", "poId": 32217}}
        self.user.get.return_value = response
        self.flow.task_set((self.nodes[0], self.user), self.flow)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.log.logger.debug')
    def test_task_set__raises_exception(self, mock_logger_debug, mock_add_error, _):
        response = Mock()
        response.ok = True
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError("HTTP 500 Internal Server Error ")
        self.user.get.return_value = response
        self.assertRaises(self.flow.task_set((self.nodes[0], self.user), self.flow))
        self.assertTrue(mock_logger_debug.called)
        self.assertTrue(mock_add_error.called)


class SEV02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="TestUser")
        self.mock_user = Mock()
        self.mock_response = Mock()
        self.profile = SEV_02()
        self.flow = SEV02Flow()
        self.flow.NUM_USERS = 5
        self.flow.USER_ROLES = ["SEV_Administartor", "SEV_Operator"]
        self.nodes = unit_test_utils.setup_test_node_objects(5, primary_type="ESC")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.execute_flow")
    def test_sev_profile_sev_02_execute_flow__successful(self, mock_flow):
        SEV_02().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.create_users', return_value=5)
    def test_execute_flow__success(self, mock_create_user, mock_keep_running, mock_nodes_list, mock_threads,
                                   mock_exchange_nodes, mock_sleep):
        users = [self.user for _ in xrange(5)]
        mock_nodes_list.return_value = self.nodes
        mock_create_user.return_value = users
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_threads.called)
        self.assertTrue(mock_exchange_nodes.called)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.create_users', return_value=5)
    def test_execute_flow__no_nodes(self, mock_create_user, mock_keep_running, mock_nodes_list,
                                    mock_add_error, mock_sleep):
        users = [self.user for _ in xrange(5)]
        mock_nodes_list.return_value = []
        mock_create_user.return_value = users
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.create_users', return_value=5)
    def test_execute_flow__exception(self, mock_create_users, mock_keep_running, mock_nodes_list,
                                     mock_add_error, mock_sleep):
        mock_nodes_list.return_value = Mock(stdout="error")
        mock_create_users.return_value = [Mock(username="test")]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.log.logger.debug')
    def test_task_set__success(self, mock_logger_debug, *_):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"node": {"name": "Transport111ERS-SN-ESC37", "poId": 32217}}
        self.user.get.return_value = response
        self.flow.task_set((self.nodes[0], self.user), self.flow)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.time.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.SEV02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.sev_flows.sev_flow.log.logger.debug')
    def test_task_set__raises_exception(self, mock_logger_debug, mock_add_error, _):
        response = Mock()
        response.ok = True
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError("HTTP 500 Internal Server Error ")
        self.user.get.return_value = response
        self.assertRaises(self.flow.task_set((self.nodes[0], self.user), self.flow))
        self.assertTrue(mock_logger_debug.called)
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
