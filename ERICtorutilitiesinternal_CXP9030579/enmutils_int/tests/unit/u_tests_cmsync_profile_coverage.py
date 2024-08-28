#!/usr/bin/env python
import unittest2
from mock import patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils_int.lib.workload import (cmsync_01, cmsync_02, cmsync_04, cmsync_06, cmsync_11,
                                       cmsync_15, cmsync_19, cmsync_20, cmsync_21, cmsync_22, cmsync_23, cmsync_24,
                                       cmsync_25, cmsync_26, cmsync_27, cmsync_28, cmsync_29, cmsync_30, cmsync_32,
                                       cmsync_33, cmsync_34, cmsync_35, cmsync_37, cmsync_38, cmsync_39, cmsync_40,
                                       cmsync_41, cmsync_42, cmsync_43, cmsync_44, cmsync_45, cmsync_setup)
from testslib import unit_test_utils


class CmSyncProfileCoverageUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload.cmsync_01.CMSYNC_01.execute_flow')
    def test_cmsync_01__execute_flow(self, mock_execute):
        flow = cmsync_01.CMSYNC_01()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_02.CMSYNC_02.execute_flow')
    def test_cmsync_02__execute_flow(self, mock_execute):
        flow = cmsync_02.CMSYNC_02()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_04.CMSYNC_04.execute_flow')
    def test_cmsync_04__execute_flow(self, mock_execute):
        flow = cmsync_04.CMSYNC_04()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_06.CMSYNC_06.execute_flow')
    def test_cmsync_06__execute_flow(self, mock_execute):
        flow = cmsync_06.CMSYNC_06()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_11.CMSYNC_11.execute_flow')
    def test_cmsync_11__execute_flow(self, mock_execute):
        flow = cmsync_11.CMSYNC_11()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_15.CMSYNC_15.execute_flow')
    def test_cmsync_15__execute_flow(self, mock_execute):
        flow = cmsync_15.CMSYNC_15()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_19.CMSYNC_19.execute_flow')
    def test_cmsync_19__execute_flow(self, mock_execute):
        flow = cmsync_19.CMSYNC_19()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_20.CMSYNC_20.execute_flow')
    def test_cmsync_20__execute_flow(self, mock_execute):
        flow = cmsync_20.CMSYNC_20()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_21.CMSYNC_21.execute_flow')
    def test_cmsync_21__execute_flow(self, mock_execute):
        flow = cmsync_21.CMSYNC_21()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_22.CMSYNC_22.execute_flow')
    def test_cmsync_22__execute_flow(self, mock_execute):
        flow = cmsync_22.CMSYNC_22()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_23.CMSYNC_23.execute_flow')
    def test_cmsync_23__execute_flow(self, mock_execute):
        flow = cmsync_23.CMSYNC_23()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_24.CMSYNC_24.execute_flow')
    def test_cmsync_24__execute_flow(self, mock_execute):
        flow = cmsync_24.CMSYNC_24()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_25.CMSYNC_25.execute_flow')
    def test_cmsync_25__execute_flow(self, mock_execute):
        flow = cmsync_25.CMSYNC_25()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_26.CMSYNC_26.execute_flow')
    def test_cmsync_26__execute_flow(self, mock_execute):
        flow = cmsync_26.CMSYNC_26()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_27.CMSYNC_27.execute_flow')
    def test_cmsync_27__execute_flow(self, mock_execute):
        flow = cmsync_27.CMSYNC_27()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_28.CMSYNC_28.execute_flow')
    def test_cmsync_28__execute_flow(self, mock_execute):
        flow = cmsync_28.CMSYNC_28()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_29.CMSYNC_29.execute_flow')
    def test_cmsync_29__execute_flow(self, mock_execute):
        flow = cmsync_29.CMSYNC_29()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_30.CMSYNC_30.execute_flow')
    def test_cmsync_30__execute_flow(self, mock_execute):
        flow = cmsync_30.CMSYNC_30()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_32.CMSYNC_32.execute_flow')
    def test_cmsync_32__execute_flow(self, mock_execute):
        flow = cmsync_32.CMSYNC_32()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_33.CMSYNC_33.execute_flow')
    def test_cmsync_33__execute_flow(self, mock_execute):
        flow = cmsync_33.CMSYNC_33()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_34.CMSYNC_34.execute_flow')
    def test_cmsync_34__execute_flow(self, mock_execute):
        flow = cmsync_34.CMSYNC_34()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_35.CMSYNC_35.execute_flow')
    def test_cmsync_35__execute_flow(self, mock_execute):
        flow = cmsync_35.CMSYNC_35()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_37.CMSYNC_37.execute_flow')
    def test_cmsync_37__execute_flow(self, mock_execute):
        flow = cmsync_37.CMSYNC_37()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_38.CMSYNC_38.execute_flow')
    def test_cmsync_38__execute_flow(self, mock_execute):
        flow = cmsync_38.CMSYNC_38()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_39.CMSYNC_39.execute_flow')
    def test_cmsync_39__execute_flow(self, mock_execute):
        flow = cmsync_39.CMSYNC_39()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_40.CMSYNC_40.execute_flow')
    def test_cmsync_40__execute_flow(self, mock_execute):
        flow = cmsync_40.CMSYNC_40()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_41.CMSYNC_41.execute_flow')
    def test_cmsync_41__execute_flow(self, mock_execute):
        flow = cmsync_41.CMSYNC_41()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_42.CMSYNC_42.execute_flow')
    def test_cmsync_42__execute_flow(self, mock_execute):
        flow = cmsync_42.CMSYNC_42()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_43.CMSYNC_43.execute_flow')
    def test_cmsync_43__execute_flow(self, mock_execute):
        flow = cmsync_43.CMSYNC_43()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_44.CMSYNC_44.execute_flow')
    def test_cmsync_44__execute_flow(self, mock_execute):
        flow = cmsync_44.CMSYNC_44()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_45.CMSYNC_45.execute_flow')
    def test_cmsync_45__execute_flow(self, mock_execute):
        flow = cmsync_45.CMSYNC_45()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.cmsync_setup.CMSYNC_SETUP.execute_flow')
    def test_cmsync_setup__execute_flow(self, mock_execute):
        flow = cmsync_setup.CMSYNC_SETUP()
        flow.run()
        self.assertEqual(1, mock_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
