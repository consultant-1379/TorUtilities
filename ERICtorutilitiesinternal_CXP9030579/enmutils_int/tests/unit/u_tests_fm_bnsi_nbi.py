#!/usr/bin/env python

import unittest2
from mock import patch, Mock
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.fm_bnsi_nbi import FmBnsiNbi, HTTPError


class FmBnsiNbiUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.fm_bnsi_nbi = FmBnsiNbi()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.fm_bnsi_nbi.deployment_info_helper_methods')
    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.fm_bnsi_nbi.cache')
    def test_create_bnsiman_user_and_enable_bnsi_nbi__enables_bnsi_if_user_available_if_not_cloud_native(self, mock_cache,
                                                                                                         mock_update_pib,
                                                                                                         mock_check_and_create_bnsiman,
                                                                                                         mock_log,
                                                                                                         mock_enm_deployment, _):
        mock_cache.is_enm_on_cloud_native.return_value = False
        mock_enm_deployment.get_values_from_global_properties.return_value = [unit_test_utils.generate_configurable_ip()]
        mock_check_and_create_bnsiman.return_value = True
        mock_update_pib.return_value = True
        self.fm_bnsi_nbi.create_bnsiman_user_and_enable_bnsi_nbi()
        self.assertTrue(self.fm_bnsi_nbi.bnsi_enabled)
        mock_update_pib.assert_called_with('bnsiserv', self.fm_bnsi_nbi.pib_parameter, 'true')
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch('enmutils_int.lib.fm_bnsi_nbi.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.deployment_info_helper_methods')
    @patch('enmutils_int.lib.fm_bnsi_nbi.cache')
    def test_create_bnsiman_user_and_enable_bnsi_nbi__enables_bnsi_if_user_available_if_cloud_native(self, mock_cache,
                                                                                                     mock_deployment,
                                                                                                     mock_check_and_create_bnsiman,
                                                                                                     mock_log,
                                                                                                     mock_update_pib, _):
        mock_cache.is_enm_on_cloud_native.return_value = True
        mock_deployment.get_cloud_native_service_vip.return_value = [unit_test_utils.generate_configurable_ip()]
        mock_check_and_create_bnsiman.return_value = True
        mock_update_pib.return_value = True
        self.fm_bnsi_nbi.create_bnsiman_user_and_enable_bnsi_nbi()
        self.assertTrue(self.fm_bnsi_nbi.bnsi_enabled)
        mock_update_pib.assert_called_with('nbi-bnsi-fm', self.fm_bnsi_nbi.pib_parameter, 'true')
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch('enmutils_int.lib.fm_bnsi_nbi.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.deployment_info_helper_methods')
    @patch('enmutils_int.lib.fm_bnsi_nbi.cache')
    def test_create_bnsiman_user_and_enable_bnsi_nbi__fails_to_enable_bnsi_if_user_available(self, mock_cache,
                                                                                             mock_deployment,
                                                                                             mock_check_and_create_bnsiman,
                                                                                             mock_log, mock_update_pib, _):
        mock_cache.is_enm_on_cloud_native.return_value = False
        mock_deployment.get_cloud_native_service_vip.return_value = [unit_test_utils.generate_configurable_ip()]
        mock_check_and_create_bnsiman.return_value = True
        mock_update_pib.return_value = False
        self.fm_bnsi_nbi.create_bnsiman_user_and_enable_bnsi_nbi()
        self.assertFalse(self.fm_bnsi_nbi.bnsi_enabled)
        self.assertTrue(mock_log.logger.debug.called)

    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch('enmutils_int.lib.fm_bnsi_nbi.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.deployment_info_helper_methods')
    @patch('enmutils_int.lib.fm_bnsi_nbi.cache')
    def test_create_bnsiman_user_and_enable_bnsi_nbi__not_enable_bnsi_if_user_not_available(self, mock_cache,
                                                                                            mock_deployment,
                                                                                            mock_check_and_create_bnsiman,
                                                                                            mock_log, mock_update_pib, _):
        mock_cache.is_enm_on_cloud_native.return_value = False
        mock_deployment.get_cloud_native_service_vip.return_value = [unit_test_utils.generate_configurable_ip()]
        mock_check_and_create_bnsiman.return_value = False
        mock_update_pib.return_value = True
        self.fm_bnsi_nbi.create_bnsiman_user_and_enable_bnsi_nbi()
        self.assertFalse(self.fm_bnsi_nbi.bnsi_enabled)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.fm_bnsi_nbi.get_workload_admin_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.user_exists')
    def test_check_for_bnsiman_user_returns__if_user_already_exists_in_enm(self, mock_user_exists,
                                                                           mock_create_user, mock_log, *_):
        mock_user_exists.return_value = True
        self.fm_bnsi_nbi.check_and_create_bnsiman_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)
        self.assertEqual(mock_user_exists.call_count, 1)

    @patch('enmutils_int.lib.fm_bnsi_nbi.get_workload_admin_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.user_exists')
    def test_check_for_bnsiman_user_creates_user__if_not_already_existing_in_enm(self, mock_user_exists,
                                                                                 mock_create_user, mock_log, *_):
        response = Mock(status_code=404)
        response.reason = "User Not Found"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.fm_bnsi_nbi.check_and_create_bnsiman_user()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.fm_bnsi_nbi.get_workload_admin_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.create_bnsiman_user')
    @patch('enmutils_int.lib.fm_bnsi_nbi.user_exists')
    def test_check_for_bnsiman_user__logs_exception_while_checking_if_user_exists(self, mock_user_exists,
                                                                                  mock_create_user, mock_log, *_):
        response = Mock(status_code=504)
        response.reason = "Gateway Time-out"
        mock_user_exists.side_effect = HTTPError(response=response)
        self.fm_bnsi_nbi.check_and_create_bnsiman_user()
        self.assertFalse(mock_create_user.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.fm_bnsi_nbi.time.sleep')
    @patch('enmutils_int.lib.fm_bnsi_nbi.Target')
    @patch('enmutils_int.lib.fm_bnsi_nbi.EnmRole')
    @patch('enmutils_int.lib.fm_bnsi_nbi.CustomUser')
    def test_create_bnsiman_user__creates_user_successfully(self, mock_custom_user, *_):
        self.fm_bnsi_nbi.create_bnsiman_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)

    @patch('enmutils_int.lib.fm_bnsi_nbi.time.sleep')
    @patch('enmutils_int.lib.fm_bnsi_nbi.Target')
    @patch('enmutils_int.lib.fm_bnsi_nbi.EnmRole')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.CustomUser')
    def test_create_bnsiman_user__retires_if_user_creation_fails(self, mock_custom_user, mock_log, *_):
        mock_custom_user.return_value.create.side_effect = [Exception, Exception, Exception, Mock()]
        self.fm_bnsi_nbi.create_bnsiman_user()
        self.assertEqual(mock_custom_user.return_value.create.call_count, 3)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 6)

    @patch('enmutils_int.lib.fm_bnsi_nbi.time.sleep')
    @patch('enmutils_int.lib.fm_bnsi_nbi.Target')
    @patch('enmutils_int.lib.fm_bnsi_nbi.EnmRole')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.CustomUser')
    def test_create_bnsiman_user__raises_exception_if_session_is_not_established(self, mock_custom_user, mock_log, *_):
        mock_custom_user.return_value.is_session_established.return_value = False
        self.assertRaises(EnmApplicationError, self.fm_bnsi_nbi.create_bnsiman_user)
        self.assertEqual(mock_custom_user.return_value.create.call_count, 1)
        self.assertEqual(mock_custom_user.return_value.is_session_established.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.fm_bnsi_nbi.shell')
    @patch('enmutils_int.lib.fm_bnsi_nbi.process')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test_check_and_remove_if_bnsi_sendalarms_is_already_running__is_successful_if_pid_exists(self, mock_log,
                                                                                                 mock_process,
                                                                                                 mock_shell):
        response = Mock()
        response.ok = True
        response.stdout = "1324"
        mock_shell.run_local_cmd.return_value = response
        self.fm_bnsi_nbi.check_and_remove_if_bnsi_sendalarms_is_already_running()
        self.assertTrue(mock_process.kill_process_id.called)
        self.assertTrue(mock_shell.run_local_cmd.called)
        self.assertEqual(mock_log.logger.debug.call_count, 3)

    @patch('enmutils_int.lib.fm_bnsi_nbi.shell')
    @patch('enmutils_int.lib.fm_bnsi_nbi.process')
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test_check_and_remove_if_bnsi_sendalarms_is_already_running__is_successful_if_pid_does_not_exist(self, mock_log,
                                                                                                         mock_process,
                                                                                                         mock_shell):
        response = Mock()
        response.ok = False
        response.stdout = "error"
        mock_shell.run_local_cmd.return_value = response
        self.fm_bnsi_nbi.check_and_remove_if_bnsi_sendalarms_is_already_running()
        self.assertFalse(mock_process.kill_process_id.called)
        self.assertTrue(mock_shell.run_local_cmd.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    @patch('enmutils_int.lib.fm_bnsi_nbi.shell')
    @patch('enmutils_int.lib.fm_bnsi_nbi.process')
    def test_check_and_remove_if_bnsi_sendalarms_is_already_running__raises_environ_error(self, mock_process,
                                                                                          mock_shell, *_):
        mock_shell.run_local_cmd.side_effect = Exception
        self.assertRaises(EnvironError, self.fm_bnsi_nbi.check_and_remove_if_bnsi_sendalarms_is_already_running)
        self.assertFalse(mock_process.kill_process_id.called)
        self.assertTrue(mock_shell.run_local_cmd.called)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_remove_if_bnsi_sendalarms_is_already_running")
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test_check_if_bnsi_session_is_available_and_close_it__is_successful(self, mock_log, mock_check_and_remove_bnsi,
                                                                            *_):
        self.fm_bnsi_nbi.check_if_bnsi_session_is_available_and_close_it(Mock())
        self.assertTrue(mock_log.logger.debug.call_count, 2)
        self.assertTrue(mock_check_and_remove_bnsi.called)

    @patch("enmutils_int.lib.fm_bnsi_nbi.time.sleep")
    @patch("enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_remove_if_bnsi_sendalarms_is_already_running")
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test_check_if_bnsi_session_is_available_and_close_it__is_successful_if_terminal_does_not_exist(self, mock_log,
                                                                                                       mock_check_and_remove_bnsi,
                                                                                                       *_):
        self.fm_bnsi_nbi.check_if_bnsi_session_is_available_and_close_it()
        self.assertTrue(mock_log.logger.debug.call_count, 1)
        self.assertTrue(mock_check_and_remove_bnsi.called)

    @patch("enmutils_int.lib.fm_bnsi_nbi.time.sleep")
    @patch("enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_remove_if_bnsi_sendalarms_is_already_running")
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test_check_if_bnsi_session_is_available_and_close_it__logs_exception(self, mock_log, mock_check_and_remove_bnsi,
                                                                             *_):
        mock_check_and_remove_bnsi.side_effect = Exception
        self.fm_bnsi_nbi.check_if_bnsi_session_is_available_and_close_it()
        self.assertTrue(mock_log.logger.debug.call_count, 2)
        self.assertTrue(mock_check_and_remove_bnsi.called)

    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch("enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_remove_if_bnsi_sendalarms_is_already_running")
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test__teardown__if_cmd_successful(self, mock_log, mock_remove_sub_if_running, mock_enm_deployment):
        mock_enm_deployment.update_pib_parameter_on_enm.return_value = True
        self.fm_bnsi_nbi._teardown()
        self.assertTrue(mock_remove_sub_if_running.called)
        self.assertTrue(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.fm_bnsi_nbi.enm_deployment')
    @patch("enmutils_int.lib.fm_bnsi_nbi.FmBnsiNbi.check_and_remove_if_bnsi_sendalarms_is_already_running")
    @patch('enmutils_int.lib.fm_bnsi_nbi.log')
    def test__teardown__if_cmd_unsuccessful(self, mock_log, mock_remove_sub_if_running, mock_enm_deployment):
        mock_enm_deployment.update_pib_parameter_on_enm.return_value = False
        self.fm_bnsi_nbi._teardown()
        self.assertTrue(mock_remove_sub_if_running.called)
        self.assertTrue(mock_log.logger.debug.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
