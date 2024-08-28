#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (launcher_01, launcher_02, launcher_03)


class LauncherProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.execute_flow")
    def test_launcher_profile_launcher_01_execute_flow__successful(self, mock_flow):
        launcher_01.LAUNCHER_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.execute_flow")
    def test_launcher_profile_launcher_02_execute_flow__successful(self, mock_flow):
        launcher_02.LAUNCHER_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.execute_flow")
    def test_launcher_profile_launcher_03_execute_flow__successful(self, mock_flow):
        launcher_03.LAUNCHER_03().run()
        self.assertEquals(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
