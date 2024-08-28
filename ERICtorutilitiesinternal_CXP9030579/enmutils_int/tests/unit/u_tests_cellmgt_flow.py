#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ViewAllLteCellsInTheNetwork, \
    CreateAndDeleteCells, ReadCellDataForDifferentNodes, ExecuteModifyCellParameters, CreateDeleteCellsAndRelationsFlow, \
    LockUnlockAllCellsOnAnNode
from enmutils_int.lib.cell_management import RncCreateDeleteCells, CreateDeleteCellsObject, ERBSCreateDeleteCells

from enmutils_int.lib.profile import Profile
from testslib import unit_test_utils

GERAN_CELL_RELATIONS = [
    {
        "sourceFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003351",
        "relationFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003351,ExternalGeranCellRelation=1020731",
        "targetFdn": "SubNetwork=NETSimG,MeContext=MSC37BSC74,ManagedElement=MSC37BSC74,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1020731",
        "targetCellGlobalIdentity": {}
    },
    {
        "sourceFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003351",
        "relationFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003351,ExternalGeranCellRelation=1010630",
        "targetFdn": "SubNetwork=NETSimG,MeContext=MSC18BSC36,ManagedElement=MSC18BSC36,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1010630",
        "targetCellGlobalIdentity": {}
    },
    {
        "sourceFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356",
        "relationFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356,ExternalGeranCellRelation=43",
        "targetFdn": "",
        "targetCellGlobalIdentity": {"mnc": 999, "cellIdentity": 43, "mcc": 999, "lac": 9998}
    },
    {
        "sourceFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356",
        "relationFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356,ExternalGeranCellRelation=50",
        "targetFdn": "",
        "targetCellGlobalIdentity": {"mnc": 800, "cellIdentity": 50, "mcc": 800, "lac": 8000}
    },
    {
        "sourceFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356",
        "relationFdn": "SubNetwork=NETSimG,MeContext=MSC06BSC12,ManagedElement=MSC06BSC12,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1003356,ExternalGeranCellRelation=60",
        "targetFdn": "",
        "targetCellGlobalIdentity": {"mnc": 800, "cellIdentity": 60, "mcc": 800, "lac": 8000}
    }
]


class ReadCellDataForDifferentNodesUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = ReadCellDataForDifferentNodes()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.exchange_nodes')
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    def test_read_cell_data_for_different_nodes_execute_flow__successful(self, mock_create_users, mock_nodes_list,
                                                                         mock_add_error, mock_tq, *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = self.nodes

        self.cell_profile.execute_flow()

        self.assertTrue(mock_tq.called)
        self.assertFalse(mock_add_error.called)

    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    def test_read_cell_data_for_different_nodes_execute_flow__adds_error_if_no_nodes(self, mock_create_users,
                                                                                     mock_nodes_list, mock_add_error):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = []
        self.assertFalse(self.cell_profile.execute_flow())
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.exchange_nodes')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    def test_read_cell_data_for_different_nodes_execute_flow__adds_error_if_no_poids(self, mock_create_users,
                                                                                     mock_nodes_list, mock_add_error,
                                                                                     mock_exchange_nodes, *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = self.nodes
        self.cell_profile.execute_flow()
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.exchange_nodes')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ReadCellDataForDifferentNodes.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    def test_read_cell_data_for_different_nodes_execute_flow__error_exchanging_nodes(self, mock_create_users,
                                                                                     mock_nodes_list, mock_add_error,
                                                                                     mock_exchange_nodes, *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = self.nodes
        self.cell_profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_exchange_nodes.call_count, 1)

    def test_calculate_num_nodes_per_available_user__no_noid_poids(self):
        mock_list_of_node_poids = []
        self.assertTrue(0 or 1, self.cell_profile.calculate_num_nodes_per_available_user(mock_list_of_node_poids))


class ViewAllLteCellsInTheNetworkUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = ViewAllLteCellsInTheNetwork()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ViewAllLteCellsInTheNetwork.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt', return_value=[Mock()])
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[Mock()])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_view_all_lte_cells_in_the_network_execute_flow__success(self, mock_add_error_as_exception, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(0, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile.Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ViewAllLteCellsInTheNetwork.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt', side_effect=Exception)
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[Mock()])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_view_all_lte_cells_in_the_network_execute_flow__add_error_as_exception(self, mock_add_error_as_exception,
                                                                                    *_):
        self.cell_profile.execute_flow()
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile.Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ViewAllLteCellsInTheNetwork.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    def test_view_all_lte_cells_in_the_network_execute_flow__no_poids(self, mock_fetch_cell_fdns, *_):
        mock_fetch_cell_fdns.return_value = [Mock()]
        self.cell_profile.execute_flow()
        self.assertEqual(0, mock_fetch_cell_fdns.call_count)

    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_view_all_lte_cells_in_the_network_execute_flow__add_error_as_exception_when_no_poid_data_avalibale(self,
                                                                                                                mock_add_error_as_exception, *_):
        self.cell_profile.execute_flow()
        self.assertTrue(mock_add_error_as_exception.assert_not_called)


class CreateAndDeleteCellsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = CreateAndDeleteCells()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.state')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.node_pool_mgr.filter_unsynchronised_nodes', return_value=["BSC01"])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.generate_resources_for_create_delete',
        return_value=([Mock()], [Mock()]))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.determine_usable_node_fdns')
    @patch('enmutils_int.lib.network_mo_info.group_mos_by_node')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    def test_create_and_delete_cells_execute_flow__no_failed_creates(self, mock_add_error, mock_create_threads, *_):
        self.cell_profile.RELATION_TYPE = "GeranCellRelation"
        self.cell_profile.RELATIONS_TO_DELETE = ['Relation1']
        self.cell_profile.execute_flow()
        self.assertEqual(2, mock_create_threads.call_count)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.state')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    @patch('enmutils_int.lib.network_mo_info.group_mos_by_node')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.generate_resources_for_create_delete',
        return_value=([Mock()], [Mock()]))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.determine_usable_node_fdns')
    @patch('enmutils_int.lib.node_pool_mgr.filter_unsynchronised_nodes', return_value=["BSC01"])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.clean_up_failed_creates')
    def test_create_and_delete_cells_execute_flow__clean_up_failed_creates_called(self, mock_failed_creates, *_):
        self.cell_profile.RELATION_TYPE = "GeranCellRelation"
        self.cell_profile.RELATIONS_TO_DELETE = []
        self.cell_profile.FAILED_CREATES = ["Cell1"]
        self.cell_profile.execute_flow()
        self.assertEqual(1, mock_failed_creates.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.determine_usable_node_fdns')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.generate_resources_for_create_delete',
        return_value=([], []))
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.node_pool_mgr.filter_unsynchronised_nodes', return_value=["BSC01"])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    def test_create_and_delete_cells_execute_flow__adds_error_empty_user_node_list(self, mock_add_error, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.state')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.determine_usable_node_fdns',
           side_effect=EnmApplicationError('Error'))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.log.logger.debug')
    def test_create_and_delete_cells_execute_flow__max_read_attempts_reached(self, mock_debug, mock_add_error, *_):
        self.cell_profile.execute_flow()
        mock_debug.assert_called_once_with('Profile will now go to COMPLETED state until manual intervention')
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.group_mos_by_node')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_nodes_with_fdn_result',
           return_value=[Mock()] * 2)
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_fdn_for_nodes',
           return_value=[['FDN1', 'FDN2'], ['FDN3', 'FDN4']])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.create_target_gsm_cgi_proxy_object')
    def test_generate_resources_for_create_delete(self, *_):
        user_fdn_list, matched_nodes = self.cell_profile.generate_resources_for_create_delete(
            Mock(), [Mock()], [Mock()] * 2)

        self.assertEqual(2, len(user_fdn_list))
        self.assertEqual(2, len(matched_nodes))

    @patch('time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.remove_invalid_cardinality_cells',
        return_value=['Cell1', 'Cell2'])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.create_list_of_node_poids')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    def test_determine_usable_node_fdns__fetch_cell_fdns_fails(self, mock_add_error, mock_fetch_cell_fdns, *_):
        http_error = HTTPError('Error')  # Need the same error object to assert on
        mock_fetch_cell_fdns.side_effect = [http_error, ['Cell1', 'Cell2']]
        self.cell_profile.determine_usable_node_fdns(Mock(), Mock(), 'GSM', 'GeranCell')
        mock_add_error.assert_called_once_with(http_error)

    @patch('time.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.create_list_of_node_poids')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt',
        return_value=['Cell1', 'Cell2'])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.remove_invalid_cardinality_cells')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_determine_usable_node_fdns__remove_invalid_cardinality_cells_fails(self, mock_add_error,
                                                                                mock_remove_invalid_cells, *_):
        enm_application_error = EnmApplicationError('Error')  # Need the same error object to assert on
        mock_remove_invalid_cells.side_effect = [enm_application_error, ['Cell1', 'Cell2']]
        self.cell_profile.determine_usable_node_fdns(Mock(), Mock(), 'GSM', 'GeranCell')
        mock_add_error.assert_called_once_with(enm_application_error)

    def test_get_nodes_with_fdn_result(self):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        list_of_fdn_keys = ["BSC01", "BSC03", "BSC04"]
        result = self.cell_profile.get_nodes_with_fdn_result(nodes, list_of_fdn_keys)
        expected = [node]
        self.assertEqual(expected, result)
        result = self.cell_profile.get_nodes_with_fdn_result(nodes, [])
        self.assertEqual([], result)
        result = self.cell_profile.get_nodes_with_fdn_result([], [])
        self.assertEqual([], result)

    def test_get_fdn_for_nodes__successful(self):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        self.cell_profile.NUM_CELLS_PER_USER = 2
        fdns = {"BSC01": ["FDN1", "FDN2", "FDN3"], "BSC02": ["FDN1"]}
        result = self.cell_profile.get_fdn_for_nodes(nodes, fdns)
        expected = [["FDN1", "FDN2"], ["FDN1"]]
        self.assertListEqual(expected, result)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    def test_get_fdn_for_nodes__catches_type_error(self, mock_add_error):
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        nodes = [node, node1]
        self.cell_profile.NUM_CELLS_PER_USER = 2
        fdns = {"BSC03": ["FDN1", "FDN2", "FDN3"], "BSC02": ["FDN1"]}
        self.cell_profile.get_fdn_for_nodes(nodes, fdns)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.cellmgt.get_cell_relations')
    def test_get_gsm_relation_info__successful_get_relations(self, mock_get_cell_relations):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'successfulMoOperations': ["Some FDN"]}
        mock_get_cell_relations.return_value = response
        self.assertEqual(["Some FDN"], self.cell_profile.get_gsm_relation_info(self.user, ["FDN1"]))

    @patch('time.sleep')
    @patch('enmutils_int.lib.cellmgt.get_cell_relations', side_effect=HTTPError("Bad request"))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    def test_get_gsm_relation_info__catch_request_exception_error_raise_and_enm_application_error(self, *_):
        with self.assertRaises(EnmApplicationError):
            self.cell_profile.get_gsm_relation_info(self.user, ["FDN1"])

    @patch('time.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    @patch('enmutils_int.lib.cellmgt.get_cell_relations')
    def test_get_gsm_relation_info__handle_failed_operations(self, mock_get_cell_relations, mock_add_error, *_):
        response = Mock()
        response.json.return_value = {u'successfulMoOperations': [], u'failedMoOperations': ["FDN"]}
        mock_get_cell_relations.return_value = response
        with self.assertRaises(EnmApplicationError):
            self.cell_profile.get_gsm_relation_info(self.user, ["FDN1"])
        self.assertEqual(3, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.cmedit_clean_up',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.check_cgi_in_reserved_range',
           side_effect=[True, False, True])
    def test_validate_gsm_relations__remove_relations(self, *_):
        geran_relations = GERAN_CELL_RELATIONS
        result = self.cell_profile.validate_gsm_relations(Mock(), geran_relations)
        self.assertEqual(len(result), 4)

    def test_check_cgi_in_reserved_range(self):
        self.cell_profile.RESERVED_CGI_VALUE = {"mnc": 999, "mcc": 999, "lac": 9998}
        cgi_values = [{"mnc": 999, "cellIdentity": 43, "mcc": 999, "lac": 9998},
                      {"mnc": 900, "cellIdentity": 50, "mcc": 900, "lac": 9000}]

        self.assertTrue(self.cell_profile.check_cgi_in_reserved_range(cgi_values[0]))
        self.assertFalse(self.cell_profile.check_cgi_in_reserved_range(cgi_values[1]))

    @patch(
        "enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.clean_up_external_geran_cells")
    @patch("enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.validate_gsm_relations")
    @patch("enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_gsm_relation_info")
    def test_clean_up_failed_creates__successful(self, mock_relation_info, *_):
        failed_cells = [relation["sourceFdn"] for relation in GERAN_CELL_RELATIONS]

        self.cell_profile.clean_up_failed_creates(Mock(), failed_cells)
        self.assertEqual(mock_relation_info.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.clean_up_external_geran_cells")
    @patch("enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.validate_gsm_relations")
    @patch("enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_gsm_relation_info",
           side_effect=EnmApplicationError("Error"))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.log.logger.debug')
    def test_clean_up_failed_creates__catch_error(self, mock_debug, *_):
        failed_cells = [relation["sourceFdn"] for relation in GERAN_CELL_RELATIONS]
        self.cell_profile.clean_up_failed_creates(Mock(), failed_cells)
        self.assertEqual(mock_debug.call_count, 1)

    def test_cmedit_clean_up(self):
        user = Mock()
        user.enm_execute.side_effect = [True, Exception("Error")]
        self.assertTrue(self.cell_profile.cmedit_clean_up("GeranCellRelation", user))
        self.assertFalse(self.cell_profile.cmedit_clean_up("GeranCellRelation", user))

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.cmedit_clean_up')
    def test_clean_up_external_geran_cells__successful_cleanup(self, mock_cmedit_clean_up):
        self.cell_profile.RESERVED_CGI_VALUE = {"mnc": 999, "mcc": 999, "lac": 9998}
        node_fdns = ["Node1", "Node2"]
        output = ["FDN : SubNetwork=NETSimG,MeContext=MSC31BSC62....ExternalGeranCell=1003777", "cgi : 046-04-19-3777",
                  "FDN : SubNetwork=NETSimG,MeContext=MSC31BSC62....ExternalGeranCell=1003804",
                  "cgi : 999-999-9998-3804",
                  "FDN : SubNetwork=NETSimG,MeContext=MSC31BSC62....ExternalGeranCell=1003812", "cgi : 046-04-20-3812",
                  "3 instance(s)"]
        response_output = Mock()
        response_output.get_output.return_value = output
        mock_user = Mock()
        mock_user.enm_execute.return_value = response_output
        self.cell_profile.clean_up_external_geran_cells(mock_user, node_fdns)
        self.assertEqual(2, mock_cmedit_clean_up.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.cmedit_clean_up',
           side_effect=Exception("Error"))
    def test_clean_up_external_geran_cells__catch_exception(self, mock_cmedit_clean_up, mock_debug):
        self.cell_profile.RESERVED_CGI_VALUE = {"mnc": 999, "mcc": 999, "lac": 9998}
        node_fdns = ["Node1"]
        output = ["FDN : SubNetwork=NETSimG,MeContext=MSC31BSC62....ExternalGeranCell=1003804",
                  "cgi : 999-999-9998-3804",
                  "1 instance(s)"]
        response_output = Mock()
        response_output.get_output.return_value = output
        mock_user = Mock()
        mock_user.enm_execute.return_value = response_output
        self.cell_profile.clean_up_external_geran_cells(mock_user, node_fdns)
        self.assertEqual(1, mock_cmedit_clean_up.call_count)
        mock_debug.assert_called_with("Could not verify the clean up of cells for Node1 due to Error")

    @patch('time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.remove_invalid_cardinality_cells',
        return_value=['Cell1', 'Cell2'])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.create_list_of_node_poids',
           return_value=['12345', '6789'])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    def test_determine_usable_node_fdns__no_exceptions(self, mock_fetch_fdns, *_):
        fdns = self.cell_profile.determine_usable_node_fdns(Mock(), Mock(), 'GSM', 'GeranCell')
        self.assertEqual(['Cell1', 'Cell2'], fdns)
        self.assertEqual(1, mock_fetch_fdns.call_count)

    @patch('time.sleep')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.create_list_of_node_poids')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt',
        return_value=['Cell1', 'Cell2'])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.add_error_as_exception')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.remove_invalid_cardinality_cells',
        side_effect=EnmApplicationError('Error'))
    def test_determine_usable_node_fdns__max_read_attempts_reached(self, mock_remove_invalid_cells, *_):
        with self.assertRaises(EnmApplicationError):
            self.cell_profile.determine_usable_node_fdns(Mock(), Mock(), 'GSM', 'GeranCell')
        self.assertEqual(20, mock_remove_invalid_cells.call_count)

    def test_get_cell_relation_cardinality(self):
        relations = [
            {u'sourceFdn': u"ManagedElement=BSC01,BscFunction,GeranCell=Cell1",
             u'targetFdn': u"ManagedElement=BSC02,BscFunction,GeranCell=Cell1"},
            {u'sourceFdn': u"ManagedElement=BSC01,BscFunction,GeranCell=Cell1",
             u'targetFdn': u"ManagedElement=BSC02,BscFunction,GeranCell=Cell2"},
            {u'sourceFdn': u"ManagedElement=BSC02,BscFunction,GeranCell=Cell2",
             u'targetFdn': u"ManagedElement=BSC03,BscFunction,GeranCell=Cell1"}
        ]

        expected_result = {"BSC01": {"Cell1": 2}, "BSC02": {"Cell2": 1}}
        result = self.cell_profile.get_cell_relation_cardinality(relations)
        self.assertEqual(expected_result, result)

    def test_get_max_cardinality_cells(self):
        relation_cardinality = {"BSC01": {"Cell1": 2, "Cell2": 20}, "BSC02": {"Cell1": 10, "Cell2": 15}}
        result = self.cell_profile.get_max_cardinality_cells(relation_cardinality, max_cardinality=3)
        expected = [("BSC01", "Cell2"), ("BSC02", "Cell1"), ("BSC02", "Cell2")]
        self.assertListEqual(result, expected)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.validate_gsm_relations')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_gsm_relation_info')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_cell_relation_cardinality')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_max_cardinality_cells')
    def test_remove_invalid_cardinality_cells(self, mock_max_cardinality, mock_cell_relation_caridnality, *_):
        mock_max_cardinality.return_value = [("MSC24BSC48", "84"), ("MSC24BSC49", "84")]
        mock_cell_relation_caridnality.return_value = {"MSC24BSC48": {"84": 64}, "MSC24BSC49": {"84": 64}}
        fdn_list = [u'SubNetwork=NETSimG,MeContext=MSC24BSC48,ManagedElement=MSC24BSC48,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84',
                    u'SubNetwork=NETSimG,MeContext=MSC24BSC47,ManagedElement=MSC24BSC47,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84',
                    u'SubNetwork=NETSimG,MeContext=MSC24BSC49,ManagedElement=MSC24BSC49,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84']
        expected_result = [fdn_list[1]]
        result = self.cell_profile.remove_invalid_cardinality_cells(self.user, fdn_list)
        self.assertListEqual(result, expected_result)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.validate_gsm_relations')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_gsm_relation_info')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_max_cardinality_cells')
    def test_remove_invalid_cardinality_cells_n0_exceeds(self, mock_max_cardinality, *_):
        mock_max_cardinality.return_value = []
        fdn_list = [u'SubNetwork=NETSimG,MeContext=MSC24BSC48,ManagedElement=MSC24BSC48,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84',
                    u'SubNetwork=NETSimG,MeContext=MSC24BSC47,ManagedElement=MSC24BSC47,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84',
                    u'SubNetwork=NETSimG,MeContext=MSC24BSC49,ManagedElement=MSC24BSC49,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=84']
        result = self.cell_profile.remove_invalid_cardinality_cells(self.user, fdn_list)
        self.assertListEqual(result, fdn_list)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateAndDeleteCells.get_gsm_relation_info',
           side_effect=EnmApplicationError("Error"))
    def test_remove_invalid_cardinality_cells__raises_enm_application_error(self, *_):
        fdn_list = [""]
        with self.assertRaises(EnmApplicationError):
            self.cell_profile.remove_invalid_cardinality_cells(self.user, fdn_list)

    def test_create_target_gsm_cgi_proxy_object(self):
        self.cell_profile.MO_ID_START_RANGE = 40
        self.cell_profile.RESERVED_CGI_VALUE = {"mnc": 999, "mcc": 999, "lac": 9998}

        result = self.cell_profile.create_target_gsm_cgi_proxy_object("MSC02", 4)
        self.assertIn("ncc", result[0].get('attributes').get("ExternalGeranCell").keys())
        self.assertTrue(result[0].get('attributes').get("ExternalGeranCell").get('ncc').isdigit())
        self.assertEqual(4, len(result))
        self.assertEqual(type(result[0]), dict)

    def test_create_target_gsm_cgi_proxy_object__creates_unique_cgi(self):
        self.cell_profile.MO_ID_START_RANGE = 40
        self.cell_profile.RESERVED_CGI_VALUE = {"mnc": 999, "mcc": 999, "lac": 9998}

        results = self.cell_profile.create_target_gsm_cgi_proxy_object("MSC02", 4)
        cgis = [result.get("cellGlobalIdentity").get("cellIdentity") for result in results]
        self.assertEqual(4, len(set(cgis)))
        self.assertListEqual([40, 41, 42, 43], cgis)


class ExecuteModifyCellParametersUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = ExecuteModifyCellParameters()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.exceptions.EnvironError")
    def test_populate_teardown_list__success(self, mock_exception, *_):
        mock_node_cell_data = {"EUtranCellFDD": {
            "cell_fdn_A1": {"DEFAULT": {"attribute_values_default": {"NEW": {"attribute_values_new"}}}}}}
        self.cell_profile.populate_teardown_list(mock_node_cell_data)
        self.assertTrue(mock_exception.assert_not_called)

    @patch("enmutils.lib.exceptions.EnvironError")
    def test_populate_teardown_list__empty_attribute(self, mock_exception, *_):
        mock_node_cell_data = {"EUtranCellFDD": {"cell_fdn_A1": {"DEFAULT": {}}}}
        with self.assertRaises(EnvironError):
            self.cell_profile.populate_teardown_list(mock_node_cell_data)

    @patch("enmutils.lib.exceptions.EnvironError")
    def test_populate_teardown_list__null_value_for_attribute(self, mock_exception, *_):
        mock_node_cell_data = {"EUtranCellFDD": {"cell_fdn_A1": {"DEFAULT": {"attribute_values_default": ""}}}}
        with self.assertRaises(EnvironError):
            self.cell_profile.populate_teardown_list(mock_node_cell_data)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.populate_teardown_list')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.populate_node_cell_data')
    def test_prepare_data_for_use_during_each_iteration__return_multiple_cell_data(self, mock_populate, *_):
        self.cell_profile.REQUIRED_NUMBER_OF_CELLS_PER_NODE = 40
        self.cell_profile.MO_TYPE = "EUtranCellFDD"
        self.cell_profile.MO_ATTRIBUTE_DATA = {
            "EUtranCellFDD": {"cell_fdn_A1": {"DEFAULT": "attribute_values_default", "NEW": "attribute_values_new"}},
            "EUtranCellTDD": {"cell_fdn_B1": {"DEFAULT": "attribute_values_default", "NEW": "attribute_values_new"}}}
        node2 = Mock(lte_cell_type=None)
        self.nodes.append(node2)
        expected = {'Node': 'Some data', 'Node1': 'Some data1'}
        mock_populate.side_effect = [{"Node": "Some data"}, {"Node1": "Some data1"}]
        self.assertDictEqual(expected, self.cell_profile.prepare_data_for_use_during_each_iteration(user=Mock(),
                                                                                                    nodes=self.nodes))
        self.assertEqual(2, mock_populate.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.populate_teardown_list')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.populate_node_cell_data')
    def test_prepare_data_for_use_during_each_iteration__single_mo_type(self, mock_populate, *_):
        self.cell_profile.REQUIRED_NUMBER_OF_CELLS_PER_NODE = 40
        self.cell_profile.MO_TYPE = "UtranCell"
        self.cell_profile.MO_ATTRIBUTE_DATA = {}
        expected = {'Node': 'Some data'}
        mock_populate.return_value = expected
        self.assertDictEqual(expected, self.cell_profile.prepare_data_for_use_during_each_iteration(user=Mock(),
                                                                                                    nodes=self.nodes))
        self.assertEqual(1, mock_populate.call_count)

    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.add_error_as_exception')
    @patch('enmutils_int.lib.cellmgt.update_cells_attributes_via_cell_management')
    @patch('enmutils_int.lib.profile.Profile.keep_running')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ExecuteModifyCellParameters.prepare_data_for_use_during_each_iteration')
    def test_execute_modify_cell_parameters_execute_flow(self, mock_prepare, mock_keep_running, mock_update_cells,
                                                         mock_add_error, *_):
        node_cell_data = {
            "node_name": {"cell_fdn_A1": {"DEFAULT": "attribute_values_default", "NEW": "attribute_values_new"}},
            "node_name2": {"cell_fdn_B1": {"DEFAULT": "attribute_values_default", "NEW": "attribute_values_new"}}}

        mock_prepare.side_effect = [EnvironError, node_cell_data]

        self.cell_profile.execute_flow()
        self.assertEqual(2, mock_add_error.call_count)

        mock_keep_running.side_effect = [True, True, False]
        mock_update_cells.side_effect = ["blah", Exception]
        self.cell_profile.execute_flow()
        self.assertEqual(4, mock_add_error.call_count)


