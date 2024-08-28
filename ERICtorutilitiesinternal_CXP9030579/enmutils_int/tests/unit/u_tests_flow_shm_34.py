from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_34_flow import Shm34Flow
from enmutils_int.lib.workload.shm_34 import SHM_34
from testslib import unit_test_utils


class Shm34FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = Shm34Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["23:00:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["23:30:00"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.execute_flow")
    def test_shm_profile_shm_34_execute_flow__successful(self, mock_flow):
        SHM_34().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.get_schedule_time_strings',
           return_value=(["01:30:00", "23:00:00"], [datetime(2022, 11, 30, 02, 00), datetime(2022, 11, 30, 23, 30)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.keep_running',
           side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.sleep_until_time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.select_required_number_of_nodes_for_profile',
           side_effect=[[Mock()], [Mock()], []])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.BackupJobSpitFire.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.execute_backup_jobs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_34_flow.Shm34Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_execute_backup_jobs, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertEqual(mock_execute_backup_jobs.call_count, 4)
        self.assertEqual(mock_add_error_as_exception.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
