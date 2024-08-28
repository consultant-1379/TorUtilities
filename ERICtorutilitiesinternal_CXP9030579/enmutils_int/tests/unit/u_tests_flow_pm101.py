#!/usr/bin/env python
import unittest2

from mock import patch, PropertyMock
from testslib import unit_test_utils

from enmutils_int.lib.profile_flows.pm_flows.pm101profile import Pm101Profile
from enmutils_int.lib.workload import pm_101
from enmutils.lib.exceptions import EnvironError


class Pm101ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.pm_101 = pm_101.PM_101()
        self.profile = Pm101Profile()
        self.profile.CELLTRACE_AND_EBM_RETENTION = {"pmicCelltraceFileRetentionPeriodInMinutes": [360, 300, 240],
                                                    "pmicEbmFileRetentionPeriodInMinutes": [300, 240, 180]}
        self.profile.SCHEDULE_SLEEP = 1
        self.profile.SCHEDULED_TIMES_STRINGS = ["00:00:00"]
        self.profile.RETENTION_VALUES_SLEEP_TIME = zip(self.profile.CELLTRACE_AND_EBM_RETENTION['pmicEbmFileRetentionPeriodInMinutes'],
                                                       self.profile.CELLTRACE_AND_EBM_RETENTION['pmicCelltraceFileRetentionPeriodInMinutes'], [4, 0.5, 0.5])

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.execute_flow')
    def test_run__in_pm_101_is_successful(self, mock_execute_flow):
        self.pm_101.run()
        self.assertTrue(mock_execute_flow.called)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile._sleep_until')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.check_profile_memory_usage')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.perform_pib_operations')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.keep_running')
    def test_execute_flow__is_successful(self, mock_keep_running, mock_perform_pib_operations, *_):
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_perform_pib_operations.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile._sleep_until')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.keep_running')
    def test_execute_flow__raises_EnvironError_when_calling_updating_pib_parameter_value(self,
                                                                                         mock_keep_running,
                                                                                         mock_update_pib_parameter_on_enm,
                                                                                         *_):
        mock_update_pib_parameter_on_enm.side_effect = Exception(EnvironError("Unable to update PIB parameter"))
        mock_keep_running.side_effect = [True, False]
        with self.assertRaises(EnvironError):
            self.profile.execute_flow()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.update_pib_parameter_on_enm')
    def test_update_pib_parameter__is_successful(self, mock_update_pib_parameter_on_enm, *_):
        celltrace_retention = self.profile.CELLTRACE_AND_EBM_RETENTION['pmicCelltraceFileRetentionPeriodInMinutes'][0]
        ebm_retention = self.profile.CELLTRACE_AND_EBM_RETENTION['pmicEbmFileRetentionPeriodInMinutes'][0]
        self.profile.update_pib_parameter(celltrace_retention, ebm_retention)
        self.assertTrue(mock_update_pib_parameter_on_enm.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.add_error_as_exception')
    def test_update_pib_parameter__raises_EnvironError_when_calling_updating_pib_parameter_value(self, mock_add_exception, mock_update_pib_parameter_on_enm,
                                                                                                 mock_log_debug):
        mock_update_pib_parameter_on_enm.side_effect = Exception(EnvironError("Unable to update PIB parameter"))
        celltrace_retention = self.profile.CELLTRACE_AND_EBM_RETENTION['pmicCelltraceFileRetentionPeriodInMinutes'][0]
        ebm_retention = self.profile.CELLTRACE_AND_EBM_RETENTION['pmicEbmFileRetentionPeriodInMinutes'][0]
        self.profile.update_pib_parameter(celltrace_retention, ebm_retention)
        self.assertTrue(mock_update_pib_parameter_on_enm.called)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(mock_log_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.update_pib_parameter')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile.check_profile_memory_usage')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.Pm101Profile._log_when_sleeping_for_gt_four_hours', return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm101profile.time.sleep', return_value=None)
    def test_perform_pib_operations__is_successful(self, mock_sleep, *_):
        self.profile.perform_pib_operations()
        mock_sleep.assert_called_with(60 * 60 * 0.5)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