class CreateDeleteCellsAndRelationsFlowUnitTests(unittest2.TestCase):

    @patch("__builtin__.super")
    def setUp(self, *_):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = CreateDeleteCellsAndRelationsFlow()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ERBSCreateDeleteCells.create_cells')
    def test_create_cells_flow__successful(self, _):
        mock_obj = ERBSCreateDeleteCells(self.cell_profile, user=Mock(), node=Mock(lte_cell_type="FDD"))
        mock_obj.created_cells = ['cell1', 'cell2']
        self.assertTrue(self.cell_profile.create_cells_flow([mock_obj]))

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.ERBSCreateDeleteCells.create_cells')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.add_error_as_exception')
    def test_create_cells_flow__fails(self, mock_add_error, *_):
        mock_node = Mock(lte_cell_type=None)
        mock_node.node_id = 'RNC11'
        mock_obj = CreateDeleteCellsObject(self.cell_profile, Mock(), mock_node)
        mock_obj.created_cells = []
        self.assertFalse(self.cell_profile.create_cells_flow([mock_obj]))
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.delete_all_cells')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.reset')
    def test_delete_cells_flow(self, mock_reset, mock_delete, *_):
        mock_obj = CreateDeleteCellsObject(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        self.cell_profile.delete_cells_flow([mock_obj])
        self.assertEqual(1, mock_reset.call_count)
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup_completed', new_callable=PropertyMock,
           side_effect=[False, True, False, False, True])
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    def test_setup_create_delete_objects(self, mock_sleep, mock_setup, *_):
        mock_obj = CreateDeleteCellsObject(self.cell_profile, user=Mock(), node=Mock(lte_cell_type="FDD"))
        self.cell_profile.setup_create_delete_objects([mock_obj])
        self.assertEqual(2, mock_setup.call_count)
        self.assertEqual(1, mock_sleep.call_count)

    def test_get_create_delete_object_list__rnc_node(self):
        self.cell_profile.SUPPORTED_NODE_TYPES = ["RNC"]
        mock_node = Mock()
        mock_node.node_id = 'RNC11'
        mock_node.lte_cell_type = None
        self.assertEqual(RncCreateDeleteCells, type(
            self.cell_profile.get_create_delete_object_list(Mock(), [mock_node])[0]))

    def test_get_create_delete_object_list__erbs_node(self):
        self.cell_profile.SUPPORTED_NODE_TYPES = ["ERBS"]
        mock_node = Mock()
        mock_node.node_id = 'LTE01ERBS00048'
        mock_node.lte_cell_type = "FDD"
        self.assertEqual(ERBSCreateDeleteCells, type(
            self.cell_profile.get_create_delete_object_list(Mock(), [mock_node])[0]))

    def test_get_create_delete_object_list__unsupported_node(self):
        self.cell_profile.SUPPORTED_NODE_TYPES = ["abc"]
        self.assertEqual(None, self.cell_profile.get_create_delete_object_list(Mock(), Mock(lte_cell_type="FDD")))

    @patch('enmutils_int.lib.cell_management.RncCreateDeleteCells.create_relations')
    def test_create_relations_flow(self, mock_create_relations):
        node1, node2 = Mock(lte_cell_type=None), Mock(lte_cell_type=None)
        node1.node_id, node2.node_id = "RNC11", "RNC12"
        mock_obj_list = [RncCreateDeleteCells(self.cell_profile, Mock(), node1),
                         RncCreateDeleteCells(self.cell_profile, Mock(), node2)]
        self.cell_profile.create_relations_flow(mock_obj_list)
        self.assertEqual(2, mock_create_relations.call_count)

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.'
           'CreateDeleteCellsAndRelationsFlow.get_synchronised_nodes', return_value=[Mock()])
    @patch('time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.delete_relations_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.keep_running',
           side_effect=[True, True, False])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.setup_create_delete_objects')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.get_create_delete_object_list')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.get_nodes_list_by_attribute', return_value=Mock())
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_relations_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.delete_cells_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_cells_flow',
        side_effect=[True, False])
    def test_create_delete_cells_and_relations_execute_flow__is_successful(self, mock_create_cells, mock_delete_cells,
                                                                           mock_create_relations, mock_nodes_list, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(2, mock_create_cells.call_count)
        self.assertEqual(1, mock_create_relations.call_count)
        self.assertEqual(1, mock_delete_cells.call_count)
        self.assertEqual(3, len(mock_nodes_list.call_args[1]["node_attributes"]))

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.'
           'CreateDeleteCellsAndRelationsFlow.get_synchronised_nodes', return_value=[])
    @patch('time.sleep')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.state',
           new_callable=PropertyMock, return_value=None)
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.delete_relations_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.keep_running',
           side_effect=[True, False])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.setup_create_delete_objects')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.get_create_delete_object_list')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.get_nodes_list_by_attribute',
        return_value=Mock())
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_relations_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.delete_cells_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.create_cells_flow',
        side_effect=[True, False])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.CreateDeleteCellsAndRelationsFlow.add_error_as_exception')
    def test_create_delete_cells_and_relations_execute_flow__adds_exception_when_no_synced_nodes(self,
                                                                                                 mock_add_error_as_exception,
                                                                                                 mock_create_cells,
                                                                                                 mock_delete_cells,
                                                                                                 mock_create_relations,
                                                                                                 mock_nodes_list, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(0, mock_create_cells.call_count)
        self.assertEqual(0, mock_create_relations.call_count)
        self.assertEqual(0, mock_delete_cells.call_count)
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cellmgt.delete_cell_relation')
    def test_delete_relations_flow__success(self, mock_delete):
        created_obj = Mock(relations_created_on_cell=["Rel", "Rel1"])
        created_obj1 = Mock()
        delattr(created_obj1, 'relations_created_on_cell')
        self.cell_profile.delete_relations_flow(Mock(), [created_obj, created_obj1])
        self.assertEqual(2, mock_delete.call_count)

    @patch('enmutils_int.lib.cellmgt.delete_cell_relation', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.log.logger.debug')
    def test_delete_relations_flow__logs_exception(self, mock_debug, _):
        created_obj = Mock(relations_created_on_cell=["Rel", "Rel1"])
        self.cell_profile.delete_relations_flow(Mock(), [created_obj])
        self.assertEqual(2, mock_debug.call_count)
        mock_debug.assert_called_with("Error")


class LockUnlockAllCellsOnAnNodeUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = LockUnlockAllCellsOnAnNode()
        self.cell_profile.NUM_USERS = 1
        self.cell_profile.USER_ROLES = ['ADMINISTRATOR']
        self.cell_profile.UI_DISPLAY_LIMIT = 50
        self.cell_profile.THREAD_QUEUE_TIMEOUT = 60
        self.cell_profile.NUM_CELLS_PER_USER = 1
        self.cell_profile.MO_ID_START_RANGE = 0
        self.cell_profile.CELL_TYPE = "EUtranCellFDD"
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "BSC01", "BSC02"
        node.lte_cell_type, node1.lte_cell_type = "FDD", "TDD"
        self.nodes = [node, node1]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.sleep')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users')
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[])
    @patch(
        'enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.add_error_as_exception')
    def test_lock_unlock_all_cells_on_a_node_execute_flow_adds_error_empty_list(self, mock_add_error_as_exception, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch("__builtin__.zip", return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.sleep')
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users', user=Mock())
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow.LockUnlockAllCellsOnAnNode.create_and_execute_threads')
    def test_lock_unlock_all_cells_on_a_node_execute_flow__success(self, mock_create_and_execute_execute, *_):
        self.cell_profile.execute_flow()
        self.assertEqual(1, mock_create_and_execute_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
