#!/usr/bin/env python
import unittest2
from mock import Mock, patch
from requests.exceptions import ConnectionError
from websocket import (WebSocketBadStatusException,
                       WebSocketConnectionClosedException, WebSocketException,
                       WebSocketTimeoutException)

from enmutils_int.lib.amos_executor import (
    AmosNodeExecutor, EnvironError, check_ldap_is_configured_on_radio_nodes,
    construct_command_list, delete_user_sessions, get_radio_erbs_nodes,
    set_max_amos_sessions, taskset)
from enmutils_int.lib.profile import Profile
from testslib import unit_test_utils


class AmosNodeExecutorTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()] * 2
        self.radionodes = [Mock(primary_type="RadioNode", host_name="host")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.amos_executor.time.sleep', return_value=0)
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.connect')
    @patch("enmutils_int.lib.amos_executor.AmosNodeExecutor.execute_exit")
    @patch("enmutils_int.lib.amos_executor.AmosNodeExecutor.execute_exit_shell")
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.execute')
    def test_001_verify_amos_run_cmds_successfully_complete_and_exit_shell(self, mock_execute, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.run_commands()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_003_amosnodeexecutor_raises_websocket_timeout_exception(self, mock_create_connection, *_):
        mock_create_connection.side_effect = WebSocketTimeoutException
        self.assertRaises(WebSocketTimeoutException, AmosNodeExecutor, user=self.user, node=self.nodes[0],
                          commands=['test'])

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_004_amosnodeexecutor_raises_websocket_badstatus_exception(self, mock_create_connection, *_):
        self.user.username = "abc"
        mock_create_connection.side_effect = WebSocketBadStatusException(message="abc %s %s", status_code="307")
        self.assertRaises(WebSocketBadStatusException, AmosNodeExecutor, user=self.user, node=self.nodes[0],
                          commands=['test'])

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_005_amosnodeexecutor_raises_exception(self, mock_create_connection, *_):
        mock_create_connection.side_effect = Exception
        self.assertRaises(Exception, AmosNodeExecutor, user=self.user, node=self.nodes[0], commands=['test'])

    @patch('enmutils_int.lib.amos_executor.time.sleep', return_value=0)
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.connect', side_effect=WebSocketConnectionClosedException())
    @patch("enmutils_int.lib.amos_executor.AmosNodeExecutor.execute_exit")
    @patch("enmutils_int.lib.amos_executor.AmosNodeExecutor.execute_exit_shell")
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    def test_006_verify_run_commands_raises_websocket_connection_closed_exception(self, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        self.assertRaises(WebSocketConnectionClosedException, amos_node_executor.run_commands)

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.amos_executor.update_pib_parameter_on_enm')
    def test_007_set_max_amos_sessions__update_pib_parameter_raises_enm_application_error(
            self, mock_update_pib_parameter_on_enm, mock_error):
        Profile.NAME = "TEST_PROFILE"
        base_profile = Profile()
        mock_update_pib_parameter_on_enm.side_effect = Exception
        set_max_amos_sessions(base_profile, 150)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.amos_executor.update_pib_parameter_on_enm')
    def test_008_set_max_amos_sessions__update_pib_parameter_on_enm_success(self, mock_update_pib_parameter_on_enm):
        set_max_amos_sessions(Mock(), 150)
        self.assertTrue(mock_update_pib_parameter_on_enm.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_010_teardown_successful(self, mock_create_connection, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor._teardown()
        self.assertTrue(mock_create_connection.return_value.close.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_011_close_raises_websocket_connection_closed_exception(self, mock_create_connection, mock_logger_debug,
                                                                    *_):
        response = mock_create_connection.return_value
        response.close.side_effect = WebSocketConnectionClosedException
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.close()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_012_teardown_raises_exceptions(self, mock_create_connection, *_):
        response = mock_create_connection.return_value
        response.recv.side_effect = Exception
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        self.assertRaises(Exception, amos_node_executor._teardown)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    def test_013_verify_taskset(self, mock_debug, *_):
        user_nodes = (self.user, self.nodes, 0)
        taskset(user_nodes, ['test'], 0)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor')
    def test_014_verify_taskset_raises_websocket_connection_closed_exception(self, mock_amos_node_executor, *_):
        user_nodes = (self.user, self.nodes, 0)
        amos_node_executor = mock_amos_node_executor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.run_commands.side_effect = WebSocketConnectionClosedException
        self.assertRaises(WebSocketConnectionClosedException, taskset, user_nodes, ['test'], 0)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor')
    def test_015_verify_taskset_raises_websocket_badstatus_exception(self, mock_amos_node_executor, *_):
        self.user.username = "xyz"
        user_nodes = (self.user, self.nodes, 0)
        amos_node_executor = mock_amos_node_executor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.run_commands.side_effect = [WebSocketBadStatusException(message="abc %s %s",
                                                                                   status_code="307"), '']
        self.assertRaises(WebSocketBadStatusException, taskset, user_nodes, ['test'], 0)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    def test_033_verify_taskset_raises_WebSocketException_exception(self, mock_create_websocket, *_):
        self.user.username = "xyz"
        user_nodes = (self.user, self.nodes, 0)
        AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_create_websocket.side_effect = [WebSocketException]
        self.assertRaises(EnvironError, taskset, user_nodes, ['test'], 0)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    def test_taskset__raises_environ_error_exception_for_connection_error(self, mock_create_websocket, *_):
        self.user.username = "xyz"
        user_nodes = (self.user, self.nodes, 0)
        AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_create_websocket.side_effect = [ConnectionError]
        self.assertRaises(EnvironError, taskset, user_nodes, ['test'], 0)

    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_034_get_radio_erbs_nodes(self, mock_log):
        radio_nodes = Mock(primary_type="RadioNode")
        erbs_nodes = Mock(primary_type="ERBS")
        other_nodes = Mock(primary_type="OtherNode")
        self.nodes = [radio_nodes, erbs_nodes, other_nodes]
        self.assertEqual(len(get_radio_erbs_nodes(self.nodes)), 2)
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor')
    def test_016_verify_taskset_raises_exception_due_to_run_commands(self, mock_amos_node_executor, *_):
        user_nodes = (self.user, self.nodes, 0)
        amos_node_executor = mock_amos_node_executor(user=self.user, node=self.nodes, commands=['test'])
        amos_node_executor.run_commands.side_effect = Exception
        self.assertRaises(Exception, taskset, user_nodes, ['test'], 0)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('datetime.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_017_verify_taskset_raises_exception_close(self, mock_logger_debug, mock_create_connection, *_):
        user_nodes = (self.user, self.nodes, 0)
        response = mock_create_connection.return_value
        response.recv.side_effect = Exception
        response.close.side_effect = Exception
        self.assertRaises(EnvironError, taskset, user_nodes, ['test'], 0)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.amos_executor.re.compile")
    @patch("enmutils_int.lib.amos_executor.check_sync_and_remove")
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_018_check_ldap_is_configured_on_radio_nodes_not_synced(self, mock_debug, mock_check_sync_and_remove,
                                                                    mock_re_compile, *_):
        name = "TEST"
        response = Mock()
        response.get_output.return_value = "0 instance(s) found"
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.return_value = True
        mock_check_sync_and_remove.return_value = (self.radionodes, [])
        Profile.NAME = 'AMOS'
        check_ldap_is_configured_on_radio_nodes(Profile(), self.user, self.radionodes, name)
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.amos_executor.check_sync_and_remove")
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_019_check_ldap_is_configured_on_radio_nodes_all_are_synced(self, mock_debug, mock_check_sync_and_remove,
                                                                        *_):
        name = "TEST"
        response = Mock()
        response.get_output.return_value = "who cares!"
        self.user.enm_execute.return_value = response
        mock_check_sync_and_remove.return_value = (self.radionodes, [])
        check_ldap_is_configured_on_radio_nodes(Profile, self.user, self.radionodes, name)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_020_verify_taskset_raises_exception_close(self, mock_logger_debug, mock_create_connection, *_):
        user_nodes = (self.user, self.nodes, 0)
        response = mock_create_connection.return_value
        response.close.side_effect = Exception
        taskset(user_nodes, ['test'], 0)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.is_exit', return_value=True)
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_021_verify_execute_exit_is_exiting(self, mock_logger_debug, mock_create_connection, *_):
        response = mock_create_connection.return_value
        response.recv.return_value = "exit response"
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.execute_exit(['test'])
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.amos_executor.re.compile")
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch('enmutils_int.lib.amos_executor.check_sync_and_remove')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.amos_executor.LDAP.configure_ldap_mo_from_enm')
    @patch('enmutils_int.lib.amos_executor.LDAP.set_filter_on_ldap_mo')
    @patch('enmutils_int.lib.amos_executor.LDAP.create_and_issue_ldap_certificate')
    def test_022_check_ldap_is_configured_on_radio_nodes_throws_exception(
            self, mock_create_certificate, mock_set_filter, mock_configure_mo, mock_add_error_as_exception,
            mock_check_sync, *_):
        name = "TEST"
        response = Mock()
        response.get_output.return_value = "string"
        self.user.enm_execute.return_value = response
        mock_check_sync.return_value = (self.nodes, [])
        mock_create_certificate.side_effect = Exception
        mock_configure_mo.side_effect = Exception
        mock_set_filter.side_effect = Exception
        check_ldap_is_configured_on_radio_nodes(Profile, self.user, self.radionodes, name)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.execute', return_value="Not OK")
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_023_connect_raises_websocket_connection_closed_exception(self, mock_debug, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        self.assertRaises(WebSocketConnectionClosedException, amos_node_executor.connect)
        self.assertEqual(4, mock_debug.call_count)

    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.is_prompt', return_value=False)
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch("enmutils_int.lib.amos_executor.re.search")
    @patch('enmutils_int.lib.amos_executor.datetime')
    def test_024_execute_match(self, mock_datetime, mock_re_search, mock_delta, *_):
        mock_datetime.now.side_effect = [1, 1, 1, 3]
        mock_delta.return_value = 1
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_re_search.side_effect = [False, True]
        result = amos_node_executor.execute("test", match=True, verify_timeout=0.0001)
        self.assertTrue(result)

    @patch("enmutils_int.lib.amos_executor.ceil")
    def test_025_construct_command_list_is_success(self, mock_ceil):
        commands = ["lt all", "get ManagedElement", "get EUtranCellFDD", "fget sec noofusedAntenna", "st fdd",
                    "st termpointtoenb", "st cell", "lst RfPort"]
        command_per_iteration = 72
        mock_ceil.return_value = 9
        commands_list = construct_command_list(commands, command_per_iteration)
        self.assertEqual(len(commands_list), command_per_iteration)

    @patch("enmutils_int.lib.amos_executor.ceil")
    def test_026_construct_command_list_is_success(self, mock_ceil):
        commands = ["lt all", "get ManagedElement", "get EUtranCellFDD", "fget sec noofusedAntenna", "st fdd",
                    "st termpointtoenb", "st cell", "lst RfPort"]
        command_per_iteration = 69
        mock_ceil.return_value = 9
        commands_list = construct_command_list(commands, command_per_iteration)
        self.assertEqual(len(commands_list), command_per_iteration)

    @patch('enmutils_int.lib.amos_executor.time.sleep')
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.is_exit_shell', return_value=True)
    @patch('enmutils_int.lib.amos_executor.urlparse')
    @patch('enmutils_int.lib.amos_executor.copy')
    @patch('enmutils_int.lib.amos_executor.timedelta')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.websocket.create_connection')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_027_verify_execute_exit_shell_is_exiting(self, mock_logger_debug, mock_create_connection, *_):
        response = mock_create_connection.return_value
        response.recv.return_value = "exit response"
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        amos_node_executor.execute_exit_shell(['test'])
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.amos_executor.re.search', return_value=False)
    @patch('enmutils_int.lib.amos_executor.AmosNodeExecutor.is_prompt', return_value=True)
    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch("enmutils_int.lib.amos_executor.re.compile")
    @patch("datetime.datetime")
    def test_028_execute_not_match(self, mock_datetime, mock_re_compile, *_):
        mock_datetime.now.side_effect = [0, 1]
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_re_compile.return_value.search.return_value = False
        result = amos_node_executor.execute("test", match=False, verify_timeout=0.0001)
        self.assertFalse(result)

    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    @patch("enmutils_int.lib.amos_executor.re.compile")
    def test_029_is_prompt_match_found(self, mock_re_compile, mock_logger_debug, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_re_compile.return_value.search.return_value = True
        result = amos_node_executor.is_prompt("ABC")
        self.assertTrue(result)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.amos_executor.create_websocket_connection')
    @patch('enmutils_int.lib.amos_executor.websocket.recv')
    @patch('enmutils_int.lib.amos_executor.websocket.send')
    @patch("enmutils_int.lib.amos_executor.re.compile")
    def test_030_is_prompt_match_not_found(self, mock_re_compile, *_):
        amos_node_executor = AmosNodeExecutor(user=self.user, node=self.nodes[0], commands=['test'])
        mock_re_compile.return_value.search.return_value = None
        result = amos_node_executor.is_prompt("ABC")
        self.assertFalse(result)

    @patch('enmutils_int.lib.amos_executor.delete_left_over_sessions')
    @patch('enmutils_int.lib.amos_executor.get_workload_admin_user')
    @patch('enmutils_int.lib.amos_executor.log.logger.debug')
    def test_031_delete_user_sessions(self, mock_logger_debug, mock_admin_user, mock_delete_sessions):
        users = [Mock(), Mock()]
        mock_admin_user.return_value = Mock()
        mock_delete_sessions.return_value = Mock()
        delete_user_sessions(users)
        self.assertTrue(mock_logger_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
