from datetime import datetime
import unittest2
from testslib import unit_test_utils
from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils.lib.exceptions import (EnmApplicationError, EnvironError)
from enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow import ShmRestoreFlow, Shm18Flow, Shm26Flow
from enmutils_int.lib.workload.shm_18 import SHM_18
from enmutils_int.lib.workload.shm_26 import SHM_26
from mock import Mock, PropertyMock, patch


class ShmRestoreFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = ShmRestoreFlow()
        self.flow.BACKUP_DESCRIPTION = "backup flow"
        self.flow.RESTORE_DESCRIPTION = "restore flow"
        self.flow.SCHEDULED_TIMES_STRINGS = ["18:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["19:00:00"]
        self.node = erbs(node_id='testNode', primary_type='ERBS')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.execute_flow")
    def test_shm_profile_shm_18_execute_flow__successful(self, mock_flow):
        SHM_18().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.execute_flow")
    def test_shm_profile_shm_26_execute_flow__successful(self, mock_flow):
        SHM_26().run()
        self.assertTrue(mock_flow.called)

    def test_restore_task_set__success(self):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s)']
        self.user.enm_execute.return_value = response
        self.flow.restore_task_set(self.node, self.user, file_name="19-04-20")

    def test_restore_task_set__raises_enm_application_error(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.restore_task_set, self.node, self.user, file_name="19-04-20")

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.select_required_number_of_nodes_for_profile',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.create_restore_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm18Flow.keep_running')
    def test_execute_flow__shm_18_success(self, mock_keep_running, mock_restore, *_):
        mock_keep_running.side_effect = [True, False]
        shm_18 = Shm18Flow()
        shm_18.NAME = "SHM_18"
        shm_18.execute_flow()
        self.assertTrue(mock_restore.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.select_nodes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.create_restore_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.keep_running')
    def test_execute_flow__shm_26_success(self, mock_keep_running, mock_restore, *_):
        mock_keep_running.side_effect = [True, False]
        shm_26 = Shm26Flow()
        shm_26.NAME = "SHM_26"
        shm_26.execute_flow()
        self.assertTrue(mock_restore.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.Shm26Flow.get_schedule_time_strings',
           return_value=([], []))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.keep_running')
    def test_execute_flow__shm_00_success(self, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, False]
        shm_00 = ShmRestoreFlow()
        shm_00.NAME = "SHM_00"
        shm_00.execute_flow()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.RestoreJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.DeleteBackupOnNodeJobCPP')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.BackupJobCPP')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.timestamp_str')
    def test_create_restore_job__success_shm_18(self, *_):
        self.flow.NAME = "SHM_18"
        self.flow.create_restore_job(self.user, [Mock()])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ThreadQueue.execute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.RestoreJob.wait_time_for_job_to_complete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ThreadQueue')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.RestoreJob')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.DeleteBackupOnNodeJobCPP')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.BackupJobCPP')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.timestamp_str')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.SHMUtils.execute_restart_delay')
    def test_create_restore_job__success_shm_26(self, *_):
        self.flow.NAME = "SHM_26"
        self.flow.create_restore_job(self.user, [Mock()])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.enm_annotate_method')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.start_stopped_nodes_or_remove')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow.ShmRestoreFlow.add_error_as_exception')
    def test_create_restore_job__raises_environ_error(self, mock_error, *_):
        self.flow.create_restore_job(self.user, [])
        self.assertTrue(mock_error.called)
        mock_error.assertIn(EnvironError("No available synced nodes, can't proceed further job execution"))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
