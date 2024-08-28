import unittest2
from mock import Mock, PropertyMock, patch

from enmutils_int.lib.profile_flows.shm_flows.shm_07_flow import Shm07Flow
from enmutils_int.lib.workload.shm_07 import SHM_07
from testslib import unit_test_utils


class Shm07FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.flow = Shm07Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = Mock()
        self.flow.initial_task = True
        self.flow.SCHEDULE_SLEEP = 1
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.execute_flow")
    def test_shm_profile_shm_07_execute_flow__successful(self, mock_flow):
        SHM_07().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_help')
    def test_taskset_software_help(self, mock_software_help):
        self.flow._taskset_software_help(self.user)
        self.assertTrue(mock_software_help.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.return_nodes_to_shm_app')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_backup_go_to_topology_browser')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_backup_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_backup(self, mock_shm_home, mock_backup_admin,
                                         mock_backup_topology, mock_return_nodes, *_):
        user_app_tuple_mock = (self.user, "backup")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), Mock())
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_backup_admin.called)
        self.assertTrue(mock_backup_topology.called)
        self.assertTrue(mock_return_nodes)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_backup_administration_home', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_backup_exception(self, mock_shm_home, mock_error, *_):
        user_app_tuple_mock = (self.user, "backup")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), self.flow)
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.return_nodes_to_shm_app')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_license_go_to_topology_browser')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_license_inventory_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_license(self, mock_shm_home, mock_license_home,
                                          mock_license_topology, mock_return_nodes, *_):
        user_app_tuple_mock = (self.user, "license")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), Mock())
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_license_home.called)
        self.assertTrue(mock_license_topology.called)
        self.assertTrue(mock_return_nodes)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.return_nodes_to_shm_app')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_go_to_topology_browser')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_administration_upgrade_tab')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_upgrade_pkg_list(self, mock_shm_home, mock_software_home,
                                                   mock_software_upgrade, mock_software_topology,
                                                   mock_return_nodes, *_):
        user_app_tuple_mock = (self.user, "upgrade_pkg_list")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), Mock())
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_software_home.called)
        self.assertTrue(mock_software_upgrade.called)
        self.assertTrue(mock_software_topology.called)
        self.assertTrue(mock_return_nodes)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.return_nodes_to_shm_app')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_go_to_topology_browser')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_software_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_software(self, mock_shm_home, mock_software_home,
                                           mock_software_topology, mock_return_nodes, *_):
        user_app_tuple_mock = (self.user, "software")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), Mock())
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_software_home.called)
        self.assertTrue(mock_software_topology.called)
        self.assertTrue(mock_return_nodes)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.return_nodes_to_shm_app')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_hardware_go_to_topology_browser')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_hardware_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.shm_home')
    def test_taskset_return_nodes_hardware(self, mock_shm_home, mock_hardware_home,
                                           mock_hardware_topology, mock_return_nodes, *_):
        user_app_tuple_mock = (self.user, "hardware")
        self.flow._taskset_return_nodes(user_app_tuple_mock, Mock(), Mock())
        self.assertTrue(mock_shm_home.called)
        self.assertTrue(mock_hardware_home.called)
        self.assertTrue(mock_hardware_topology.called)
        self.assertTrue(mock_return_nodes)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.sleep')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_profile_users',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.keep_running', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.get_started_annotated_nodes')
    def test_execute_flow__if_service_is_not_used(self, mock_nodes, mock_deallocate_nodes, *_):
        mock_nodes.return_value = Mock()
        self.flow.execute_flow()
        self.assertTrue(mock_deallocate_nodes.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_profile_users',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.keep_running', side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=True)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.nodemanager_adaptor.deallocate_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.get_started_annotated_nodes')
    def test_execute_flow__if_service_is_used(self, mock_nodes, mock_deallocate_nodes,
                                              mock_get_nodes_list_by_attribute, *_):
        mock_nodes.return_value = Mock()
        self.flow.execute_flow()
        self.assertTrue(mock_deallocate_nodes.called)
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=["node_id", "node_ip", "netsim", "poid", "simulation", "primary_type", "node_name"])

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.sleep')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.create_profile_users',
           return_value=[Mock(), Mock(), Mock(), Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.keep_running', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.node_pool_mgr.deallocate_nodes', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.Shm07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_07_flow.ShmFlow.get_started_annotated_nodes')
    def test_execute_flow_exception(self, mock_nodes, mock_error, *_):
        mock_nodes.return_value = Mock()
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
