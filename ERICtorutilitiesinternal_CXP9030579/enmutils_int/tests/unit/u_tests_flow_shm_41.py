from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_41_flow import Shm41Flow
from enmutils_int.lib.workload.shm_41 import SHM_41
from testslib import unit_test_utils


class Shm41FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = Shm41Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["23:00:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["23:30:00"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.execute_flow")
    def test_shm_profile_shm_41_execute_flow__successful(self, mock_flow):
        SHM_41().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.keep_running', side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.sleep_until_time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.select_required_number_of_nodes_for_profile',
           side_effect=[[Mock()], [Mock()], []])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.get_schedule_time_strings',
           return_value=(["23:00:00"], [datetime(2021, 3, 22, 23, 30)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.BackupJobRouter6675.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.timestamp_str')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.datetime.datetime')
    def test_execute_flow(self, mock_datetime, mock_create_profile_users, mock_execute_backup_jobs, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_datetime.now.side_effect = [datetime(2021, 3, 22, 23, 31), datetime(2021, 3, 22, 23, 28), datetime(2021, 3, 22, 23, 29)]
        self.flow.execute_flow()
        self.assertEqual(mock_execute_backup_jobs.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.sleep_until_time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.get_schedule_time_strings',
           return_value=(["23:00:00"], [datetime(2021, 3, 22, 23, 30)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.BackupJobRouter6675.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_41_flow.Shm41Flow.create_profile_users')
    def test_execute_flow__raises_exception(self, mock_create_profile_users, mock_get_required_nodes, mock_exception, *_):
        mock_get_required_nodes.side_effect = Exception
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
