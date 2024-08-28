#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (cmimport_01, cmimport_02, cmimport_03, cmimport_04, cmimport_05,
                                       cmimport_08, cmimport_10, cmimport_11, cmimport_12, cmimport_13, cmimport_14,
                                       cmimport_15, cmimport_16, cmimport_17, cmimport_18, cmimport_19, cmimport_20,
                                       cmimport_21, cmimport_22, cmimport_23, cmimport_24, cmimport_25, cmimport_26,
                                       cmimport_27, cmimport_28, cmimport_29, cmimport_30, cmimport_31, cmimport_32,
                                       cmimport_33, cmimport_34)


class ProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_01_success(self, mock_flow):
        cmimport_01.CMIMPORT_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_02_success(self, mock_flow):
        cmimport_02.CMIMPORT_02().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_03_success(self, mock_flow):
        cmimport_03.CMIMPORT_03().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_04_success(self, mock_flow):
        cmimport_04.CMIMPORT_04().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_05_success(self, mock_flow):
        cmimport_05.CMIMPORT_05().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.execute_flow')
    def test_run__cmimport_08_success(self, mock_flow):
        cmimport_08.CMIMPORT_08().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_10_success(self, mock_flow):
        cmimport_10.CMIMPORT_10().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_11_success(self, mock_flow):
        cmimport_11.CMIMPORT_11().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_12_success(self, mock_flow):
        cmimport_12.CMIMPORT_12().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.execute_flow')
    def test_run__cmimport_13_success(self, mock_flow):
        cmimport_13.CMIMPORT_13().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_14_success(self, mock_flow):
        cmimport_14.CMIMPORT_14().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.execute_flow')
    def test_run__cmimport_15_success(self, mock_flow):
        cmimport_15.CMIMPORT_15().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_16_success(self, mock_flow):
        cmimport_16.CMIMPORT_16().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_17_success(self, mock_flow):
        cmimport_17.CMIMPORT_17().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_18_success(self, mock_flow):
        cmimport_18.CMIMPORT_18().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_19_success(self, mock_flow):
        cmimport_19.CMIMPORT_19().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_20_success(self, mock_flow):
        cmimport_20.CMIMPORT_20().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_21_success(self, mock_flow):
        cmimport_21.CMIMPORT_21().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'execute_flow')
    def test_run__cmimport_22_success(self, mock_flow):
        cmimport_22.CMIMPORT_22().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.execute_flow')
    def test_run__cmimport_23_success(self, mock_flow):
        cmimport_23.CMIMPORT_23().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_24_success(self, mock_flow):
        cmimport_24.CMIMPORT_24().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_25_success(self, mock_flow):
        cmimport_25.CMIMPORT_25().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_26_success(self, mock_flow):
        cmimport_26.CMIMPORT_26().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'execute_flow')
    def test_run__cmimport_27_success(self, mock_flow):
        cmimport_27.CMIMPORT_27().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_28_success(self, mock_flow):
        cmimport_28.CMIMPORT_28().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_29_success(self, mock_flow):
        cmimport_29.CMIMPORT_29().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_30_success(self, mock_flow):
        cmimport_30.CMIMPORT_30().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.execute_cmimport_common_flow')
    def test_run__cmimport_31_success(self, mock_flow):
        cmimport_31.CMIMPORT_31().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_32_success(self, mock_flow):
        cmimport_32.CMIMPORT_32().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_33_success(self, mock_flow):
        cmimport_33.CMIMPORT_33().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'execute_cmimport_common_flow')
    def test_run__cmimport_34_success(self, mock_flow):
        cmimport_34.CMIMPORT_34().run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
