#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnvironError, EnmApplicationError, JobValidationError
from enmutils_int.lib.nhm import SETUP_PROFILE
from enmutils_int.lib.profile_flows.npa_flows.npa_flow import Npa01Flow
from mock import Mock, PropertyMock, patch, mock_open
from requests import HTTPError
from testslib import unit_test_utils

radio_node_package = {u'productRelease': None, u'packageName': u'CXP9024418_6_R2CXS2', u'productRevision': u'R2CXS2',
                      u'productData': u'CXP9024418/6_R2CXS2', u'productNumber': u'CXP9024418/6'}


class Npa01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(primary_type="RadioNode", node_id="LTE109dg2ERBS00078", node_version="18.Q1"),
                      Mock(primary_type="RadioNode", node_id="LTE104dg2ERBS00055", node_version="19.Q1"),
                      Mock(primary_type="RadioNode", node_id="LTE111dg2ERBS00005", node_version="20.Q1")]
        self.mock_node_ids_with_cells = {'LTE109dg2ERBS00078': ['LTE109dg2ERBS00078-1'],
                                         'LTE104dg2ERBS00055': ['LTE104dg2ERBS00055-1', 'LTE104dg2ERBS00055-3'],
                                         'LTE111dg2ERBS00005': ['LTE111dg2ERBS00005-1', 'LTE111dg2ERBS00005-2',
                                                                'LTE111dg2ERBS00005-3']}
        self.nodes_names = ["LTE109dg2ERBS00078", "LTE104dg2ERBS00055", "LTE111dg2ERBS00005", "LTE104dg2ERBS00055",
                            "LTE111dg2ERBS00005", "LTE111dg2ERBS00005"]
        self.cells_names = ["LTE109dg2ERBS00078-1", "LTE104dg2ERBS00055-1", "LTE111dg2ERBS00005-1",
                            "LTE104dg2ERBS00055-3", "LTE111dg2ERBS00005-2", "LTE111dg2ERBS00005-3"]
        self.node_ids_with_cells_flow_instance = (1, self.mock_node_ids_with_cells)
        self.flow = Npa01Flow()
        self.flow.NAME = "NPA_01"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = []
        self.flow.NUMBER_OF_FLOWS = 1
        self.flow.NUMBER_OF_CELLS = 6
        self.flow.NODE_VERSION_FORMAT = ["20.Q1", "20.Q2", "20.Q3", "20.Q4", "21.Q1", "21.Q2", "21.Q3", "21.Q4"]
        self.flow.CELL_TYPE = {'RadioNode': ['EUtranCellFDD', 'EUtranCellTDD']}
        self.flow.KPI_ADJUST = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_asu_health_check_profile',
           return_value='test-name')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.node_allocation_and_load_balance_as_a_prerequisite')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_and_execute_threads')
    def test_execute_flow__success(self, mock_create_and_execute, mock_node_allocation, mock_add_error, mock_get_nodes,
                                   mock_create_profile_users, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_create_profile_users.return_value[0].is_session_established.return_value = True
        mock_get_nodes.return_value = self.nodes
        mock_node_allocation.return_value = self.node_ids_with_cells_flow_instance
        self.flow.execute_flow()
        mock_create_and_execute.assert_called_with(self.node_ids_with_cells_flow_instance, self.flow.NUMBER_OF_FLOWS,
                                                   args=[self.user, 'test-name', self.flow])
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_asu_health_check_profile',
           return_value='test-name')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.node_allocation_and_load_balance_as_a_prerequisite')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_and_execute_threads')
    def test_execute_flow__no_cells(self, mock_create_and_execute, mock_node_allocation, mock_add_error, mock_sleep,
                                    mock_create_profile_users, *_):
        mock_create_profile_users.return_value[0].is_session_established.return_value = True
        mock_node_allocation.return_value = []
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute.called)
        self.assertIsInstance(mock_add_error.call_args[0][0], EnvironError)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_asu_health_check_profile',
           return_value='test-name')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch(
        'enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.node_allocation_and_load_balance_as_a_prerequisite')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_and_execute_threads')
    def test_execute_flow__user_session_not_established(self, mock_create_and_execute, mock_node_allocation,
                                                        mock_add_error, mock_sleep, mock_create_profile_users, *_):
        mock_create_profile_users.return_value[0].is_session_established.return_value = False
        mock_node_allocation.return_value = self.node_ids_with_cells_flow_instance
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute.called)
        self.assertIsInstance(mock_add_error.call_args[0][0], EnmApplicationError)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_asu_health_check_profile',
           return_value='test-name')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch(
        'enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.node_allocation_and_load_balance_as_a_prerequisite')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_and_execute_threads')
    def test_execute_flow__balance_setup_exception(self, mock_create_and_execute, mock_node_allocation, mock_add_error,
                                                   mock_create_profile_users, mock_sleep, *_):
        mock_create_profile_users.return_value[0].is_session_established.return_value = True
        mock_node_allocation.side_effect = Exception
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute.called)
        self.assertIsInstance(mock_add_error.call_args[0][0], EnvironError)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_profile_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_asu_health_check_profile')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.node_allocation_and_load_balance_as_a_prerequisite')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_and_execute_threads')
    def test_execute_flow__threads_add_error_as_exception(self, mock_create_and_execute, mock_node_allocation,
                                                          mock_create_health_check, mock_add_error, mock_sleep, *_):
        mock_node_allocation.return_value = self.node_ids_with_cells_flow_instance, 'test-name'
        mock_create_and_execute.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.balance_npa_load_with_nhm_setup')
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.group_cells_per_each_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_names_of_nodes_and_cells')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.allocate_radionodes_from_synced_nodes')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_synced_nodes_from_setup_profile')
    def test_node_allocation_and_load_balance_as_a_prerequisite__is_successful(self, mock_synced_nodes, mock_nodes_list,
                                                                               mock_node_ids_with_cells,
                                                                               mock_list_cells_per_flow, mock_log, *_):
        mock_synced_nodes.return_value = self.nodes
        mock_nodes_list.return_value = self.nodes[:2]
        mock_node_ids_with_cells.return_value = self.nodes_names, self.cells_names
        self.flow.node_allocation_and_load_balance_as_a_prerequisite(self.user)
        self.assertEqual(4, len(mock_node_ids_with_cells.call_args[0]))
        self.assertEqual((self.nodes_names, self.cells_names), mock_list_cells_per_flow.call_args[0])
        self.assertTrue(mock_nodes_list.called)
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.check_sync_and_remove')
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.allocate_specific_nodes_to_profile")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_allocated_nodes")
    def test_get_synced_nodes_from_setup_profile__is_successful(
            self, mock_get_allocated_nodes, mock_allocate_specific_nodes_to_profile, mock_sync, mock_nodes_list):
        mock_get_allocated_nodes.return_value = self.nodes
        mock_nodes_list.return_value = self.nodes
        node_type = "RadioNode"
        self.flow.get_synced_nodes_from_setup_profile(self.user, SETUP_PROFILE, node_type)
        self.assertEqual(2, len(mock_allocate_specific_nodes_to_profile._mock_call_args))
        self.assertEqual(6, len(mock_nodes_list.call_args[1]["node_attributes"]))
        mock_sync.assert_called_with(self.nodes, self.user)

    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_allocate_radionodes_from_synced_nodes__is_successful(self, mock_log):
        self.assertEqual(self.flow.allocate_radionodes_from_synced_nodes(self.nodes), (self.nodes[-1:], self.nodes[:2]))
        self.assertEqual(1, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.create_nhc_profile')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_radio_node_package')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.SoftwareOperations')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.SoftwarePackage')
    def test_create_asu_health_check_profile__successful(self, mock_package, mock_operations, mock_get_radio_package,
                                                         mock_create_nhc_profile):
        package = Mock()
        package.name = "CXP"
        mock_package.return_value = package
        mock_get_radio_package.return_value = radio_node_package
        mock_create_nhc_profile.return_value = 'test-name'
        self.flow.create_asu_health_check_profile(self.user, self.nodes)
        mock_package.assert_called_with(self.nodes, self.user, use_default=True, profile_name=self.flow.NAME)
        mock_operations.assert_called_with(user=self.user, package=package, ptype=self.nodes[0].primary_type)
        mock_create_nhc_profile.assert_called_with(self.user, self.nodes[0].primary_type, radio_node_package,
                                                   self.flow.NAME)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.create_nhc_profile')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_radio_node_package')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.SoftwareOperations')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.SoftwarePackage')
    def test_create_asu_health_check_profile__exception(self, mock_package, mock_operations, mock_get_radio_package,
                                                        mock_create_nhc_profile, mock_add_error):
        package = Mock()
        package.name = "CXP"
        mock_package.return_value = package
        mock_get_radio_package.return_value = radio_node_package
        mock_create_nhc_profile.side_effect = Exception
        self.flow.create_asu_health_check_profile(self.user, self.nodes)
        mock_package.assert_called_with(self.nodes, self.user, use_default=True, profile_name=self.flow.NAME)
        mock_operations.assert_called_with(user=self.user, package=package, ptype=self.nodes[0].primary_type)
        self.assertTrue(mock_add_error.called)
        self.assertEqual(self.flow.create_asu_health_check_profile(self.user, self.nodes), None)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.select_node_and_cell_names')
    def test_get_names_of_nodes_and_cells__if_required_version_available(self, mock_select):
        mock_select.return_value = self.nodes_names, self.cells_names[:5]
        self.flow.get_names_of_nodes_and_cells(self.user, self.nodes[-1:], self.nodes[:2], self.flow.NUMBER_OF_CELLS)
        self.assertEqual(2, mock_select.call_count)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.select_node_and_cell_names')
    def test_get_names_of_nodes_and_cells__if_required_version_not_available(self, mock_select):
        mock_select.return_value = self.nodes_names, self.cells_names
        self.flow.get_names_of_nodes_and_cells(self.user, [], self.nodes, self.flow.NUMBER_OF_CELLS)
        self.assertEqual(1, mock_select.call_count)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.select_node_and_cell_names')
    def test_get_names_of_nodes_and_cells__if_required_version_available_greater(self, mock_select):
        mock_select.return_value = self.nodes_names, self.cells_names
        self.flow.get_names_of_nodes_and_cells(self.user, self.nodes[-1:], self.nodes[:2], 5)
        self.assertEqual(1, mock_select.call_count)

    def test_select_node_and_cell_names__returns_node_ids_and_cells_names_single_chunk(self):
        response = ["FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-1",
                    "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-3",
                    "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-2"]
        self.user.enm_execute.return_value.get_output.return_value = response
        node_ids_and_cells_names = self.flow.select_node_and_cell_names(self.user, self.nodes, 6)
        self.assertEqual(2, len(node_ids_and_cells_names))
        self.assertEqual(["LTE104dg2ERBS00055", "LTE104dg2ERBS00055", "LTE104dg2ERBS00055"],
                         node_ids_and_cells_names[0])
        self.assertEqual(["LTE104dg2ERBS00055-1", "LTE104dg2ERBS00055-3", "LTE104dg2ERBS00055-2"],
                         node_ids_and_cells_names[1])

    def test_select_node_and_cell_names__returns_node_ids_and_cells_names_multiple_chunks(self):
        response = ["FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-1",
                    "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-3",
                    "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE104dg2ERBS00055,"
                    "ENodeBFunction=1,EUtranCellTDD=LTE104dg2ERBS00055-2"]
        self.user.enm_execute.return_value.get_output.return_value = response
        node_ids_and_cells_names = self.flow.select_node_and_cell_names(self.user, self.nodes * 40, 6)
        self.assertEqual(2, len(node_ids_and_cells_names))
        self.assertEqual(6, len(node_ids_and_cells_names[0]))
        self.assertEqual(6, len(node_ids_and_cells_names[1]))

    def test_select_node_and_cell_names__no_response(self):
        self.user.enm_execute.return_value = []
        node_ids_and_cells_names = self.flow.select_node_and_cell_names(self.user, self.nodes, 7)
        self.assertEqual(2, len(node_ids_and_cells_names))
        self.assertEqual([], node_ids_and_cells_names[0])
        self.assertEqual([], node_ids_and_cells_names[1])

    def test_select_node_and_cell_names__assert_raises_environ_error(self):
        self.assertRaises(EnvironError, self.flow.select_node_and_cell_names, self.user, [], 3)

    def test_group_cells_per_each_flow__success(self):
        self.flow.NUMBER_OF_FLOWS = 1
        list_of_cells_per_flow = self.flow.group_cells_per_each_flow(self.nodes_names, self.cells_names)
        self.assertEqual(1, len(list_of_cells_per_flow))
        self.assertEqual(1, list_of_cells_per_flow[0][0])
        self.assertEqual(3, len(list_of_cells_per_flow[0][1]))
        self.assertEqual(3, len(list_of_cells_per_flow[0][1].values()))

    def test_limit_nodes_and_cells_per_each_flow__cells_limit_500_plus(self):
        dict_nodes_and_cells = self.mock_node_ids_with_cells
        dict_nodes_and_cells["LTE109dg2ERBS00078"] = [str(i) for i in range(600)]
        list_nodes_cells_all_flows = self.flow.limit_nodes_and_cells_per_each_flow(dict_nodes_and_cells, 1)
        self.assertEqual(1, len(list_nodes_cells_all_flows))

    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.partial")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_active_profile_names', return_value=[SETUP_PROFILE])
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.reactivate_nhm_kpi_load')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.reduce_nhm_kpi_load')
    def test_balance_npa_load_with_nhm_setup__nhm_setup_running(self, mock_reduce, *_):
        self.flow.balance_npa_load_with_nhm_setup(self.user)
        self.assertTrue(mock_reduce.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_active_profile_names', return_value=["NPA_01"])
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_balance_npa_load_with_nhm_setup__nhm_setup_not_running(self, mock_log, _):
        self.flow.balance_npa_load_with_nhm_setup(self.user)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.NhmWidget._get_available_kpis",
           return_value=[{u"kpiName": "NHM_SETUP_kpi1", u"active": True},
                         {"kpiName": "NHM_SETUP_kpi2", "active": True}])
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.NhmWidget.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_reduce_nhm_kpi_load__success(self, mock_log, *_):
        response = Mock(ok=True)
        self.user.put.return_value = response
        self.flow.reduce_nhm_kpi_load(self.user)
        self.assertEqual(1, len(self.flow.KPIS_DEACTIVATE))
        mock_log.assert_called_with("Kpis deactivation was Success")

    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.NhmWidget._get_available_kpis",
           return_value=[{u"kpiName": "NHM_SETUP_kpi1", u"active": False},
                         {"kpiName": "NHM_SETUP_kpi2", "active": False}])
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.NhmWidget.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_reduce_nhm_kpi_load__fail(self, mock_log, *_):
        response = Mock(ok=False)
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.reduce_nhm_kpi_load, self.user)
        self.assertTrue(mock_log.called)

    def test_reactivate_nhm_kpi_load__empty_kpis(self):
        self.flow.KPIS_DEACTIVATE = []
        self.flow.reactivate_nhm_kpi_load(self.user)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_active_profile_names', return_value=[SETUP_PROFILE])
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_reactivate_nhm_kpi_load__success_response_ok(self, mock_log, *_):
        self.flow.KPIS_DEACTIVATE = ["kpi1", "kpi2"]
        response = Mock(ok=True)
        self.user.put.return_value = response
        self.flow.reactivate_nhm_kpi_load(self.user)
        mock_log.assert_called_with("Kpis re-activation was Success")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.get_active_profile_names', return_value=[SETUP_PROFILE])
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_reactivate_nhm_kpi_load__success_response_not_ok(self, mock_log, *_):
        self.flow.KPIS_DEACTIVATE = ["kpi1", "kpi2"]
        response = Mock(ok=False)
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.reactivate_nhm_kpi_load, self.user)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_directory_for_npa_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.verify_flow_status')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.prepare_json_file_for_npa_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_npa_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_task_set__flow_execution_success(self, mock_log, mock_create_flow, mock_prepare_json, mock_flow_status,
                                              *_):
        self.flow.task_set(self.node_ids_with_cells_flow_instance, self.user, 'test-name', self.flow)
        self.assertEqual(self.mock_node_ids_with_cells, mock_prepare_json.call_args[0][0])
        self.assertEqual('test-name', mock_prepare_json.call_args[0][1])
        self.assertIn("npa_flow_input.json", mock_prepare_json.call_args[0][2])
        self.assertEqual(3, len(mock_create_flow.call_args[0]))
        self.assertEqual(2, len(mock_flow_status.call_args[0]))
        self.assertEqual(3, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_directory_for_npa_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.create_npa_flow', side_effect=HTTPError)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.prepare_json_file_for_npa_flow')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.add_error_as_exception')
    def test_task_set__flow_execution_add_error_as_exception(self, mock_error, *_):
        self.flow.task_set(self.node_ids_with_cells_flow_instance, self.user, 'test-name', self.flow)
        self.assertIsInstance(mock_error.call_args[0][0], EnmApplicationError)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.filesystem.does_dir_exist', return_value=True)
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.partial")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.delete_directory_for_npa_flow')
    def test_create_directory_for_npa_flow__directory_does_not_exists(self, *_):
        self.flow.create_directory_for_npa_flow("/home/enmutils/npa01/npa_2014")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.filesystem.create_dir')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.filesystem.does_dir_exist', return_value=False)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.partial')
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.delete_directory_for_npa_flow')
    def test_create_directory_for_npa_flow__directory_exists(self, *_):
        self.flow.create_directory_for_npa_flow("/home/enmutils/npa01/npa_1420")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.filesystem.remove_dir')
    def test_delete_directory_for_npa_flow__success(self, _):
        self.flow.delete_directory_for_npa_flow("/home/enmutils/npa01/npa_0809")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_delete_health_check_profile__success(self, mock_log):
        response = Mock(status_code=200)
        self.user.post.return_value = response
        self.flow.delete_health_check_profile(self.user, 'test-name')
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_delete_health_check_profile__exception(self, mock_log):
        self.user.post.side_effect = Exception
        self.flow.delete_health_check_profile(self.user, 'test-name')
        self.assertEqual(mock_log.call_count, 2)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.partial')
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.stop_npa_flow_in_ui')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_create_npa_flow__successful_response(self, mock_log, *_):
        response = Mock(status_code=200)
        self.user.post.return_value = response
        self.flow.create_npa_flow(self.user, "NPA01Time08200914Flow2", "/NPA_01/npa_flow_input.json")
        mock_log.assert_called_with("Completed creating NPA_01 new flow with name NPA01Time08200914Flow2")

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.raise_for_status')
    def test_create_npa_flow__failed_response(self, mock_raise_error, *_):
        request = Mock(headers={'Accept': 'application/json'}, body="asu_payload")
        response = Mock(status_code=404, request=request)
        self.user.post.return_value = response
        self.flow.create_npa_flow(self.user, "NPA01Time09140820Flow2", "/NPA_01/npa_flow_input.json")
        self.assertTrue(mock_raise_error.called)

    def test_get_current_state_of_npa_flow__response_not_ok(self):
        response = Mock(ok=False)
        self.user.get.return_value = response
        self.assertRaises(JobValidationError, self.flow.get_current_state_of_npa_flow,
                          self.user, "NPA01Time08200914Flow2")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_get_current_state_of_npa_flow__response_ok(self, mock_log):
        response = Mock(ok=True)
        response.json.return_value = [{"state": "Executed", "summaryReport": "Execution phase completed"}]
        self.user.get.return_value = response
        flow_state = self.flow.get_current_state_of_npa_flow(self.user, "NPA01Time08200914Flow2")
        mock_log.assert_called_with("NPA_01 NPA Flow: NPA01Time08200914Flow2 current state is: Executed and "
                                    "summary report is: Execution phase completed")
        self.assertEqual("Executed", flow_state)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Executing")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_verify_flow_status__state_executing(self, mock_log, *_):
        self.flow.verify_flow_status(self.user, "NPA01Time08200914Flow2")
        self.assertEqual(3, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Execute")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_verify_flow_status__state_execute_raises_enm_application_error(self, *_):
        self.assertRaises(EnmApplicationError, self.flow.verify_flow_status, self.user, "NPA01Time08200914Flow2")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Setup Phase")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_verify_flow_status__state_setup_raises_enm_application_error(self, *_):
        self.assertRaises(EnmApplicationError, self.flow.verify_flow_status, self.user, "NPA01Time08200914Flow2")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Setup Failed")
    def test_verify_flow_status__state_fail_raises_enm_application_error(self, _):
        self.assertRaises(EnmApplicationError, self.flow.verify_flow_status, self.user, "NPA01Time08200914Flow2")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Setup Phase")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_stop_npa_flow_in_ui__flow_cannot_be_stopped(self, mock_log, _):
        self.flow.stop_npa_flow_in_ui(self.user, "NPA01Time08200914Flow1")
        mock_log.assert_called_with("NPA flow: NPA01Time08200914Flow1 state is in Setup Phase and cannot be stopped "
                                    "forcefully. Note: Also there is a chance that flow resumes its execution at "
                                    "later point of time")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Executing")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_stop_npa_flow_in_ui__response_ok(self, mock_log, _):
        response = Mock(ok=True)
        self.user.put.return_value = response
        self.flow.stop_npa_flow_in_ui(self.user, "NPA01Time08200914Flow1")
        mock_log.assert_called_with("NPA flow: NPA01Time08200914Flow1 stop Completed")

    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.Npa01Flow.get_current_state_of_npa_flow',
           return_value="Execute")
    @patch('enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug')
    def test_stop_npa_flow_in_ui__response_not_ok(self, mock_log, _):
        response = Mock(ok=False)
        self.user.put.return_value = response
        self.flow.stop_npa_flow_in_ui(self.user, "NPA01Time08200914Flow1")
        mock_log.assert_called_with("NPA flow: NPA01Time08200914Flow1 stop Failed")

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.load")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dump")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_prepare_json_file_for_npa_flow__create_json_file(self, mock_log, *_):
        self.flow.prepare_json_file_for_npa_flow(self.mock_node_ids_with_cells, 'test-name',
                                                 "/asu/npa01_2020/flow-input.json")
        self.assertTrue(mock_log.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.load")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.json.dump")
    @patch("enmutils_int.lib.profile_flows.npa_flows.npa_flow.log.logger.debug")
    def test_prepare_json_file_for_npa_flow__no_health_check_profile(self, mock_log, *_):
        self.flow.prepare_json_file_for_npa_flow(self.mock_node_ids_with_cells, '', "/asu/npa01_2020/flow-input.json")
        self.assertTrue(mock_log.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
