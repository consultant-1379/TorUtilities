#!/usr/bin/python

import unittest2
from mock import patch

from enmutils_int.lib.ddp_info_logging import update_cm_ddp_info_log_entry, LOG_FILES
from testslib import unit_test_utils


class DDPInfoLoggingUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.ddp_info_logging.shell.run_local_cmd')
    @patch('enmutils_int.lib.ddp_info_logging.shell.Command')
    @patch('enmutils_int.lib.ddp_info_logging.filesystem.write_data_to_file')
    def test_update_cm_ddp_info_log_entry__removes_old_entry_and_updates(self, mock_write, mock_cmd, _):
        profile_name = "CMIMPORT_00"
        update_cm_ddp_info_log_entry(profile_name, profile_name)
        mock_cmd.assert_called_with("sed -i '/{1}/d' {0}".format(LOG_FILES.get("CMIMPORT"), profile_name))
        mock_write.assert_called_with(profile_name, LOG_FILES.get("CMIMPORT"), append=True, log_to_log_file=False)

    @patch('enmutils_int.lib.ddp_info_logging.shell.run_local_cmd')
    @patch('enmutils_int.lib.ddp_info_logging.shell.Command')
    @patch('enmutils_int.lib.ddp_info_logging.filesystem.write_data_to_file', side_effect=Exception("Error"))
    def test_update_cm_ddp_info_log_entry__logs_failure(self, mock_write, *_):
        update_cm_ddp_info_log_entry("CMSYNC_00", "Log entry")
        mock_write.assert_called_with("Log entry", LOG_FILES.get("CMSYNC"), append=True, log_to_log_file=False)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
