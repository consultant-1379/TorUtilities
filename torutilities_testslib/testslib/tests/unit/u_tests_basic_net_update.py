#!/usr/bin/env python

import sys
import unittest2
from mock import patch, Mock, mock_open
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils
from testslib.bin import basic_net_update
from enmutils_int.lib.common_utils import get_internal_file_path_for_import

path = Mock()
test_line_1 = ("'AID_01': {UPDATE: 0, SUPPORTED: True, NOTE: '-', PRIORITY: 2}\n")
test_line_2 = ("'AID_02': {UPDATE: 0, SUPPORTED: False, NOTE: '-', PRIORITY: 2}\n")
test_line_3 = ("'AID_03': {UPDATE: 0, SUPPORTED: False, NOTE: MANUAL, PRIORITY: 2}\n")
test_list = [test_line_1, test_line_2, test_line_3]


class BasicUpdateUnitTests(ParameterizedTestCase):

    def setUp(self):

        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    # Checks if we have moved Update,Supported,Note into different lines
    def test_if_lines_are_broken_in_basic(self):
        path = get_internal_file_path_for_import("lib", "nrm_default_configurations", "basic_network.py").strip()
        with open(path, "r") as f:
            lines = f.readlines()
        for line in lines:
            if "UPDATE: " in line and any(c not in line for c in ("SUPPORTED: ", "NOTE: ")):
                # With the exception of SHM_SETUP, due to its large comment in Notes
                if all(c in line for c in ("SUPPORTED: ", "SHM_SETUP", "UPDATE")):
                    continue
                else:
                    raise Exception("Broken line found in basic file in line {}".format(line))

    def test_increment_update_success(self):
        test_file = Mock()
        test_file.write = Mock()
        basic_net_update.increment_update(test_file, test_line_1)
        test_file.write.assert_called_with("'AID_01': {UPDATE: 1, SUPPORTED: True, NOTE: '-', PRIORITY: 2}\n")

    @patch("testslib.bin.basic_net_update.get_categories",)
    @patch("testslib.bin.basic_net_update.get_all_profile_names", return_value=["pm_01"])
    def test_validate_arguments_removes_duplicates(self, *_):
        output = basic_net_update.validate_arguments(["PM_01", "PM_01"])
        self.assertEqual(output, ["PM_01"])

    @patch("testslib.bin.basic_net_update.get_categories", return_value=["pm"])
    @patch("testslib.bin.basic_net_update.get_all_profile_names", return_value=["pm_01", "pm_02", "amos_01"])
    def test_validate_arguments_removes_conflicting_names(self, *_):
        output = basic_net_update.validate_arguments(["PM", "PM_01", "PM_02", "AMOS_01"])
        self.assertEqual(output, ["PM", "AMOS_01"])

    @patch("testslib.bin.basic_net_update.get_categories")
    @patch("testslib.bin.basic_net_update.get_all_profile_names")
    def test_validate_arguments_raises_exception_on_invalid_names(self, *_):
        with self.assertRaises(Exception):
            basic_net_update.validate_arguments(["P"])

    @patch("testslib.bin.basic_net_update.read_lines_from_file", return_value=test_list)
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("testslib.bin.basic_net_update.increment_update")
    def test_increment_all_success(self, mock_increment, *_):
        basic_net_update.increment_all(path)
        self.assertEqual(mock_increment.call_count, 1)

    @patch("testslib.bin.basic_net_update.read_lines_from_file", return_value=test_list)
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("testslib.bin.basic_net_update.increment_update")
    def test_increment_all_inc_unsupport_success(self, mock_increment, *_):
        basic_net_update.increment_all(path, inc_unsupported=True)
        self.assertEqual(mock_increment.call_count, 2)

    @patch("testslib.bin.basic_net_update.read_lines_from_file", return_value=test_list)
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("testslib.bin.basic_net_update.increment_update")
    def test_increment_category_success(self, mock_increment, *_):
        basic_net_update.increment_category("AID", path)
        self.assertEqual(mock_increment.call_count, 1)

    @patch("testslib.bin.basic_net_update.read_lines_from_file", return_value=test_list)
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("testslib.bin.basic_net_update.increment_update")
    def test_increment_category_inc_unsupported_success(self, mock_increment, *_):
        basic_net_update.increment_category("AID_02", path, inc_unsupported=True)
        self.assertEqual(mock_increment.call_count, 1)

    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("testslib.bin.basic_net_update.increment_all", side_effect=Exception)
    @patch("shutil.move")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_restore_on_exception(self, mock_handler, mock_move, *_):
        sys.argv = ["./basic_net_update.py", "update"]
        basic_net_update.cli()
        self.assertTrue(mock_handler.called)
        self.assertTrue(mock_move.called)

    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("os.remove")
    @patch("shutil.copy2", side_effect=IOError("Can't find file"))
    @patch("shutil.move")
    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("testslib.bin.basic_net_update.increment_all")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_catches_IOERROR__when_file_not_found_during_copy2(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "update"]
        basic_net_update.cli()
        mock_handler.assert_called_with("basic_net_update", msg="Can't find file")

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("shutil.move")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.exception.handle_exception")
    @patch("enmutils.lib.exception.handle_invalid_argument")
    def test_cli_errors_on_invalid_arg(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "asd"]
        basic_net_update.cli()
        self.assertTrue(mock_handler.called)

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("testslib.bin.basic_net_update.increment_all")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_all_success(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "update"]
        basic_net_update.cli()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("testslib.bin.basic_net_update.validate_arguments", return_value="AMOS")
    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("testslib.bin.basic_net_update.increment_category")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_category_success(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "update", "amos"]
        basic_net_update.cli()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("testslib.bin.basic_net_update.increment_all")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_all_inc_all_success(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "update", "--inc-all"]
        basic_net_update.cli()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("testslib.bin.basic_net_update.validate_arguments", return_value="AMOS")
    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("testslib.bin.basic_net_update.increment_category")
    @patch("enmutils.lib.exception.handle_exception")
    def test_cli_category_inc_all_success(self, mock_handler, *_):
        sys.argv = ["./basic_net_update.py", "update", "amos", "--inc-all"]
        basic_net_update.cli()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.common_utils.get_internal_file_path_for_import")
    @patch("os.remove")
    @patch("shutil.copy2")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.global_init")
    @patch("testslib.bin.basic_net_update.increment_all")
    def test_cli_raises_system_exit_when_help_is_called(self, *_):
        with self.assertRaises(SystemExit):
            sys.argv = ["./basic_net_update.py", "update", "--help"]
            basic_net_update.cli()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
