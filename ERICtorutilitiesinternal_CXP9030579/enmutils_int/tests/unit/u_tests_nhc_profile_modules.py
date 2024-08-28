#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (nhc_01, nhc_02, nhc_04)


class NhcProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow.Nhc01.execute_nhc_01_flow")
    def test_nhc_profile_nhc_01_execute_flow__successful(self, mock_flow):
        nhc_01.NHC_01().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.execute_nhc_02_flow")
    def test_nhc_profile_nhc_02_execute_flow__successful(self, mock_flow):
        nhc_02.NHC_02().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.execute_nhc_04_flow")
    def test_nhc_profile_nhc_04_execute_flow__successful(self, mock_flow):
        nhc_04.NHC_04().run()
        self.assertEquals(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
