#!/usr/bin/env python
from parameterizedtestcase import ParameterizedTestCase
import unittest2
from mock import Mock, patch
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, ScriptEngineResponseValidationError
from enmutils_int.lib import winfiol_operations
from testslib import unit_test_utils


class WinfiolOperationsTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.user.username = "mock"
        self.user.password = "mock"
        self.username_data = "User1,User2,User3"
        winfiol_operations.TIMEOUT = Mock()
        winfiol_operations.WINFIOL_CMD = Mock()
        winfiol_operations.WINFIOL_TIMEOUT_SECS = 2
        winfiol_operations.CMD_PKI_SETUP_COMMAND = Mock()
        winfiol_operations.CMD_LIST_TMP_DIR = Mock()
        self.response_OK = Mock(rc=0, stdout="Error opening terminal")
        self.response_NOK = Mock(rc=1, stdout="Error")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.winfiol_operations.shell')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_login_to_general_scripting_to_download_certificates__success(self, mock_log, mock_shell):
        self.assertTrue(winfiol_operations.login_to_general_scripting_to_download_certificates("username", "password", Mock()))
        self.assertEqual(mock_log.call_count, 2)
        self.assertTrue(mock_shell.run_remote_cmd.called)

    @patch('enmutils_int.lib.winfiol_operations.shell')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_login_to_general_scripting_to_download_certificates__raises_environ_error_for_unreachable_host(self, mock_log, mock_shell):
        mock_response = Mock()
        mock_response.rc = 5
        mock_response.stdout = "Error: Unable to reach host, please ensure the host is available"
        mock_shell.run_remote_cmd.return_value = mock_response
        self.assertRaises(EnvironError, winfiol_operations.login_to_general_scripting_to_download_certificates, "username",
                          "password", Mock())
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.winfiol_operations.shell')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_login_to_general_scripting_to_download_certificates__verify_cert_folder_success(self, mock_log, mock_shell):
        mock_response = Mock()
        mock_response.rc = 0
        mock_shell.run_remote_cmd.side_effect = [Exception, mock_response]
        self.assertTrue(winfiol_operations.login_to_general_scripting_to_download_certificates("username", "password", Mock()))
        self.assertEqual(mock_log.call_count, 4)

    @patch('enmutils_int.lib.winfiol_operations.shell')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_login_to_general_scripting_to_download_certificates__verify_cert_folder_failure(self, mock_log, mock_shell):
        mock_response = Mock()
        mock_response.rc = 1
        mock_shell.run_remote_cmd.side_effect = [Exception, mock_response]
        self.assertFalse(winfiol_operations.login_to_general_scripting_to_download_certificates("username", "password", Mock()))
        self.assertEqual(mock_log.call_count, 4)

    @patch('enmutils_int.lib.winfiol_operations.shell')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_login_to_general_scripting_to_download_certificates__verify_cert_folder_exception(self, mock_log, mock_shell):
        mock_shell.run_remote_cmd.side_effect = [Exception, Exception]
        self.assertFalse(winfiol_operations.login_to_general_scripting_to_download_certificates("username", "password", Mock()))
        self.assertEqual(mock_log.call_count, 4)

    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_perform_winfiol_operations__login_success(self, mock_log, mock_download_cert):
        scp_ip = unit_test_utils.generate_configurable_ip()
        winfiol_operations.perform_winfiol_operations([self.user], [scp_ip])
        mock_download_cert.assert_called_with("mock", "mock", scp_ip)
        mock_log.assert_called_with("Successfully completed executing WINFIOL operations..")

    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_perform_winfiol_operations__continues_with_other_scp_ip_if_one_fails(self, mock_log, mock_download_cert):
        user1 = Mock(username="mock", password="mock")
        user2 = Mock(username="mock1", password="mock1")
        scp_ip_1 = unit_test_utils.generate_configurable_ip()
        scp_ip_2 = unit_test_utils.generate_configurable_ip(start=2)
        scp_ip_3 = unit_test_utils.generate_configurable_ip(start=3)
        mock_download_cert.side_effect = [Exception, False, True, False, True]
        winfiol_operations.perform_winfiol_operations([user1, user2], [scp_ip_1, scp_ip_2, scp_ip_3])
        mock_log.assert_called_with("Successfully completed executing WINFIOL operations..")

    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_perform_winfiol_operations__stops_execution_if_ten_continuous_failures_are_observed(self, mock_log, mock_download_cert):
        user_list = [Mock(username="mock", password="mock")] * 20
        scp_ip_1 = unit_test_utils.generate_configurable_ip()
        mock_download_cert.side_effect = [False] * 10
        with self.assertRaisesRegex(EnmApplicationError, "Winfiol operations have failed for users"):
            winfiol_operations.perform_winfiol_operations(user_list, [scp_ip_1])

    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_perform_winfiol_operations__raises_exception_if_scripting_ips_empty(self, _):
        self.assertRaises(EnmApplicationError, winfiol_operations.perform_winfiol_operations, [self.user], [])

    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates', side_effect=Exception)
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_perform_winfiol_operations__raises_enm_application_error_if_connection_to_scripting_unsuccessful(self, *_):
        self.assertRaises(EnmApplicationError, winfiol_operations.perform_winfiol_operations, [self.user], [Mock()])

    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates')
    def test_perform_winfiol_operations__raises_enm_application_error_if_winfiol_PKI_failed_for_users(self,
                                                                                                      mock_login_to_scp,
                                                                                                      *_):
        user1 = Mock(username="AMOS_01_12345678", password="12345678")
        user2 = Mock(username="AMOS_01_98765432", password="10101010")
        ip_address = unit_test_utils.generate_configurable_ip()
        mock_login_to_scp.side_effect = [False, True]
        self.assertRaises(EnmApplicationError, winfiol_operations.perform_winfiol_operations, [user1, user2],
                          [ip_address])

    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    @patch('enmutils_int.lib.winfiol_operations.login_to_general_scripting_to_download_certificates')
    @ParameterizedTestCase.parameterize(
        ("value", "result"),
        [
            ([True], True),
            (Exception, None)
        ]
    )
    def test_execute_script_with_user__returns_as_expected(self, value, result, mock_download_certs, *_):
        mock_download_certs.side_effect = value
        self.assertEqual(winfiol_operations.execute_script_with_user(Mock(), Mock()), result)

    @patch('enmutils_int.lib.winfiol_operations.time.sleep', return_value=0)
    @patch('enmutils_int.lib.winfiol_operations.divide_users_per_scripting_vm')
    @patch('enmutils_int.lib.winfiol_operations.get_workload_admin_user')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    @patch('enmutils_int.lib.winfiol_operations.shell.run_remote_cmd')
    @patch('enmutils_int.lib.winfiol_operations.shell.Command')
    def test_run_setupeeforamosusers_scripting_cluster__is_successful(self, mock_cmd, mock_run_cmd, mock_log,
                                                                      mock_admin, mock_divide_users, *_):
        user1 = Mock(username="AMOS_01_111111")
        user2 = Mock(username="AMOS_01_222222")
        ip1 = unit_test_utils.generate_configurable_ip()
        ip2 = unit_test_utils.generate_configurable_ip(start=2, end=9)
        mock_admin.return_value = self.user
        mock_divide_users.return_value = {ip1: [user1, user2], ip2: []}
        mock_run_cmd.return_value = Mock(rc=0, stdout="Script Not running")
        winfiol_operations.run_setupeeforamosusers_scripting_cluster([user1, user2], [Mock()])
        self.assertEqual(mock_log.call_count, 2)
        self.assertTrue(mock_admin.called)
        self.assertTrue(mock_run_cmd.called)
        self.assertTrue(mock_cmd.called)

    @patch('enmutils_int.lib.winfiol_operations.time.sleep', return_value=0)
    @patch('enmutils_int.lib.winfiol_operations.divide_users_per_scripting_vm')
    @patch('enmutils_int.lib.winfiol_operations.get_workload_admin_user')
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    @patch('enmutils_int.lib.winfiol_operations.shell.run_remote_cmd')
    @patch('enmutils_int.lib.winfiol_operations.shell.Command')
    def test_run_setupeeforamosusers_scripting_cluster__continues_if_rc_is_non_zero_on_one_scripting_vm(
            self, mock_cmd, mock_run_cmd, mock_log, mock_admin, mock_divide_users, *_):
        user1 = Mock(username="AMOS_01_111111")
        user2 = Mock(username="AMOS_01_222222")
        ip1 = unit_test_utils.generate_configurable_ip()
        ip2 = unit_test_utils.generate_configurable_ip(start=2, end=9)
        mock_admin.return_value = self.user
        mock_divide_users.return_value = {ip1: [user1], ip2: [user2]}
        mock_run_cmd.side_effect = [Mock(rc=177, stdout="Error"), Mock(rc=0, stdout="Script Not running")]
        winfiol_operations.run_setupeeforamosusers_scripting_cluster([user1, user2], [Mock()])
        self.assertEqual(mock_log.call_count, 3)
        self.assertTrue(mock_admin.called)
        self.assertTrue(mock_run_cmd.call_count, 2)
        self.assertTrue(mock_cmd.called)

    @patch('enmutils_int.lib.winfiol_operations.divide_users_per_scripting_vm', side_effect=Exception)
    @patch('enmutils_int.lib.winfiol_operations.get_workload_admin_user', )
    @patch('enmutils_int.lib.winfiol_operations.log.logger.debug')
    def test_run_setupeeforamosusers_scripting_cluster__empty_scripting_cluster(self, mock_log, mock_admin, *_):
        mock_admin.return_value = self.user
        self.assertRaises(EnmApplicationError, winfiol_operations.run_setupeeforamosusers_scripting_cluster, [Mock()],
                          [Mock()])
        self.assertTrue(mock_admin.called)

    @patch('enmutils_int.lib.winfiol_operations.arguments')
    def test_divide_users_per_scripting_vm__returns_user_per_scritping_vm_if_odd_users_greater_than_vms(self,
                                                                                                        mock_args):
        users = ["AMOS_01_1111", "AMOS_01_2222", "AMOS_01_3333", "AMOS_01_4444", "AMOS_01_5555"]
        ip1 = unit_test_utils.generate_configurable_ip()
        ip2 = unit_test_utils.generate_configurable_ip(start=2, end=9)
        expected_result = {ip1: ["AMOS_01_1111", "AMOS_01_2222", "AMOS_01_5555"], ip2: ["AMOS_01_3333", "AMOS_01_4444"]}
        scp_ips = [ip1, ip2]
        mock_args.split_list_into_chunks.return_value = [["AMOS_01_1111", "AMOS_01_2222"],
                                                         ["AMOS_01_3333", "AMOS_01_4444"], ["AMOS_01_5555"]]
        actual_result = winfiol_operations.divide_users_per_scripting_vm(scp_ips, users)
        self.assertEqual(actual_result, expected_result)

    @patch('enmutils_int.lib.winfiol_operations.arguments')
    def test_divide_users_per_scripting_vm__returns_user_per_scritping_vm_if_even_users_greater_than_vms(self,
                                                                                                         mock_args):
        users = ["AMOS_01_1111", "AMOS_01_2222", "AMOS_01_3333", "AMOS_01_4444"]
        ip1 = unit_test_utils.generate_configurable_ip()
        ip2 = unit_test_utils.generate_configurable_ip(start=2, end=9)
        expected_result = {ip1: ["AMOS_01_1111", "AMOS_01_2222"], ip2: ["AMOS_01_3333", "AMOS_01_4444"]}
        scp_ips = [ip1, ip2]
        mock_args.split_list_into_chunks.return_value = [["AMOS_01_1111", "AMOS_01_2222"],
                                                         ["AMOS_01_3333", "AMOS_01_4444"]]
        actual_result = winfiol_operations.divide_users_per_scripting_vm(scp_ips, users)
        self.assertEqual(actual_result, expected_result)

    def test_divide_users_per_scripting_vm__returns_user_per_scritping_vm_if_users_less_than_vms(self):
        users = ["AMOS_01_1111", "AMOS_01_2222"]
        ip1 = unit_test_utils.generate_configurable_ip()
        ip2 = unit_test_utils.generate_configurable_ip(start=2, end=9)
        ip3 = unit_test_utils.generate_configurable_ip(start=3, end=10)
        expected_result = {ip1: ["AMOS_01_1111"], ip2: ["AMOS_01_2222"]}
        scp_ips = [ip1, ip2, ip3]
        actual_result = winfiol_operations.divide_users_per_scripting_vm(scp_ips, users)
        self.assertEqual(actual_result, expected_result)

    @patch('enmutils_int.lib.winfiol_operations.time.sleep')
    @patch('enmutils_int.lib.winfiol_operations.mutexer.mutex')
    @patch('enmutils_int.lib.winfiol_operations.deploymentinfomanager_adaptor')
    @patch('enmutils_int.lib.winfiol_operations.run_setupeeforamosusers_scripting_cluster')
    @patch('enmutils_int.lib.winfiol_operations.perform_winfiol_operations')
    def test_create_pki_entity_and_download_tls_certs__user_list(self, mock_winfiol_op, mock_amos_sc, mock_dep_adaptor, *_):
        user = [Mock(username="Testuser")]
        scp_ips = [Mock()]
        mock_dep_adaptor.get_list_of_scripting_service_ips.return_value = scp_ips
        winfiol_operations.create_pki_entity_and_download_tls_certs(user)
        mock_amos_sc.assert_called_with(user, scp_ips)
        mock_winfiol_op.assert_called_with(user, scp_ips)

    @patch('enmutils_int.lib.winfiol_operations.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.winfiol_operations.mutexer.mutex')
    @patch('enmutils_int.lib.winfiol_operations.deploymentinfomanager_adaptor')
    @patch('enmutils_int.lib.winfiol_operations.run_setupeeforamosusers_scripting_cluster', side_effect=Exception)
    def test_create_pki_entity_and_download_tls_certs__raises_environ_error(self, mock_run, mock_dep_adaptor, *_):
        user = [Mock(username="Testuser")]
        mock_dep_adaptor.get_list_of_scripting_service_ips.return_value = [unit_test_utils.generate_configurable_ip()]
        self.assertRaises(EnvironError, winfiol_operations.create_pki_entity_and_download_tls_certs, user)
        self.assertEqual(2, mock_run.call_count)

    @patch('enmutils_int.lib.winfiol_operations.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.winfiol_operations.mutexer.mutex')
    @patch('enmutils_int.lib.winfiol_operations.deploymentinfomanager_adaptor')
    @patch('enmutils_int.lib.winfiol_operations.run_setupeeforamosusers_scripting_cluster', side_effect=Exception)
    def test_create_pki_entity_and_download_tls_certs__raises_environ_error_if_scripting_ips_empty(self, mock_run,
                                                                                                   mock_dep_adaptor, *_):
        user = [Mock(username="Testuser")]
        mock_dep_adaptor.get_list_of_scripting_service_ips.return_value = []
        self.assertRaises(EnvironError, winfiol_operations.create_pki_entity_and_download_tls_certs, user)

    @patch('enmutils_int.lib.winfiol_operations.check_revoke_delete_entity_status')
    @patch("enmutils_int.lib.winfiol_operations.get_workload_admin_user")
    def test_perform_revoke_activity__execute_revoke_activity(self, mock_user, mock_revoke):
        revoke_response = Mock()
        revoke_response.get_output.return_value = [u'revoked successfully']
        mock_user.return_value.enm_execute.return_value = revoke_response
        winfiol_operations.perform_revoke_activity([self.user])
        self.assertTrue(mock_revoke.called)

    @patch("enmutils_int.lib.winfiol_operations.log.logger.debug")
    def test_check_revoke_delete_entity_status__success(self, mock_debug):
        mock_user = Mock()
        mock_user.enm_execute.return_value.get_output.return_value = [u'successfully deleted']
        winfiol_operations.check_revoke_delete_entity_status(self.user, mock_user, 'revoked successfully')
        mock_debug.assert_called_with("mock entity deleted successfully")

    def test_check_revoke_delete_entity_status__fail(self):
        mock_user = Mock()
        mock_user.enm_execute.return_value.get_output.return_value = [u'failed to delete']
        self.assertRaises(ScriptEngineResponseValidationError, winfiol_operations.check_revoke_delete_entity_status,
                          self.user, mock_user, 'revoked successfully')

    def test_check_revoke_delete_entity_status__revoke_fail(self):
        self.assertRaises(ScriptEngineResponseValidationError, winfiol_operations.check_revoke_delete_entity_status,
                          self.user, Mock(), 'revoke failed')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
