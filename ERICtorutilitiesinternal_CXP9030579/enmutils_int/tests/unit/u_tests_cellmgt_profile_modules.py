#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (cellmgt_01, cellmgt_02, cellmgt_03, cellmgt_05, cellmgt_07, cellmgt_08,
                                       cellmgt_09, cellmgt_10, cellmgt_11, cellmgt_12, cellmgt_13, cellmgt_14,
                                       cellmgt_15)


class ProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.execute_flow')
    def test_run__cellmgt_01_success(self, mock_flow):
        cellmgt_01.CELLMGT_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.execute_flow')
    def test_run__cellmgt_02_success(self, mock_flow):
        cellmgt_02.CELLMGT_02().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.execute_flow')
    def test_run__cellmgt_03_success(self, mock_flow):
        cellmgt_03.CELLMGT_03().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.execute_flow')
    def test_run__cellmgt_05_success(self, mock_flow):
        cellmgt_05.CELLMGT_05().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.execute_flow')
    def test_run__cellmgt_07_success(self, mock_flow):
        cellmgt_07.CELLMGT_07().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ViewAllLteCellsInTheNetwork.execute_flow')
    def test_run__cellmgt_08_success(self, mock_flow):
        cellmgt_08.CELLMGT_08().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.execute_flow')
    def test_run__cellmgt_09_success(self, mock_flow):
        cellmgt_09.CELLMGT_09().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.execute_flow')
    def test_run__cellmgt_10_success(self, mock_flow):
        cellmgt_10.CELLMGT_10().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellViewRelationsFlow.execute_cell_mgt_11_flow')
    def test_run__cellmgt_11_success(self, mock_flow):
        cellmgt_11.CELLMGT_11().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellViewRelationsFlow.execute_cell_mgt_11_flow')
    def test_run__cellmgt_12_success(self, mock_flow):
        cellmgt_12.CELLMGT_12().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.execute_flow')
    def test_run__cellmgt_13_success(self, mock_flow):
        cellmgt_13.CELLMGT_13().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.execute_flow')
    def test_run__cellmgt_14_success(self, mock_flow):
        cellmgt_14.CELLMGT_14().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.execute_flow')
    def test_run__cellmgt_15_success(self, mock_flow):
        cellmgt_15.CELLMGT_15().run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
