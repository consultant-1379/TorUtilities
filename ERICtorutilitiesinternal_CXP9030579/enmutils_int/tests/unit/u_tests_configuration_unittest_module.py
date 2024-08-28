#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (ca_01, cbrs_setup, cmevents_nbi_01, cmevents_nbi_02)


class ConfigurationProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow.CmEventsNbi01.execute_flow")
    def test_cmevents_nbi_01_profile_execute_flow__successful(self, mock_execute_flow):
        cmevents_nbi_01.CMEVENTS_NBI_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow.CmEventsNbi02.execute_flow")
    def test_cmevents_nbi_02_profile_execute_flow__successful(self, mock_execute_flow):
        cmevents_nbi_02.CMEVENTS_NBI_02().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.execute_flow")
    def test_cbrs_setup_profile_execute_flow__successful(self, mock_execute_flow):
        cbrs_setup.CBRS_SETUP().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.execute_flow")
    def test_ca_01_profile_execute_flow__successful(self, mock_flow):
        ca_01.CA_01().run()
        self.assertEqual(mock_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
