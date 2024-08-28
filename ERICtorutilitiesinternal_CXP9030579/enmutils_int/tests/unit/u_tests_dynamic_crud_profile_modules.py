import unittest2
from mock import patch

from enmutils_int.lib.workload import (dynamic_crud_01, dynamic_crud_02, dynamic_crud_03, dynamic_crud_04,
                                       dynamic_crud_05)
from testslib import unit_test_utils


class DynamicCrudProfileCoverageUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow.DynamicCrud01Flow.execute_flow')
    def test_run__dynamic_crud_01_success(self, mock_execute):
        dynamic_crud_01.DYNAMIC_CRUD_01().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.execute_flow')
    def test_run__dynamic_crud_02_success(self, mock_execute):
        dynamic_crud_02.DYNAMIC_CRUD_02().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow.DynamicCrud03Flow.execute_flow')
    def test_run__dynamic_crud_03_success(self, mock_execute):
        dynamic_crud_03.DYNAMIC_CRUD_03().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow.DynamicCrud04Flow.execute_flow')
    def test_run__dynamic_crud_04_success(self, mock_execute):
        dynamic_crud_04.DYNAMIC_CRUD_04().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow.DynamicCrud05Flow.execute_flow')
    def test_run__dynamic_crud_05_success(self, mock_execute):
        dynamic_crud_05.DYNAMIC_CRUD_05().run()
        self.assertEqual(1, mock_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
