# !/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.workload.nas_outage_01 import NAS_OUTAGE_01
from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01 import (NasOutage01Flow, check_status_of_nas)
from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow import is_nas_accessible


class NasOutage01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = NasOutage01Flow()
        self.flow.SLEEP_TIME = 5

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.shell.run_cmd_on_ms")
    def test_is_nas_accessible__if_available(self, mock_run_cmd_on_ms, mock_debug_log):
        mock_run_cmd_on_ms.return_value = Mock(rc=0, stdout="nasconsole")
        self.assertEqual(is_nas_accessible(), True)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.shell.run_cmd_on_ms")
    def test_is_nas_accessible__if_not_available(self, mock_run_cmd_on_ms, mock_debug_log):
        mock_run_cmd_on_ms.return_value = Mock(rc=0, stdout="test")
        self.assertEqual(is_nas_accessible(), False)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow.shell.run_cmd_on_ms")
    def test_is_nas_accessible__raises_env_error(self, mock_run_cmd_on_ms, mock_debug_log):
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout="error")
        self.assertRaises(EnvironError, is_nas_accessible)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.cache.get_ms_host", return_value="host")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_check_status_of_nas__is_successful(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        check_status_of_nas()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.cache.get_ms_host", return_value="host")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_check_status_of_nas__if_lms_login_failed(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 1, 0, 0]
        self.assertRaises(EnvironError, check_status_of_nas)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.cache.get_ms_host", return_value="host")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_check_status_of_nas__if_nas_login_failed(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 3, 0, 0]
        self.assertRaises(EnvironError, check_status_of_nas)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.cache.get_ms_host", return_value="host")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_check_status_of_nas__if_nas_login_pwd_propmpt_not_appear(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 2, 0]
        self.assertRaises(EnvironError, check_status_of_nas)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.cache.get_ms_host", return_value="host")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_check_status_of_nas__if_nas_is_offline(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 2]
        check_status_of_nas()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.is_nas_accessible", return_value=True)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.nfs_server_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    def test_execute_flow__is_successful(self, mock_add_error, mock_nfs_server_change, mock_debug_log, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_nfs_server_change.call_count, 2)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.is_nas_accessible", return_value=False)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.nfs_server_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    def test_execute_flow__if_nas_not_found(self, mock_add_error, mock_nfs_server_change, mock_debug_log, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 0)
        self.assertEqual(mock_nfs_server_change.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.is_nas_accessible",
           side_effect=EnvironError("error"))
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.nfs_server_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    def test_execute_flow__add_error_exception(self, mock_add_error, mock_nfs_server_change, mock_debug_log, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 0)
        self.assertEqual(mock_nfs_server_change.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__is_successful_with_start(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.check_status_of_nas", return_value="OFFLINE")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__add_error_with_start(self, mock_spawn, mock_debug_log, mock_add, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_add.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.check_status_of_nas", return_value="OFFLINE")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug", side_effect=['q',
                                                                                                          'w', 'e',
                                                                                                          Exception])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__Exception(self, mock_spawn, mock_debug_log, mock_add, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_add.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.check_status_of_nas", return_value="OFFLINE")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__status_check_failed(self, mock_spawn, mock_debug_log, mock_add, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_add.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__is_successful_with_stop(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        self.flow.nfs_server_change("stop")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__if_lms_login_failed(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 1, 0, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__if_nas_login_failed(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 2, 0, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.pexpect.spawn")
    def test_nfs_server_change__if_nas_login_pwd_propmpt_not_appear(self, mock_spawn, mock_debug_log, _):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0]
        self.flow.nfs_server_change("start")
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01.NasOutage01Flow.execute_flow")
    def test_run__nas_outage_01_is_successful(self, _):
        nas_outage_01 = NAS_OUTAGE_01()
        nas_outage_01.run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
