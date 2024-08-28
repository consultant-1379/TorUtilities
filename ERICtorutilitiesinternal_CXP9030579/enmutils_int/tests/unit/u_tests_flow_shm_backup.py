from datetime import datetime
import unittest2
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow import ShmBackupFlow, execute_user_tasks
from enmutils_int.lib.workload.shm_01 import SHM_01
from enmutils_int.lib.workload.shm_02 import SHM_02
from enmutils_int.lib.workload.shm_46 import SHM_46
from mock import Mock, PropertyMock, patch


class ShmBackupFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = ShmBackupFlow()
        self.user = Mock()
        self.flow.SCHEDULED_TIMES_STRINGS = ["12:00:00", "15:00:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["12:30:00", "15:30:00"]
        self.flow.MAX_NODES = 2
        self.node = Mock()
        self.node.primary_type = "ERBS"
        self.node.node_id = "A"
        self.unused_node = Mock()
        self.unused_node.primary_type = "ERBS"
        self.unused_node.node_id = "B"
        self.flow.NUM_NODES_PER_BATCH = 1
        self.flow.NAME = "SHM_BACKUP"
        self.flow.REPEAT_COUNT = 0

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.Shm01Flow.execute_flow")
    def test_shm_profile_shm_01_execute_flow__successful(self, mock_flow):
        SHM_01().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.Shm02Flow.execute_flow")
    def test_shm_profile_shm_02_execute_flow__successful(self, mock_flow):
        SHM_02().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.Shm02Flow.execute_flow")
    def test_shm_profile_shm_46_execute_flow__successful(self, mock_flow):
        SHM_46().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.arguments.split_list_into_chunks')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.'
           'select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.multitasking.create_single_process_and_execute_task')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.exchange_nodes')
    def test_execute_flow__success(self, mock_exchange_nodes, mock_create_process, mock_get_synced, mock_batch, *_):
        mock_get_synced.side_effect = [[self.node], [self.node]]
        mock_batch.return_value = [self.node]
        self.flow.execute_flow()
        self.assertEqual(5, len(mock_create_process.call_args[1]['args']))
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.state')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow'
           '.select_required_number_of_nodes_for_profile',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.add_error_as_exception')
    def test_execute_flow_raises_exception(self, mock_add_error_as_exception, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.BackupJobCPP')
    def test_task_set__cpp_success(self, mock_backup_job, mock_cleanup_job, mock_execute_backup,
                                   mock_schedule_time_str):
        self.flow.PLATFORM = "CPP"
        batch_synced_nodes = (1, [self.node])
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.task_set(batch_synced_nodes, self.user, self.flow)
        mock_execute_backup.assert_call(mock_backup_job, mock_cleanup_job, self.user)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.BackupJobCOMECIM')
    def test_task_set__ecim_success(self, mock_backup_job, mock_cleanup_job, mock_execute_backup,
                                    mock_schedule_time_str):
        self.flow.PLATFORM = "ECIM"
        batch_synced_nodes = (1, [self.node])
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.task_set(batch_synced_nodes, self.user, self.flow)
        mock_execute_backup.assert_call(mock_backup_job, mock_cleanup_job, self.user)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.get_schedule_time_strings')
    def test_task_set__other_platform_success(self, mock_schedule_time_str):
        self.flow.PLATFORM = "SHM"
        batch_synced_nodes = (1, [self.node])
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.task_set(batch_synced_nodes, self.user, self.flow)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackUpCleanUpJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.BackupJobCPP')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.add_error_as_exception')
    def test_task_set__add_error_as_exception(self, mock_add_error, mock_execute_backup, mock_schedule_time_str, *_):
        mock_execute_backup.side_effect = EnmApplicationError
        batch_synced_nodes = (1, [self.node])
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.task_set(batch_synced_nodes, self.user, self.flow)
        self.assertIsInstance(mock_add_error.call_args[0][0], EnmApplicationError)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow.ShmBackupFlow.create_and_execute_threads')
    def test_execute_user_tasks(self, mock_threads):
        nodes_per_batch = [(1, ['netsim_LTE02ERBS00040', 'netsim_LTE31dg2ERBS00034'])]
        execute_user_tasks(self.flow, nodes_per_batch, len(nodes_per_batch), self.user, 8100)
        self.assertTrue(mock_threads.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
