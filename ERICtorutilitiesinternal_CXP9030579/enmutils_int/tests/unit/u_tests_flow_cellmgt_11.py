#!/usr/bin/env python

import unittest2
from mock import patch, Mock, PropertyMock
from requests.exceptions import HTTPError

from enmutils_int.lib.workload.cellmgt_11 import CELLMGT_11
from testslib import unit_test_utils


class CellMgt11FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.cellmgt_11 = CELLMGT_11()
        self.cellmgt_11.USER_ROLES = ["ADMINISTRATOR"]
        self.cellmgt_11.NUM_USERS = 15
        self.cellmgt_11.THREAD_QUEUE_TIMEOUT = 60 * 5
        self.cellmgt_11.RANDOM_SLEEP_TIME_RANGE = 10
        self.cellmgt_11.NUM_CELLS_PER_USER = 15
        self.user = Mock()
        self.nodes = [Mock(), Mock()]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.'
           'verify_nodes_on_enm_and_return_mo_cell_fdn_dict')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.create_profile_users')
    def test_cell_mgt_11__success(self, mock_create_users, mock_verify_nodes_return_cells,
                                  mock_create_and_execute_tests, mock_get_nodes, *_):
        mock_get_nodes.return_value = self.nodes
        profile = self.cellmgt_11
        users, fdd_cells = [Mock()] * 15, [Mock()] * 15
        mock_create_users.return_value = users
        mock_verify_nodes_return_cells.return_value = {'EUtranCellFDD': fdd_cells, 'UtranCell': []}
        profile.run()

        self.assertEqual(1, mock_create_and_execute_tests.call_count)
        self.assertEqual((users[0], fdd_cells), mock_create_and_execute_tests.call_args[0][0][0])

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.'
           'verify_nodes_on_enm_and_return_mo_cell_fdn_dict')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.keep_running')
    def test_cell_mgt_11__raises_http_error(self, mock_keep_running, mock_verify_nodes_return_cells,
                                            mock_create_and_execute_tests, mock_add_error, mock_get_nodes, *_):
        profile = self.cellmgt_11
        mock_get_nodes.return_value = self.nodes
        mock_verify_nodes_return_cells.side_effect = HTTPError()
        profile.run()

        self.assertEqual(0, mock_create_and_execute_tests.call_count)
        self.assertEqual(0, mock_keep_running.call_count)
        self.assertEqual(2, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.'
           'verify_nodes_on_enm_and_return_mo_cell_fdn_dict', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow.CellMgt11.create_profile_users')
    def test_execute_cell_mgt_11_flow__adds_error_as_exception(self, mock_create_users, mock_nodes_list, mock_add_error,
                                                               mock_get_nodes, *_):
        mock_create_users.return_value = self.user
        mock_get_nodes.return_value = self.nodes
        mock_nodes_list.return_value = self.nodes
        self.cellmgt_11.execute_cell_mgt_11_flow()
        self.assertEqual(2, mock_add_error.call_count)
        mock_nodes_list.assert_called_with(node_attributes=['node_id', 'poid'])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
