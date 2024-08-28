from datetime import datetime
import unittest2
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmSingleUpgradeFlow
from enmutils_int.lib.workload.shm_24 import SHM_24
from enmutils_int.lib.workload.shm_27 import SHM_27
from enmutils_int.lib.workload.shm_31 import SHM_31
from enmutils_int.lib.workload.shm_33 import SHM_33
from enmutils_int.lib.workload.shm_36 import SHM_36
from enmutils_int.lib.workload.shm_40 import SHM_40
from enmutils_int.lib.workload.shm_42 import SHM_42
from mock import Mock, patch


class ShmSingleUpgradeFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = ShmSingleUpgradeFlow()
        node1 = Mock()
        node1.node_id = '123'
        node2 = Mock()
        node2.node_id = '234'
        self.flow.STARTED_NODES = [node1, node2]
        self.flow.MAX_NODES = 50
        self.flow.SCHEDULED_TIMES_STRINGS = ["06:30:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["07:00:00"]
        self.DEFAULT = True
        self.job_name_prefix = Mock()
        self.flow.MLTN_TIMEOUT = 2
        self.flow.PARAMS_MLTN_SET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x={0};"
        self.flow.PARAMS_MLTN_UNSET_TIMEOUT = "shmerror:ActionName=sbl_timer,OperationType=set,T0x=30;"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = [Mock()]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.Shm24Flow.execute_flow")
    def test_shm_profile_shm_24_execute_flow__successful(self, mock_flow):
        SHM_24().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.execute_flow")
    def test_shm_profile_shm_27_execute_flow__successful(self, mock_flow):
        SHM_27().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmUpdateSoftwarePkgNameFlow.execute_flow")
    def test_shm_profile_shm_31_execute_flow__successful(self, mock_flow):
        SHM_31().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmUpdateSoftwarePkgNameFlow.execute_flow")
    def test_shm_profile_shm_33_execute_flow__successful(self, mock_flow):
        SHM_33().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.execute_flow")
    def test_shm_profile_shm_36_execute_flow__successful(self, mock_flow):
        SHM_36().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmUpdateSoftwarePkgNameFlow.execute_flow")
    def test_shm_profile_shm_40_execute_flow__successful(self, mock_flow):
        SHM_40().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.Shm42Flow.execute_flow")
    def test_shm_profile_shm_42_execute_flow__successful(self, mock_flow):
        SHM_42().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.check_sync_status_and_enable_supervision')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_36(self, mock_user, mock_upgrade, mock_download_certs, mock_check_sync, *_):
        mock_user.return_value = [self.user, self.user]
        self.flow.NAME = "SHM_36"
        mock_upgrade.return_value = (Mock(), Mock())
        self.flow.execute_flow()
        self.assertTrue(mock_user.called)
        self.assertTrue(mock_upgrade.called)
        self.assertTrue(mock_upgrade.mock_check_sync)
        self.assertEqual(mock_download_certs.call_args[0][0], ([self.user]))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.check_sync_status_and_enable_supervision')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.convert_shm_scheduled_times',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_36_empty_winfiol_iplist(self, mock_user, mock_exchange_nodes, *_):
        mock_user.return_value = [self.user, self.user]
        self.flow.NAME = "SHM_36"
        self.flow.execute_flow()
        self.assertTrue(mock_user.called)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.check_sync_status_and_enable_supervision')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_36_fails_for_first_winfiol_ip(self, mock_user, mock_upgrade, mock_home, *_):
        mock_user.return_value = [self.user, self.user]
        self.flow.NAME = "SHM_36"
        self.flow.execute_flow()
        self.assertTrue(mock_user.called)
        self.assertTrue(mock_home.called)
        self.assertTrue(mock_upgrade.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.convert_shm_scheduled_times')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_schedule_time_strings')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_33(self, mock_create_profile_user, mock_upgrade, mock_schedule_time_str, *_):
        mock_create_profile_user.return_value = [self.user]
        self.flow.NAME = "SHM_33"
        mock_schedule_time_str.return_value = (["04:00:00"], [datetime(2021, 3, 22, 5, 0)])
        mock_upgrade.return_value = (Mock(), Mock())
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.get_inventory_sync_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.set_netsim_values')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_24(self, mock_create_profile_user, mock_upgrade, mock_netsim, mock_inventory,
                                 mock_high_mim_nodes, *_):
        self.flow.NAME = "SHM_24"
        mock_create_profile_user.return_value = [self.user]
        mock_inventory.return_value = ['123', '456']
        mock_high_mim_nodes.return_value = self.flow.STARTED_NODES
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)
        self.assertTrue(mock_netsim.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.partial')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.select_nodes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'return_highest_mim_count_started_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.get_inventory_sync_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_31(self, mock_create_profile_user, mock_upgrade, mock_inventory, mock_high_mim_nodes, *_):
        mock_create_profile_user.return_value = [self.user]
        mock_inventory.return_value = ['123', '456']
        mock_high_mim_nodes.return_value = self.flow.STARTED_NODES
        self.flow.NAME = "SHM_31"
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'return_highest_mim_count_started_nodes', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.get_inventory_sync_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_31_with_no_sync_nodes(self, mock_create_profile_user, mock_upgrade, mock_exchange_nodes, *_):
        mock_create_profile_user.return_value = [self.user]

        self.flow.NAME = "SHM_31"
        self.assertRaises(EnvironError, self.flow.execute_flow())
        self.assertEqual(0, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'return_highest_mim_count_started_nodes', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_31_exception(self, mock_create_profile_user, mock_upgrade, mock_error,
                                           mock_exchange_nodes, *_):
        mock_create_profile_user.return_value = [self.user]

        self.flow.NAME = "SHM_31"
        self.flow.execute_flow()
        self.assertEqual(0, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)
        self.assertTrue(mock_error.called)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_27(self, mock_create_profile_user, mock_upgrade, *_):
        mock_create_profile_user.return_value = [self.user]
        self.flow.NAME = "SHM_27"
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.set_netsim_values', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.add_error_as_exception')
    def test_teardown_unset_timeout_exception(self, mock_error, *_):
        self.flow.teardown_unset_timeout()
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_24_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, mock_log, _):
        self.flow.NAME = "SHM_24"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertEqual(mock_log.call_count, 1)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_27_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, *_):
        self.flow.NAME = "SHM_27"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_31_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, *_):
        self.flow.NAME = "SHM_31"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_33_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, mock_log, _):
        self.flow.NAME = "SHM_33"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertEqual(mock_log.call_count, 1)
        self.assertTrue(mock_delete_inactive_job.called)
        self.assertTrue(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_36_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, *_):
        self.flow.NAME = "SHM_36"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_40_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, *_):
        self.flow.NAME = "SHM_40"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.get_current_epoch_time_in_milliseconds')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_activity')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__shm_42_successful(self, mock_pkg,
                                                                                mock_delete_inactive_job,
                                                                                mock_cleanup_job, *_):
        self.flow.NAME = "SHM_42"
        mock_pkg.return_value = (Mock(), self.flow.STARTED_NODES)
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.upgrade_setup')
    def test_create_upgrade_and_delete_inactive_upgrade_jobs__no_available_nodes(self, mock_pkg, *_):
        mock_pkg.return_value = Exception
        self.flow.create_upgrade_and_delete_inactive_upgrade_jobs(self.user, self.flow.STARTED_NODES)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    def test_delete_inactive_upgrade_activity__shm_33(self, mock_delete_inactive_job, mock_cleanup_job):
        self.flow.NAME = "SHM_33"
        package_nodes = self.flow.STARTED_NODES
        self.flow.delete_inactive_upgrade_activity(self.user, package_nodes, 1619779442788)
        mock_delete_inactive_job.assert_called_with(user=self.user, nodes=package_nodes, profile_name=self.flow.NAME)
        mock_cleanup_job.assert_called_with(self.user, package_nodes, profile_name=self.flow.NAME)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.cleanup_after_upgrade')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmFlow.delete_inactive_upgrade_packages')
    def test_delete_inactive_upgrade_activity__shm_24(self, mock_delete_inactive_job, mock_cleanup_job):
        self.flow.NAME = "SHM_24"
        self.flow.delete_inactive_upgrade_activity(self.user, self.flow.STARTED_NODES, 1619779442788)
        self.assertFalse(mock_delete_inactive_job.called)
        self.assertFalse(mock_cleanup_job.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_40(self, mock_create_profile_user, mock_upgrade, *_):
        mock_create_profile_user.return_value = [self.user]
        self.flow.NAME = "SHM_40"
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.get_schedule_time_strings',
           return_value=(["18:30:00"], [datetime(2021, 3, 22, 19, 0)]))
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.'
           'select_required_number_of_nodes_for_profile', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.timestamp_str',
           return_value="0801-090201")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_upgrade_job')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.ShmSingleUpgradeFlow.create_profile_users')
    def test_execute_flow_shm_42(self, mock_create_profile_user, mock_upgrade, mock_exchange_nodes, *_):
        mock_create_profile_user.return_value = [self.user]
        self.flow.NAME = "SHM_42"
        self.flow.execute_flow()
        self.assertEqual(1, mock_upgrade.call_count)
        self.assertEqual(1, mock_create_profile_user.call_count)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.CmManagement')
    def test_check_sync_status_and_enable_supervision__does_not_call_supervise_when_unsync_nodes_not_found(self, mock_cm_manage, _):
        mock_cm_manage.get_status.return_value = {"node1": "SYNCHRONIZED", "node2": "SYNCHRONIZED"}
        self.flow.check_sync_status_and_enable_supervision(self.user, self.flow.STARTED_NODES)
        self.assertFalse(mock_cm_manage.return_value.supervise.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.CmManagement')
    def test_check_sync_status_and_enable_supervision__calls_supervise_when_unsync_nodes_are_found(self, mock_cm_manage, _):
        mock_cm_manage.get_status.return_value = {"node1": "UNSYNCHRONIZED", "node2": "SYNCHRONIZED"}
        self.flow.check_sync_status_and_enable_supervision(self.user, self.flow.STARTED_NODES)
        self.assertTrue(mock_cm_manage.return_value.supervise.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.log')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow.CmManagement')
    def test_check_sync_status_and_enable_supervision__calls_log_when_exception_occurs(self, mock_cm_manage, mock_log):
        mock_cm_manage.get_status.side_effect = Exception()
        self.flow.check_sync_status_and_enable_supervision(self.user, self.flow.STARTED_NODES)
        self.assertTrue(mock_log.logger.error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
