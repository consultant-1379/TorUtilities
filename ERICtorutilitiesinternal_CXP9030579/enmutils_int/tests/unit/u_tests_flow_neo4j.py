#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2

from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow import Neo4JProfile01, get_neo4j_leader_ip, Neo4JProfile02
from enmutils.lib.exceptions import EnvironError


class Neo4JProfile01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = Neo4JProfile01()
        self.flow.EXPIRE_TIME = 5
        self.flow.SLEEP_TIME = 1

        self.response = ("INFO: 18 peer nodes found.\r\n  "
                         "------------  -------  ----------  ------\r\n        "
                         "System    State     Cluster  Frozen\r\n  "
                         "------------  -------  ----------  ------\r\n  "
                         "ieatrcxb6248  RUNNING  db_cluster       -\r\n  "
                         "ieatrcxb6254  RUNNING  db_cluster       -\r\n  "
                         "ieatrcxb6312  RUNNING  db_cluster       -\r\n  "
                         "ieatrcxb6318  RUNNING  db_cluster    Perm\r\n  "
                         "------------  -------  ----------  ------\r\n")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.neo4j_lock_unlock")
    def test_execute_flow__without_schedule(self, mock_sleep_until_day, mock_keep_running,
                                            mock_neo4j_lock_unlock, *_):
        self.flow.execute_flow()
        mock_keep_running.assert_called(mock_keep_running.return_value)
        mock_sleep_until_day.assert_called(mock_sleep_until_day, 0)
        mock_neo4j_lock_unlock.assert_called(mock_neo4j_lock_unlock.return_value)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.neo4j_lock_unlock")
    def test_execute_flow__with_schedule(self, mock_sleep_until_day, mock_keep_running,
                                         mock_neo4j_lock_unlock, *_):
        setattr(self.flow, "SCHEDULED_DAYS", "Monday")
        self.flow.execute_flow()
        mock_keep_running.assert_called(mock_keep_running.return_value)
        mock_sleep_until_day.assert_called(mock_sleep_until_day, 0)
        mock_neo4j_lock_unlock.assert_called(mock_neo4j_lock_unlock.return_value)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.neo4j_lock_unlock", side_effect=[Exception])
    def test_execute_flow__Exception(self, mock_sleep_until_day, mock_neo4j_lock_unlock, *_):
        self.flow.execute_flow()
        mock_sleep_until_day.assert_called(mock_sleep_until_day, 0)
        mock_neo4j_lock_unlock.assert_called(mock_neo4j_lock_unlock.return_value)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.unfreeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.freeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_neo4j_leader_ip")
    def test_neo4j_lock_unlock__is_success(self, mock_leader, mock_freeze, mock_unfreeze, mock_debug, mock_sleep):
        self.flow.neo4j_lock_unlock()
        mock_sleep.assert_called(mock_sleep.return_value)
        mock_freeze.assert_called(mock_freeze)
        mock_unfreeze.assert_called(mock_unfreeze)
        mock_debug.assert_called(mock_debug)
        mock_sleep.assert_called(mock_sleep)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.unfreeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.freeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_neo4j_leader_ip", return_value=None)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    def test_neo4j_lock_unlock__no_neo4j_leader(self, mock_debug, *_):
        self.flow.neo4j_lock_unlock()
        mock_debug.assert_called(mock_debug)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.unfreeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.freeze_the_leader")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_neo4j_leader_ip", return_value=None)
    def test_neo4j_lock_unlock__add_error_as_exception(self, mock_get_neo4j_leader_ip, *_):
        mock_get_neo4j_leader_ip.side_effect = EnvironError("Something is wrong")
        self.flow.neo4j_lock_unlock()

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_get_neo4j_leader_ip__is_success(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout=self.response), Mock(rc=0, stdout="true")]
        self.assertEqual(get_neo4j_leader_ip(), "ieatrcxb6248")
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_shell.run_cmd_on_ms.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_get_neo4j_leader_ip__raises_environ_error(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=1, stdout="error")]
        self.assertRaises(EnvironError, get_neo4j_leader_ip)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_shell.run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_get_neo4j_leader_ip__if_neo4j_data_empty(self, mock_shell, mock_debug_log):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="")]
        get_neo4j_leader_ip()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_shell.run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_get_neo4j_leader_ip__if_neo4j_leader_not_found(self, mock_shell, mock_debug_log):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout=self.response), Mock(rc=0, stdout="false"),
                                                Mock(rc=0, stdout="false"), Mock(rc=0, stdout="false"),
                                                Mock(rc=0, stdout="true")]
        get_neo4j_leader_ip()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_shell.run_cmd_on_ms.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_unfreeze_the_leader__raises_environ_error(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="Result code: 1"), ]
        self.flow.unfreeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_freeze_the_leader__response_has_true(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="Result code: 0"),
                                                Mock(rc=0, stdout="Result code: 0")]
        self.flow.freeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 7)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_freeze_the_leader__response_doesnt_have_result_code(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="nothing")]
        self.flow.freeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 7)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime.timedelta')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime')
    def test_freeze_the_leader__response_raise_timeout_error(self, mock_datetime, mock_timedelta,
                                                             mock_shell, mock_debug_log, mock_add_error, _):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.flow.EXPIRE_TIME)
        mock_datetime.now.side_effect = [time_now, expiry_time]
        mock_timedelta.return_value = expiry_time

        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="Result code: 1"),
                                                Mock(rc=0, stdout="Result code: 1"),
                                                Mock(rc=0, stdout="Result code: 1")]
        self.flow.freeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime.timedelta')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime')
    def test_unfreeze_the_leader__response_raise_timeout_error(self, mock_datetime, mock_timedelta,
                                                               mock_shell, mock_debug_log, mock_add_error, _):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.flow.EXPIRE_TIME)
        mock_datetime.now.side_effect = [time_now, expiry_time]
        mock_timedelta.return_value = expiry_time

        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="Result code: 1"),
                                                Mock(rc=0, stdout="Result code: 1"),
                                                Mock(rc=0, stdout="Result code: 1")]
        self.flow.unfreeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_freeze_the_leader__freeze_is_false_has_correct_response_code(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=0, stdout="Result code: 0"),
                                                Mock(rc=0, stdout="Result code: 1")]
        self.flow.freeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 11)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_freeze_unfreeze_the_leader___freeze_is_false_but_doesnot_have_correct_response_code(self, mock_shell,
                                                                                                 mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=1, stdout="Result code: 0"), Mock(rc=1, stdout="Result code: 0")]
        self.flow.unfreeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell")
    def test_freeze_unfreeze_the_leader___freeze_is_false_has_rc_code_1(self, mock_shell, mock_debug_log, _):
        mock_shell.run_cmd_on_ms.side_effect = [Mock(rc=1, stdout="Result code: 0"),
                                                Mock(rc=0, stdout="Result code: 1")]
        self.flow.unfreeze_the_leader(neo4j_leader="leader")
        self.assertEqual(mock_debug_log.call_count, 10)


