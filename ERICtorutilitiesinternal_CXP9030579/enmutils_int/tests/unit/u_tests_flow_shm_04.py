from mock import patch, Mock, PropertyMock

import unittest2

from enmutils.lib.enm_node_management import ShmManagement
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.shm_flows.shm_04_flow import Shm04Flow
from enmutils_int.lib.workload.shm_04 import SHM_04
from testslib import unit_test_utils


class Shm04FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm04Flow()
        self.user = Mock()
        self.nodes_list = [Mock(), Mock()]
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = [Mock()]
        self.flow.TIMEOUT = 10
        self.shm_obj = ShmManagement(node_ids=self.nodes_list, user=self.user, ne_type="ERBS")
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.execute_flow")
    def test_shm_profile_shm_04_execute_flow__successful(self, mock_flow):
        SHM_04().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow._verify_sync_status')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.supervise', return_value=True)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.unsupervise', return_value=True)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.create_profile_users')
    def test_execute_flow_shm_04_success(self, mock_create_profile_users, mock_info, mock_keep_running, mock_nodes, *_):
        mock_nodes.return_value = self.nodes_list
        mock_keep_running.side_effect = [True, False]
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_info.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow._verify_sync_status', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.supervise', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.unsupervise', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.create_profile_users')
    def test_execute_flow_shm_04_raises_exception(self, mock_create_profile_users, mock_debug,
                                                  mock_keep_running, mock_add_error, *_):
        mock_keep_running.side_effect = [True, False]
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_debug.called)
        self.assertEqual(mock_add_error.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.get_inventory_sync_nodes')
    def test_execute_flow_shm_04_verify_sync_status(self, mock_inventory, mock_nodes, *_):
        mock_nodes.return_value = self.nodes_list
        mock_inventory.side_effect = [EnmApplicationError("Exception"), self.nodes_list]
        self.assertRaises(EnmApplicationError, self.flow._verify_sync_status(self.shm_obj))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.Shm04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_04_flow.ShmManagement.get_inventory_sync_nodes')
    def test_execute_flow_shm_04_verify_sync_status_exception(self, mock_inventory, mock_nodes, *_):
        mock_nodes.return_value = self.nodes_list
        mock_inventory.side_effect = [[Mock()]] + [EnmApplicationError("Exception")] * 19
        self.assertRaises(EnmApplicationError, self.flow._verify_sync_status, self.shm_obj)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
