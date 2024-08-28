#!/usr/bin/env python
import os
import subprocess
import sys

import unittest2
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase

import enmutils_int
import enmutils_int.bin.configure_wlvm as tool
import enmutils_int.lib.configure_wlvm_operations as operations
import enmutils_int.lib.configure_wlvm_packages as packages
from testslib import unit_test_utils

ENMUTILS_INT_PATH = os.path.dirname(enmutils_int.__file__)
TOOL_NAME = "configure_wlvm.py"

ATHTEM_DOMAINNAME = "athtem.eei.ericsson.se"

empty_command_result = ""
malformed_json = ","
empty_json = []


class ConfigureWlvmUnitTests(ParameterizedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.bad_command_result = subprocess.CalledProcessError(returncode=2, cmd=["bad"], output="some_output")
        cls.ddc_service_not_running = subprocess.CalledProcessError(returncode=2, cmd=["service ddc status"],
                                                                    output="DDC not running")

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    # Tests

    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    @patch('enmutils_int.bin.configure_wlvm.initialize_logger')
    @patch('enmutils_int.bin.configure_wlvm.sys.stderr')
    @patch('enmutils_int.bin.configure_wlvm.optparse.OptionParser.format_help')
    @patch('enmutils_int.bin.configure_wlvm.optparse.IndentedHelpFormatter.format_usage')
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME],),
            ([TOOL_NAME, "-h"],),
            ([TOOL_NAME, "test_enm"],),
            ([TOOL_NAME, "test_enm", "junk"],),
            ([TOOL_NAME, "test_enm", "--all", "junk"],),
            ([TOOL_NAME, "test_enm", "--check_packages1"],),
            ([TOOL_NAME, "test_enm", "--check_packages", "--configure_ntp", "junk"],),
        ]
    )
    def test_cli_handles_invalid_args(self, sys_argv, mock_format_option_help, mock_format_help, *_):
        sys.argv = sys_argv
        mock_format_option_help.return_value = ""
        mock_format_help.return_value = ""
        self.assertRaises(SystemExit, tool.cli)

    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    @patch('enmutils_int.bin.configure_wlvm.initialize_logger')
    @patch('enmutils_int.bin.configure_wlvm.configure_cloud')
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME, "test_enm", "--all"],),
            ([TOOL_NAME, "test_enm", "--check_packages"],),
            ([TOOL_NAME, "test_enm", "--configure_ntp"],),
            ([TOOL_NAME, "test_enm", "--set_enm_locations"],),
            ([TOOL_NAME, "test_enm", "--fetch_private_key"],),
            ([TOOL_NAME, "test_enm", "--store_private_key_on_emp"],),
            ([TOOL_NAME, "test_enm", "--install_ddc"],),
            ([TOOL_NAME, "test_enm", "--configure_ddc_on_enm"],),
            ([TOOL_NAME, "test_enm", "--setup_ddc_collection_of_workload_files"],),
            ([TOOL_NAME, "test_enm", "--get_wlvm_hostname_from_dit"],),
        ]
    )
    def test_cli_handles_valid_args(self, sys_argv, mock_configure_cloud, *_):
        sys.argv = sys_argv
        mock_configure_cloud.side_effect = [True, False]
        self.assertEqual(0, tool.cli())
        self.assertEqual(1, tool.cli())

    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    @patch('argparse.ArgumentParser._print_message')
    @patch('enmutils_int.bin.configure_wlvm.initialize_logger')
    @patch('enmutils_int.bin.configure_wlvm.log.logger.error')
    @patch('enmutils_int.bin.configure_wlvm.configure_cloud')
    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            ([TOOL_NAME, "test_enm", "--fetch_private_key"],),
        ]
    )
    def test_cli__deals_with_different_return_values_from_configure_cloud(self, sys_argv, mock_configure_cloud,
                                                                          mock_error, *_):
        sys.argv = sys_argv
        mock_configure_cloud.side_effect = [Exception(), False, True]
        self.assertEqual(1, tool.cli())
        self.assertTrue(mock_error.called)
        self.assertEqual(1, tool.cli())
        self.assertEqual(0, tool.cli())

    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    @patch('enmutils_int.bin.configure_wlvm.initialize_logger')
    @patch('enmutils_int.bin.configure_wlvm.parse_arguments')
    def test_cli_returns_error_if_arguments_parsing_returns_nothing(self, mock_parse_arguments, *_):
        mock_parse_arguments.return_value = ""
        self.assertRaises(SystemExit, tool.cli)

    @patch('enmutils_int.bin.configure_wlvm.logging.Formatter')
    @patch('enmutils_int.bin.configure_wlvm.log.logging')
    @patch('enmutils_int.bin.configure_wlvm.logging.StreamHandler')
    @patch('enmutils_int.bin.configure_wlvm.logging.FileHandler')
    @patch('enmutils_int.bin.configure_wlvm.logging.getLogger')
    @patch('enmutils_int.bin.configure_wlvm.check_log_dir')
    def test_initialize_logger(self, mock_check_log_dir, mock_logger, mock_filehandler, mock_streamhandler, *_):
        tool.TOOL_NAME = "test_tool"
        tool.initialize_logger()
        self.assertTrue(mock_check_log_dir.called)
        self.assertTrue(call(mock_streamhandler.return_value) in mock_logger.return_value.addHandler.mock_calls)
        self.assertTrue(call(mock_filehandler.return_value) in mock_logger.return_value.addHandler.mock_calls)
        mock_filehandler.assert_called_with("/var/log/enmutils/test_tool.log")

    @patch("enmutils_int.bin.configure_wlvm.os")
    def test_mock_check_log_dir__successful_if_log_dir_exists(self, mock_os):
        mock_os.path.exists.return_value = True
        tool.check_log_dir()
        self.assertTrue(mock_os.path.exists.called)
        self.assertFalse(mock_os.mkdir.called)

    @patch("enmutils_int.bin.configure_wlvm.os")
    def test_mock_check_log_dir__successful_if_log_dir_does_not_exist(self, mock_os):
        mock_os.path.exists.return_value = False
        tool.check_log_dir()
        mock_os.path.exists.assert_called_with("/var/log/enmutils")
        mock_os.mkdir.assert_called_with("/var/log/enmutils")

    @patch('enmutils_int.bin.configure_wlvm.os')
    def test_mock_check_log_dir__unsuccessful_if_cannot_create_dir(self, mock_os):
        mock_os.path.exists.return_value = False
        mock_os.mkdir.side_effect = Exception("some error")

        with self.assertRaises(SystemExit) as e:
            tool.check_log_dir()
        self.assertEqual(e.exception.message, "Problem accessing log dir (/var/log/enmutils): some error")
        mock_os.path.exists.assert_called_with("/var/log/enmutils")
        mock_os.mkdir.assert_called_with("/var/log/enmutils")

    @patch('enmutils_int.bin.configure_wlvm.sys.exit')
    def test_signal_handler(self, mock_sys_exit, *_):
        tool.signal_handler(15, _)
        self.assertTrue(mock_sys_exit.called)

    @patch('enmutils_int.bin.configure_wlvm.operations.export_deployment_name')
    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    def test_configure_cloud__calls_all_applicable_tasks_with_the_all_option_set_to_false(self, *_):
        argument_dict = {'all': False,
                         'deployment_name': 'blah',
                         'check_packages': True,
                         'configure_ntp': True,
                         'set_enm_locations': True,
                         'fetch_private_key': True,
                         'install_cluster_client': True,
                         'update_local_kubectl_version': True,
                         'store_private_key_on_emp': True,
                         'install_ddc': True,
                         'configure_ddc_on_enm': True,
                         'setup_ddc_collection_of_workload_files': True,
                         'get_wlvm_hostname_from_dit': True}

        with patch('enmutils_int.bin.configure_wlvm.get_wlvm_hostname_from_dit') as mock_get_wlvm_hostname_from_dit, \
                patch('enmutils_int.bin.configure_wlvm.setup_ddc_collection_of_workload_files') as \
                mock_setup_ddc_collection_of_workload_files, \
                patch('enmutils_int.bin.configure_wlvm.configure_ddc_on_enm') as mock_configure_ddc_on_enm, \
                patch('enmutils_int.bin.configure_wlvm.install_ddc') as mock_install_ddc, \
                patch('enmutils_int.bin.configure_wlvm.store_private_key_on_emp') as mock_store_private_key_on_emp, \
                patch('enmutils_int.bin.configure_wlvm.fetch_private_key') as mock_fetch_private_key, \
                patch('enmutils_int.bin.configure_wlvm.install_cluster_client') as mock_install_cluster_client, \
                patch('enmutils_int.bin.configure_wlvm.set_enm_locations') as mock_set_enm_locations, \
                patch('enmutils_int.bin.configure_wlvm.configure_ntp') as mock_configure_ntp, \
                patch('enmutils_int.bin.configure_wlvm.check_packages') as mock_check_packages:
            self.assertTrue(tool.configure_cloud(argument_dict))
            self.assertTrue(mock_check_packages.called)
            self.assertTrue(mock_configure_ntp.called)
            self.assertTrue(mock_set_enm_locations.called)
            self.assertTrue(mock_configure_ddc_on_enm.called)
            self.assertTrue(mock_setup_ddc_collection_of_workload_files.called)
            self.assertTrue(mock_get_wlvm_hostname_from_dit.called)
            self.assertTrue(mock_install_ddc.called)
            self.assertTrue(mock_fetch_private_key.called)
            self.assertTrue(mock_store_private_key_on_emp.called)
            self.assertTrue(mock_install_cluster_client.called)

    @patch('enmutils_int.bin.configure_wlvm.operations.export_deployment_name')
    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    def test_configure_cloud__calls_all_tasks_with_the_all_option_set_to_true(self, *_):
        argument_dict = {'all': True,
                         'deployment_name': 'blah',
                         'check_packages': False,
                         'configure_ntp': False,
                         'set_enm_locations': False,
                         'store_private_key_on_emp': False,
                         'fetch_private_key': False,
                         'install_cluster_client': False,
                         'update_local_kubectl_version': False,
                         'install_ddc': False,
                         'configure_ddc_on_enm': False,
                         'setup_ddc_collection_of_workload_files': False,
                         'get_wlvm_hostname_from_dit': False}

        with patch('enmutils_int.bin.configure_wlvm.get_wlvm_hostname_from_dit') as mock_get_wlvm_hostname_from_dit, \
                patch('enmutils_int.bin.configure_wlvm.setup_ddc_collection_of_workload_files') as \
                mock_setup_ddc_collection_of_workload_files, \
                patch('enmutils_int.bin.configure_wlvm.configure_ddc_on_enm') as mock_configure_ddc_on_enm, \
                patch('enmutils_int.bin.configure_wlvm.install_ddc') as mock_install_ddc, \
                patch('enmutils_int.bin.configure_wlvm.store_private_key_on_emp') as mock_store_private_key_on_emp, \
                patch('enmutils_int.bin.configure_wlvm.fetch_private_key') as mock_fetch_private_key, \
                patch('enmutils_int.bin.configure_wlvm.install_cluster_client') as mock_install_cluster_client, \
                patch('enmutils_int.bin.configure_wlvm.set_enm_locations') as mock_set_enm_locations, \
                patch('enmutils_int.bin.configure_wlvm.configure_ntp') as mock_configure_ntp, \
                patch('enmutils_int.bin.configure_wlvm.check_packages') as mock_check_packages:
            self.assertTrue(tool.configure_cloud(argument_dict))
            self.assertTrue(mock_set_enm_locations.called)
            self.assertTrue(mock_configure_ntp.called)
            self.assertTrue(mock_check_packages.called)
            self.assertTrue(mock_setup_ddc_collection_of_workload_files.called)
            self.assertTrue(mock_configure_ddc_on_enm.called)
            self.assertTrue(mock_get_wlvm_hostname_from_dit.called)
            self.assertTrue(mock_install_ddc.called)
            self.assertTrue(mock_fetch_private_key.called)
            self.assertTrue(mock_store_private_key_on_emp.called)
            self.assertTrue(mock_install_cluster_client.called)

    @patch('enmutils_int.bin.configure_wlvm.operations.export_deployment_name')
    @patch('enmutils_int.bin.configure_wlvm.signal.signal')
    def test_configure_cloud__calls_two_tasks_with_all_option_false(self, *_):
        argument_dict = {'all': False,
                         'deployment_name': 'blah',
                         'check_packages': True,
                         'configure_ntp': False,
                         'set_enm_locations': False,
                         'store_private_key_on_emp': False,
                         'fetch_private_key': False,
                         'install_cluster_client': False,
                         'update_local_kubectl_version': False,
                         'install_ddc': False,
                         'configure_ddc_on_enm': False,
                         'setup_ddc_collection_of_workload_files': True,
                         'get_wlvm_hostname_from_dit': False}

        with patch('enmutils_int.bin.configure_wlvm.get_wlvm_hostname_from_dit') as mock_get_wlvm_hostname_from_dit, \
                patch('enmutils_int.bin.configure_wlvm.setup_ddc_collection_of_workload_files') as \
                mock_setup_ddc_collection_of_workload_files, \
                patch('enmutils_int.bin.configure_wlvm.configure_ddc_on_enm') as mock_configure_ddc_on_enm, \
                patch('enmutils_int.bin.configure_wlvm.install_ddc') as mock_install_ddc, \
                patch('enmutils_int.bin.configure_wlvm.store_private_key_on_emp') as mock_store_private_key_on_emp, \
                patch('enmutils_int.bin.configure_wlvm.fetch_private_key') as mock_fetch_private_key, \
                patch('enmutils_int.bin.configure_wlvm.install_cluster_client') as mock_install_cluster_client, \
                patch('enmutils_int.bin.configure_wlvm.set_enm_locations') as mock_set_enm_locations, \
                patch('enmutils_int.bin.configure_wlvm.configure_ntp') as mock_configure_ntp, \
                patch('enmutils_int.bin.configure_wlvm.check_packages') as mock_check_packages:
            self.assertTrue(tool.configure_cloud(argument_dict))
            self.assertTrue(mock_check_packages.called)
            self.assertTrue(mock_setup_ddc_collection_of_workload_files.called)
            self.assertFalse(mock_set_enm_locations.called)
            self.assertFalse(mock_configure_ntp.called)
            self.assertFalse(mock_configure_ddc_on_enm.called)
            self.assertFalse(mock_get_wlvm_hostname_from_dit.called)
            self.assertFalse(mock_install_ddc.called)
            self.assertFalse(mock_fetch_private_key.called)
            self.assertFalse(mock_store_private_key_on_emp.called)
            self.assertFalse(mock_install_cluster_client.called)

            mock_check_packages.return_value = False
            self.assertFalse(tool.configure_cloud(argument_dict))

    @patch("subprocess.check_output")
    def test_check_packages(self, mock_check_output, *_):
        rpm_output_incomplete = "blah"
        rpm_output_complete = ("java-1.6.0-openjdk-revision1-revision2.el6.x86_64"
                               "rsync-3.0.6-12.el6.x86_64"
                               "wget-1.12-5.el6.x86_64"
                               "openssh-clients-5.3p1-104.el6.x86_64"
                               "python-setuptools-0.6.10-3.el6.noarch")
        mock_check_output.side_effect = [self.bad_command_result, "", rpm_output_incomplete, rpm_output_complete]

        self.assertFalse(tool.check_packages("deployment_name", "slogan"))
        self.assertFalse(tool.check_packages("deployment_name", "slogan"))
        self.assertFalse(tool.check_packages("deployment_name", "slogan"))
        self.assertTrue(tool.check_packages("deployment_name", "slogan"))

    @patch('enmutils_int.lib.configure_wlvm_operations.time.sleep')
    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch('enmutils_int.lib.configure_wlvm_operations.restart_ntp')
    @patch("subprocess.check_output")
    def test_add_ntp_configuration_returns_true(self, mock_check_output, mock_restart_ntp, mock_logger, *_):
        mock_restart_ntp.side_effect = [False, True]
        sed_output_bad_rc = self.bad_command_result
        sed_output_unexpected = "blah"
        sed_output_expected = ""
        echo_output_bad_rc = self.bad_command_result
        echo_output_expected = ""
        egrep_output_bad_rc = self.bad_command_result

        mock_check_output.side_effect = [
            sed_output_bad_rc,
            sed_output_unexpected,
            sed_output_expected, echo_output_bad_rc,
            sed_output_expected, echo_output_expected, echo_output_expected, egrep_output_bad_rc,
            sed_output_expected, echo_output_expected, echo_output_expected, "0",
            sed_output_expected, echo_output_expected, echo_output_expected, "2",
            sed_output_expected, echo_output_expected, echo_output_expected, "2"]

        self.assertFalse(operations.add_ntp_configuration(mock_logger))
        self.assertFalse(operations.add_ntp_configuration(mock_logger))
        self.assertFalse(operations.add_ntp_configuration(mock_logger))
        self.assertFalse(operations.add_ntp_configuration(mock_logger))
        self.assertFalse(operations.add_ntp_configuration(mock_logger))
        self.assertTrue(operations.add_ntp_configuration(mock_logger))
        self.assertTrue(operations.add_ntp_configuration(mock_logger))

    @patch('enmutils_int.lib.configure_wlvm_operations.time.sleep')
    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch('enmutils_int.lib.configure_wlvm_operations.enable_ntp_service_at_reboot')
    @patch("subprocess.check_output")
    def test_restart_ntp(self, mock_check_output, mock_enable_ntp_service_at_reboot, mock_logger, *_):
        mock_enable_ntp_service_at_reboot.return_value = [False, True]
        mock_check_output.side_effect = [self.bad_command_result, "blah",
                                         "Starting ntpd: blah [OK]", self.bad_command_result,
                                         "Starting ntpd: blah [OK]", "is stopped", "is stopped", "is stopped",
                                         "Starting ntpd: blah [OK]", "is stopped", "is stopped", "is running"]

        self.assertFalse(operations.restart_ntp(mock_logger))
        self.assertFalse(operations.restart_ntp(mock_logger))
        self.assertFalse(operations.restart_ntp(mock_logger))
        self.assertFalse(operations.restart_ntp(mock_logger))
        self.assertTrue(operations.restart_ntp(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.time.sleep")
    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_check_if_ntp_synchronized(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "synchronizing", self.bad_command_result,
                                         self.bad_command_result, "synchronised to NTP server"]

        self.assertFalse(operations.check_if_ntp_synchronized(mock_logger, 1))
        self.assertFalse(operations.check_if_ntp_synchronized(mock_logger, 1))
        self.assertTrue(operations.check_if_ntp_synchronized(mock_logger, 3))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch('enmutils_int.lib.configure_wlvm_operations.add_ntp_configuration')
    @patch('enmutils_int.lib.configure_wlvm_operations.check_if_ntp_synchronized')
    def test_configure_ntp(self, mock_check_synchronized, mock_add_config, *_):
        mock_check_synchronized.side_effect = [True, False, False, False, False, True]
        mock_add_config.side_effect = [False, True, True]
        self.assertTrue(tool.configure_ntp("deployment_name", "slogan"))
        self.assertFalse(tool.configure_ntp("deployment_name", "slogan"))
        self.assertTrue(tool.configure_ntp("deployment_name", "slogan"))
        self.assertTrue(tool.configure_ntp("deployment_name", "slogan"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_enable_ntp_service_at_reboot(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "blah", "", self.bad_command_result, "", "blah", "",
                                         "blah 2:on 3:on 4:off blah"]

        self.assertFalse(operations.enable_ntp_service_at_reboot(mock_logger))
        self.assertFalse(operations.enable_ntp_service_at_reboot(mock_logger))
        self.assertFalse(operations.enable_ntp_service_at_reboot(mock_logger))
        self.assertFalse(operations.enable_ntp_service_at_reboot(mock_logger))
        self.assertTrue(operations.enable_ntp_service_at_reboot(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_sed_id(self, mock_check_output, mock_logger, *_):
        curl_output_enm_missing = '[{"something_else":{"sed_id":""}}]'
        curl_output_sed_id_missing = '[{"enm":{"something_else":""}}]'
        curl_output_sed_id_not_set = '[{"enm":{"sed_id":""}}]'
        curl_output_sed_id_set = '[{"enm":{"sed_id":"99999"}}]'
        mock_check_output.side_effect = [self.bad_command_result, "", ",", "[]", curl_output_enm_missing,
                                         curl_output_sed_id_missing, curl_output_sed_id_not_set, curl_output_sed_id_set]

        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_sed_id(mock_logger, "deployment_name"))
        self.assertEqual("99999", operations.fetch_sed_id(mock_logger, "deployment_name"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.fetch_parameter_value_from_sed_on_dit")
    def test_fetch_emp_external_ip__is_successful(self, mock_fetch_parameter_value_from_sed_on_dit, mock_logger):
        sed_id = "99999"
        operations.DIT_URL = "DIT_URL"

        curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                        r"{parameters_keyword}\({sed_parameter_key}\)\)")

        operations.fetch_emp_external_ip(mock_logger, sed_id)
        mock_fetch_parameter_value_from_sed_on_dit.assert_called_with(mock_logger, curl_command, "emp_external_ip_list")

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.fetch_parameter_value_from_sed_on_dit")
    def test_fetch_httpd_fqdn__is_successful(self, mock_fetch_parameter_value_from_sed_on_dit, mock_logger):
        sed_id = "99999"
        operations.DIT_URL = "DIT_URL"

        curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                        r"{parameters_keyword}\({sed_parameter_key}\)\)")

        operations.fetch_httpd_fqdn(mock_logger, sed_id)
        mock_fetch_parameter_value_from_sed_on_dit.assert_called_with(mock_logger, curl_command, "httpd_fqdn")

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.extract_sed_value_from_output")
    @patch("subprocess.check_output")
    def test_fetch_parameter_value_from_sed_on_dit__returns_none_if_curl_is_unsuccessful(
            self, mock_check_output, mock_extract_sed_value_from_output, mock_logger):
        curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                        r"{parameters_keyword}\({sed_parameter_key}\)\)")
        last_curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                             r"parameters\(httpd_fqdn\)\)")

        mock_check_output.side_effect = [self.bad_command_result, self.bad_command_result]
        self.assertEqual("", operations.fetch_parameter_value_from_sed_on_dit(mock_logger, curl_command, "httpd_fqdn"))
        mock_check_output.assert_called_with(last_curl_command, stderr=subprocess.STDOUT, shell=True)
        self.assertFalse(mock_extract_sed_value_from_output.called)
        self.assertEqual(mock_check_output.call_count, 2)

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.extract_sed_value_from_output")
    @patch("subprocess.check_output")
    def test_fetch_parameter_value_from_sed_on_dit__is_successful(
            self, mock_check_output, mock_extract_sed_value_from_output, mock_logger):
        curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                        r"{parameters_keyword}\({sed_parameter_key}\)\)")
        last_curl_command = (r"curl -s DIT_URL/api/documents/99999?fields=content\("
                             r"parameter_defaults\(httpd_fqdn\)\)")

        mock_check_output.return_value = "command_output"
        mock_extract_sed_value_from_output.return_value = "some_ip_address"
        self.assertEqual("some_ip_address",
                         operations.fetch_parameter_value_from_sed_on_dit(mock_logger, curl_command, "httpd_fqdn"))
        mock_extract_sed_value_from_output.assert_called_with("command_output", "parameter_defaults", "httpd_fqdn")
        mock_check_output.assert_called_with(last_curl_command, stderr=subprocess.STDOUT, shell=True)
        self.assertEqual(mock_check_output.call_count, 1)

    @ParameterizedTestCase.parameterize(
        ("sys_argv",),
        [
            (empty_command_result,),
            (malformed_json,),
            (empty_json,),
            ('{"something_else":{"parameters":{"emp_external_ip_list":""}}}',),
            ('{"content":{"something_else":{"emp_external_ip_list":""}}}',),
            ('{"content":{"parameters":{"something_else":""}}}',),
            ('{"content":{"parameters":{"emp_external_ip_list":""}}}',),
            ('{"content":{"parameter_defaults":{"something_else":""}}}',),
            ('{"content":{"parameter_defaults":{"emp_external_ip_list":""}}}',),
        ]
    )
    def test_extract_sed_value_from_output__returns_empty_if_output_is_incorrect(self, sys_argv):
        self.assertEqual("", operations.extract_sed_value_from_output(sys_argv, "parameter_defaults",
                                                                      "emp_external_ip_list"))

    def test_extract_sed_value_from_output__is_successful(self):
        output = '{"content":{"parameter_defaults":{"emp_external_ip_list":"some_ip_address"}}}'
        self.assertEqual("some_ip_address", operations.extract_sed_value_from_output(output, "parameter_defaults",
                                                                                     "emp_external_ip_list"))
        output = '{"content":{"parameters":{"emp_external_ip_list":"some_ip_address"}}}'
        self.assertEqual("some_ip_address", operations.extract_sed_value_from_output(output, "parameters",
                                                                                     "emp_external_ip_list"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_update_bashrc_file_with_variable(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "False", "True", self.bad_command_result,
                                         "True", "blah", "True", "", self.bad_command_result, "True", "", "blah",
                                         "True", "", ""]

        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertFalse(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))
        self.assertTrue(operations.update_bashrc_file_with_variable(mock_logger, "EMP", "blah"))

    @patch('enmutils_int.bin.configure_wlvm.restart_services')
    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.operations.set_enm_locations_flow")
    @patch("enmutils_int.bin.configure_wlvm.set_cenm_variables")
    def test_set_enm_locations__successful_for_cenm(self, mock_set_cenm_variables, mock_set_enm_locations_flow,
                                                    mock_get_dit_deployment_info, mock_restart_services):
        tool.set_enm_locations("deployment_name", "slogan")
        mock_set_cenm_variables.assert_called_with("deployment_name", "slogan")
        self.assertFalse(mock_set_enm_locations_flow.called)
        self.assertTrue(mock_get_dit_deployment_info.called)
        self.assertTrue(mock_restart_services.called)

    @patch('enmutils_int.bin.configure_wlvm.restart_services')
    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", Mock()))
    @patch("enmutils_int.bin.configure_wlvm.operations.set_enm_locations_flow")
    @patch("enmutils_int.bin.configure_wlvm.set_cenm_variables")
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_set_enm_locations__successful_for_venm(
            self, mock_logger, mock_set_cenm_variables, mock_set_enm_locations_flow,
            mock_get_dit_deployment_info, mock_restart_services):
        tool.set_enm_locations("deployment_name", "slogan")
        mock_set_enm_locations_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        self.assertFalse(mock_set_cenm_variables.called)
        self.assertTrue(mock_get_dit_deployment_info.called)
        self.assertTrue(mock_restart_services.called)

    @patch('enmutils_int.bin.configure_wlvm.restart_services')
    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", Mock()))
    @patch("enmutils_int.bin.configure_wlvm.operations.set_enm_locations_flow")
    @patch("enmutils_int.bin.configure_wlvm.set_cenm_variables")
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_set_enm_locations__if_set_enm_locations_returs_none(
            self, mock_logger, mock_set_cenm_variables, mock_set_enm_locations_flow,
            mock_get_dit_deployment_info, mock_restart_services):
        mock_set_enm_locations_flow.return_value = None
        tool.set_enm_locations("deployment_name", "slogan")
        mock_set_enm_locations_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        self.assertFalse(mock_set_cenm_variables.called)
        self.assertTrue(mock_get_dit_deployment_info.called)
        self.assertFalse(mock_restart_services.called)

    @patch('enmutils_int.lib.configure_wlvm_operations.update_bashrc_file_with_variable')
    @patch('enmutils_int.lib.configure_wlvm_operations.fetch_httpd_fqdn')
    @patch('enmutils_int.lib.configure_wlvm_operations.fetch_emp_external_ip')
    @patch('enmutils_int.lib.configure_wlvm_operations.fetch_sed_id')
    def test_set_enm_locations_flow__successful(
            self, mock_fetch_sed_id, mock_fetch_emp_external_ip, mock_fetch_httpd_fqdn,
            mock_update_bashrc_file_with_variable, *_):
        mock_fetch_sed_id.side_effect = ["", "blah", "blah", "blah", "blah", "blah"]
        mock_fetch_emp_external_ip.side_effect = ["", "blah", "blah", "blah", "blah", "blah"]
        mock_fetch_httpd_fqdn.side_effect = ["", "blah", "blah", "blah", "blah", "blah"]
        mock_update_bashrc_file_with_variable.side_effect = [False, False, True, False, True, True]
        self.assertFalse(operations.set_enm_locations_flow(Mock(), "deployment_name", "slogan"))
        self.assertFalse(operations.set_enm_locations_flow(Mock(), "deployment", "slogan"))
        self.assertFalse(operations.set_enm_locations_flow(Mock(), "deployment", "slogan"))
        self.assertFalse(operations.set_enm_locations_flow(Mock(), "deployment", "slogan"))
        self.assertTrue(operations.set_enm_locations_flow(Mock(), "deployment", "slogan"))

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.operations.fetch_private_key_flow")
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_fetch_private_key__successful_for_venm(
            self, mock_logger, mock_fetch_private_key_flow, mock_get_dit_deployment_info):
        tool.fetch_private_key("deployment_name", "slogan")
        mock_fetch_private_key_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", Mock()))
    @patch("enmutils_int.bin.configure_wlvm.operations.fetch_private_key_flow")
    def test_fetch_private_key__does_not_do_anything_in_cenm(
            self, mock_fetch_private_key_flow, mock_get_dit_deployment_info):
        self.assertTrue(tool.fetch_private_key("deployment_name", "slogan"))
        self.assertFalse(mock_fetch_private_key_flow.called)
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.lib.configure_wlvm_operations.fetch_keypair_data_from_dit")
    @patch("enmutils_int.lib.configure_wlvm_operations.write_keypair_data_to_file")
    def test_fetch_private_key_flow__successful(
            self, mock_fetch_keypair_data_from_dit, mock_write_keypair_data_to_file, *_):
        mock_fetch_keypair_data_from_dit.side_effect = ["", "private_key", "private_key"]
        mock_write_keypair_data_to_file.side_effect = [False, True, True]
        self.assertFalse(operations.fetch_private_key_flow(Mock(), "deployment_name", "slogan"))
        self.assertFalse(operations.fetch_private_key_flow(Mock(), "deployment_name", "slogan"))
        self.assertTrue(operations.fetch_private_key_flow(Mock(), "deployment_name", "slogan"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_private_key_flow__is_successful(self, mock_check_output, mock_logger, *_):
        curl_output = '[{"enm":{"private_key":"blah-di-blah"}}]'
        echo_output = ""
        cat_output = "END RSA PRIVATE KEY"
        chmod_output = ""
        mock_check_output.side_effect = [curl_output, echo_output, cat_output, chmod_output]
        self.assertTrue(operations.fetch_private_key_flow(mock_logger, "deployment_name", "slogan"))

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.setup_cluster_connection")
    def test_install_cluster_client__successful_for_cenm(
            self, mock_setup_cluster_connection, mock_get_dit_deployment_info, _):
        tool.install_cluster_client("deployment_name", "slogan")
        mock_setup_cluster_connection.assert_called_with("deployment_name", {"key1": "value1"}, "slogan", True)
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.setup_cluster_connection")
    def test_install_cluster_client__successful_for_venm(
            self, mock_setup_cluster_connection, mock_get_dit_deployment_info):
        tool.install_cluster_client("deployment_name", "slogan")
        self.assertFalse(mock_setup_cluster_connection.called)
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.bin.configure_wlvm.commands.getstatusoutput", return_value=(0, "enm12 uiserv"))
    def test_is_cloudnative_namaspace_found__returns_true_when_found(self, _):
        self.assertTrue(tool.is_cloudnative_namespace_found())

    @patch("enmutils_int.bin.configure_wlvm.commands.getstatusoutput", return_value=(1, ""))
    def test_is_cloudnative_namaspace_found__returns_false_when_found(self, _):
        self.assertFalse(tool.is_cloudnative_namespace_found())

    @patch("enmutils_int.bin.configure_wlvm.is_cloudnative_namespace_found", return_value=True)
    @patch("enmutils_int.bin.configure_wlvm.install_kubectl_client")
    @patch("enmutils_int.bin.configure_wlvm.compare_kubectl_client_and_server_version")
    def test_update_local_kubectl_version__is_successful_for_cenm(self, mock_compare_kubectl_client_and_server_version,
                                                                  mock_install_kubectl_client, *_):
        version = "v1.20.5"
        mock_compare_kubectl_client_and_server_version.return_value = version
        mock_install_kubectl_client.return_value = True
        tool.update_local_kubectl_version("deployment_name", "slogan")
        mock_compare_kubectl_client_and_server_version.called_with("deployment_name", "slogan")
        mock_install_kubectl_client.called_with(version)

    @patch("enmutils_int.bin.configure_wlvm.is_cloudnative_namespace_found", return_value=True)
    @patch("enmutils_int.bin.configure_wlvm.install_kubectl_client")
    @patch("enmutils_int.bin.configure_wlvm.compare_kubectl_client_and_server_version")
    def test_update_local_kubectl_version__will_not_update_version_if_same(self,
                                                                           mock_compare_kubectl_client_and_server_version,
                                                                           mock_install_kubectl_client, *_):
        mock_compare_kubectl_client_and_server_version.return_value = None
        tool.update_local_kubectl_version("deployment_name", "slogan")
        mock_compare_kubectl_client_and_server_version.called_with("deployment_name", "slogan")
        self.assertFalse(mock_install_kubectl_client.called)

    @patch("enmutils_int.bin.configure_wlvm.is_cloudnative_namespace_found", return_value=False)
    @patch("enmutils_int.bin.configure_wlvm.install_kubectl_client")
    @patch("enmutils_int.bin.configure_wlvm.compare_kubectl_client_and_server_version")
    def test_update_local_kubectl_version__will_not_update_if_not_cenm(self,
                                                                       mock_compare_kubectl_client_and_server_version,
                                                                       mock_install_kubectl_client, *_):
        tool.update_local_kubectl_version("deployment_name", "slogan")
        self.assertFalse(mock_compare_kubectl_client_and_server_version.called)
        self.assertFalse(mock_install_kubectl_client.called)

    @patch("subprocess.check_output")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_emp_external_ip_address_from_bashrc")
    @patch("enmutils_int.lib.configure_wlvm_operations.check_if_file_exists")
    def test_store_private_key_on_emp_flow__successful(
            self, mock_check_if_file_exists, mock_get_emp_external_ip_address, mock_check_output, *_):
        mock_check_if_file_exists.side_effect = [False, True, True, True, False, True, True]
        mock_get_emp_external_ip_address.side_effect = ["", "blah", "blah", "blah", "blah", "blah", "blah"]
        mock_check_output.side_effect = [self.bad_command_result, "", ""]

        self.assertFalse(operations.store_private_key_on_emp_flow(Mock(), "deployment_name", "slogan"))
        self.assertFalse(operations.store_private_key_on_emp_flow(Mock(), "deployment_name", "slogan"))
        self.assertFalse(operations.store_private_key_on_emp_flow(Mock(), "deployment_name", "slogan"))
        self.assertFalse(operations.store_private_key_on_emp_flow(Mock(), "deployment_name", "slogan"))
        self.assertTrue(operations.store_private_key_on_emp_flow(Mock(), "deployment_name", "slogan"))

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.operations.store_private_key_on_emp_flow")
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_store_private_key_on_emp__successful_for_venm(
            self, mock_logger, mock_store_private_key_on_emp_flow, mock_get_dit_deployment_info):
        tool.store_private_key_on_emp("deployment_name", "slogan")
        mock_store_private_key_on_emp_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.operations.store_private_key_on_emp_flow")
    def test_store_private_key_on_emp__does_not_do_anything_in_cenm(
            self, mock_store_private_key_on_emp_flow, mock_get_dit_deployment_info):
        self.assertTrue(tool.store_private_key_on_emp("deployment_name", "slogan"))
        self.assertFalse(mock_store_private_key_on_emp_flow.called)
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_keypair_data_from_dit(self, mock_check_output, mock_logger, *_):
        curl_output_enm_missing = '[{"something_else1":{"something_else2":""}}]'
        curl_output_private_key_missing = '[{"enm":{"something_else":""}}]'
        curl_output_private_key_data_not_set = '[{"enm":{"private_key":""}}]'
        curl_output_private_key_data_set = '[{"enm":{"private_key":"blah-di-blah"}}]'
        mock_check_output.side_effect = [self.bad_command_result, "", ",", "[]", curl_output_enm_missing,
                                         curl_output_private_key_missing, curl_output_private_key_data_not_set,
                                         curl_output_private_key_data_set]

        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))
        self.assertEqual("blah-di-blah", operations.fetch_keypair_data_from_dit(mock_logger, "deployment"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_write_keypair_data_to_file(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "blah", "", self.bad_command_result,
                                         "", self.bad_command_result, "", "blah",
                                         "", "END RSA PRIVATE KEY", "blah",
                                         "", "END RSA PRIVATE KEY", self.bad_command_result,
                                         "", "END RSA PRIVATE KEY", ""]

        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertFalse(operations.write_keypair_data_to_file(mock_logger, "blah"))
        self.assertTrue(operations.write_keypair_data_to_file(mock_logger, "blah"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_check_if_file_exists(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "False", "True", "True"]

        self.assertFalse(operations.check_if_file_exists(mock_logger, "some_path"))
        self.assertFalse(operations.check_if_file_exists(mock_logger, "some_path"))
        self.assertTrue(operations.check_if_file_exists(mock_logger, "some_path", "emp_ip"))
        self.assertTrue(operations.check_if_file_exists(mock_logger, "some_path"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_get_emp_external_ip_address_from_bashrc(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = ["some_ip_address1", "", self.bad_command_result]

        self.assertTrue(operations.get_emp_external_ip_address_from_bashrc(mock_logger))
        self.assertFalse(operations.get_emp_external_ip_address_from_bashrc(mock_logger))
        self.assertFalse(operations.get_emp_external_ip_address_from_bashrc(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_emp_external_ip_address_from_bashrc")
    @patch("subprocess.check_output")
    def test_get_package_version_in_enm_repo(self, mock_check_output, mock_get_emp_ip, mock_logger, *_):
        dummy_ip = "some_ip_address1"
        mock_get_emp_ip.side_effect = ["", dummy_ip, dummy_ip, dummy_ip]
        mock_check_output.side_effect = ["4.99.99", "A bad result", self.bad_command_result]
        ddc_package = {'cxp': "ddc", 'nexus_path': "some_path"}

        self.assertFalse(packages.get_package_version_in_enm_repo(mock_logger, ddc_package['cxp']))
        self.assertTrue(packages.get_package_version_in_enm_repo(mock_logger, ddc_package['cxp']))
        self.assertFalse(packages.get_package_version_in_enm_repo(mock_logger, ddc_package['cxp']))
        self.assertFalse(packages.get_package_version_in_enm_repo(mock_logger, ddc_package['cxp']))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_check_package_is_installed(self, mock_check_output, mock_logger, *_):
        service_command_output = "DDC running"
        mock_check_output.side_effect = ["", self.bad_command_result, "1", service_command_output, "2",
                                         service_command_output]

        ddc_package = {'cxp': "ddc", 'nexus_path': "some_path"}

        self.assertFalse(packages.check_package_is_installed(mock_logger, ddc_package['cxp'], "version"))
        self.assertFalse(packages.check_package_is_installed(mock_logger, ddc_package['cxp'], "version"))
        self.assertTrue(packages.check_package_is_installed(mock_logger, ddc_package['cxp'], "version"))
        self.assertTrue(packages.check_package_is_installed(mock_logger, ddc_package['cxp']))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_remove_old_rpm_versions(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = ["", "blah", self.bad_command_result]
        ddc_package = {'cxp': "ddc", 'nexus_path': "some_path"}

        self.assertTrue(packages.remove_old_rpm_versions(mock_logger, ddc_package['cxp']))
        self.assertFalse(packages.remove_old_rpm_versions(mock_logger, ddc_package['cxp']))
        self.assertFalse(packages.remove_old_rpm_versions(mock_logger, ddc_package['cxp']))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_package_from_nexus(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = ["blah blah", self.bad_command_result, "blah saved blah"]
        ddc_package = {'cxp': "ddc", 'nexus_path': "some_path"}

        self.assertFalse(
            packages.fetch_package_from_nexus(mock_logger, ddc_package['cxp'], ddc_package['nexus_path'], "version"))
        self.assertFalse(
            packages.fetch_package_from_nexus(mock_logger, ddc_package['cxp'], ddc_package['nexus_path'], "version"))
        self.assertTrue(
            packages.fetch_package_from_nexus(mock_logger, ddc_package['cxp'], ddc_package['nexus_path'], "version"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_packages.check_package_is_installed")
    @patch("subprocess.check_output")
    def test_install_package(self, mock_check_output, mock_check_package_installed, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "", "some yum output", "some yum output"]
        mock_check_package_installed.side_effect = [False, True]
        ddc_package = {'cxp': "ddc", 'nexus_path': "some_path"}
        other_package = {'cxp': "other", 'nexus_path': "some_path"}

        self.assertFalse(packages.install_package(mock_logger, ddc_package['cxp'], "version"))
        self.assertFalse(packages.install_package(mock_logger, ddc_package['cxp'], "version"))
        self.assertFalse(packages.install_package(mock_logger, ddc_package['cxp'], "version"))
        self.assertTrue(packages.install_package(mock_logger, other_package['cxp'], "version"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_create_ddc_flag_file(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = ["", "blah", self.bad_command_result]

        self.assertTrue(packages.create_ddc_flag_file(mock_logger))
        self.assertFalse(packages.create_ddc_flag_file(mock_logger))
        self.assertFalse(packages.create_ddc_flag_file(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("enmutils_int.lib.configure_wlvm_operations.check_if_file_exists")
    @patch("subprocess.check_output")
    def test_add_entry_to_server_txt_file_on_enm(self, mock_check_output, mock_check_if_file_exists, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "blah", ""]
        mock_check_if_file_exists.side_effect = [False, True, True]

        self.assertFalse(packages.add_entry_to_server_txt_file_on_enm(mock_logger, "blah", "blah"))
        self.assertFalse(packages.add_entry_to_server_txt_file_on_enm(mock_logger, "blah", "blah"))
        self.assertTrue(packages.add_entry_to_server_txt_file_on_enm(mock_logger, "blah", "blah"))

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.create_ddc_secret_on_cluster")
    @patch("enmutils_int.bin.configure_wlvm.packages.configure_ddc_on_enm_flow", return_value=True)
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_configure_ddc_on_enm__successful_for_venm(
            self, mock_logger, mock_configure_ddc_on_enm_flow, mock_create_ddc_secret_on_cluster,
            mock_get_dit_deployment_info):
        self.assertTrue(tool.configure_ddc_on_enm("deployment_name", "slogan"))
        mock_configure_ddc_on_enm_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        mock_get_dit_deployment_info.assert_called_with("deployment_name")
        self.assertFalse(mock_create_ddc_secret_on_cluster.called)

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.packages.configure_ddc_on_enm_flow")
    @patch("enmutils_int.bin.configure_wlvm.create_ddc_secret_on_cluster")
    def test_configure_ddc_on_enm__successful_for_cenm(
            self, mock_create_ddc_secret_on_cluster, mock_configure_ddc_on_enm_flow, mock_get_dit_deployment_info):
        self.assertTrue(tool.configure_ddc_on_enm("deployment_name", "slogan"))
        mock_create_ddc_secret_on_cluster.assert_called_with("deployment_name", "slogan", {"key1": "value1"})
        self.assertFalse(mock_configure_ddc_on_enm_flow.called)
        mock_get_dit_deployment_info.assert_called_with("deployment_name")

    @patch("enmutils_int.lib.configure_wlvm_packages.add_entry_to_server_txt_file_on_enm")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_workload_fqdn")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_emp_external_ip_address_from_bashrc")
    @patch("enmutils_int.lib.configure_wlvm_operations.check_if_file_exists")
    def test_configure_ddc_on_enm(self, mock_check_if_file_exists, mock_get_emp_external_ip,
                                  mock_get_workload_fqdn, mock_add_entry_to_server_txt, *_):
        mock_check_if_file_exists.return_value = False
        self.assertFalse(packages.configure_ddc_on_enm_flow(Mock(), "deployment_name", "slogan"))

        mock_check_if_file_exists.return_value = True
        mock_get_emp_external_ip.return_value = ""
        self.assertFalse(packages.configure_ddc_on_enm_flow(Mock(), "deployment_name", "slogan"))

        mock_get_emp_external_ip.return_value = "blah"
        mock_get_workload_fqdn.return_value = ""
        self.assertFalse(packages.configure_ddc_on_enm_flow(Mock(), "deployment_name", "slogan"))

        mock_get_workload_fqdn.return_value = "blah"
        mock_add_entry_to_server_txt.return_value = False
        self.assertFalse(packages.configure_ddc_on_enm_flow(Mock(), "deployment_name", "slogan"))

        mock_add_entry_to_server_txt.return_value = True
        self.assertTrue(packages.configure_ddc_on_enm_flow(Mock(), "deployment_name", "slogan"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_get_workload_fqdn(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = ["", "myhost", self.bad_command_result]

        self.assertEqual("", operations.get_workload_fqdn(mock_logger))
        self.assertEqual("myhost.{}".format(ATHTEM_DOMAINNAME), operations.get_workload_fqdn(mock_logger))
        self.assertEqual("", operations.get_workload_fqdn(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_create_ddc_plugin_for_workload_script_file(self, mock_check_output, mock_logger, *_):
        mock_check_output.side_effect = [self.bad_command_result, "blah", "", self.bad_command_result, "", "blah",
                                         "", "", self.bad_command_result, "", "", "blah", "", "", ""]

        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_script_file(mock_logger))
        self.assertTrue(packages.create_ddc_plugin_for_workload_script_file(mock_logger))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_create_ddc_plugin_for_workload_dat_file(self, mock_check_output, mock_logger, *_):
        service_command_output = "DDC running"

        mock_check_output.side_effect = ["0", "0",
                                         "1", service_command_output, self.bad_command_result,
                                         "1", service_command_output, "blah",
                                         "1", service_command_output, "", self.bad_command_result,
                                         "1", service_command_output, "", "blah",
                                         "1", service_command_output, "", ""]

        self.assertFalse(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))
        self.assertFalse(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))
        self.assertTrue(packages.create_ddc_plugin_for_workload_dat_file(mock_logger))

    @patch('enmutils_int.lib.configure_wlvm_packages.create_ddc_plugin_for_workload_script_file')
    @patch('enmutils_int.lib.configure_wlvm_packages.create_ddc_plugin_for_workload_dat_file')
    def test_setup_ddc_collection_of_workload_files(self, mock_dat_file, mock_script_file, *_):
        mock_script_file.side_effect = [False, True, True]
        mock_dat_file.side_effect = [False, True]
        self.assertFalse(tool.setup_ddc_collection_of_workload_files("deployment_name", "slogan"))
        self.assertFalse(tool.setup_ddc_collection_of_workload_files("deployment_name", "slogan"))
        self.assertTrue(tool.setup_ddc_collection_of_workload_files("deployment_name", "slogan"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_workload_id(self, mock_check_output, mock_logger, *_):
        curl_output_documents_missing = ('[{"something_else":['
                                         '{"document_id":"blah","schema_name":"netsim"},'
                                         '{"document_id":"","schema_name":"workload"}'
                                         ']}]')
        curl_output_schema_name_missing = ('[{"documents":['
                                           '{"document_id":"blah","schema_name":"netsim"},'
                                           '{"document_id":"99999","other":"blah"}'
                                           ']}]')
        curl_output_workload_id_missing = ('[{"documents":['
                                           '{"document_id":"blah","schema_name":"netsim"}'
                                           ']}]')
        curl_output_workload_id_not_set = ('[{"documents":['
                                           '{"document_id":"blah","schema_name":"netsim"},'
                                           '{"document_id":"","schema_name":"workload"}'
                                           ']}]')
        curl_output_workload_id_set = ('[{"documents":['
                                       '{"document_id":"blah","schema_name":"netsim"},'
                                       '{"document_id":"99999","schema_name":"workload"}'
                                       ']}]')

        mock_check_output.side_effect = [self.bad_command_result, "[]", "[],", "", curl_output_documents_missing,
                                         curl_output_schema_name_missing, curl_output_workload_id_missing,
                                         curl_output_workload_id_not_set, curl_output_workload_id_set]

        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("", operations.fetch_workload_id(mock_logger, "deployment_name"))
        self.assertEqual("99999", operations.fetch_workload_id(mock_logger, "deployment_name"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch("subprocess.check_output")
    def test_fetch_workload_vm_hostname(self, mock_check_output, mock_logger, *_):
        curl_output_content_missing = '{"blah":{"vm":[]}}'
        curl_output_content_empty = '{"blah":{}}'
        curl_output_vm_missing = '{"content":{"blah":[]}}'
        curl_output_vm_empty = '{"content":{"vm":[]}}'
        curl_output_hostname_missing = '{"content":{"vm":[{"blah":""}]}}'
        curl_output_hostname_not_set = '{"content":{"vm":[{"hostname":""}]}}'
        curl_output_hostname_set = '{"content":{"vm":[{"hostname":"wlvm_hostname"}]}}'

        mock_check_output.side_effect = [self.bad_command_result, "", ",", curl_output_content_missing,
                                         curl_output_content_empty, curl_output_vm_missing, curl_output_vm_empty,
                                         curl_output_hostname_missing, curl_output_hostname_not_set,
                                         curl_output_hostname_set]

        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))
        self.assertEqual("wlvm_hostname", operations.fetch_workload_vm_hostname(mock_logger, "blah"))

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger")
    @patch('enmutils_int.lib.configure_wlvm_operations.json.loads')
    @patch("subprocess.check_output")
    def test_fetch_workload_vm_hostname_json_data_empty(self, mock_check_output, mock_json_loads, mock_logger, *_):
        mock_check_output.return_value = "blah"
        mock_json_loads.return_value = ""

        self.assertEqual("", operations.fetch_workload_vm_hostname(mock_logger, "blah"))

    @patch("enmutils_int.lib.configure_wlvm_operations.fetch_workload_vm_hostname")
    @patch("enmutils_int.lib.configure_wlvm_operations.fetch_workload_id")
    def test_get_wlvm_hostname_from_dit(self, mock_fetch_workload_id, mock_fetch_workload_vm_hostname, *_):
        mock_fetch_workload_id.side_effect = ["", "blah", "blah"]
        mock_fetch_workload_vm_hostname.side_effect = ["", "blah"]

        self.assertFalse(tool.get_wlvm_hostname_from_dit("deployment_name", "slogan"))
        self.assertFalse(tool.get_wlvm_hostname_from_dit("deployment_name", "slogan"))
        self.assertTrue(tool.get_wlvm_hostname_from_dit("deployment_name", "slogan"))

    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("vENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.packages.install_ddc_flow")
    @patch("enmutils_int.bin.configure_wlvm.operations.log.logger")
    def test_install_ddc__successful_for_venm(
            self, mock_logger, mock_install_ddc_flow, mock_get_dit_deployment_info):
        tool.install_ddc("deployment_name", "slogan")
        mock_install_ddc_flow.assert_called_with(mock_logger, "deployment_name", "slogan")
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.bin.configure_wlvm.get_dit_deployment_info", return_value=("cENM", {"key1": "value1"}))
    @patch("enmutils_int.bin.configure_wlvm.packages.install_ddccore_release_package", return_value=True)
    def test_install_ddc__successful_for_cenm(
            self, mock_install_ddccore_release_package, mock_get_dit_deployment_info, _):
        self.assertTrue(tool.install_ddc("deployment_name", "slogan"))
        mock_install_ddccore_release_package.assert_called_with("deployment_name", "slogan", True)
        self.assertTrue(mock_get_dit_deployment_info.called)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.commands.getstatusoutput")
    @patch("enmutils_int.lib.configure_wlvm_packages.perform_service_operation", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_packages.install_rpm_package")
    @patch("enmutils_int.lib.configure_wlvm_packages.download_release_package_from_nexus")
    @patch("enmutils_int.lib.configure_wlvm_packages.check_if_rpm_package_is_installed", return_value=True)
    def test_install_ddccore_release_package__successful_if_package_already_installed_but_ddc_not_running(
            self, mock_check_if_rpm_package_is_installed, mock_download_release_package_from_nexus,
            mock_install_rpm_package, mock_perform_service_operation, *_):
        self.assertTrue(packages.install_ddccore_release_package("deployment_name", "slogan", True))
        mock_check_if_rpm_package_is_installed.assert_called_with("ERICddccore_CXP9035927")
        self.assertFalse(mock_download_release_package_from_nexus.called)
        self.assertFalse(mock_install_rpm_package.called)
        self.assertTrue(call("ddc", "status") in mock_perform_service_operation.mock_calls)
        self.assertTrue(call("ddc", "start") in mock_perform_service_operation.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.commands.getstatusoutput")
    @patch("enmutils_int.lib.configure_wlvm_packages.perform_service_operation", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.install_rpm_package", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.download_release_package_from_nexus", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.check_if_rpm_package_is_installed", return_value=False)
    def test_install_ddccore_release_package__successful_if_package_not_already_installed(
            self, mock_check_if_rpm_package_is_installed, mock_download_release_package_from_nexus,
            mock_install_rpm_package, mock_perform_service_operation, *_):
        self.assertTrue(packages.install_ddccore_release_package("deployment_name", "slogan", True))
        mock_check_if_rpm_package_is_installed.assert_called_with("ERICddccore_CXP9035927")
        mock_download_release_package_from_nexus.assert_called_with(
            "ERICddccore_CXP9035927", "com/ericsson/oss/itpf/monitoring", "/tmp/ERICddccore_CXP9035927.rpm", True)
        mock_install_rpm_package.assert_called_with("/tmp/ERICddccore_CXP9035927.rpm")
        mock_perform_service_operation.assert_called_with("ddc", "status")

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_packages.commands.getstatusoutput")
    @patch("enmutils_int.lib.configure_wlvm_packages.perform_service_operation")
    @patch("enmutils_int.lib.configure_wlvm_packages.install_rpm_package")
    @patch("enmutils_int.lib.configure_wlvm_packages.download_release_package_from_nexus", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_packages.check_if_rpm_package_is_installed", return_value=False)
    def test_install_ddccore_release_package__unsuccessful_if_package_not_already_installed_and_download_failed(
            self, mock_check_if_rpm_package_is_installed, mock_download_release_package_from_nexus,
            mock_install_rpm_package, mock_perform_service_operation, *_):
        self.assertFalse(packages.install_ddccore_release_package("deployment_name", "slogan", True))
        mock_check_if_rpm_package_is_installed.assert_called_with("ERICddccore_CXP9035927")
        mock_download_release_package_from_nexus.assert_called_with(
            "ERICddccore_CXP9035927", "com/ericsson/oss/itpf/monitoring", "/tmp/ERICddccore_CXP9035927.rpm", True)
        self.assertFalse(mock_install_rpm_package.called)
        self.assertFalse(mock_perform_service_operation.called)

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_true_if_ddccore_is_already_installed(
            self, mock_check_output, *_):
        ddccore_rpm_version = "1.3.3"
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        service_command_output = "DDC running"

        mock_check_output.side_effect = [check_if_file_exists, get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version, "1", service_command_output]
        self.assertTrue(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_false_if_private_key_not_found(
            self, mock_check_output, *_):
        mock_check_output.return_value = "False"
        self.assertFalse(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_true_if_ddccore_is_not_installed_on_wlvm_and_ddc_is_already_installed(
            self, mock_check_output, *_):
        ddccore_rpm_version = "1.3.3"
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddccore_listed_in_rpm_printout = ["0", "1"]
        uninstall_package_output = "blah"
        number_of_times_ddc_listed_in_rpm_printout = ["1", "0"]
        remove_old_rpm_versions_output = ""
        nexus_fetch_output = "saved"
        create_ddc_flag_file_output = ""
        install_package_output = "installed"
        service_command_output = ["DDC running", self.ddc_service_not_running, "Starting ddc:"]

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddccore_listed_in_rpm_printout[0],
                                         number_of_times_ddc_listed_in_rpm_printout[0],
                                         service_command_output[0],
                                         uninstall_package_output,
                                         number_of_times_ddc_listed_in_rpm_printout[1],
                                         remove_old_rpm_versions_output, nexus_fetch_output,
                                         create_ddc_flag_file_output, install_package_output,
                                         number_of_times_ddccore_listed_in_rpm_printout[1],
                                         service_command_output[1],
                                         service_command_output[2]]

        self.assertTrue(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_true_if_ddccore_is_not_installed_on_wlvm_and_ddc_is_not_installed_either(
            self, mock_check_output, *_):
        ddccore_rpm_version = "1.3.3"
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddccore_listed_in_rpm_printout = ["0", "1"]
        number_of_times_ddc_listed_in_rpm_printout = "0"
        remove_old_rpm_versions_output = ""
        nexus_fetch_output = "saved"
        create_ddc_flag_file_output = ""
        install_package_output = "installed"
        service_command_output = [self.ddc_service_not_running, "Starting ddc:"]

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddccore_listed_in_rpm_printout[0],
                                         number_of_times_ddc_listed_in_rpm_printout,
                                         remove_old_rpm_versions_output, nexus_fetch_output,
                                         create_ddc_flag_file_output, install_package_output,
                                         number_of_times_ddccore_listed_in_rpm_printout[1],
                                         service_command_output[0], service_command_output[1]]

        self.assertTrue(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_false_if_ddccore_is_not_installed_on_wlvm_and_ddc_cant_be_uninstalled(
            self, mock_check_output, *_):
        ddccore_rpm_version = "1.3.3"
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddccore_listed_in_rpm_printout = ["0", "1"]
        uninstall_package_output = self.bad_command_result
        ddc_service_not_installed = self.bad_command_result
        number_of_times_ddc_listed_in_rpm_printout = "1"

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddccore_listed_in_rpm_printout[0],
                                         number_of_times_ddc_listed_in_rpm_printout,
                                         uninstall_package_output,
                                         ddc_service_not_installed]

        self.assertFalse(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_false_if_ddccore_is_not_found_on_enm_but_ddccore_rpm_cant_be_fetched_from_nexus(
            self, mock_check_output, *_):
        ddccore_rpm_version = ""
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddccore_listed_in_rpm_printout = ["0", "1"]
        remove_old_rpm_versions_output = ""
        nexus_fetch_output = "not found"

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddccore_listed_in_rpm_printout[0],
                                         remove_old_rpm_versions_output, nexus_fetch_output]

        self.assertFalse(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_true_if_ddccore_is_not_found_on_enm_and_ddc_not_installed_on_wlvm(
            self, mock_check_output, *_):
        ddccore_rpm_version = ""
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddc_listed_in_rpm_printout = ["0", "1"]
        remove_old_rpm_versions_output = ""
        nexus_fetch_output = "saved"
        create_ddc_flag_file_output = ""
        install_package_output = "installed"
        service_command_output = [self.ddc_service_not_running, self.bad_command_result]

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddc_listed_in_rpm_printout[0],
                                         remove_old_rpm_versions_output, nexus_fetch_output,
                                         create_ddc_flag_file_output, install_package_output,
                                         number_of_times_ddc_listed_in_rpm_printout[1],
                                         service_command_output[0], service_command_output[1]]

        self.assertTrue(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch("subprocess.check_output")
    def test_install_ddc_flow__returns_true_if_ddccore_is_not_found_on_enm_and_ddc_already_installed_on_wlvm(
            self, mock_check_output, *_):
        ddccore_rpm_version = ""
        ddc_rpm_version = "4.61.2"
        check_if_file_exists = "True"
        get_external_ip_address_output = "a.b.c.d"
        number_of_times_ddc_listed_in_rpm_printout = "1"
        service_command_output = "DDC running"

        mock_check_output.side_effect = [check_if_file_exists,
                                         get_external_ip_address_output, ddccore_rpm_version,
                                         get_external_ip_address_output, ddc_rpm_version,
                                         number_of_times_ddc_listed_in_rpm_printout,
                                         service_command_output]

        self.assertTrue(packages.install_ddc_flow(Mock(), "deployment_name", "slogan"))

    @patch('enmutils_int.lib.configure_wlvm_operations.subprocess.check_output')
    @patch('enmutils_int.lib.configure_wlvm_operations.log.logger.debug')
    def test_export_deployment_name__success(self, mock_debug, _):
        name = "ieatenmc"
        operations.export_deployment_name(name)
        mock_debug.assert_called_with("Value of 'export DEPLOYMENTNAME=ieatenmc' is added to '/root/.bashrc'.")

    @patch('enmutils_int.lib.configure_wlvm_operations.subprocess.check_output',
           side_effect=subprocess.CalledProcessError(1, "cmd", "Error"))
    @patch('enmutils_int.lib.configure_wlvm_operations.log.logger.info')
    def test_export_deployment_name__process_error(self, mock_info, _):
        name = "ieatenmc"
        operations.export_deployment_name(name)
        self.assertTrue(call("Problem encountered during command execution: Command 'cmd' "
                             "returned non-zero exit status 1\n - Error") in mock_info.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger.info")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_workload_fqdn")
    def test_check_deployment_to_disable_proxy__if_proxy_not_required(self, mock_get_workload_fqdn, mock_log_info):
        mock_get_workload_fqdn.return_value = "seli122344"
        self.assertEqual(False, operations.check_deployment_to_disable_proxy())
        self.assertEqual(mock_log_info.call_count, 2)

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger.info")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_workload_fqdn")
    def test_check_deployment_to_disable_proxy__if_proxy_required(self, mock_get_workload_fqdn, mock_log_info):
        mock_get_workload_fqdn.return_value = "ieatwlvm1234"
        self.assertEqual(True, operations.check_deployment_to_disable_proxy())
        self.assertEqual(mock_log_info.call_count, 1)

    @patch("enmutils_int.lib.configure_wlvm_operations.log.logger.info")
    @patch("enmutils_int.lib.configure_wlvm_operations.get_workload_fqdn")
    def test_check_deployment_to_disable_proxy__if_wlvm_name_empty(self, mock_get_workload_fqdn, mock_log_info):
        mock_get_workload_fqdn.return_value = ""
        self.assertEqual(True, operations.check_deployment_to_disable_proxy())
        self.assertEqual(mock_log_info.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
