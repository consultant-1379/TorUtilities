import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.shm_flows.shm_44_flow import Shm44Flow
from enmutils_int.lib.workload.shm_44 import SHM_44
from testslib import unit_test_utils


class Shm44FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = Shm44Flow()
        self.flow.MAX_NODES = 50
        self.DEFAULT = True
        self.job_name_prefix = Mock()
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.execute_flow")
    def test_shm_profile_shm_44_execute_flow__successful(self, mock_flow):
        SHM_44().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.timestamp_str', return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.create_profile_users')
    def test_execute_flow__success(self, mock_create_profile_user, mock_upgrade, mock_schedule_time_str, *_):
        mock_create_profile_user.return_value = [self.user]
        mock_schedule_time_str.return_value = (["04:00:00"], ["05:00:00"])
        mock_upgrade.return_value = (Mock(), Mock())
        self.flow.execute_flow()
        self.assertTrue(mock_upgrade.called)
        self.assertTrue(mock_create_profile_user.called)
        self.assertTrue(mock_schedule_time_str.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.exchange_nodes', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.timestamp_str', return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.select_required_number_of_nodes_for_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.create_upgrade_job', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_44_flow.Shm44Flow.create_profile_users')
    def test_execute_flow__add_error_as_exception(self, mock_create_profile_user, mock_upgrade, mock_schedule_time_str,
                                                  mock_error, *_):
        mock_create_profile_user.return_value = [self.user]
        mock_schedule_time_str.return_value = (["04:00:00"], ["05:00:00"])
        self.flow.execute_flow()
        self.assertTrue(mock_upgrade.called)
        self.assertTrue(mock_create_profile_user.called)
        self.assertTrue(mock_schedule_time_str.called)
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
