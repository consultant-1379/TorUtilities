#!/usr/bin/env python
import unittest2
from mock import Mock, patch
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow import CmExport08
from testslib import unit_test_utils


class Cmexport08UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.users = [Mock(), Mock()]
        self.nodes = [Mock(), Mock()]
        self.flow = CmExport08()
        self.flow.TOTAL_NODES = 5
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['CM_REST_Administrator']
        self.flow.NUMBER_OF_EXPORTS = 2
        self.flow.NUMBER_OF_CELLS = 3
        self.flow.FILETYPE = 'dynamic'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_export_object')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.'
           'get_nodes_with_required_number_of_cells')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.exchange_nodes')
    def test_execute_flow_cmexport_08_is_successful(self, mock_exchange_nodes,
                                                    mock_three_cell, mock_cm_export,
                                                    mock_execute_threads, mock_add_error, *_):
        self.flow.NAME = "CMEXPORT_08"
        mock_three_cell.return_value = [Mock(), Mock()]
        export = Mock()
        mock_cm_export.return_value = export
        with patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_users') as mock_create_users:
            self.flow.execute_flow()
            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_exchange_nodes.called)
            self.assertTrue(mock_three_cell.called)
            self.assertTrue(mock_cm_export.called)
            self.assertTrue(mock_execute_threads.called)
            self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_export_object')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.create_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.'
           'get_nodes_with_required_number_of_cells')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport08.exchange_nodes')
    def test_execute_flow_cmexport_08_adds_exception(self, mock_exchange_nodes, mock_three_cell_nodes, mock_add_error,
                                                     *_):
        mock_three_cell_nodes.side_effect = Exception
        self.flow.execute_flow()
        self.assertEqual(1, mock_exchange_nodes.call_count)
        self.assertEqual(mock_add_error.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow.CmExport')
    def test_create_export_objects_is_successful(self, mock_cm_export):
        self.flow.create_export_object(self.users, self.nodes)
        self.assertEqual(mock_cm_export.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