class Neo4JProfile02FlowUnitTests(unittest2.TestCase):
    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = Neo4JProfile02()
        self.flow.SLEEP_TIME = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_leader_check__success1(self, mock_shell, mock_debug_log, _):
        response_mock = Mock()
        response_mock.rc = 1
        response_mock.stdout = "false"
        mock_shell.return_value = response_mock
        self.assertRaises(EnvironError, self.flow.neo4j_leader_check)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native', return_value=None)
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_leader_check__no_vm_value(self, mock_shell, _):
        response_mock = Mock()
        response_mock.rc = 1
        response_mock.stdout = "false"
        mock_shell.return_value = response_mock
        self.assertRaises(EnvironError, self.flow.neo4j_leader_check)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_leader_check__fail(self, mock_shell, mock_debug_log, _):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = "false"
        mock_shell.return_value = response_mock
        self.flow.neo4j_leader_check()
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_leader_check__success(self, mock_shell, mock_debug_log, _):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = 'true'
        mock_shell.return_value = response_mock
        self.flow.neo4j_leader_check()
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_command_execution__success(self, mock_shell, mock_log):
        response_mock = Mock()
        response_mock.rc = 0
        mock_shell.return_value = response_mock
        self.flow.neo4j_command_execution('a', 'b')
        self.assertFalse(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_command_execution__failure(self, mock_shell, mock_log):
        response_mock = Mock()
        response_mock.rc = 1
        mock_shell.return_value = response_mock
        self.assertRaises(EnvironError, self.flow.neo4j_command_execution, 'a', 'b')
        self.assertFalse(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.pexpect')
    def test_neo4j_pexpect__success(self, mock_pexpect, mock_log, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 0]
        self.flow.neo4j_pexpect("l", "o")
        self.assertTrue(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.pexpect')
    def test_neo4j_pexpect__success1(self, mock_pexpect, mock_log, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 1]
        self.flow.neo4j_pexpect("l", "o")
        self.assertTrue(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.pexpect')
    def test_neo4j_pexpect__failure(self, mock_pexpect, mock_log, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 2]
        self.assertRaises(EnvironError, self.flow.neo4j_pexpect, "l", "o")
        self.assertTrue(mock_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.check_dps_online')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_leader_check')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_flow__success(self, mock_shell, mock_log, *_):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = ['LEA', 'FOL', 'FOL']
        mock_shell.return_value = response_mock
        self.assertFalse(mock_log.called)
        self.flow.neo4j_flow('a')
        self.assertTrue(mock_log.call_count, 7)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_leader_check')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_flow__success1(self, mock_shell, *_):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = ['L', 'FOL', 'FOL']
        mock_shell.return_value = response_mock
        self.assertRaises(EnvironError, self.flow.neo4j_flow, 'a')

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_pexpect')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_leader_check')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_neo4j_flow__failure(self, mock_shell, *_):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = ['L', 'F', 'FOL']
        mock_shell.return_value = response_mock
        self.assertRaises(EnvironError, self.flow.neo4j_flow, 'a')

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_flow')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.is_enm_on_cloud_native')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    def test_execute_flow__failure_if_no_vm_addresses(self, mock_vm, mock_add_exception, *_):
        mock_vm.return_value = []
        self.flow.execute_flow()
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_flow')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.is_enm_on_cloud_native')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    def test_execute_flow__failure_if_vm_addresses(self, mock_vm, mock_add_exception, *_):
        mock_vm.return_value = ['a']
        self.flow.execute_flow()
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_flow')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.is_enm_on_cloud_native')
    def test_execute_flow__success(self, mock_cloud_native, *_):
        mock_cloud_native.return_value = False
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod')
    def test_check_dps_online__response_has_true(self, mock_shell, mock_debug_log, *_):
        response_mock = Mock()
        response_mock.rc = 0
        response_mock.stdout = ['online']
        mock_shell.return_value = response_mock
        self.flow.check_dps_online('neo4j')
        self.assertTrue(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native",
           return_value="trouble pod")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.time.sleep", return_value=0)
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime.timedelta')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.shell.run_cmd_on_cloud_native_pod")
    def test_check_dps_online__response_has_failure(self, mock_shell, mock_debug_log, mock_datetime, mock_timedelta, *_):
        time_now = datetime(2022, 9, 6, 9, 0, 0)
        expiry_time = datetime(2022, 9, 6, 9, 9, 2, 0)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = expiry_time - time_now
        mock_shell.run_cmd_on_cloud_native_pod.side_effect = [Mock(rc=0, stdout="nothing")]
        self.flow.check_dps_online('neo4j')
        self.assertEqual(mock_debug_log.call_count, 7)

    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile02.neo4j_command_execution')
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.get_pod_hostnames_in_cloud_native",
           return_value="trouble pod")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.Neo4JProfile01."
           "add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime.timedelta')
    @patch('enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow.datetime')
    def test_check_dps_online__response_raise_timeout_error1(self, mock_datetime, mock_timedelta,
                                                             mock_add_error, mock_debug_log, *_):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.flow.EXPIRE_TIME)
        mock_datetime.now.side_effect = [time_now, expiry_time]
        mock_timedelta.return_value = expiry_time
        self.flow.check_dps_online('neo4j')
        self.assertEqual(mock_debug_log.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
