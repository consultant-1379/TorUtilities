#!/usr/bin/env python
import sys
import unittest2

import enmutils_int.bin.utilities as tool
from mock import patch, mock_open
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils

TOOL_NAME = "utilities.py"


class UtilitiesUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    # Tests

    @patch("signal.signal")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.exception.handle_invalid_argument")
    @patch("docopt.extras")
    @patch("enmutils.lib.init.exit")
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME],),
            ([TOOL_NAME, "blah"],),
            ([TOOL_NAME, "monitor_redis", "-blah"],),
        ]
    )
    def test_cli__handles_invalid_args(self, sys_argv, mock_exit, *_):
        sys.argv = sys_argv
        tool.cli()
        mock_exit.assert_called_with(1)

    @patch("signal.signal")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.exception.handle_invalid_argument")
    @patch("enmutils.lib.init.exit")
    @patch("docopt.extras", side_effect=SystemExit)
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME, "-h"],),
        ]
    )
    def test_cli__handles_help(self, sys_argv, *_):
        sys.argv = sys_argv
        self.assertRaises(SystemExit, tool.cli)

    @patch("signal.signal")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils_int.bin.utilities.remove_workload_admin_session_key")
    @patch("enmutils.lib.exception.handle_invalid_argument")
    @patch("enmutils_int.bin.utilities.monitor_redis", return_value=True)
    @patch("enmutils_int.bin.utilities.remove_workload_admin_session_key", return_value=True)
    @patch("enmutils_int.bin.utilities.ddc_plugin_create_increment_files", return_value=True)
    @patch("enmutils.lib.init.exit")
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME, "monitor_redis"],),
            ([TOOL_NAME, "remove_workload_admin_session_key"],),
            ([TOOL_NAME, "ddc_plugin_create_increment_files"],),
        ]
    )
    def test_cli__handles_valid_args(self, sys_argv, mock_exit, *_):
        sys.argv = sys_argv
        tool.cli()
        mock_exit.assert_called_with(0)

    @patch("enmutils_int.bin.utilities.signal.signal")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.exception.handle_exception")
    @patch("docopt.extras")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils_int.bin.utilities.monitor_redis")
    def test_cli__returns_non_zero_result_code_if_monitor_redis_throws_exception(
            self, mock_monitor_redis, mock_exit, *_):
        mock_monitor_redis.side_effect = Exception
        sys.argv = [TOOL_NAME, "monitor_redis"]
        tool.cli()
        mock_exit.assert_called_with(1)

    @patch("enmutils_int.bin.utilities.get_redis_big_keys")
    @patch("enmutils_int.bin.utilities.get_redis_info")
    @patch("enmutils_int.bin.utilities.shell.run_local_cmd")
    @patch("enmutils_int.bin.utilities.shell.Command")
    @patch("enmutils_int.bin.utilities.log.logger.error")
    def test_monitor_redis__is_successful(self, mock_error, *_):
        tool.monitor_redis()
        self.assertFalse(mock_error.called)

    @patch("enmutils_int.bin.utilities.get_redis_big_keys", return_value=False)
    @patch("enmutils_int.bin.utilities.get_redis_info")
    @patch("enmutils_int.bin.utilities.shell.run_local_cmd")
    @patch("enmutils_int.bin.utilities.shell.Command")
    @patch("enmutils_int.bin.utilities.log.logger.error")
    def test_monitor_redis__is_unsuccessful(self, mock_error, *_):
        tool.monitor_redis()
        self.assertTrue(mock_error.called)

    @patch("enmutils_int.bin.utilities.shell.run_local_cmd")
    @patch("enmutils_int.bin.utilities.shell.Command")
    def test_get_redis_big_keys__is_successful(self, *_):
        tool.get_redis_big_keys()

    @patch("enmutils_int.bin.utilities.shell.run_local_cmd")
    @patch("enmutils_int.bin.utilities.shell.Command")
    def test_get_redis_info__is_successful(self, *_):
        tool.get_redis_info()

    @patch("enmutils_int.bin.utilities.mutexer.mutex")
    @patch("enmutils_int.bin.utilities.persistence.get", return_value=True)
    @patch("enmutils_int.bin.utilities.persistence.remove")
    def test_remove_workload_admin_session_key__removes_key(self, mock_remove, *_):
        tool.remove_workload_admin_session_key()
        self.assertEqual(1, mock_remove.call_count)

    @patch("enmutils_int.bin.utilities.mutexer.mutex")
    @patch("enmutils_int.bin.utilities.persistence.get", return_value=None)
    @patch("enmutils_int.bin.utilities.persistence.remove")
    def test_remove_workload_admin_session_key__removes_key_if_exists(self, mock_remove, *_):
        tool.remove_workload_admin_session_key()
        self.assertEqual(0, mock_remove.call_count)

    @patch("enmutils_int.bin.utilities.create_workload_log_file_increments", return_value=True)
    def test_ddc_plugin_create_increment_files__successful(self, _):
        self.assertTrue(tool.ddc_plugin_create_increment_files())

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch("enmutils_int.bin.utilities.append_history_of_commands")
    def test_update_history_cmd_options__successful(self, mock_append, *_):
        tool.improve_command_history_logs()
        self.assertTrue(mock_append.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
