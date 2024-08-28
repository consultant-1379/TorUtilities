#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock
from testslib import unit_test_utils
from enmutils.lib.enm_user_2 import User

from enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow import Nhm07


class Nhm07UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Nhm07()
        self.users = [User(username='nhm_07_test_operator'), User(username='nhm_07_test_admin')]
        self.nodes = unit_test_utils.get_nodes(2)
        self.flow.REPORTING_OBJECT = ['ENodeBFunction']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.Nhm07.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.Nhm07.sleep")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.ThreadQueue.execute")
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.Nhm07.keep_running")
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.NodesBreached')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.NhmMultiNodeFlow.create_and_configure_widgets')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow.NhmMultiNodeFlow.setup')
    def test_execute_flow_is_successful(self, mock_setup, mock_create_and_configure_widgets, mock_nodes_breached,
                                        mock_keep_running, mock_thread_queue, *_):
        mock_setup.return_value = self.users, self.nodes
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_nodes_breached.call_count, 2)
        self.assertTrue(mock_create_and_configure_widgets.called)
        self.assertTrue(mock_thread_queue.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
