from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_43_flow import Shm43Flow
from enmutils_int.lib.workload.shm_43 import SHM_43
from testslib import unit_test_utils


class Shm43FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm43Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["02:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["03:00:00"]
        self.user = Mock()
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.execute_flow")
    def test_shm_profile_shm_43_execute_flow__successful(self, mock_flow):
        SHM_43().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.keep_running', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.select_required_number_of_nodes_for_profile',
           side_effect=[[Mock()], []])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.BackupJobMiniLink669x')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_backup_job, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_backup_job.return_value.create.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.select_required_number_of_nodes_for_profile',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.BackupJobMiniLink669x')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_43_flow.Shm43Flow.create_profile_users')
    def test_execute_flow_add_error_as_exception_if_backupjob_create_throws_exception(self, mock_create_profile_users,
                                                                                      mock_backup_job,
                                                                                      mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_backup_job.return_value.create.side_effect = Exception
        self.flow.execute_flow()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
