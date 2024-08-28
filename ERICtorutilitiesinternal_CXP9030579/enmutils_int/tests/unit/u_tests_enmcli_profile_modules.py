#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (enmcli_01, enmcli_02, enmcli_03, enmcli_05, enmcli_06, enmcli_07,
                                       enmcli_08)


class EnmCliProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.execute_flow")
    def test_enmcli_profile_enmcli_01_execute_flow__successful(self, mock_flow):
        enmcli_01.ENMCLI_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.execute_flow")
    def test_enmcli_profile_enmcli_02_execute_flow__successful(self, mock_flow):
        enmcli_02.ENMCLI_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.execute_flow")
    def test_enmcli_profile_enmcli_03_execute_flow__successful(self, mock_flow):
        enmcli_03.ENMCLI_03().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.execute_flow")
    def test_enmcli_profile_enmcli_05_execute_flow__successful(self, mock_flow):
        enmcli_05.ENMCLI_05().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_06_flow.EnmCli06Flow.execute_flow")
    def test_enmcli_profile_enmcli_06_execute_flow__successful(self, mock_flow):
        enmcli_06.ENMCLI_06().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708.ENMCLI0708Flow.execute_flow")
    def test_enmcli_profile_enmcli_07_execute_flow__successful(self, mock_flow):
        enmcli_07.ENMCLI_07().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.execute_flow")
    def test_enmcli_profile_enmcli_08_execute_flow__successful(self, mock_flow):
        enmcli_08.ENMCLI_08().run()
        self.assertEquals(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
