import unittest2
from mock import Mock, patch, PropertyMock

from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils_int.lib.profile_flows.shm_flows.shm_35_flow import Shm35Flow
from enmutils_int.lib.workload.shm_35 import SHM_35
from testslib import unit_test_utils


class Shm35FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm35Flow()
        self.bsc_node = Mock()
        self.bsc_node.primary_type = "BSC"
        self.node = Mock()
        self.node.primary_type = "ERBS"
        self.user = Mock()
        self.flow.MAX_NODES = 10
        self.flow.SCHEDULE_SLEEP = 1
        self.flow.USER_ROLES = [Mock()]
        self.nodes = {"ERBS": [erbs(node_id='testNode1', primary_type='ERBS')],
                      "RadioNode": [erbs(node_id='testNode2', primary_type='RadioNode')],
                      "Router6672": [erbs(node_id='testNode3', primary_type='Router6672')],
                      "Router6675": [erbs(node_id='testNode4', primary_type='Router6675')],
                      "BSC": [erbs(node_id='testNode4', primary_type='BSC')]}
        self.bsc_synced_nodes = [self.bsc_node]
        self.synced_nodes = [self.node, self.bsc_node]
        self.flow.NODES_PER_CHUNK = 1
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.execute_flow")
    def test_shm_profile_shm_35_execute_flow__successful(self, mock_flow):
        SHM_35().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.timestamp_str')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.get_nodes_list_by_attribute')
    def test_shm_35_execute_flow__success(self, mock_pool, mock_node_types, *_):
        mock_pool.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmBSCBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.timestamp_str')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.get_nodes_list_by_attribute')
    def test_shm_35_execute_flow__bsc_success(self, mock_pool, mock_node_types, mock_sync_nodes, *_):
        mock_pool.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        mock_sync_nodes.return_value = self.bsc_synced_nodes
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.log.logger.debug')
    def test_shm_35_execute_flow__without_nodes(self, mock_log, mock_pool, mock_node_types, *_):
        mock_pool.return_value = {"ERBS": [], "RadioNode": [], "Router6672": [], "Router6675": [], "BSC": []}
        mock_node_types.return_value = {"ERBS": [], "RadioNode": [], "Router6672": [], "Router6675": [], "BSC": []}
        self.flow.execute_flow()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.add_error_as_exception')
    def test_shm_35_execute_flow__without_synced_nodes(self, mock_error, mock_pool, mock_node_types, *_):
        mock_pool.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmBackUpCleanUpJob.create', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.timestamp_str')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.generate_basic_dictionary_from_list_of_objects')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.Shm35Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_35_flow.ShmFlow.add_error_as_exception')
    def test_shm_35_execute_flow__add_error_as_exception(self, mock_error, mock_pool, mock_node_types, *_):
        mock_pool.return_value = self.nodes
        mock_node_types.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
