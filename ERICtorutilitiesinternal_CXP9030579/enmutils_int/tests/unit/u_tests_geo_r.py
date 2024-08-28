#!/usr/bin/env python

import unittest2
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils
from requests.exceptions import HTTPError
from enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow import GeoRFlow
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, ShellCommandReturnedNonZero


class GeoRUnitTests(ParameterizedTestCase):

    def setUp(self):

        unit_test_utils.setup()
        with patch('enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_workload_vm_credentials'):
            self.profile = GeoRFlow()
        self.profile.EXPORT_SIZE = "5"
        self.profile.MAX_FM_HISTORY_SIZE = "1"
        self.profile.system_user = Mock()
        self.profile.user_name = ""
        self.profile.system_user.username = ""
        self.profile.system_user.password = ""
        self.profile.USER_ROLES = [""]

    def tearDown(self):

        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.get_vm_name")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.setup_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.config.is_a_cloud_deployment")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_geo_user", side_effect=HTTPError)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup__repeat_create_user(self, mock_handler, *_):
        self.profile.system_user = None
        self.profile.setup()
        self.assertEqual(mock_handler.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.get_vm_name")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.residue_cleanup")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.setup_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_geo_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_geo_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_certs_encryption")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_ldap_export")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_configure_cfg_file")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.copy_cfg_file")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.geo_rep_export")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.nfs_and_fmx_export", side_effect=EnmApplicationError)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup__repeat_setup_on_ENMApplicationError(self, mock_handler, *_):
        self.profile.setup()
        self.assertEqual(mock_handler.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.get_vm_name")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.residue_cleanup")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.setup_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_geo_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_certs_encryption")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_ldap_export")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_configure_cfg_file")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.copy_cfg_file")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.geo_rep_export")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.nfs_and_fmx_export")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_geo_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup__successful(self, mock_handler, mock_create_geo_user, *_):
        def set_system_user():
            self.profile.system_user = Mock()
        self.profile.system_user = None
        mock_create_geo_user.side_effect = set_system_user
        self.profile.setup()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_opendj_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips",
           return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__errors_on_unreachable_vms_cloud_native(self, mock_handler, mock_get_ip, *_):
        self.profile.is_cloud = False
        mock_response = [False]
        mock_get_ip.return_value = mock_response
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_opendj_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips", return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__errors_on_unreachable_vms_cloud(self, mock_handler, mock_get_ip, *_):
        self.profile.is_cloud = True
        mock_response = [False]
        mock_get_ip.return_value = mock_response
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_db_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips", return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__errors_on_unreachable_vms_physical(self, mock_handler, *_):
        self.profile.is_cloud = False
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_opendj_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips", return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__success_cloud(self, mock_handler, *_):
        self.profile.is_cloud = True
        self.profile.is_cloud_native = False
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_opendj_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips",
           return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__success_cloud_native(self, mock_handler, *_):
        self.profile.is_cloud_native = True
        self.profile.is_cloud = False
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_db_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_key_location")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips", return_value=[1, 2, 3])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_db_vms")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_setup_vms__success_physical(self, mock_handler, *_):
        self.profile.is_cloud = False
        self.profile.list_of_db_vms = [1, 2, 3]
        self.profile.setup_vms()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.Command")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.run_local_cmd")
    def test_check_pod_is_running__is_successful(self, mock_run_cmd_cn, mock_debug_log, *_):
        mock_run_cmd_cn.return_value = Mock(ok=True)
        self.profile.check_pod_is_running("general_scripting-0")
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.Command")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.run_local_cmd")
    def test_check_pod_is_running__raises_environ_error(self, mock_run_cmd_cn, mock_debug_log):
        mock_run_cmd_cn.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.profile.check_pod_is_running, "item-1")
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_key_location__errors_on_no_key_cloud_native(self, mock_handler, *_):
        self.profile.is_cloud_native = True
        self.profile.set_key_location()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_key_location__errors_on_no_key(self, mock_handler, *_):
        self.profile.is_cloud = True
        self.profile.set_key_location()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_key_location__success_cloud(self, mock_handler, *_):
        self.profile.is_cloud = True
        self.profile.set_key_location()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_key_location__success_physical(self, mock_handler, *_):
        self.profile.is_cloud = False
        self.profile.is_physical = True
        self.profile.set_key_location()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["dataSets"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn", return_value=Mock())
    def test_residue_cleanup__raises_error_on_residue_remaining(self, *_):
        with self.assertRaises(EnvironError):
            self.profile.residue_cleanup()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_residue_cleanup__is_successful_on_cloud_native(self, mock_logger, *_):
        self.profile.is_cloud_native = True
        self.profile.list_of_scp_vms = ["item_1"]
        self.profile.residue_cleanup()
        mock_logger.assert_called_with("Finished cleaning up residue")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_residue_cleanup__is_successful_on_cloud(self, mock_logger, *_):
        self.profile.is_cloud = True
        self.profile.residue_cleanup()
        mock_logger.assert_called_with("Finished cleaning up residue")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_residue_cleanup__is_successful_on_physical(self, mock_logger, *_):
        self.profile.is_cloud = False
        self.profile.residue_cleanup()
        mock_logger.assert_called_with("Finished cleaning up residue")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_geo_r_role_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.geo_r_role_capabilities")
    def test_create_geo_user__success(self, mock_capabilities, mock_create_role_on_enm, mock_create_profile_users,
                                      mock_debug, *_):
        mock_create_profile_users.return_value = [Mock(username='Test'), Mock(password='Testpassword')]
        self.profile.create_geo_user()
        self.assertEqual(1, mock_capabilities.call_count)
        self.assertEqual(1, mock_create_role_on_enm.call_count)
        self.assertEqual(1, mock_create_profile_users.call_count)
        mock_debug.assert_called_with('Username = Test')

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.create_geo_r_role_on_enm")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.geo_r_role_capabilities")
    def test_create_geo_user__success_cloud_native(self, mock_capabilities, mock_create_role_on_enm,
                                                   mock_create_profile_users, mock_debug, *_):
        mock_create_profile_users.return_value = [Mock(username='Test')]
        self.profile.is_cloud_native = True
        self.profile.create_geo_user()
        self.assertEqual(1, mock_capabilities.call_count)
        self.assertEqual(1, mock_create_role_on_enm.call_count)
        self.assertEqual(1, mock_create_profile_users.call_count)
        mock_debug.assert_called_with('Username = Test')

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.RoleCapability.get_role_capabilities_for_resource")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_geo_r_role_capabilities__success(self, mock_debug, mock_get_role_capabilities_for_resource):
        self.profile.geo_r_role_capabilities()
        calls = [call('credentials_plain_text'), call('snmpv3_plain_text')]
        mock_get_role_capabilities_for_resource.assert_has_calls(calls, any_order=True)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.EnmComRole")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.EnmRole.check_if_role_exists")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.CustomRole")
    def test_create_geo_r_role_on_enm__create_role(self, mock_custom_role, mock_debug, mock_check_if_role_exists, *_):
        mock_check_if_role_exists.return_value = {'name': 'test'}
        self.profile.create_geo_r_role_on_enm(Mock())
        mock_debug.assert_any_call('Geo role not found, creating new geo role')
        mock_custom_role().create.assert_called_once_with(role_details={'name': 'test'})

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.EnmRole.check_if_role_exists")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_create_geo_r_role_on_enm__logs_when_role_exists_already(self, mock_debug, mock_check_if_role_exists, *_):
        mock_check_if_role_exists.return_value = None
        self.profile.create_geo_r_role_on_enm(Mock())
        mock_debug.assert_any_call("Geo role found")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_haproxy_host")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_geo_user__is_successful_cloud_native(self, mock_logger, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.is_cloud_native = True
        self.profile.configure_geo_user()
        mock_logger.assert_called_with("Finished configuring the geo-user")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_haproxy_host")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    def test_configure_geo_user_cloud_native__is_successful_cloud_native(self, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.configure_geo_user_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_haproxy_host")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_user__is_successful(self, mock_logger, *_):
        self.profile.configure_geo_user()
        mock_logger.assert_called_with("Finished configuring the geo-user")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exists_on_cloud_native_pod", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value="")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    def test_configure_certs_encryption_cloud_native__copy_failed(self, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.configure_certs_encryption_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir", return_value="")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    def test_configure_certs_encryption__copy_failed(self, *_):
        with self.assertRaises(EnvironError):
            self.profile.configure_certs_encryption()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exists_on_cloud_native_pod", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_certs_encryption_cloud_native__create_dir_failed(self, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.configure_certs_encryption_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_remote_dir_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_certs_encryption__create_dir_failed(self, *_):
        with self.assertRaises(EnvironError):
            self.profile.configure_certs_encryption()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_certs_encryption_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["ENM_GRS.p12", "geo_rep_sec_cert.pem"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_certs_encryption__is_successful_when_cloud_native_is_true(self, mock_logger, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.is_cloud_native = True
        self.profile.configure_certs_encryption()
        self.assertEqual(mock_logger.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_file_exists_on_cloud_native_pod", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["ENM_GRS.p12", "geo_rep_sec_cert.pem"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_certs_encryption_cloud_native__is_successful(self, mock_logger, *_):
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.is_cloud_native = True
        self.profile.configure_certs_encryption_cloud_native()
        self.assertEqual(mock_logger.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["ENM_GRS.p12", "geo_rep_sec_cert.pem"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_certs_encryption__is_successful_when_cloud_is_true(self, mock_logger, *_):
        self.profile.is_cloud = True
        self.profile.configure_certs_encryption()
        self.assertEqual(mock_logger.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_internal_file_path_for_import")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["ENM_GRS.p12", "geo_rep_sec_cert.pem"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_configure_certs_encryption__is_successful_when_cloud_is_false(self, mock_logger, *_):
        self.profile.is_cloud = False
        self.profile.configure_certs_encryption()
        self.assertEqual(mock_logger.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value="mock")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file_cloud_native__errors_on_copy_fail(self, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir", return_value="mock")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file__errors_on_copy_fail(self, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file_cloud_native__errors_connection_fail(self, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 1
        mock_spawn.return_value = child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file__errors_connection_fail(self, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 1
        mock_spawn.return_value = child
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["geoReplication.cfg"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file_cloud_native__failed_to_delete_local(self, mock_spawn, mock_run, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        response = Mock()
        response.rc = 1
        mock_run.return_value = response
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["geoReplication.cfg"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_copy_cfg_file__failed_to_delete_local(self, mock_spawn, mock_run, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        response = Mock()
        response.rc = 1
        mock_run.return_value = response
        with self.assertRaises(EnvironError):
            self.profile.copy_cfg_file()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.copy_cfg_file_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["geoReplication.cfg"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_copy_cfg_file__success_in_cloud_native(self, mock_logger, *_):
        self.profile.is_cloud_native = True
        self.profile.copy_cfg_file()
        mock_logger.assert_called_with("Finished copying cfg file")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["geoReplication.cfg"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_cloud_native_pod")
    def test_copy_cfg_file_cloud_native__success(self, mock_run, mock_logger, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        self.profile.list_of_scp_vms = ["item_1"]
        self.profile.is_cloud_native = True
        self.profile.copy_cfg_file_cloud_native()
        self.assertEqual(mock_logger.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["geoReplication.cfg"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_local_cmd")
    def test_copy_cfg_file__success(self, mock_run, mock_logger, mock_spawn, *_):
        child = Mock()
        child.expect.return_value = 0
        mock_spawn.return_value = child
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        self.profile.copy_cfg_file()
        mock_logger.assert_called_with("Finished copying cfg file")

    @patch("configparser.ConfigParser")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.get_vm_name")
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_create_configure_cfg_file_physical(self, mock_logger, *_):
        self.profile.is_cloud = False
        self.profile.create_configure_cfg_file()
        mock_logger.assert_called_with("Local cfg file created")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.configparser.ConfigParser")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.get_vm_name")
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_create_configure_cfg_file_cloud(self, mock_logger, *_):
        self.profile.is_cloud = True
        self.profile.create_configure_cfg_file()
        mock_logger.assert_called_with("Local cfg file created")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_ldap_export_cloud_native__raise_error_on_login_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.list_of_db_vms = ["item-2"]
        with self.assertRaises(EnvironError):
            self.profile.configure_ldap_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_ldap_export_cloud_native__setfacl_and_ldap_successful(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect = Mock()
        mock_child.expect.side_effect = [1, 0, 0, 2, 0]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.list_of_db_vms = ["item-2"]
        self.profile.configure_ldap_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_ldap_export_cloud_native__rasie_error_on_setfacl_faliure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect = Mock()
        mock_child.expect.side_effect = [1, 0, 0, 0]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.list_of_db_vms = ["item-2"]
        with self.assertRaises(EnmApplicationError):
            self.profile.configure_ldap_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_cloud_db__cloud_success(self, mock_spawn, mock_logger, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.login_to_cloud_db()
        mock_logger.assert_called_with("Connecting to opendj")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_cloud_db__cloud_raises_errors_on_login_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnvironError):
            self.profile.login_to_cloud_db()

        mock_child.expect.side_effect = [0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnvironError):
            self.profile.login_to_cloud_db()

        mock_child.expect.side_effect = [0, 0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnvironError):
            self.profile.login_to_cloud_db()

        mock_child.expect.side_effect = [0, 0, 0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnmApplicationError):
            self.profile.login_to_cloud_db()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_configure_ldap_export_cloud_native__raises_errors_on_ldap_script_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 0, 1, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.list_of_db_vms = ["item-2"]
        with self.assertRaises(EnmApplicationError):
            self.profile.configure_ldap_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_ldap_export__physical_raises_errors_on_login_failure(self, mock_spawn, *_):
        self.profile.is_cloud = False
        mock_child = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnvironError):
            self.profile.configure_ldap_export()

        mock_child.expect.side_effect = [0, 0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnmApplicationError):
            self.profile.configure_ldap_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.configure_ldap_export_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_ldap_export__success_in_cloud_native(self, mock_spawn, mock_logger, *_):
        self.profile.is_cloud_native = True
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.configure_ldap_export()
        mock_logger.assert_called_with("Finished configuring ldap export")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_ldap_export__cloud_success(self, mock_spawn, mock_logger, *_):
        self.profile.is_cloud = True
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.configure_ldap_export()
        mock_logger.assert_called_with("Finished configuring ldap export")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_ldap_export__success(self, mock_spawn, mock_logger, *_):
        self.profile.is_cloud = False
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.configure_ldap_export()
        mock_logger.assert_called_with("Finished configuring ldap export")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_rep_export_cloud_native__raises_errors_on_first_login_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 0, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.geo_rep_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_rep_export_cloud_native__raises_errors_on_second_login_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [1, 1, 1, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnvironError):
            self.profile.geo_rep_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_reo_export__raises_exception_on_login_error(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnvironError):
            self.profile.geo_rep_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_rep_export__raises_exception_on_script_failure(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnmApplicationError):
            self.profile.geo_rep_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.geo_rep_export_cloud_native")
    def test_geo_reo_export__success_cloud_native(self, *_):
        self.profile.is_cloud_native = True
        self.profile.geo_rep_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_rep_export_cloud_native__success(self, mock_spawn, mock_logger, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.geo_rep_export_cloud_native()
        self.assertEqual(mock_logger.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_rep_export_cloud_native__rasie_error_on_script_failure(self, mock_spawn, mock_logger, *_):
        mock_child = Mock()
        mock_child.expect = Mock()
        mock_child.expect.side_effect = [0, 1, 1, 0, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnmApplicationError):
            self.profile.geo_rep_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_geo_reo_export__success(self, mock_spawn, mock_logger, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.geo_rep_export()
        self.assertEqual(mock_logger.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_export_cloud_native__nfs_fail(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnmApplicationError):
            self.profile.nfs_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_export_cloud_native__fmx_fail(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [1, 0, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        with self.assertRaises(EnmApplicationError):
            self.profile.nfs_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_and_fmx_export__nfs_fail(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnmApplicationError):
            self.profile.nfs_and_fmx_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_and_fmx_export__fmx_fail(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 1]
        mock_spawn.return_value = mock_child
        with self.assertRaises(EnmApplicationError):
            self.profile.nfs_and_fmx_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.nfs_export_cloud_native")
    def test_nfs_and_fmx_export__success_cloud_native(self, *_):
        self.profile.is_cloud_native = True
        self.profile.nfs_and_fmx_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_export_cloud_native__success(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.nfs_export_cloud_native()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.command_handler")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_nfs_and_fmx_export__success(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.nfs_and_fmx_export()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_command_handler__fail(self, *_):
        child = Mock()
        child.expect.return_value = 1
        with self.assertRaises(EnmApplicationError):
            self.profile.command_handler("cmd", child)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_command_handler__success(self, mock_logger, *_):
        child = Mock()
        child.expect.return_value = 6
        self.profile.command_handler("cmd", child)
        mock_logger.assert_called_with("Successful executing command: cmd, \nRc: 6")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_pod_hostnames_in_cloud_native")
    def test_set_db_vms__is_successful_for_cloud_native(self, _):
        self.profile.is_cloud_native = True
        self.profile.is_cloud = False
        self.profile.set_db_vms()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_values_from_global_properties")
    def test_set_db_vms__is_successful_for_cloud(self, _):
        self.profile.is_cloud = True
        self.profile.is_cloud_native = False
        self.profile.set_db_vms()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_db_vms_host_names",
           return_value=[unit_test_utils.generate_configurable_ip()] * 4)
    def test_set_db_vms__is_successful_for_physical(self, _):
        self.profile.is_cloud = False
        self.profile.is_cloud_native = False
        self.profile.set_db_vms()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_vm")
    def test_get_vm_name__raise_error(self, mock_run, *_):
        mock_response = Mock()
        mock_response.rc = 1
        mock_response.stdout = 123
        mock_run.return_value = mock_response
        self.profile.is_cloud_native = False
        with self.assertRaises(ShellCommandReturnedNonZero):
            self.profile.get_vm_name(unit_test_utils.generate_configurable_ip())

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_vm")
    def test_get_vm_name(self, mock_run, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_response.stdout = 123
        mock_run.return_value = mock_response
        self.profile.is_cloud_native = False
        response = self.profile.get_vm_name("123")
        self.assertEqual(response, mock_response.stdout)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_pod_hostnames_in_cloud_native", return_value="a")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_vm")
    def test_get_vm_name_cloud_native(self, mock_run, *_):
        mock_response = Mock()
        mock_response.stdout = "a"
        mock_run.return_value = mock_response
        response = self.profile.get_vm_name("a")
        self.assertEqual(response, mock_response.stdout)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_scripting_vm__errors(self, mock_spawn, mock_handler):
        mock_child = Mock()
        mock_child.expect.return_value = 3
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ""
        self.profile.test_scripting_vm()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_scripting_vm__is_successful_with_fingerprint(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ""
        self.assertTrue(self.profile.test_scripting_vm())
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_scripting_vm__unexpected_rc_encountered(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 4
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ""
        self.assertTrue(self.profile.test_scripting_vm())
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_db_vm__is_successful(self, mock_spawn, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.assertTrue(self.profile.test_db_vm())

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_db_vm__errors(self, mock_spawn, mock_debug, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 3
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ""
        self.assertFalse(self.profile.test_db_vm())

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_db_vm__unexpected_rc_encountered_db_node_not_online(self, mock_spawn, mock_debug, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 4, 0]
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.assertFalse(self.profile.test_db_vm())
        self.assertEqual(mock_debug.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_db_vm__unexpected_rc_encountered_opendj_not_running(self, mock_spawn, mock_debug, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 0, 4]
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.assertFalse(self.profile.test_db_vm())
        self.assertEqual(mock_debug.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_db_vm__unexpected_rc_encountered_unable_to_login_db_node(self, mock_spawn, mock_debug, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 4
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.assertFalse(self.profile.test_db_vm())
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_emp")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_opendj_vm__is_successful_with_fingerprint(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.profile.test_opendj_vm()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_emp")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_opendj_vm__is_successful_without_fingerprint(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 1
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.profile.test_opendj_vm()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_emp")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_opendj_vm__errors_emp(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 3
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ""
        self.profile.test_opendj_vm()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_emp")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_opendj_vm__unexpected_rc_encountered(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.return_value = 4
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ["a", "b"]
        self.profile.test_opendj_vm()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.cache.get_emp")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_test_opendj_vm__errors_opendj(self, mock_spawn, mock_handler, *_):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 3]
        mock_spawn.return_value = mock_child
        self.profile.list_of_db_vms = ""
        self.profile.test_opendj_vm()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           side_effect=OSError)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_verify_tarball_creation__raises_error_no_dir(self, mock_handler, *_):
        self.profile.verify_tarball_creation([""])
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir",
           return_value=["tarball1"])
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_verify_tarball_creation__raises_error_no_tarball(self, mock_handler, *_):
        self.profile.verify_tarball_creation(["tarball1"])
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir")
    def test_verify_tarball_creation__is_successful(self, mock_list_files_in_scripting_vm_dir, _):
        mock_list_files_in_scripting_vm_dir.return_value = ['tarball']
        self.assertEqual(['tarball'], self.profile.verify_tarball_creation(["tarball1"]))

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_scripting_vm_ip")
    @patch('enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.list_files_in_scripting_vm_dir")
    def test_verify_tarball_creation__raises_exception_when_no_new_tarball(self, mock_list_files_in_scripting_vm_dir, mock_debug, _):

        mock_list_files_in_scripting_vm_dir.return_value = ['tarball']
        with self.assertRaises(Exception):
            self.profile.verify_tarball_creation(["tarball"])
            mock_debug.assert_called_with("No new tarball found")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.login_to_scripting_vm_as_geo_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.setup")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.set_teardown_objects")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.verify_tarball_creation")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.keep_running", side_effect=[True, False])
    def test_execute_flow__success(self, *_):
        self.profile.setup_finished = True
        self.profile.execute_flow()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.teardown_role_and_user")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.residue_cleanup")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.picklable_boundmethod")
    def test_set_teardown_objects__is_successful(self, mock_picklable_boundmethod, mock_residue, mock_role_user):
        self.assertEqual(self.profile.teardown_list, [])
        self.profile.set_teardown_objects()
        self.assertNotEqual(self.profile.teardown_list, [])
        mock_picklable_boundmethod.assert_any_call(mock_residue)
        mock_picklable_boundmethod.assert_any_call(mock_role_user)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.CustomRole.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.CustomRole.delete")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.user_cleanup")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    def test_teardown_role_and_user__success(self, mock_debug, mock_user_cleanup, mock_delete, _):
        self.profile.teardown_role_and_user()
        mock_debug.assert_called_with("Cleaning up GEO user and role")
        mock_user_cleanup.assert_called_with()
        mock_delete.assert_called_once_with()

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_pod_hostnames_in_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips",
           return_value=[unit_test_utils.generate_configurable_ip()] * 2)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm",
           return_value=True)
    def test_set_scripting_vm_ip__is_successful_cloud_native(self, mock_test_scripting_vm, *_):
        self.profile.is_cloud_native = True
        self.profile.set_scripting_vm_ip()
        self.assertEqual(mock_test_scripting_vm.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips",
           return_value=[unit_test_utils.generate_configurable_ip()] * 2)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm",
           return_value=True)
    def test_set_scripting_vm_ip__is_successful(self, mock_test_scripting_vm, _):
        self.profile.set_scripting_vm_ip()
        self.assertEqual(mock_test_scripting_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_pod_hostnames_in_cloud_native",
           return_value=[unit_test_utils.generate_configurable_ip()] * 2)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.check_pod_is_running", return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_scripting_vm_ip__raises_exception_when_pod_running_is_false_cloud_native(
            self, mock_add_error_as_exception, *_):
        self.profile.is_cloud_native = True
        self.profile.set_scripting_vm_ip()
        self.assertEqual(mock_add_error_as_exception.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.get_list_of_scripting_service_ips",
           return_value=[unit_test_utils.generate_configurable_ip()] * 2)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_scripting_vm",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_scripting_vm_ip__raises_exception_when_test_scripting_vm_is_false(self, mock_add_error_as_exception,
                                                                                   *_):
        self.profile.set_scripting_vm_ip()
        self.assertEqual(mock_add_error_as_exception.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_db_vm",
           return_value=True)
    def test_set_db_vm_ip__is_successful_in_physical(self, mock_test_db_vm):
        self.profile.list_of_db_vms = [unit_test_utils.generate_configurable_ip()] * 2
        self.profile.is_cloud = False
        self.profile.set_db_vm_ip()
        self.assertEqual(mock_test_db_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.check_pod_is_running",
           return_value=True)
    def test_set_db_vm_ip__is_successful_in_cloud_native(self, mock_test_opendj_vm):
        self.profile.list_of_db_vms = [unit_test_utils.generate_configurable_ip()] * 2
        self.profile.is_cloud_native = True
        self.profile.set_db_vm_ip()
        self.assertEqual(mock_test_opendj_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_opendj_vm",
           return_value=True)
    def test_set_db_vm_ip__is_successful_in_cloud(self, mock_test_opendj_vm):
        self.profile.list_of_db_vms = [unit_test_utils.generate_configurable_ip()] * 2
        self.profile.is_cloud = True
        self.profile.set_db_vm_ip()
        self.assertEqual(mock_test_opendj_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.test_db_vm",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.GeoRFlow.add_error_as_exception")
    def test_set_db_vm_ip__raises_exception_when_test_db_vm_is_false(self, mock_add_error_as_exception, *_):
        self.profile.list_of_db_vms = [unit_test_utils.generate_configurable_ip()] * 2
        self.profile.is_cloud = False
        self.profile.set_db_vm_ip()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_cloud_native_pod")
    def test_list_files_in_scripting_vm_dir__raise_error_failed_get_files_cloud_native(self, mock_run, *_):
        mock_response = Mock()
        mock_response.rc = 1
        mock_response.stdout = 123
        mock_run.return_value = mock_response
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.is_cloud_native = True
        with self.assertRaises(EnvironError):
            self.profile.list_files_in_scripting_vm_dir("123")

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.get_files_in_remote_directory")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.shell.run_cmd_on_cloud_native_pod")
    def test_list_files_in_scripting_vm_dir__is_success_cloud_native(self, mock_run, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_response.stdout = 123
        mock_run.return_value = mock_response
        self.profile.list_of_scp_vms = ["item-1"]
        self.profile.is_cloud_native = True
        self.profile.list_files_in_scripting_vm_dir("123")
        self.assertEqual(mock_run.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.filesystem.get_files_in_remote_directory")
    def test_list_files_in_scripting_vm_dir__is_success(self, mock_get_files_in_remote_directory):
        self.profile.list_files_in_scripting_vm_dir("test")
        self.assertEqual(mock_get_files_in_remote_directory.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_scripting_vm_as_geo_user__is_successful_cloud_native(self, mock_spawn, mock_debug):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item_1"]
        self.profile.is_cloud_native = True
        self.profile.login_to_scripting_vm_as_geo_user()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertIn("Successfully", mock_debug.call_args[0][0])

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_scripting_vm_as_geo_user__is_successful(self, mock_spawn, mock_debug):
        mock_child = Mock()
        mock_child.expect.return_value = 0
        mock_spawn.return_value = mock_child
        self.profile.login_to_scripting_vm_as_geo_user()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertIn("Successfully", mock_debug.call_args[0][0])

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_scripting_vm_as_geo_user__is_failure_when_no_password_prompt(self, mock_spawn, mock_debug):
        mock_child = Mock()
        mock_child.expect.side_effect = [1, 0]
        mock_spawn.return_value = mock_child
        self.profile.login_to_scripting_vm_as_geo_user()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertIn("Issue", mock_debug.call_args[0][0])

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_scripting_vm_as_geo_user__is_failure_when_unable_to_login_cloud_native(self, mock_spawn, mock_debug):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 1]
        mock_spawn.return_value = mock_child
        self.profile.list_of_scp_vms = ["item_1"]
        self.profile.is_cloud_native = True
        self.profile.login_to_scripting_vm_as_geo_user()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertIn("Issue", mock_debug.call_args[0][0])

    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow.pexpect.spawn")
    def test_login_to_scripting_vm_as_geo_user__is_failure_when_unable_to_login(self, mock_spawn, mock_debug):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 1]
        mock_spawn.return_value = mock_child
        self.profile.login_to_scripting_vm_as_geo_user()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertIn("Issue", mock_debug.call_args[0][0])

if __name__ == "__main__":
    unittest2.main(verbosity=2)
