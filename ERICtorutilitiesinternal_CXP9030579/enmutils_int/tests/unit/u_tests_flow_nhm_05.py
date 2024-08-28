#!/usr/bin/env python
import unittest2
from mock import patch
from enmutils.lib.enm_user_2 import User
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow import Nhm05


class Nhm05UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm05()
        self.users = [User(username='nhm_05_test_operator'), User(username='nhm_05_test_admin')]
        self.nodes = unit_test_utils.get_nodes(2)
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.CellStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.NetworkOperationalState')
    def test_init_widgets_is_successful(self, mock_network_op_state, mock_cell_status, *_):
        self.flow._init_widgets(user=self.users[1], nodes=self.nodes)
        self.assertTrue(mock_network_op_state.called)
        self.assertTrue(mock_cell_status.called)

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.Nhm05.sleep')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.CellStatus')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.NetworkOperationalState')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.NhmMultiNodeFlow.execute_multi_node_flow')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.NhmMultiNodeFlow.create_and_configure_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow.NhmMultiNodeFlow.setup')
    def test_execute_flow_is_successful(self, mock_setup, mock_create_and_configure_widgets, mock_execute_05_06_flow,
                                        mock_network_op_state, mock_cell_status, *_):
        mock_setup.return_value = self.users, self.nodes
        self.flow.execute_flow()
        self.assertEqual(mock_network_op_state.call_count, 2)
        self.assertEqual(mock_cell_status.call_count, 2)
        self.assertTrue(mock_create_and_configure_widgets.called)
        self.assertTrue(mock_execute_05_06_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
