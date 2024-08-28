from datetime import datetime

import unittest2
from mock import Mock, patch

from enmutils_int.lib.profile_flows.shm_flows.shm_25_flow import Shm25Flow
from enmutils_int.lib.workload.shm_25 import SHM_25
from testslib import unit_test_utils


class Shm25FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm25Flow()
        self.flow.SCHEDULED_TIMES_STRINGS = ["02:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["03:00:00"]
        self.user = Mock()
        self.flow.MAX_NODES = 10
        self.flow.JOB_NAME_PREFIX = "abc"
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.execute_flow")
    def test_shm_profile_shm_25_execute_flow__successful(self, mock_flow):
        SHM_25().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.select_nodes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.SHMUtils.execute_restart_delay')
    def test_execute_flow(self, mock_restart, mock_upgrade, mock_schedule_time_str, *_):
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.execute_flow()
        self.assertEqual(mock_restart.call_count, 2)
        self.assertTrue(mock_upgrade.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_upgrade_job',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.select_nodes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.SHMUtils.execute_restart_delay', side_effect=Exception)
    def test_execute_flow_exception_restart_delay(self, mock_restart, mock_error, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_restart.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.select_nodes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.nodes', return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_upgrade_job', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.SHMUtils.execute_restart_delay')
    def test_execute_flow_exception_upgrade(self, mock_restart, mock_error, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_restart.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.select_nodes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.nodes', return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.create_upgrade_job', side_effect=[Exception,
                                                                                                             Exception])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.Shm25Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_25_flow.SHMUtils.execute_restart_delay')
    def test_execute_flow_exception_unset_restart_delay(self, mock_restart, mock_error, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_restart.call_count, 2)
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
