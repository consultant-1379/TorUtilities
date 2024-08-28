#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (cmexport_01, cmexport_02, cmexport_03, cmexport_05, cmexport_07,
                                       cmexport_08, cmexport_11, cmexport_12, cmexport_13, cmexport_14, cmexport_16,
                                       cmexport_17, cmexport_18, cmexport_19, cmexport_20, cmexport_21, cmexport_22,
                                       cmexport_23, cmexport_25, cmexport_26, cmexport_27)


class ProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_01_success(self, mock_flow):
        cmexport_01.CMEXPORT_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.execute_flow')
    def test_run__cmexport_02_success(self, mock_flow):
        cmexport_02.CMEXPORT_02().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_parallel_flow')
    def test_run__cmexport_03_success(self, mock_flow):
        cmexport_03.CMEXPORT_03().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_05_success(self, mock_flow):
        cmexport_05.CMEXPORT_05().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_07_success(self, mock_flow):
        cmexport_07.CMEXPORT_07().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.execute_flow')
    def test_run__cmexport_08_success(self, mock_flow):
        cmexport_08.CMEXPORT_08().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow.CmExport11.execute_flow')
    def test_run__cmexport_11_success(self, mock_flow):
        cmexport_11.CMEXPORT_11().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_12_success(self, mock_flow):
        cmexport_12.CMEXPORT_12().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_13_success(self, mock_flow):
        cmexport_13.CMEXPORT_13().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_14_success(self, mock_flow):
        cmexport_14.CMEXPORT_14().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.execute_flow')
    def test_run__cmexport_16_success(self, mock_flow):
        cmexport_16.CMEXPORT_16().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.execute_flow')
    def test_run__cmexport_17_success(self, mock_flow):
        cmexport_17.CMEXPORT_17().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_flow')
    def test_run__cmexport_18_success(self, mock_flow):
        cmexport_18.CMEXPORT_18().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_flow')
    def test_run__cmexport_19_success(self, mock_flow):
        cmexport_19.CMEXPORT_19().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_20_success(self, mock_flow):
        cmexport_20.CMEXPORT_20().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_21_success(self, mock_flow):
        cmexport_21.CMEXPORT_21().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_22_success(self, mock_flow):
        cmexport_22.CMEXPORT_22().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow.CmExport23Flow.execute_flow')
    def test_run__cmexport_23_success(self, mock_flow):
        cmexport_23.CMEXPORT_23().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_25_success(self, mock_flow):
        cmexport_25.CMEXPORT_25().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_26_success(self, mock_flow):
        cmexport_26.CMEXPORT_26().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.execute_flow')
    def test_run__cmexport_27_success(self, mock_flow):
        cmexport_27.CMEXPORT_27().run()
        self.assertTrue(mock_flow.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
