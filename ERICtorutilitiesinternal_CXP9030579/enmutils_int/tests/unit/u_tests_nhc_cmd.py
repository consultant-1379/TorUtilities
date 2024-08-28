#!/usr/bin/env python
from datetime import datetime, timedelta

from testslib import unit_test_utils
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, TimeOutError
import unittest2
from mock import patch, Mock
from enmutils_int.lib.nhc_cmd import NHCCmds


class NHCcommandsTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nhc_run_command = NHCCmds(self.user, 0)
        self.nodes_list = [Mock(node_id="id")] * 5

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.nhc_cmd.log.logger.info')
    @patch('enmutils_int.lib.nhc_cmd.log.logger.debug')
    def test_execute__is_successful(self, mock_logger_debug, _):
        response = Mock()
        response.get_output.return_value = [' ', 'Job post_upgrade_check1_2016_06_28_022704_826 successfully created.']
        self.user.enm_execute.return_value = response
        self.nhc_run_command.execute(self.nodes_list)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.nhc_cmd.log.logger.info')
    def test_execute__raises_ScriptEngineResponseValidationError(self, _):
        response = Mock()
        response.get_output.return_value = [' ', 'Job post_upgrade_check1_2016_06_28_022704_826 failed.']
        self.user.enm_execute.return_value = response
        with self.assertRaises(ScriptEngineResponseValidationError):
            self.nhc_run_command.execute(self.nodes_list)

    def test_check_results__is_successful(self):
        response = Mock()
        response.get_output.return_value = [' ',
                                            'HC_2016_08_09_070001_782        NHC_01_2016-08-08_13-56-38-2923_USER_0  '
                                            '100       2016-08-09T07:00:01     Completed       Failure']
        self.user.enm_execute.return_value = response
        self.nhc_run_command.timeout = 1
        execution_time = self.nhc_run_command.check_result(self.nodes_list)
        self.assertEqual(execution_time, 0)

    @patch('enmutils_int.lib.nhc_cmd.time.sleep')
    @patch('enmutils_int.lib.nhc_cmd.log.logger.debug')
    def test_check_results__does_not_retry_if_timed_out_and_raises_TimeOutError(self, mock_debug, mock_sleep):
        response = self.user.enm_execute.return_value = Mock()
        response.get_output.return_value = [
            'HC_2016_08_09_073002_454        NHC_01_2016-08-08_13-56-14-0460_USER_0  1000    2016-08-09T07:30:03'
            '     In progress (94%)']

        with self.assertRaises(TimeOutError):
            self.nhc_run_command.check_result(self.nodes_list)

        self.assertEqual(0, mock_debug.call_count)
        self.assertEqual(0, mock_sleep.call_count)

    @patch('enmutils_int.lib.nhc_cmd.timedelta', return_value=timedelta(minutes=2))
    @patch('enmutils_int.lib.nhc_cmd.time.sleep')
    @patch('enmutils_int.lib.nhc_cmd.log.logger.debug')
    @patch('enmutils_int.lib.nhc_cmd.datetime')
    def test_check_results__retries_if_not_timed_out_without_raising_timeout_error(self, mock_datetime, mock_debug,
                                                                                   mock_sleep, *_):
        response = self.user.enm_execute.return_value = Mock()
        mock_datetime.now.return_value = datetime(2020, 10, 8, 11, 50)
        response.get_output.side_effect = [
            'HC_2016_08_09_073002_454        NHC_01_2016-08-08_13-56-14-0460_USER_0  1000    2016-08-09T07:30:03'
            '     In progress (94%)', " "]

        self.nhc_run_command.check_result(self.nodes_list)

        mock_debug.assert_called_with('NHC report in progress. Checking every 30s')
        mock_sleep.assert_called_with(30)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
