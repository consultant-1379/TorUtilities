from datetime import datetime


import unittest2
from mock import Mock, PropertyMock, patch

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.shm_flows.shm_39_flow import Shm39Flow
from enmutils_int.lib.workload.shm_39 import SHM_39
from testslib import unit_test_utils


class Shm39FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm39Flow()
        self.user = Mock()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = [Mock()]
        self.flow.SKIP_SYNC_CHECK = True
        self.flow.NODES_PER_HOST = 1
        self.flow.SCHEDULED_TIMES_STRINGS = ["02:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["03:00:00"]
        self.flow.SCHEDULED_DAYS = 'MONDAY'
        self.flow.NAME = "SHM_39"
        self.flow.MAX_NODES = 1
        self.node = Mock()
        self.node.ne_type = "BSC"
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.execute_flow")
    def test_shm_profile_shm_39_execute_flow__successful(self, mock_flow):
        SHM_39().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.get_schedule_time_strings',
           return_value=(["02:30:00"], [datetime(2021, 3, 22, 3, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.keep_running',
           side_effect=[True, True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.select_required_number_of_nodes_for_profile',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.DeleteBackupOnNodeJobBSC')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.BackupJobBSC')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.create_profile_users')
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_backup_job, mock_delete,
                                         mock_download_certs, mock_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_backup_job.return_value.create.side_effect = [None, Exception]
        mock_download_certs.side_effect = [Exception, None]
        self.flow.execute_flow()
        self.assertTrue(mock_backup_job.return_value.create.called)
        self.assertTrue(mock_delete.return_value.create.called)
        self.assertEqual(mock_download_certs.call_args[0][0], ([self.user]))
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.get_schedule_time_strings',
           return_value=(["02:30:00"], [datetime(2021, 3, 22, 3, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.select_required_number_of_nodes_for_profile',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.add_error_as_exception')
    def test_execute_flow_without_started_nodes_add_error_as_exception(self, mock_add_error, mock_create_profile_users,
                                                                       *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.get_schedule_time_strings',
           return_value=(["02:30:00"], [datetime(2021, 3, 22, 3, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_39_flow.Shm39Flow.add_error_as_exception')
    def test_execute_flow__add_error_as_exception_when_select_nodes_raises_execption(self, mock_add_error,
                                                                                     mock_create_profile_users,
                                                                                     mock_select_nodes, *_):
        mock_select_nodes.side_effect = EnmApplicationError
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
