#!/usr/bin/python
import os
from StringIO import StringIO

import unittest2
from mock import patch, Mock

from enmutils.lib import filesystem
from testslib import unit_test_utils


class FilesystemUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.good_response = Mock(rc=0, stdout="D", elapsed_time=.12)
        self.bad_response = Mock(rc=1, stdout="blah", elapsed_time=.123, ok=False)

    def tearDown(self):
        unit_test_utils.tear_down()

        if filesystem.is_dir("mock"):
            filesystem.remove_dir("mock")

    def test_does_file_exist__returns_false_when_file_path_is_none(self):
        self.assertFalse(filesystem.does_file_exist(None))

    @patch("enmutils.lib.filesystem.os.path")
    def test_does_file_exist__returns_true_when_os_path_exists_returns_true_with_verbose(self, mock_os_path):
        mock_os_path.exists.return_value = True
        mock_os_path.realpath.return_value = "mock/test/path/"
        self.assertTrue(filesystem.does_file_exist(mock_os_path.realpath))

    @patch("enmutils.lib.filesystem.os.path")
    def test_does_file_exist__returns_true_when_os_path_exists_returns_true_without_verbose(self, mock_os_path):
        mock_os_path.exists.return_value = True
        mock_os_path.realpath.return_value = "mock/test/path/"
        self.assertTrue(filesystem.does_file_exist(mock_os_path.realpath, verbose=False))

    @patch("enmutils.lib.filesystem.os.path")
    def test_does_file_exist__returns_false_os_path_realpath_returns_false_with_verbose(self, mock_os_path):
        mock_os_path.exists.return_value = False
        self.assertFalse(filesystem.does_file_exist("mock/test/path/"))

    @patch("enmutils.lib.filesystem.os.path")
    def test_does_file_exist__returns_false_os_path_realpath_returns_false_without_verbose(self, mock_os_path):
        mock_os_path.exists.return_value = False
        self.assertFalse(filesystem.does_file_exist("mock/test/path/", verbose=False))

    @patch("enmutils.lib.filesystem.os.path.exists")
    def test_assert_file_exists_does_not_raise_runtime_error_when_does_file_exist_returns_true(self,
                                                                                               mock_os_path_exists):
        mock_os_path_exists.return_value = True
        try:
            filesystem.assert_file_exists("mock/test/path/which/does/exist")
        except:
            self.fail("File does not exist")

    def test_assert_file_exists_does_raises_runtime_error_when_does_file_exist_returns_false(self):
        self.assertRaises(RuntimeError, filesystem.assert_file_exists, "mock/test/path/which/does/not/exist")

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("os.remove")
    def test_delete_file_does_not_raise_exception_if_file_deleted_successfully(self, mock_os_remove,
                                                                               mock_does_file_exist):
        mock_does_file_exist.return_value = False
        mock_os_remove.return_value = None
        # NOTE: There is no assertion here as delete_file() is void;
        # if the test doesn't raise a runtime exception, it's a pass
        filesystem.delete_file("mock/test/path/which/does/exist")

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("os.remove")
    def test_delete_file_raises_exception_if_file_exists_after_deletion_attempt(self, mock_os_remove,
                                                                                mock_does_file_exist):
        mock_does_file_exist.return_value = True
        mock_os_remove.return_value = None

        self.assertRaises(RuntimeError, filesystem.delete_file, "mock/test/path/which/does/exist")

    def test_delete_file_raises_exception_if_file_does_not_exist(self):
        self.assertRaises(OSError, filesystem.delete_file, "mock/test2/path/which/does/exist")

    @patch("os.path.isdir")
    def test_assert_dir_exist_does_not_raise_runtime_error_when_does_file_exist_returns_true(self, mock_os_path_isdir):
        mock_os_path_isdir.return_value = True
        try:
            filesystem.assert_dir_exists("mock/test/path/which/does/exist")
        except:
            self.fail("Directory does not exist")

    def test_assert_dir_exist_raises_runtime_error_when_does_file_exist_returns_false(self):
        self.assertRaises(RuntimeError, filesystem.assert_dir_exists, "mock/test/path/which/does/not/exist")

    @patch("os.path.isdir")
    def test_does_dir_exist_returns_true_when_os_path_isdir_returns_true(self, mock_os_path_isdir):
        mock_os_path_isdir.return_value = True
        self.assertTrue(filesystem.does_dir_exist("mock/test/dir/which/does/not/exist"))

    def test_does_dir_exist_returns_false_when_dir_does_not_exist(self):
        self.assertFalse(filesystem.does_dir_exist("mock/test/dir/which/does/exist"))

    @patch('enmutils.lib.filesystem.change_owner')
    @patch('os.makedirs')
    def test_create_dir_makes_dir_if_dir_does_not_exist(self, mock_makedirs, mock_change_owner):
        filesystem.create_dir("mock/test/path/for/creation", group_name="root")
        self.assertEqual(mock_makedirs.call_count, 1)
        self.assertEqual(mock_change_owner.call_count, 1)

    @patch('enmutils.lib.filesystem.change_owner')
    @patch('enmutils.lib.log.logger.debug')
    @patch('os.makedirs')
    def test_create_dir_makes_dir_if_dir_does_not_exist_with_no_logging(self, mock_makedirs, mock_debug, _):
        filesystem.create_dir("mock/test/path/for/creation", log_output=False)
        self.assertEqual(mock_makedirs.call_count, 1)
        self.assertFalse(mock_debug.called)

    @patch('os.makedirs', side_effect=OSError("Error"))
    @patch('enmutils.lib.filesystem.change_owner')
    @patch('enmutils.lib.log.logger.debug')
    def test_create_dir_makes_logs_os_error(self, mock_debug, mock_change_owner, *_):
        filesystem.create_dir("mock/test/path/for/creation")
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_change_owner.call_count, 0)

    @patch('os.makedirs', side_effect=OSError("Error"))
    @patch('enmutils.lib.filesystem.change_owner')
    @patch('enmutils.lib.log.logger.debug')
    def test_create_dir_makes_logs_os_error_with_no_logging(self, mock_debug, *_):
        filesystem.create_dir("mock/test/path/for/creation", log_output=False)
        self.assertFalse(mock_debug.called)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_create_remote_dir_makes_dir_when_password_is_none(self, mock_does_remote_dir_exist, mock_run_remote_cmd):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = self.good_response
        # NOTE: There is no assertion here as create_remote_dir() is void;
        # if the test doesn't raise a runtime exception, it's a pass
        filesystem.create_remote_dir("mock/test/dir", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_create_remote_dir_makes_dir_when_password_is_not_none(self, mock_does_remote_dir_exist,
                                                                   mock_run_remote_cmd):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = self.good_response
        # NOTE: There is no assertion here as create_remote_dir() is void;
        # if the test doesn't raise a runtime exception, it's a pass
        filesystem.create_remote_dir("mock/test/dir", "test_host", "test_user", "secret")

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_create_remote_dir_raises_runtime_error_when_rc_is_not_0(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.create_remote_dir, "mock/test/dir", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("os.path.isdir")
    def test_remove_dir__executes_successfully_when_rc_is_0_and_file_no_longer_exists(self, mock_os_path_isdir,
                                                                                      mock_run_local_cmd):
        mock_os_path_isdir.side_effect = [True, False]
        mock_run_local_cmd.return_value = self.good_response

        try:
            filesystem.remove_dir("mock/test/path")
        except:
            self.fail("Directory could not be removed")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("os.path.isdir")
    def test_remove_dir__raises_runtime_error_when_rc_is_not_0(self, mock_os_path_isdir, mock_run_local_cmd):
        mock_os_path_isdir.side_effect = [True, True]
        mock_run_local_cmd.return_value = self.bad_response

        self.assertRaises(RuntimeError, filesystem.remove_dir, "mock/test/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("os.path.isdir")
    def test_remove_dir__raises_runtime_error_when_rc_is_0_but_dir_still_exists_after_deletion(self, mock_os_path_isdir,
                                                                                               mock_run_local_cmd):
        mock_os_path_isdir.side_effect = [True, True]
        mock_run_local_cmd.return_value = self.good_response

        self.assertRaises(RuntimeError, filesystem.remove_dir, "mock/test/path")

    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=False)
    def test_remove_dir__directory_does_not_exist(self, *_):
        filesystem.remove_dir("mock/test/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_copy_creates_dir_and_executes_copy_command_without_runtime_exception_rc_is_0(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = self.good_response
        filesystem.copy("mock/test/source/path", "mock/test/destination/path")
        self.assertTrue(filesystem.does_dir_exist("mock/test/destination"))
        os.rmdir("mock/test/destination")

    @patch("enmutils.lib.filesystem.create_dir")
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_copy_does_not_create_dir_and_executes_copy_command_without_runtime_exception_rc_is_0(self,
                                                                                                  mock_run_local_cmd,
                                                                                                  mock_create_dir):
        mock_run_local_cmd.return_value = self.good_response
        os.makedirs("mock/test/destination")
        filesystem.copy("mock/test/source/path", "mock/test/destination/path")
        self.assertFalse(mock_create_dir.called)
        os.rmdir("mock/test/destination")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_copy_raises_runtime_exception_when_rc_is_not_0(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.copy, "mock/test/source/path", "mock/test/destination/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_file_size_in_mb_returns_stdout_when_no_runtime_errors_are_raised(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout="100", elapsed_time=.12)
        self.assertEqual(filesystem.get_file_size_in_mb("mock/test/path"), "100")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_file_size_in_mb_raises_runtime_error_when_rc_is_not_0(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.get_file_size_in_mb, "mock/test/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_file_size_in_mb_raises_runtime_error_when_stdout_is_an_empty_string(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout="", elapsed_time=.12)
        self.assertRaises(RuntimeError, filesystem.get_file_size_in_mb, "mock/test/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_file_size_in_mb_raises_runtime_error_when_stdout_is_none(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=None, elapsed_time=.12)
        self.assertRaises(RuntimeError, filesystem.get_file_size_in_mb, "mock/test/path")

    @patch("enmutils.lib.filesystem.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_file_size_in_mb__raises_runtime_error_file_size_unable_to_process(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=[1234])
        self.assertRaises(RuntimeError, filesystem.get_file_size_in_mb, "mock/test/path")

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_touch_file_executes_command_if_file_path_does_not_already_exist(self, mock_run_local_cmd,
                                                                             mock_does_file_exist):
        mock_does_file_exist.return_value = False
        mock_run_local_cmd.return_value = self.good_response
        filesystem.touch_file("mock/test/path/which/does/not/exist")
        self.assertTrue(mock_run_local_cmd.called)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_file_exist_returns_true_when_rc_is_0_and_password_is_none(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.good_response
        self.assertTrue(filesystem.does_remote_file_exist("mock/test/file", "test_host", "test_user"))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_file_exist_returns_true_when_rc_is_0_and_password_is_not_none(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.good_response
        self.assertTrue(filesystem.does_remote_file_exist("mock/test/file", "test_host", "test_user", "secret"))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_file_exist_raises_runtime_error_when_rc_is_not_0(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertFalse(filesystem.does_remote_file_exist("mock/test/file", "test_host", "test_user"))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_dir_exist_returns_true_when_rc_is_0_and_password_is_none(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.good_response
        self.assertTrue(filesystem.does_remote_dir_exist("mock/test/dir", "test_host", "test_user"))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_dir_exist_returns_true_when_rc_is_0_and_password_is_not_none(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.good_response
        self.assertTrue(filesystem.does_remote_dir_exist("mock/test/dir", "test_host", "test_user", "TestPassw0rd"))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_does_remote_dir_exist_raises_runtime_error_when_rc_is_not_0(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertFalse(filesystem.does_remote_dir_exist("mock/test/dir", "test_host", "test_user"))

    @patch('enmutils.lib.log.logger.debug')
    @patch("enmutils.lib.filesystem.shell.run_cmd_on_cloud_native_pod")
    def test_does_file_exists_on_cloud_native_pod__returns_true(self, mock_run_cmd, mock_log):
        response = Mock()
        response.rc = 0
        pod_name = "apserv"
        container_name = "ap_serv"
        file_path = "test/file/path"
        cmd = "ls {0}".format(file_path)
        mock_run_cmd.return_value = response
        filesystem.does_file_exists_on_cloud_native_pod(pod_name, container_name, file_path)
        mock_run_cmd.assert_called_with(pod_name, container_name, cmd)
        mock_log.assert_called_with("Determined that file test/file/path exists on pod ap_serv")

    @patch('enmutils.lib.log.logger.debug')
    @patch("enmutils.lib.filesystem.shell.run_cmd_on_cloud_native_pod")
    def test_does_file_exists_on_cloud_native_pod__returns_false(self, mock_run_cmd, mock_log):
        response = Mock()
        response.rc = 1
        pod_name = "apserv"
        container_name = "ap_serv"
        file_path = "test/file/path"
        cmd = "ls {0}".format(file_path)
        mock_run_cmd.return_value = response
        filesystem.does_file_exists_on_cloud_native_pod(pod_name, container_name, file_path)
        mock_run_cmd.assert_called_with(pod_name, container_name, cmd)
        mock_log.assert_called_with("Determined that file test/file/path does not exist on pod ap_serv")

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__raises_runtime_error_when_file_does_not_exist(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.get_remote_file_size_in_mb,
                          "mock/test/file/path/which/does/not/exit", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__returns_stdout_when_password_is_none_and_and_rc_is_0(
            self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="100       mock/test/path", elapsed_time=.123)
        self.assertEqual(filesystem.get_remote_file_size_in_mb("mock/test/path", "test_host", "test_user"), "100")

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__returns_stdout_when_password_is_not_none_and_and_rc_is_0(self,
                                                                                                  mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="200       mock/test/path", elapsed_time=.123)
        self.assertEqual(filesystem.get_remote_file_size_in_mb("mock/test/path", "test_host", "test_user",
                                                               "password"), "200")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__raises_runtime_error_if_rc_is_not_0(self, mock_run_remote_cmd,
                                                                             mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=1, stdout="200       mock/test/path", elapsed_time=.123)
        self.assertRaises(RuntimeError, filesystem.get_remote_file_size_in_mb,
                          "mock/test/file/path/which/does/not/exit", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__raises_runtime_error_if_stdout_is_an_empty_string(self,
                                                                                           mock_run_remote_cmd, _):
        mock_run_remote_cmd.return_value = Mock(rc=1, stdout="", elapsed_time=.451)
        self.assertRaises(RuntimeError, filesystem.get_remote_file_size_in_mb,
                          "mock/test/file/path/which/does/not/exit", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.add_sudo_if_cloud")
    @patch("enmutils.lib.filesystem.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__raises_runtime_error_if_stdout_is_none(self, mock_run_remote_cmd,
                                                                                mock_does_remote_file_exist, *_):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=None, elapsed_time=.451)
        self.assertRaises(RuntimeError, filesystem.get_remote_file_size_in_mb,
                          "mock/test/file/path/which/does/not/exit", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.does_remote_file_exist", return_value=True)
    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_size_in_mb__raises_runtime_error_file_size_unable_to_process(self, mock_run_remote_cmd,
                                                                                          *_):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=[1234])
        self.assertRaises(RuntimeError, filesystem.get_remote_file_size_in_mb, "mock/test/path", "test_host",
                          "test_user", "password")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_get_files_in_remote_directory_raises_runtime_error_when_remote_dir_does_not_exist(
            self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = False
        self.assertRaises(OSError, filesystem.get_files_in_remote_directory, "mock/test/dir/which/does/not/exist",
                          "test_host", "test_user")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_raises_runtime_error_when_rc_is_not_0(self, mock_run_remote_cmd,
                                                                                 mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.get_files_in_remote_directory,
                          "mock/test/dir/which/does/not/exist", "test_host", "test_user")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_raises_runtime_error_when_stdout_is_none(self, mock_run_remote_cmd,
                                                                                    mock_does_remote_dir_exist, *_):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=None, elapsed_time=.001)
        self.assertRaises(RuntimeError, filesystem.get_files_in_remote_directory, "mock/test/dir/which/does/not/exist",
                          "test_host", "test_user")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_returns_an_empty_list_when_stdout_is_an_empty_string(
            self, mock_run_remote_cmd, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="", elapsed_time=.001)
        self.assertItemsEqual(list(filesystem.get_files_in_remote_directory("mock/test/dir/which/does/not/exist",
                                                                            "test_host", "test_user")), [])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory__returns_appropriate_file_list_when_rc_is_0_and_password_is_none(
            self, mock_run_remote_cmd, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="one\ntwo\nthree\n", elapsed_time=.211)
        self.assertItemsEqual(list(filesystem.get_files_in_remote_directory("/mock/test/file/", "test_host",
                                                                            "test_user", full_paths=True)),
                              ["/mock/test/file/one", "/mock/test/file/two", "/mock/test/file/three"])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory__returns_appropriate_file_list_when_rc_is_0_and_password_is_not_none(
            self, mock_run_remote_cmd, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="one\ntwo\nthree\n", elapsed_time=.211)
        self.assertItemsEqual(list(filesystem.get_files_in_remote_directory("/mock/test/file/", "test_host",
                                                                            "test_user", "password", full_paths=True)),
                              ["/mock/test/file/one", "/mock/test/file/two", "/mock/test/file/three"])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_with_pattern(self, mock_run_remote_cmd, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="one.abc\ntwo.abc\n", elapsed_time=.211)
        self.assertItemsEqual(list(
            filesystem.get_files_in_remote_directory("/test/mock/dir/path/which/does/not/exist", "test_host",
                                                     "test_user", "password", ends_with=".abc")),
                              ["one.abc", "two.abc"])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_recursive(self, mock_run_remote_cmd, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(
            rc=0, stdout="/test/mock/dir/path/which/does/not/exist/one.abc\n/test/mock/dir/path/which/does/not/"
                         "exist/two.abc\n", elapsed_time=.211)
        files = filesystem.get_files_in_remote_directory_recursively(
            "/test/mock/dir/path/which/does/not/exist", "test_host", "test_user", "password", ends_with=".abc")
        self.assertItemsEqual(files, ["one.abc", "two.abc"])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=False)
    def test_get_files_in_remote_directory_recursively__raises_os_error(self, *_):
        self.assertRaises(OSError, filesystem.get_files_in_remote_directory_recursively, "/test/mock/dir/", "test_host",
                          "test_user")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_recursively__raises_runtime_error(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=1, stdout=None)
        self.assertRaises(RuntimeError, filesystem.get_files_in_remote_directory_recursively, "/test/mock/dir/",
                          "test_host", "test_user", "password")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_recursively__ignore_directory_name(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="1234")
        filesystem.get_files_in_remote_directory_recursively("/test/mock/dir/", "test_host", "test_user", "password",
                                                             ends_with="", full_paths=True)
        self.assertTrue(mock_run_remote_cmd.called)

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_created_since_last(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="1234\n")
        result = filesystem.get_files_in_remote_directory_created_since_last("/test/mock/dir/", 1, "test_host",
                                                                             "test_user", "password")
        self.assertEqual(result, ['1234'])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=False)
    def test_get_files_in_remote_directory_created_since_last__raises_runtime_error_directory_does_not_exists(self, *_):
        self.assertRaises(RuntimeError, filesystem.get_files_in_remote_directory_created_since_last, "/test/mock/dir/",
                          1, "test_host", "test_user", "password")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_files_in_remote_directory_created_since_last__raises_runtime_error_file_does_not_exists(
            self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=1, stdout=None)
        self.assertRaises(RuntimeError, filesystem.get_files_in_remote_directory_created_since_last, "/test/mock/dir/",
                          1, "test_host", "test_user", "password")

    def test_get_files_in_directory_raises_os_error_when_dir_does_not_exist(self):
        self.assertRaises(OSError, filesystem.get_files_in_directory, "test/mock/dir/path/which/does/not/exist")

    @patch("os.listdir")
    @patch("os.path.isdir")
    def test_get_files_in_directory_returns_file_list_if_dir_exists_and_os_list_dir_returns_a_list_of_files(
            self, mock_os_path_isdir, mock_os_listdir):
        mock_os_path_isdir.return_value = True
        mock_os_listdir.return_value = ["one.abc", "two.abc", "three.def"]
        self.assertItemsEqual(list(filesystem.get_files_in_directory("test/mock/dir/path/which/does/not/exist")),
                              mock_os_listdir.return_value)

    @patch("os.listdir", return_value=["one_abc", "two_abc"])
    @patch("os.path.isdir", return_value=True)
    def test_get_files_in_directory_returns_full_file_list_if_dir_exists_and_os_list_dir_returns_a_list_of_files(
            self, *_):
        result = filesystem.get_files_in_directory("test/mock/", ends_with="_abc", full_paths=True)
        self.assertEqual(result, ["test/mock/one_abc", "test/mock/two_abc"])

    @patch("os.listdir")
    @patch("os.path.isdir")
    def test_get_files_in_dir_with_pattern(self, mock_os_path_isdir, mock_os_listdir):
        mock_os_path_isdir.return_value = True
        mock_os_listdir.return_value = ["one.abc", "two.abc", "three.def"]
        file_in_directory = filesystem.get_files_in_directory("test/mock/dir/path/which/does/not/exist",
                                                              ends_with=".abc")
        self.assertItemsEqual(mock_os_listdir.return_value[0:2], file_in_directory)

    @patch("enmutils.lib.filesystem.does_file_exist", return_value=True)
    @patch("__builtin__.open")
    def test_read_lines_from_file__success(self, *_):
        filesystem.read_lines_from_file("mock/test/file/path")

    def test_read_lines_from_file__raises_exception_if_file_does_not_exist(self):
        with self.assertRaises(Exception):
            filesystem.read_lines_from_file("mock/test/file/path/which/does/not/exit")

    def test_get_lines_from_file_raises_runtime_error_if_file_does_not_exist(self):
        self.assertRaises(RuntimeError, filesystem.get_lines_from_file, "mock/test/file/path/which/does/not/exit")

    @patch("__builtin__.open")
    @patch("os.path.exists")
    def test_get_lines_from_file_returns_file_lines_excluding_comments_and_empty_lines_when_file_exists(
            self, mock_os_path_exists, mock_open):
        correct_line_list = ['This is the first line', 'This is the second line', 'The previous line was a blank line']
        mock_os_path_exists.return_value = True
        mock_open.return_value = StringIO("#This is a comment    \n This is the first line \n This is the second line "
                                          "\n            \n The previous line was a blank line")
        self.assertEqual(filesystem.get_lines_from_file("/test/path/mock_file.txt"), correct_line_list)

    def test_get_local_file_checksum_raises_runtime_error_if_file_does_not_exist(self):
        self.assertRaises(RuntimeError, filesystem.get_local_file_checksum, "mock/test/file/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("os.path.exists")
    def test_get_local_file_checksum_raises_runtime_error_when_rc_is_not_0(self, mock_os_path_exists,
                                                                           mock_run_local_cmd):
        mock_run_local_cmd.return_value = self.bad_response
        mock_os_path_exists.return_value = True
        self.assertRaises(RuntimeError, filesystem.get_local_file_checksum, "mock/test/path")

    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("os.path.exists")
    def test_get_local_file_checksum_returns_stdout_when_file_exists_and_rc_is_0(self, mock_os_path_exists,
                                                                                 mock_run_local_cmd):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout="100", elapsed_time=.12)
        mock_os_path_exists.return_value = True
        self.assertEqual(filesystem.get_local_file_checksum("mock/test/path"), "100")

    @patch("enmutils.lib.filesystem.does_file_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_get_local_file_checksum__raises_runtime_error_cannot_parse_checksum(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(ok=True, stdout=["1234"])
        self.assertRaises(RuntimeError, filesystem.get_local_file_checksum, "/test/mock/dir/")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_checksum_raises_runtime_error_if_file_does_not_exist(self, mock_run_remote_cmd,
                                                                                  mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "mock/test/file/path", "mock_host",
                          "mock_user")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_checksum_raises_runtime_error_when_rc_is_not_0(self, mock_run_remote_cmd,
                                                                            mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "mock/test/path", "mock_host", "mock_user")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_checksum_raises_runtime_error_when_stdout_is_None(self, mock_run_remote_cmd,
                                                                               mock_does_remote_file_exist, *_):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=None, elapsed_time=.654)
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "mock/test/path", "mock_host", "mock_user")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_checksum_raises_runtime_error_when_stdout_is_an_empty_string(self, mock_run_remote_cmd,
                                                                                          mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="", elapsed_time=.654)
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "mock/test/path", "mock_host", "mock_user")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_get_remote_file_checksum_returns_checksum_from_stdout_when_rc_is_0_and_password_is_none(
            self, mock_run_remote_cmd, mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="777               mock/test/path", elapsed_time=.432)
        self.assertEqual(filesystem.get_remote_file_checksum("mock/test/file/path", "test_host", "test_user"), "777")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_get_remote_file_checksum_returns_checksum_from_stdout_when_rc_is_0_and_password_is_not_none(
            self, mock_run_remote_cmd, mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="888               mock/test/path", elaped_time=.432)
        self.assertEqual(filesystem.get_remote_file_checksum("mock/test/file/path", "test_host", "test_user",
                                                             "test_password"), "888")

    @patch("enmutils.lib.filesystem.does_remote_file_exist", return_value=False)
    def test_get_remote_file_checksum__raises_runtime_error_file_not_exists(self, *_):
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "mock/test/file/path", "test_host",
                          "test_user", "test_password")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_file_checksum__raises_runtime_error_cannot_parse_remote_file(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=["1234"])
        self.assertRaises(RuntimeError, filesystem.get_remote_file_checksum, "/test/mock/dir/", "test_host",
                          "test_user", "password")

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_get_lines_from_remote_file_raises_exception_when_does_remote_file_exist_returns_false(
            self, mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = False
        self.assertEqual([], filesystem.get_lines_from_remote_file("mock/test/path", "mock_host", "mock_user"))

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_lines_from_remote_file_returns_an_empty_list_when_rc_is_not_0(self, mock_run_remote_cmd,
                                                                               mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = self.bad_response
        self.assertEqual(filesystem.get_lines_from_remote_file("mock/file/path", "test_host", "test_user"), [])

    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_lines_from_remote_file_returns_list_of_lines_from_stdout_when_rc_is_0_and_password_is_none(
            self, mock_run_remote_cmd, mock_does_remote_file_exist):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="This is line 1\nThis is line 2\nThis is line 3",
                                                elapsed_time=.654)
        self.assertEqual(filesystem.get_lines_from_remote_file("mock/file/path", "test_host", "test_user", "password"),
                         ["This is line 1", "This is line 2", "This is line 3"])

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_is_true_no_password(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        self.assertIsNone(filesystem.verify_remote_directory_exists("mock/file/path", "test_host", "test_user"))

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_is_false_password_is_none(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = False
        self.assertRaises(OSError, filesystem.verify_remote_directory_exists, "mock/file/path", "test_host",
                          "test_user", password=None)

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_is_true(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        self.assertIsNone(filesystem.verify_remote_directory_exists("mock/file/path", "test_host", "test_user"))

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_is_false(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = False
        self.assertRaises(OSError, filesystem.verify_remote_directory_exists, "mock/file/path", "test_host",
                          "test_user", password="test_password")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_no_username(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        self.assertRaises(TypeError, filesystem.verify_remote_directory_exists, "mock/file/path", "test_host",
                          password="test_password")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_password_and_no_username(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        self.assertRaises(TypeError, filesystem.verify_remote_directory_exists, "mock/file/path",
                          password="test_password")

    @patch("enmutils.lib.filesystem.does_remote_dir_exist")
    def test_verify_remote_directory_exists_no_params(self, mock_does_remote_dir_exist):
        mock_does_remote_dir_exist.return_value = True
        self.assertRaises(TypeError, filesystem.verify_remote_directory_exists)

    @patch('os.path.join', return_value=["file_path"])
    @patch('os.listdir', return_value=["file"])
    @patch('time.time', return_value=2)
    @patch('re.search', return_value=True)
    @patch('os.stat')
    @patch('enmutils.lib.log.logger.debug')
    @patch('os.remove')
    def test_remove_local_files_over_certain_age__success(self, mock_remove, mock_debug, mock_stat, *_):
        mock_stat.return_value.st_mtime = 0
        filesystem.remove_local_files_over_certain_age("test", "", 1)
        self.assertEqual(mock_remove.call_count, 1)
        mock_debug.assert_called_with("File '['file_path']' removed as it is over 1 seconds old: ['file_path']")

    @patch('os.path.join', return_value=["file_path"])
    @patch('os.listdir', return_value=["file"])
    @patch('time.time', return_value=2)
    @patch('re.search', return_value=True)
    @patch('os.stat')
    @patch('os.remove')
    def test_remove_local_files_over_certain_age__retention_not_exceeded(self, mock_remove, mock_stat, *_):
        mock_stat.return_value.st_mtime = 2
        filesystem.remove_local_files_over_certain_age("test", "", 1)
        self.assertEqual(mock_remove.call_count, 0)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_get_files_with_pattern_in_remote_file(self, mock_does_remote_file_exist, mock_run_remote_cmd):
        expected_list = ["/test/mock/dir/path/directory_one/file_one.txt",
                         "/test/mock/dir/path/directory_two/file_one.txt"]
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(
            rc=0,
            stdout="/test/mock/dir/path/directory_one/file_one.txt\n/test/mock/dir/path/directory_two/file_one.txt\n",
            elapsed_time=.211)
        self.assertEqual(
            filesystem.get_remote_files_with_pattern_in_content("/test/mock/dir/path/", "test_host", "test_user",
                                                                "file_one.txt", "some_pattern", password=None),
            expected_list)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_get_files_with_pattern_in_remote_file_returns_zero_files(self, mock_does_remote_file_exist,
                                                                      mock_run_remote_cmd):
        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="\n", elapsed_time=.211)
        self.assertRaises(RuntimeError, filesystem.get_remote_files_with_pattern_in_content, "/test/mock/dir/path/",
                          "test_host", "test_user", "file_one.txt", "some_pattern", password=None)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.log.logger.debug")
    def test_get_files_with_pattern_in_remote_file_with_errors(self, mock_logger_debug, mock_does_remote_file_exist,
                                                               mock_run_remote_cmd):
        expected_list = ["/test/mock/dir/path/directory_one/file_one.txt",
                         "/test/mock/dir/path/directory_two/file_one.txt"]

        mock_does_remote_file_exist.return_value = True
        resp_text = ("/test/mock/dir/path/directory_one/file_one.txt\negrep: can't open path/directory_one/file_one.txt"
                     "\nfind: stat() error /test/mock/dir/path/directory_three/file_one.txt: Permission denied\n"
                     "/test/mock/dir/path/directory_two/file_one.txt\n")
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout=resp_text, elapsed_time=.211)
        self.assertEqual(
            filesystem.get_remote_files_with_pattern_in_content("/test/mock/dir/path/", "test_host", "test_user",
                                                                "file_one.txt", "some_pattern", password=None),
            expected_list)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_get_files_with_pattern_in_remote_file_with_errors_and_invalid_return_code(
            self, mock_does_remote_file_exist, mock_run_remote_cmd, *_):
        expected_list = ["/test/mock/dir/path/directory_one/file_one.txt",
                         "/test/mock/dir/path/directory_two/file_one.txt"]

        mock_does_remote_file_exist.return_value = True
        mock_run_remote_cmd.return_value = Mock(
            rc=1,
            stdout="/test/mock/dir/path/directory_one/file_one.txt\negrep: can't open ath/directory_one/file_one.txt"
                   "\nfind: stat() error /test/mock/dir/path/directory_three/file_one.txt: Permission denied"
                   "\n/test/mock/dir/path/directory_two/file_one.txt\n", elapsed_time=.211)
        self.assertEqual(
            filesystem.get_remote_files_with_pattern_in_content("/test/mock/dir/path/", "test_host", "test_user",
                                                                "file_one.txt", "some_pattern", password=None),
            expected_list)

    @patch("enmutils.lib.filesystem.does_remote_dir_exist", return_value=False)
    def test_get_files_with_pattern_in_remote_file_with_non_existing_parent_directory(self, *_):
        self.assertRaises(OSError, filesystem.get_remote_files_with_pattern_in_content, "/test/mock/dir/path/",
                          "test_host", "test_user", "file_one.txt", "some_pattern", password=None)

    @patch("enmutils.lib.cache.get_vnf_laf")
    def test_add_sudo_if_cloud_returns_correct_values(self, mock_get_vnf_laf):
        mock_get_vnf_laf.return_value = "1.2.3.4"
        self.assertEqual("sudo ", filesystem.add_sudo_if_cloud('1.2.3.4'))

    def test_add_sudo_if_cloud_defaults_to_empty_string(self):
        self.assertNotEqual("sudo ", filesystem.add_sudo_if_cloud('1.2.3.4'))

    @patch("enmutils.lib.cache.get_vnf_laf")
    def test_add_sudo_if_cloud_defaults_to_empty_string_if_no_matching_hostname(self, mock_get_vnf_laf):
        mock_get_vnf_laf.return_value = "1.2.3.5"
        self.assertNotEqual("sudo ", filesystem.add_sudo_if_cloud(' 1.2.3.4'))

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_hostname(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = Mock(rc=0, stdout="1.2.3.4")
        self.assertEqual("1.2.3.4", filesystem.get_remote_hostname('localhost', 'user', 'password'))

    @patch("enmutils.lib.filesystem._is_remote_host_solaris_system", return_value=True)
    @patch("enmutils.lib.filesystem.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_remote_hostname__solaris(self, mock_run, *_):
        filesystem.get_remote_hostname('', '', '')
        self.assertEqual(1, mock_run.call_count)

    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_get_hostname_returns_empty_hostname_on_failure(self, mock_run_remote_cmd):
        mock_run_remote_cmd.return_value = Mock(ok=False, stdout="1.2.3.4")
        self.assertEqual("", filesystem.get_remote_hostname('localhost', 'user', 'password'))

    @patch("os.path.isdir")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_write_data_to_file_with_logging(self, mock_debug, mock_os_path_isdir):
        mock_os_path_isdir.return_value = False
        filesystem.write_data_to_file('Writing to file', 'mock/test/file', log_to_log_file=True)
        self.assertEqual(mock_debug.call_count - 2, 2)

    @patch("os.path.isdir")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_write_data_to_file_without_logging(self, mock_debug, mock_os_path_isdir):
        mock_os_path_isdir.return_value = False
        filesystem.write_data_to_file('Writing to file', 'mock/test/file', log_to_log_file=False)
        self.assertEqual(mock_debug.call_count - 2, 0)

    @patch("os.path.isdir")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_write_data_to_file_with_file_that_already_exists(self, mock_debug, *_):
        dir_path = os.path.dirname('mock/file2')
        filesystem.create_dir(dir_path)
        self.assertEqual(filesystem.does_dir_exist('mock/file2'), True)
        filesystem.write_data_to_file('Another line', 'mock/file2', log_to_log_file=True)
        mock_debug.assert_called_with('Finished WRITING DATA TO FILE: {0}'.format('mock/file2'))

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("enmutils.lib.filesystem.cache.get_emp", return_value='EMP IP')
    @patch("enmutils.lib.filesystem.cache.is_emp", return_value=True)
    @patch("enmutils.lib.filesystem.cache.get_ms_host", return_value=None)
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_does_file_exist_on_ms_if_cloud_is_successful(self, mock_callback_remote, *_):
        filesystem.does_file_exist_on_ms(file_path="/test/file/path")
        self.assertTrue(mock_callback_remote.called)

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    @patch("enmutils.lib.filesystem.cache.get_emp", return_value='EMP IP')
    @patch("enmutils.lib.filesystem.cache.is_emp", return_value=False)
    @patch("enmutils.lib.filesystem.cache.get_ms_host", return_value='localhost')
    @patch("enmutils.lib.filesystem.does_file_exist")
    def test_does_file_exist_on_ms_if_localhost_is_successful(self, *_):
        filesystem.does_file_exist_on_ms(file_path="/test/file/path")

    @patch("enmutils.lib.filesystem.does_file_exist")
    @patch("enmutils.lib.filesystem.cache.get_emp", return_value='EMP IP')
    @patch("enmutils.lib.filesystem.cache.is_emp", return_value=False)
    @patch("enmutils.lib.filesystem.cache.get_ms_host", return_value='host')
    @patch("enmutils.lib.filesystem.does_remote_file_exist")
    def test_does_file_exist_on_ms_if_ms_host_is_successful(self, mock_callback_remote, *_):
        filesystem.does_file_exist_on_ms(file_path="/test/file/path")
        self.assertTrue(mock_callback_remote.called)

    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=False)
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_dir__no_directory(self, mock_debug, *_):
        filesystem.delete_files_in_dir(dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_dir__remove_specific_directory(self, mock_debug, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=True)
        filesystem.delete_files_in_dir(dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 2)
        self.assertTrue(mock_local_cmd.called)

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_dir__raise_runtime_error(self, mock_debug, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=False, stdout="InvalidPath")
        self.assertRaises(RuntimeError, filesystem.delete_files_in_dir, dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 1)
        self.assertTrue(mock_local_cmd.called)

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=False)
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_directory__no_directory(self, mock_debug, *_):
        filesystem.delete_files_in_directory(dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_directory__remove_specific_directory(self, mock_debug, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=True)
        filesystem.delete_files_in_directory(dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 2)
        self.assertTrue(mock_local_cmd.called)

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.does_dir_exist", return_value=True)
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_delete_files_in_directory__raise_runtime_error(self, mock_debug, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=False, stdout="InvalidPath")
        self.assertRaises(RuntimeError, filesystem.delete_files_in_directory, dir_path="/test/file/path")
        self.assertEqual(mock_debug.call_count, 1)
        self.assertTrue(mock_local_cmd.called)

    @patch('enmutils.lib.filesystem.pwd.getpwnam')
    @patch('enmutils.lib.filesystem.grp.getgrnam')
    @patch('enmutils.lib.filesystem.os.chown')
    def test_change_owner__absolute_path(self, mock_chown, *_):
        filesystem.change_owner(path="/test/file/path", username="root", group_name="admin123")
        self.assertTrue(mock_chown.called)

    @patch('enmutils.lib.filesystem.os.stat')
    @patch('enmutils.lib.filesystem.os.walk', return_value=["home", "enmutils", "shm"])
    @patch('enmutils.lib.filesystem.os.chown')
    def test_change_owner__recursive_path(self, mock_chown, *_):
        filesystem.change_owner(path="/test/file/path", recursive=True)
        self.assertTrue(mock_chown.called)

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.does_remote_file_exist", return_value=False)
    @patch('enmutils.lib.filesystem.log.logger.debug')
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_delete_remote_file__file_deletion_success(self, mock_run_remote_cmd, mock_debug, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0)
        filesystem.delete_remote_file("mock/test/path", "test_host", "test_user", "password")
        mock_debug.assert_called_with("Successfully deleted file mock/test/path on host test_host")

    @patch("enmutils.lib.filesystem.get_remote_hostname")
    @patch("enmutils.lib.filesystem.shell.run_remote_cmd")
    def test_delete_remote_file__file_deletion_raises_runtime_error(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=1, stdout=[1234])
        self.assertRaises(RuntimeError, filesystem.delete_remote_file, "mock/test/path", "test_host", "test_user",
                          "password")

    @patch('enmutils.lib.filesystem.os.walk', return_value=[("mock", ["test/dir"], ["one.abc"]),
                                                            ("mock", ["test/dir"], ["two.abc"])])
    def test_get_files_in_directory_recursively(self, *_):
        result = filesystem.get_files_in_directory_recursively("mock/test/dir/one.abc")
        self.assertEqual(result, set(['mock/one.abc', 'mock/two.abc']))

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch('enmutils.lib.filesystem.log.logger.debug')
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_move_file_or_dir__success(self, mock_local_cmd, mock_log, *_):
        mock_local_cmd.return_value = Mock(ok=True)
        filesystem.move_file_or_dir("mock/source/abc.txt", "mock/destination/")
        mock_log.assert_called_with("Successfully moved file/directory from mock/source/abc.txt to mock/destination/")

    @patch('enmutils.lib.filesystem.log.logger.debug')
    def test_move_file_or_dir__same_path(self, mock_log):
        filesystem.move_file_or_dir("mock/source/abc.txt", "mock/source/abc.txt")
        mock_log.assert_called_with("Could not move file/directory, source and destination paths mock/source/abc.txt "
                                    "are same")

    @patch("enmutils.lib.filesystem.shell.Command")
    @patch("enmutils.lib.filesystem.shell.run_local_cmd")
    def test_move_file_or_dir__raises_runtime_error(self, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=False)
        self.assertRaises(RuntimeError, filesystem.move_file_or_dir, "mock/source/abc.txt",
                          "mock/destination/")

    # read_json_data_from_file test cases
    @patch("enmutils.lib.filesystem.does_file_exist", return_value=True)
    @patch("__builtin__.open")
    @patch("enmutils.lib.filesystem.json.loads")
    @patch("enmutils.lib.filesystem.log.logger.debug")
    def test_read_json_data_from_file__is_successful(self, mock_debug_log, mock_json_loads, *_):
        mock_json_loads.return_value = [{"test_key": "test_value"}]
        self.assertEqual(mock_json_loads.return_value,
                         filesystem.read_json_data_from_file("mock/source/abc.json", raise_error=False))
        self.assertEqual(0, mock_debug_log.call_count)
        self.assertEqual(1, mock_json_loads.call_count)

    @patch("enmutils.lib.filesystem.does_file_exist", return_value=False)
    @patch("__builtin__.open")
    @patch("enmutils.lib.filesystem.json.loads")
    @patch("enmutils.lib.filesystem.log.logger.debug")
    def test_read_json_data_from_file__if_file_not_existed(self, mock_debug_log, mock_json_loads, *_):
        self.assertEqual([], filesystem.read_json_data_from_file("mock/source/abc.json", raise_error=False))
        self.assertEqual(0, mock_debug_log.call_count)
        self.assertEqual(0, mock_json_loads.call_count)

    @patch("enmutils.lib.filesystem.does_file_exist", return_value=True)
    @patch("__builtin__.open")
    @patch("enmutils.lib.filesystem.json.loads")
    @patch("enmutils.lib.filesystem.log.logger.debug")
    def test_read_json_data_from_file__raises_run_time_error(self, mock_debug_log, mock_json_loads, *_):
        mock_json_loads.side_effect = Exception("Something is wrong")
        self.assertRaises(RuntimeError, filesystem.read_json_data_from_file, "mock/source/abc.json", raise_error=True)
        self.assertEqual(0, mock_debug_log.call_count)
        self.assertEqual(1, mock_json_loads.call_count)

    @patch("enmutils.lib.filesystem.does_file_exist", return_value=True)
    @patch("__builtin__.open")
    @patch("enmutils.lib.filesystem.json.loads")
    @patch("enmutils.lib.filesystem.log.logger.debug")
    def test_read_json_data_from_file__log_error_when_raise_error_false(self, mock_debug_log, mock_json_loads, *_):
        mock_json_loads.side_effect = Exception("Something is wrong")
        filesystem.read_json_data_from_file("mock/source/abc.json", raise_error=False)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_json_loads.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
