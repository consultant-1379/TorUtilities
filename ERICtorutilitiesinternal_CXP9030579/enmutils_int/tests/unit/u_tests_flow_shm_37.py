from collections import defaultdict

import unittest2
from mock import Mock, patch

from enmutils_int.lib.profile_flows.shm_flows.shm_37_flow import Shm37Flow
from enmutils_int.lib.workload.shm_37 import SHM_37
from testslib import unit_test_utils


class Shm37FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Shm37Flow()
        nodes_dict = defaultdict(list)
        nodes_dict["ERBS"] = [Mock(primary_type="ERBS")]
        self.nodes = nodes_dict
        self.user = Mock()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = [Mock()]
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.NODES_PER_CHUNK = 1
        self.flow.SLEEP_TIME_BETWEEN_JOBS = 0

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.execute_flow")
    def test_shm_profile_shm_37_execute_flow__successful(self, mock_flow):
        SHM_37().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_synced_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_nodes_list_by_attribute')
    def test_execute_flow_is_success_when_synced_nodes_present(self, mock_nodes, mock_node_types,
                                                               mock_upgrade_delete_inactive,
                                                               mock_add_error_as_exception, *_):
        mock_nodes.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_upgrade_delete_inactive.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_synced_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_nodes_list_by_attribute')
    def test_execute_flow_is_success_when_synced_nodes_not_present(self, mock_nodes, mock_node_types,
                                                                   mock_upgrade_delete_inactive,
                                                                   mock_add_error_as_exception, *_):
        mock_nodes.return_value = {}
        mock_node_types.return_value = {}
        self.flow.execute_flow()
        self.assertFalse(mock_upgrade_delete_inactive.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_synced_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.add_error_as_exception')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.upgrade_delete_inactive', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_37_flow.Shm37Flow.get_nodes_list_by_attribute')
    def test_execute_flow_raises_exception(self, mock_nodes, mock_node_types, mock_upgrade_delete_inactive,
                                           mock_add_error_as_exception, *_):
        mock_nodes.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_upgrade_delete_inactive.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
