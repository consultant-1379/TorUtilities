#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (netex_01, netex_02, netex_03, netex_04, netex_05, netex_07)


class NetexProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.execute_flow")
    def test_netex_profile_netex_01_execute_flow__successful(self, mock_flow):
        netex_01.NETEX_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.execute_flow")
    def test_netex_profile_netex_02_execute_flow__successful(self, mock_flow):
        netex_02.NETEX_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.execute_flow")
    def test_netex_profile_netex_03_execute_flow__successful(self, mock_flow):
        netex_03.NETEX_03().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.execute_flow")
    def test_netex_profile_netex_04_execute_flow__successful(self, mock_flow):
        netex_04.NETEX_04().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.execute_flow")
    def test_netex_profile_netex_05_execute_flow__successful(self, mock_flow):
        netex_05.NETEX_05().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.execute_flow")
    def test_netex_profile_netex_07_execute_flow__successful(self, mock_flow):
        netex_07.NETEX_07().run()
        self.assertEquals(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
