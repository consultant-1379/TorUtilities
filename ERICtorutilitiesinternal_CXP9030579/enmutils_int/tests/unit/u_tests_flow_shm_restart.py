from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow import ShmRestartFlow
from enmutils_int.lib.workload.shm_28 import SHM_28
from enmutils_int.lib.workload.shm_47 import SHM_47
from testslib import unit_test_utils


class ShmRestartFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = ShmRestartFlow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["11:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["12:00:00"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.execute_flow")
    def test_shm_profile_shm_28_execute_flow__successful(self, mock_flow):
        SHM_28().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.execute_flow")
    def test_shm_profile_shm_47_execute_flow__successful(self, mock_flow):
        SHM_47().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.get_schedule_time_strings',
           return_value=(["11:30:00"], [datetime(2021, 3, 22, 12, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.select_required_number_of_nodes_for_profile',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.RestartNodeJob.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.RestartNodeJob.create')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_create_job, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.get_schedule_time_strings',
           return_value=(["11:30:00"], [datetime(2021, 3, 22, 12, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.select_required_number_of_nodes_for_profile',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.RestartNodeJob.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.RestartNodeJob.create', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.create_profile_users')
    def test_execute_flow_adds_exception(self, mock_create_profile_users, mock_create_job, mock_add_error_as_exception,
                                         *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_job.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.get_schedule_time_strings',
           return_value=(["11:30:00"], [datetime(2021, 3, 22, 12, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.sleep_until_day', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.select_required_number_of_nodes_for_profile',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow.ShmRestartFlow.add_error_as_exception')
    def test_execute_flow_skips_job_creation_when_no_synced_nodes(self, mock_error, mock_create_profile_users, *_):

        node = Mock()
        node.primary_type = "ERBS"
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
