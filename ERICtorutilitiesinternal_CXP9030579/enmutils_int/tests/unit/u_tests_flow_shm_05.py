from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_05_flow import Shm05Flow
from enmutils_int.lib.workload.shm_05 import SHM_05
from testslib import unit_test_utils


class Shm05FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = Shm05Flow()
        self.flow.NAME = "SHM_05"
        self.flow.MAX_NODES = 50
        self.flow.SCHEDULED_TIMES_STRINGS = ["04:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["05:00:00"]
        self.DEFAULT = True
        self.flow.FILTERED_NODES_PER_HOST = 1
        self.job_name_prefix = Mock()
        self.flow.SCHEDULED_DAYS = "mock"
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.execute_flow")
    def test_shm_profile_shm_05_execute_flow__successful(self, mock_flow):
        SHM_05().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.exchange_nodes')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.upgrade_delete_inactive')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.timestamp_str', return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.create_profile_users')
    def test_execute_flow__success(self, mock_create_profile_user, mock_upgrade, mock_schedule_time_str,
                                   *_):
        mock_create_profile_user.return_value = [self.user]
        node = Mock()
        node.primary_type = "RadioNode"
        mock_upgrade.return_value = (node, [node])
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.exchange_nodes', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.timestamp_str', return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.create_upgrade_job', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_05_flow.Shm05Flow.create_profile_users')
    def test_execute_flow__add_error_as_exception(self, mock_create_profile_user, mock_upgrade, mock_schedule_time_str,
                                                  mock_error, *_):
        mock_create_profile_user.return_value = [self.user]
        node = Mock()
        node.primary_type = "RadioNode"
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
