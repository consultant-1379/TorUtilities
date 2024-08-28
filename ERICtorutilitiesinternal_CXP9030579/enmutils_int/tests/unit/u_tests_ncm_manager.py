#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.ncm_manager import (fetch_ncm_vm, lcm_db_restore, ncm_run_cmd_on_vm, ncm_rest_query,
                                          perform_db_restore, switch_to_application_vm, check_db_backup_file_available)
from testslib import unit_test_utils


class NcmManagerUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.ncm_manager.log.logger.debug')
    def test_ncm_rest_query__success(self, mock_log):
        user_response = Mock()
        user_response.status_code = 200
        user_response.text = "{}"
        user_response.post.return_value = user_response
        ncm_rest_query(user_response, "/ncm/rest/management/realign-nodes", data="node1;node2")
        mock_log.called_with("realign-nodes success")

    @patch('enmutils_int.lib.ncm_manager.log.logger.debug')
    def test_ncm_rest_query__failed_nodes(self, mock_log):
        user_response = Mock()
        user_response.status_code = 200
        user_response.text = "Error"
        user_response.json.return_value = {"errorMessage": "Unable to order the realignment for some of the nodes",
                                           "failedNodes": ["node1", "node2"]}
        user_response.post.return_value = user_response
        ncm_rest_query(user_response, "/ncm/rest/management/realign-nodes", data="node1;node2")
        mock_log.called_with("Realignment successfully ordered for some of the nodes is {0},{1}"
                             .format("Unable to order the realignment for some of the nodes", ["node1", "node2"]))

    @patch('enmutils_int.lib.ncm_manager.build_user_message')
    @patch('enmutils_int.lib.ncm_manager.log.logger.debug')
    def test_ncm_rest_query__raises_http_error(self, *_):
        user_response = Mock()
        user_response.status_code = 404
        user_response.text = "Error"
        user_response.json.return_value = {"errorMessage": "NCM Agent is not avaialble"}
        user_response.post.return_value = user_response
        self.assertRaises(HTTPError, ncm_rest_query, user_response, "/ncm/rest/management/realign-nodes",
                          data="node1;node2")

    @patch('enmutils_int.lib.ncm_manager.log.logger.debug')
    def test_ncm_rest_query__wrong_status_code(self, _):
        user_response = Mock()
        user_response.status_code = 300
        user_response.post.return_value = user_response
        ncm_rest_query(user_response, "/ncm/rest/management/realign-nodes", data="node1;node2")

    @patch("enmutils_int.lib.ncm_manager.is_enm_on_cloud_native", return_value=False)
    @patch('enmutils_int.lib.ncm_manager.get_values_from_global_properties',
           return_value=[unit_test_utils.generate_configurable_ip()])
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_fetch_ncm_vm__success(self, mock_log, *_):
        fetch_ncm_vm()
        self.assertEqual(2, mock_log.call_count)

    @patch("enmutils_int.lib.ncm_manager.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_fetch_ncm_vm__raises_environ_error(self, *_):
        self.assertRaises(EnvironError, fetch_ncm_vm)

    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    @patch("enmutils_int.lib.ncm_manager.ncm_run_cmd_on_vm")
    def test_check_db_backup_file_available__successful(self, mock_ncm_run_cmd_on_vm, *_):
        check_db_backup_file_available("ncm_backup.tar.gz", "0.0.0.0")
        self.assertEqual(mock_ncm_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    @patch("enmutils_int.lib.ncm_manager.ncm_run_cmd_on_vm")
    def test_check_db_backup_file_available__exception_raised(self, mock_run_cmd_on_vm, _):
        mock_run_cmd_on_vm.side_effect = [EnmApplicationError]
        self.assertRaises(EnvironError, check_db_backup_file_available, Mock(), Mock())

    @patch("enmutils_int.lib.ncm_manager.fetch_ncm_vm", return_value=[unit_test_utils.generate_configurable_ip()])
    @patch("enmutils_int.lib.ncm_manager.check_db_backup_file_available")
    @patch("enmutils_int.lib.ncm_manager.perform_db_restore")
    @patch("enmutils_int.lib.ncm_manager.ncm_run_cmd_on_vm")
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_lcm_db_restore__is_successful(self, mock_log, mock_ncm_run_cmd_on_vm, mock_perform_db_restore, mock_db_backup_file, *_):
        lcm_db_restore("ncm_backup.tar.gz")
        self.assertEqual(3, mock_log.call_count)
        self.assertEqual(1, mock_db_backup_file.call_count)
        self.assertEqual(6, mock_ncm_run_cmd_on_vm.call_count)
        self.assertTrue(mock_perform_db_restore.called)

    @patch("enmutils_int.lib.ncm_manager.fetch_ncm_vm", return_value=[unit_test_utils.generate_configurable_ip()])
    @patch("enmutils_int.lib.ncm_manager.perform_db_restore")
    @patch("enmutils_int.lib.ncm_manager.ncm_run_cmd_on_vm")
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_lcm_db_restore__logs_exception_and_continues(self, mock_log, mock_run_cmd_on_vm,
                                                          mock_perform_db_restore, *_):
        mock_run_cmd_on_vm.side_effect = ["", "", Exception, "", "", "", ""]
        lcm_db_restore("ncm_backup.tar.gz")
        self.assertEqual(4, mock_log.call_count)
        self.assertEqual(7, mock_run_cmd_on_vm.call_count)
        self.assertFalse(mock_perform_db_restore.called)

    @patch("enmutils_int.lib.ncm_manager.GenericFlow.switch_to_ms_or_emp", return_value=Mock())
    @patch("enmutils_int.lib.ncm_manager.switch_to_application_vm")
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_mef_perform_db_restore__is_successful(self, mock_log, mock_switch_to_app_vm, *_):
        mock_switch_to_app_vm.return_value.expect.return_value = 2
        perform_db_restore("svc-3-ncm", "ncm_backup.tar.gz")
        self.assertEqual(7, mock_log.call_count)

    @patch("enmutils_int.lib.ncm_manager.GenericFlow.switch_to_ms_or_emp", return_value=Mock())
    @patch("enmutils_int.lib.ncm_manager.switch_to_application_vm")
    def test_mef_perform_db_restore__raised_environ_error_if_invalid_file_is_given(self, mock_switch_to_app_vm, *_):
        mock_switch_to_app_vm.return_value.expect.return_value = 0
        self.assertRaises(EnvironError, perform_db_restore, "svc-3-ncm", "ncm_backup.tar.gz")

    @patch("enmutils_int.lib.ncm_manager.GenericFlow.switch_to_ms_or_emp", return_value=Mock())
    @patch("enmutils_int.lib.ncm_manager.switch_to_application_vm")
    def test_mef_perform_db_restore__raised_environ_error_if_ncm_db_is_still_running(self, mock_switch_to_app_vm, *_):
        mock_switch_to_app_vm.return_value.expect.return_value = 1
        self.assertRaises(EnvironError, perform_db_restore, "svc-3-ncm", "ncm_backup.tar.gz")

    @patch("enmutils_int.lib.ncm_manager.GenericFlow.switch_to_ms_or_emp", return_value=Mock())
    @patch("enmutils_int.lib.ncm_manager.switch_to_application_vm")
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_mef_perform_db_restore__logs_error_if_pexpect_timed_out(self, mock_log, mock_switch_to_app_vm, *_):
        mock_switch_to_app_vm.return_value.expect.return_value = 3
        perform_db_restore("svc-3-ncm", "ncm_backup.tar.gz")
        self.assertEqual(3, mock_log.call_count)

    @patch("enmutils_int.lib.ncm_manager.shell.Command")
    @patch("enmutils_int.lib.ncm_manager.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_ncm_run_cmd_on_vm__success(self, mock_log, mock_run_vm, _):
        response = Mock(rc=0)
        mock_run_vm.return_value = response
        ncm_run_cmd_on_vm("ncm start", "svc-3-ncm")
        mock_log.assert_called_with("Executed NCM command: ncm start successfully")

    @patch("enmutils_int.lib.ncm_manager.shell.Command")
    @patch("enmutils_int.lib.ncm_manager.shell.run_cmd_on_vm")
    def test_ncm_run_cmd_on_vm__raises_enm_application_error(self, mock_run_vm, _):
        response = Mock(rc=1)
        mock_run_vm.return_value = response
        self.assertRaises(EnmApplicationError, ncm_run_cmd_on_vm, "ncm dbrestore", "svc-3-ncm")

    @patch("enmutils_int.lib.ncm_manager.is_emp", return_value=True)
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_switch_to_application_vm__is_successful_for_cloud(self, mock_logger, *_):
        switch_to_application_vm(Mock(), "svc-3-ncm")
        self.assertEqual(mock_logger.call_count, 2)

    @patch("enmutils_int.lib.ncm_manager.is_emp", return_value=False)
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_switch_to_application_vm__is_successful_for_physical(self, mock_logger, *_):
        switch_to_application_vm(Mock(), "svc-3-ncm")
        self.assertEqual(mock_logger.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.ncm_manager.is_emp", return_value=True)
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_switch_to_application_vm__raises_environ_error_after_three_retries_on_cloud(self, mock_logger, *_):
        child = Mock()
        child.sendline.side_effect = Exception
        self.assertRaises(EnvironError, switch_to_application_vm, child, "svc-3-ncm")
        self.assertEqual(mock_logger.call_count, 3)

    @patch("time.sleep")
    @patch("enmutils_int.lib.ncm_manager.is_emp", return_value=False)
    @patch("enmutils_int.lib.ncm_manager.log.logger.debug")
    def test_switch_to_application_vm__raises_environ_error_after_three_retries_on_physical(self, mock_logger, *_):
        child = Mock()
        child.sendline.side_effect = Exception
        self.assertRaises(EnvironError, switch_to_application_vm, child, "svc-3-ncm")
        self.assertEqual(mock_logger.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
