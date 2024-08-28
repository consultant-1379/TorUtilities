#!/usr/bin/env python
import enmutils_int.lib.configure_wlvm_ddc_plugin as configure
import unittest2
from mock import patch, call
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class ConfigureWlvmDdcPluginUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.datetime")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.process_workload_files", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.does_dir_exist", return_value=True)
    def test_create_workload_log_file_increments__successful(
            self, mock_does_dir_exist, mock_process_workload_files, mock_datetime):
        mock_datetime.now.return_value.strftime.return_value = "310720"
        self.assertTrue(configure.create_workload_log_file_increments())
        self.assertEqual([call("/var/tmp/ddc_data/310720/plugin_data/workload")], mock_does_dir_exist.mock_calls)
        mock_process_workload_files.assert_called_with("/var/tmp/ddc_data/310720/plugin_data/workload")

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.datetime")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.process_workload_files", side_effect=Exception())
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.does_dir_exist", return_value=True)
    def test_perform_ddc_plugin_increment_operations__unsuccessful_if_cannot_create_increment_file(
            self, mock_does_dir_exist, mock_process_workload_files, mock_datetime):
        mock_datetime.now.return_value.strftime.return_value = "310720"
        self.assertFalse(configure.create_workload_log_file_increments())
        self.assertEqual([call("/var/tmp/ddc_data/310720/plugin_data/workload")], mock_does_dir_exist.mock_calls)
        mock_process_workload_files.assert_called_with("/var/tmp/ddc_data/310720/plugin_data/workload")

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.datetime")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.process_workload_files")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.does_dir_exist", return_value=False)
    def test_perform_ddc_plugin_increment_operations__unsuccessful_if_workload_dir_doesnt_exist(
            self, mock_does_dir_exist, mock_process_workload_files, mock_datetime):
        mock_datetime.now.return_value.strftime.return_value = "310720"
        self.assertFalse(configure.create_workload_log_file_increments())
        self.assertEqual([call("/var/tmp/ddc_data/310720/plugin_data/workload")], mock_does_dir_exist.mock_calls)
        self.assertFalse(mock_process_workload_files.called)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.get_files_in_directory", return_value=["file1", "file2"])
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.create_increment_file", return_value=True)
    def test_process_workload_files__successful(self, mock_create_increment_file, _):
        self.assertTrue(configure.process_workload_files("main_workload_dir"))
        self.assertEqual([call("main_workload_dir", "file1"),
                          call("main_workload_dir", "file2")], mock_create_increment_file.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.get_files_in_directory", return_value=["file1", "file2"])
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.create_increment_file", side_effect=[True, False])
    def test_process_workload_files__unsuccessful_if_unable_to_create_increment_file(self, mock_create_increment_file, _):
        self.assertFalse(configure.process_workload_files("main_workload_dir"))
        self.assertEqual([call("main_workload_dir", "file1"),
                          call("main_workload_dir", "file2")], mock_create_increment_file.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.remove_temporary_files")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.add_new_increment_file")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.create_diff_file")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.create_combined_increment_file")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.get_list_of_increment_files", return_value=["file1", "file2"])
    def test_create_increment_file__successful(
            self, mock_get_list_of_increment_files, mock_create_combined_increment_file, mock_create_diff_file,
            mock_add_new_increment_file, mock_remove_temporary_files):
        self.assertTrue(configure.create_increment_file("workload_dir", "profiles.log"))
        mock_get_list_of_increment_files.assert_called_with("workload_dir", "profiles.log")
        mock_create_combined_increment_file.assert_called_with("workload_dir", ["file1", "file2"], "profiles.log")
        mock_create_diff_file.assert_called_with("workload_dir", "profiles.log",
                                                 mock_create_combined_increment_file.return_value)
        mock_add_new_increment_file.assert_called_with("workload_dir", "profiles.log",
                                                       mock_create_diff_file.return_value, 3)
        mock_remove_temporary_files.assert_called_with("workload_dir", "profiles.log",
                                                       mock_create_diff_file.return_value,
                                                       mock_create_combined_increment_file.return_value)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command",
           return_value={"result": True, "output": "file1\nfile2\n"})
    def test_get_list_of_increment_files__succussful(self, mock_execute_command):
        self.assertEqual(["file1", "file2"], configure.get_list_of_increment_files("workload_dir", "profiles.log"))
        mock_execute_command.assert_called_with("ls -rt workload_dir | egrep ^profiles.log.[1-9]", log_output=False)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_create_combined_increment_file__successful_if_increment_files_exist(self, mock_execute_command):
        self.assertEqual("workload_dir/profiles.log.increment_files_combined",
                         configure.create_combined_increment_file("workload_dir", ["file1", "file2"], "profiles.log"))
        mock_execute_command.assert_called_with("cat workload_dir/file1 workload_dir/file2 > "
                                                "workload_dir/profiles.log.increment_files_combined")

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_create_combined_increment_file__successful_if_increment_files_dont_exist(self, mock_execute_command):
        self.assertEqual("workload_dir/profiles.log.increment_files_combined",
                         configure.create_combined_increment_file("workload_dir", [], "profiles.log"))
        mock_execute_command.assert_called_with("touch workload_dir/profiles.log.increment_files_combined")

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_create_diff_file__successful(self, mock_execute_command):
        self.assertEqual("workload_dir/profiles.log.diff",
                         configure.create_diff_file("workload_dir", "profiles.log",
                                                    "workload_dir/profiles.log.increment_files_combined"))
        mock_execute_command.assert_called_with(
            "diff --new-line-format='' --unchanged-line-format='' workload_dir/profiles.log "
            "workload_dir/profiles.log.increment_files_combined > workload_dir/profiles.log.diff",
            log_output=False)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command", return_value={"result": True, "output": "0 "})
    def test_add_new_increment_file__doesnt_create_file_if_no_differences_exist(self, mock_execute_command):
        configure.add_new_increment_file("workload_dir", "profiles.log", "workload_dir/profiles.log.diff", 1)
        wc_command = "wc -l workload_dir/profiles.log.diff"

        self.assertEqual([call(wc_command)], mock_execute_command.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.add_new_delta_file")
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command", return_value={"result": True, "output": "1 "})
    def test_add_new_increment_file__creates_increment_file_if_differences_exist(
            self, mock_execute_command, mock_add_new_delta_file):
        configure.add_new_increment_file("workload_dir", "profiles.log", "workload_dir/profiles.log.diff", 1)
        wc_command = "wc -l workload_dir/profiles.log.diff"
        mv_command = "mv workload_dir/profiles.log.diff workload_dir/profiles.log.1"

        self.assertEqual([call(wc_command), call(mv_command)], mock_execute_command.mock_calls)
        mock_add_new_delta_file.assert_called_with("workload_dir/profiles.log.1", "profiles.log")

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.does_dir_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_create_new_delta_file__successful_if_delta_dir_exists(self, mock_execute_command, _):
        configure.TODAY_DIR = "/var/tmp/ddc_data/231020"
        configure.add_new_delta_file("workload_dir/profiles.log.1", "profiles.log")
        mkdir_command = "mkdir -p /var/tmp/ddc_data/231020/delta/workload"
        cp_command = "cp workload_dir/profiles.log.1 /var/tmp/ddc_data/231020/delta/workload"
        self.assertEqual([call(mkdir_command, log_output=False), call(cp_command)], mock_execute_command.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.does_dir_exist", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_create_new_delta_file__does_nothing_if_delta_dir_does_not_exists(self, mock_execute_command, _):
        configure.TODAY_DIR = "/var/tmp/ddc_data/231020"
        configure.add_new_delta_file("workload_dir/profiles.log.1", "profiles.log")
        self.assertFalse(mock_execute_command.called)

    @patch("enmutils_int.lib.configure_wlvm_ddc_plugin.execute_command")
    def test_remove_temporary_files__successful(self, mock_execute_command):
        configure.remove_temporary_files("workload_dir", "profiles.log", "workload_dir/profiles.log.diff",
                                         "workload_dir/profiles.log.combined_increment_file")
        rm_command = ("rm -f workload_dir/profiles.log workload_dir/profiles.log.diff "
                      "workload_dir/profiles.log.combined_increment_file")
        mock_execute_command.assert_called_with(rm_command)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
