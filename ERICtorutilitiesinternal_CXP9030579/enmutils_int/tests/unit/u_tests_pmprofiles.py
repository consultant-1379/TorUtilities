#!/usr/bin/env python

import unittest2
from mock import patch

from enmutils_int.lib.workload.pm_67 import PM_67
from enmutils_int.lib.workload.pm_68 import PM_68
from enmutils_int.lib.workload.pm_61 import PM_61
from enmutils_int.lib.workload.pm_69 import PM_69
from enmutils_int.lib.workload.pm_74 import PM_74
from enmutils_int.lib.workload.pm_76 import PM_76
from enmutils_int.lib.workload.pm_73 import PM_73
from enmutils_int.lib.workload.pm_75 import PM_75
from enmutils_int.lib.workload.pm_40 import PM_40
from enmutils_int.lib.workload.pm_71 import PM_71
from enmutils_int.lib.workload.pm_72 import PM_72
from testslib import unit_test_utils


class PmProfilesUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.pm61 = PM_61()
        self.pm67 = PM_67()
        self.pm68 = PM_68()
        self.pm69 = PM_69()
        self.pm73 = PM_73()
        self.pm76 = PM_76()
        self.pm74 = PM_74()
        self.pm75 = PM_75()
        self.pm40 = PM_40()
        self.pm71 = PM_71()
        self.pm72 = PM_72()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__doesnt_raise_exception_in_pm61(self, _):
        self.pm61.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm67(self, _):
        self.pm67.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm68(self, _):
        self.pm68.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm69(self, _):
        self.pm69.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm73(self, _):
        self.pm73.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm75(self, _):
        self.pm75.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm76(self, _):
        self.pm76.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm40(self, _):
        self.pm40.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm74(self, _):
        self.pm74.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm72(self, _):
        self.pm72.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run_doesnt_raise_exception_in_pm71(self, _):
        self.pm71.run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
