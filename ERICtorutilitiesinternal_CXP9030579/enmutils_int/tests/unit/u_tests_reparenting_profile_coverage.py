import unittest2
from mock import patch

from enmutils_int.lib.workload import (reparenting_01, reparenting_02, reparenting_03, reparenting_04, reparenting_05,
                                       reparenting_06, reparenting_07, reparenting_08, reparenting_09, reparenting_10,
                                       reparenting_11, reparenting_12)
from testslib import unit_test_utils


class ReparentingProfileCoverageUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload.reparenting_01.Reparenting01Flow.execute_flow')
    def test_reparenting_01__run(self, mock_execute):
        reparenting_01.REPARENTING_01().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_02.Reparenting02Flow.execute_flow')
    def test_reparenting_02__run(self, mock_execute):
        reparenting_02.REPARENTING_02().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_03.Reparenting03Flow.execute_flow')
    def test_reparenting_03__run(self, mock_execute):
        reparenting_03.REPARENTING_03().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_04.Reparenting04Flow.execute_flow')
    def test_reparenting_04__run(self, mock_execute):
        reparenting_04.REPARENTING_04().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_05.Reparenting05Flow.execute_flow')
    def test_reparenting_05__run(self, mock_execute):
        reparenting_05.REPARENTING_05().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_06.Reparenting06Flow.execute_flow')
    def test_reparenting_06__run(self, mock_execute):
        reparenting_06.REPARENTING_06().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_07.Reparenting07Flow.execute_flow')
    def test_reparenting_07__run(self, mock_execute):
        reparenting_07.REPARENTING_07().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_08.Reparenting08Flow.execute_flow')
    def test_reparenting_08__run(self, mock_execute):
        reparenting_08.REPARENTING_08().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_09.Reparenting09Flow.execute_flow')
    def test_reparenting_09__run(self, mock_execute):
        reparenting_09.REPARENTING_09().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_10.Reparenting10Flow.execute_flow')
    def test_reparenting_10__run(self, mock_execute):
        reparenting_10.REPARENTING_10().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_11.Reparenting11Flow.execute_flow')
    def test_reparenting_11__run(self, mock_execute):
        reparenting_11.REPARENTING_11().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.workload.reparenting_12.Reparenting12Flow.execute_flow')
    def test_reparenting_12__run(self, mock_execute):
        reparenting_12.REPARENTING_12().run()
        self.assertEqual(1, mock_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
