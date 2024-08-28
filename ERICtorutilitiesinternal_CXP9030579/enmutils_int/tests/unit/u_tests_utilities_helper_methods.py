#!/usr/bin/env python

import unittest2

from mock import Mock, patch
from testslib import unit_test_utils
from enmutils_int.bin.utilities_helper_methods import append_history_of_commands


class UtilitiesHelperMethodsUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.bin.utilities_helper_methods.log.logger.debug")
    @patch("enmutils_int.bin.utilities_helper_methods.filesystem.write_data_to_file")
    @patch("enmutils_int.bin.utilities_helper_methods.shell.run_local_cmd")
    def test_append_history_of_commands__in_bashrc(self, mock_cmd, mock_write, mock_debug):
        response = Mock()
        response.ok = True
        mock_cmd.return_value = response
        append_history_of_commands()
        self.assertTrue(mock_cmd.call_count, 2)
        self.assertEqual(mock_write.call_count, 1)
        self.assertTrue(mock_debug.call_count, 2)

    @patch("enmutils_int.bin.utilities_helper_methods.log.logger.debug")
    @patch("enmutils_int.bin.utilities_helper_methods.filesystem.write_data_to_file")
    @patch("enmutils_int.bin.utilities_helper_methods.shell.run_local_cmd")
    def test_append_history_of_commands__not_in_bashrc(self, mock_cmd, mock_write, mock_debug):
        response = Mock()
        response.ok = False
        mock_cmd.return_value = response
        append_history_of_commands()
        self.assertTrue(mock_cmd.call_count, 3)
        self.assertEqual(mock_write.call_count, 1)
        self.assertTrue(mock_debug.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
