#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (nhm_setup, nhm_03, nhm_04, nhm_05, nhm_06, nhm_07, nhm_08, nhm_09,
                                       nhm_10, nhm_11, nhm_12, nhm_13, nhm_14)


class NhmProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.execute_flow")
    def test_nhm_setup_profile_execute_flow__successful(self, mock_flow):
        nhm_setup.NHM_SETUP().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow.Nhm03.execute_flow")
    def test_nhm_profile_nhm_03_execute_flow__successful(self, mock_flow):
        nhm_03.NHM_03().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_04_flow.Nhm04.execute_flow")
    def test_nhm_profile_nhm_04_execute_flow__successful(self, mock_flow):
        nhm_04.NHM_04().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.Nhm05.execute_flow")
    def test_nhm_profile_nhm_05_execute_flow__successful(self, mock_flow):
        nhm_05.NHM_05().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_06_flow.Nhm06.execute_flow")
    def test_nhm_profile_nhm_06_execute_flow__successful(self, mock_flow):
        nhm_06.NHM_06().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.Nhm07.execute_flow")
    def test_nhm_profile_nhm_07_execute_flow__successful(self, mock_flow):
        nhm_07.NHM_07().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow.Nhm08.execute_flow")
    def test_nhm_profile_nhm_08_execute_flow__successful(self, mock_flow):
        nhm_08.NHM_08().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_09_flow.Nhm09.execute_flow")
    def test_nhm_profile_nhm_09_execute_flow__successful(self, mock_flow):
        nhm_09.NHM_09().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow.Nhm10.execute_flow")
    def test_nhm_profile_nhm_10_execute_flow__successful(self, mock_flow):
        nhm_10.NHM_10().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow.Nhm11.execute_flow")
    def test_nhm_profile_nhm_11_execute_flow__successful(self, mock_flow):
        nhm_11.NHM_11().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow.Nhm12.execute_flow")
    def test_nhm_profile_nhm_12_execute_flow__successful(self, mock_flow):
        nhm_12.NHM_12().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow.Nhm13Flow.execute_flow")
    def test_nhm_profile_nhm_13_execute_flow__successful(self, mock_flow):
        nhm_13.NHM_13().run()
        self.assertEquals(mock_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow.Nhm14Flow.execute_flow")
    def test_nhm_profile_nhm_14_execute_flow__successful(self, mock_flow):
        nhm_14.NHM_14().run()
        self.assertEquals(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
