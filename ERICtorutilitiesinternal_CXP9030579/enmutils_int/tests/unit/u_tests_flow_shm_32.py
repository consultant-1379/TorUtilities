from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_32_flow import Shm32Flow
from enmutils_int.lib.workload.shm_32 import SHM_32
from testslib import unit_test_utils


class Shm32FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm32Flow()
        self.user = Mock()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = [Mock()]
        self.flow.FILTERED_NODES_PER_HOST = 1
        self.flow.MAX_NODES = 1
        self.dict_mock = {'A': [Mock()], 'B': [Mock()]}
        self.node = Mock()
        self.node.primary_type = "MINI-LINK-6352"
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.execute_flow")
    def test_shm_profile_shm_32_execute_flow__successful(self, mock_flow):
        SHM_32().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.get_schedule_time_strings',
           return_value=(["02:00:00"], [datetime(2021, 3, 22, 2, 30)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.sleep_until_time')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.keep_running', side_effect=[True, True, True,
                                                                                                       False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.ShmFlow.'
           'deallocate_IPV6_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.BackupJobMiniLink6352')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.ShmFlow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.create_profile_users')
    def test_execute_flow_is_successful(self, mock_create_profile_users, mock_inventory_sync_nodes, mock_backup_job,
                                        mock_add_error_as_exception, mock_exchange_nodes, *_):

        mock_inventory_sync_nodes.return_value = [[self.node], [self.node], []]
        mock_create_profile_users.return_value = [self.user]
        mock_backup_job.return_value.create.side_effect = [None, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_backup_job.return_value.create.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 2)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.get_schedule_time_strings',
           return_value=(["02:00:00"], [datetime(2021, 3, 22, 2, 30)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.sleep_until_time')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.ShmFlow.'
           'deallocate_IPV6_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.ShmFlow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_32_flow.Shm32Flow.create_profile_users')
    def test_execute_flow_without_nodes_adds_error_as_exception(self, mock_create_profile_users,
                                                                mock_inventory_sync_nodes, mock_add_error_as_exception,
                                                                mock_exchange_nodes, *_):
        mock_inventory_sync_nodes.return_value = []
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertTrue(mock_exchange_nodes.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
