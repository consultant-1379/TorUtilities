#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from testslib import unit_test_utils

from enmutils_int.lib.profile_flows.pm_flows.pm17profile import Pm17Profile
from enmutils_int.lib.workload import pm_17


class Pm17ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.pm_17 = pm_17.PM_17()
        self.profile = Pm17Profile()
        self.profile.STATS_RETENTION = ('param', 666)
        self.profile.CELLTRACE_RETENTION = ('param', 666)
        self.profile.UE_TRACE_RETENTION = ('param', 666)
        self.profile.CTUM_RETENTION = ('param', 666)
        self.profile.EBM_RETENTION = ('param', 666)
        self.profile.SYMBOLIC_LINK_RETENTION = ('param', 666)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.execute_flow')
    def test_run__in_pm_17_is_successful(self, mock_flow):
        self.pm_17.run()
        self.assertTrue(mock_flow.called)

    # execute_flow tests
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.keep_running')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.check_pmic_retention_period')
    def test_good_execute_flow(self, mock_check_retention_val, mock_add_exception, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, True, False]
        self.profile.PM_NBI_RETENTION_PARAMETERS = {'STATS_RETENTION': ("pmicStatisticalFileRetentionPeriodInMinutes", 4320)}
        self.profile.execute_flow()
        self.assertTrue(mock_check_retention_val.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.keep_running')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm17profile.Pm17Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.check_pmic_retention_period')
    def test_execute_flow_check_retentions_failure(self, mock_check_retention_val, mock_add_exception, mock_keep_running, *_):
        self.profile.PM_NBI_RETENTION_PARAMETERS = {'STATS_RETENTION': ("pmicStatisticalFileRetentionPeriodInMinutes", 4320), 's': ("a", 32)}
        mock_check_retention_val.side_effect = Exception('Failed to check retention')
        mock_keep_running.side_effect = [True, True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_check_retention_val.called)
        self.assertTrue(mock_add_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
