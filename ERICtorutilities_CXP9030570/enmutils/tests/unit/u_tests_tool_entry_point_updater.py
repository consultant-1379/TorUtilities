import unittest2
from mock import patch, mock_open

from enmutils.lib import tool_entry_point_updater
from testslib import unit_test_utils


class ToolEntryPointUpdaterUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('__builtin__.open', new_callable=mock_open)
    @patch("enmutils.lib.tool_entry_point_updater.os")
    def test_update_entry_points__success(self, mock_os, mock_open_file, *_):
        mock_os.listdir.return_value = ["file_name"]
        tool_entry_point_updater.update_entry_points()
        self.assertEqual(mock_os.listdir.call_count, 1)
        self.assertEqual(mock_open_file.call_count, 2)

    @patch("enmutils.lib.tool_entry_point_updater.os")
    def test_update_entry_points__raise_exception(self, mock_os, *_):
        mock_os.listdir.return_value = ["file_name"]
        tool_entry_point_updater.update_entry_points()
        self.assertEqual(mock_os.listdir.call_count, 1)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch("enmutils.lib.tool_entry_point_updater.os")
    def test_update_entry_points__file_data_exist(self, mock_os, mock_open_file, *_):
        mock_os.listdir.return_value = ["file_name"]
        mock_open_file.return_value.read.return_value = "root_file_sys"
        tool_entry_point_updater.update_entry_points()
        self.assertEqual(mock_os.listdir.call_count, 1)
        self.assertEqual(mock_open_file.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
