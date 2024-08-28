#!/usr/bin/env python
import unittest2

from testslib import unit_test_utils

from enmutils_int.lib.workload import (bur_02, enmcli_04,
                                       esm_02, fm_23, fm_24, fm_28, fm_29, lcm_01, migration_01, migration_02,
                                       migration_03, pm_35)


class PlaceholderProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_bur_02_profile_execute_flow__successful(self):
        bur_02.BUR_02().run()

    def test_enmcli_04_profile_execute_flow__successful(self):
        enmcli_04.ENMCLI_04().run()

    def test_esm_02_profile_execute_flow__successful(self):
        esm_02.ESM_02().run()

    def test_fm_23_profile_execute_flow__successful(self):
        fm_23.FM_23().run()

    def test_fm_24_profile_execute_flow__successful(self):
        fm_24.FM_24().run()

    def test_fm_28_profile_execute_flow__successful(self):
        fm_28.FM_28().run()

    def test_fm_29_profile_execute_flow__successful(self):
        fm_29.FM_29().run()

    def test_lcm_01_profile_execute_flow__successful(self):
        lcm_01.LCM_01().run()

    def test_migration_01_profile_execute_flow__successful(self):
        migration_01.MIGRATION_01().run()

    def test_migration_02_profile_execute_flow__successful(self):
        migration_02.MIGRATION_02().run()

    def test_migration_03_profile_execute_flow__successful(self):
        migration_03.MIGRATION_03().run()

    def test_pm_35_profile_execute_flow__successful(self):
        pm_35.PM_35().run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
