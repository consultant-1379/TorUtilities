#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.cell_management import CreateDeleteCellsObject, RncCreateDeleteCells, ERBSCreateDeleteCells
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


class CellManagementUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        Profile.NAME = "TEST_CELLMGT_PROFILE"
        self.cell_profile = Mock()
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

    def test_cmedit_clean_up(self):
        user = Mock()
        user.enm_execute.side_effect = [True, Exception("Error")]
        self.assertTrue(CreateDeleteCellsObject.cmedit_clean_up("GeranCellRelation", user))
        self.assertFalse(CreateDeleteCellsObject.cmedit_clean_up("GeranCellRelation", user))

    def test_create_target_lte_cgi_proxy_objects__multiple_frequencies(self):
        result = ERBSCreateDeleteCells.create_target_lte_cgi_proxy_objects("ExternalEUtranCellFDD", (10, 11), 50, 5)
        self.assertEqual(5, len(result))
        self.assertEqual(type(result[0]), dict)
        self.assertEqual(result[0].get("frequency"), "10")
        self.assertEqual(result[1].get("frequency"), "11")

    def test_create_target_lte_cgi_proxy_objects__single_frequency(self):
        result = ERBSCreateDeleteCells.create_target_lte_cgi_proxy_objects("ExternalEUtranCellFDD", 11, 50, 5)
        self.assertEqual(5, len(result))
        self.assertEqual(result[1].get("frequency"), "11")
        self.assertEqual(result[0].get("frequency"), "11")

    def test_create_target_lte_cgi_proxy_objects__more_than_24_objects(self):
        result = ERBSCreateDeleteCells.create_target_lte_cgi_proxy_objects("ExternalEUtranCellFDD", 11, 50, 30)
        self.assertEqual(30, len(result))
        self.assertEqual(result[23].get("cellGlobalIdentity")["eNBId"], "100")
        self.assertEqual(result[24].get("cellGlobalIdentity")["eNBId"], "101")

    def test_create_target_gsm_cgi_proxy_objects(self):
        result = ERBSCreateDeleteCells.create_target_gsm_cgi_proxy_objects_for_lte_nodes("ExternalGeranCell", 11, 12,
                                                                                         50, 5)
        self.assertEqual(5, len(result))
        self.assertEqual(result[0].get("cellGlobalIdentity")["cellIdentity"], "50")
        self.assertEqual(result[1].get("cellGlobalIdentity")["cellIdentity"], "51")

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.create_cells')
    def test_create_cells_flow__successful(self, *_):
        mock_obj = CreateDeleteCellsObject(self.cell_profile, user=Mock(), node=Mock(lte_cell_type="FDD"))
        mock_obj.created_cells = ['cell1', 'cell2']

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.clean_up_cells')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.fetch_existing_cells')
    def test_createdeletecellsobject_setup__successful(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.NUM_RELATIONS_PER_NODE = 5
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.setup()
        self.assertTrue(obj.setup_completed)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.fetch_existing_cells',
           side_effect=Exception('Error'))
    def test_createdeletecellsobject_setup__fail(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.setup()
        self.assertEqual(1, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt',
           side_effect=EnmApplicationError('Error'))
    def test_createdeletecellsobject_fetch_existing_cells__fail(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.CELL_TYPE = "UtranCell"
        self.cell_profile.STANDARD = "WCDMA"
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.node_poid = "1234"
        self.assertRaises(EnmApplicationError, obj.fetch_existing_cells)

    @patch('enmutils_int.lib.cell_management.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt',
           return_value=['cell'])
    def test_createdeletecellsobject_fetch_existing_cells__successful(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.CELL_TYPE = "UtranCell"
        self.cell_profile.STANDARD = "WCDMA"
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.node_poid = "1234"
        self.assertEqual(['cell'], obj.fetch_existing_cells())

    @patch('enmutils_int.lib.cell_management.time.sleep')
    @patch("enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest")
    @patch('enmutils_int.lib.cell_management.cellmgt.create_cell_via_rest',
           side_effect=[(['cell1', 'cell2'], {"cell1": "already exists with id"}), (['cell1', 'cell2'], {})])
    def test_createdeletecellsobject_create_cells__create_cell_via_rest_called_second_time(self,
                                                                                           mock_create_cell_via_rest,
                                                                                           *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.CELL_TYPE = "UtranCell"
        self.cell_profile.created_cells = []
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.create_cells()
        self.assertTrue(mock_create_cell_via_rest.called, 2)

    @patch('enmutils_int.lib.cell_management.time.sleep')
    @patch('enmutils_int.lib.cell_management.cellmgt.create_cell_via_rest', return_value=(['cell1', 'cell2'], {}))
    def test_createdeletecellsobject_create_cells__successful(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.CELL_TYPE = "UtranCell"
        self.cell_profile.created_cells = []
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.create_cells()
        self.assertEqual(['cell1', 'cell2'], obj.created_cells)

    @patch('enmutils_int.lib.cell_management.time.sleep')
    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest')
    @patch('enmutils_int.lib.cell_management.cellmgt.create_cell_via_rest')
    def test_createdeletecellsobject_create_cells__delete_and_retry_exisiting_cell(self, mock_create,
                                                                                   mock_delete, *_):
        mock_create.side_effect = [(['cell1'], {'cell2': '[UtranCell] already exists with id [cell2-test]',
                                                'cell3': '[UtranCell] already exists with id [cell3-test]',
                                                'cell4': 'Cellmgt unavailable'}),
                                   (["cell2"], {}), ([], {'cell3': 'Cellmgt unavailable'})]
        mock_delete.side_effect = [Exception("Error"), None, None]
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.CELL_TYPE = "UtranCell"
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.create_cells()
        self.assertEqual(2, mock_delete.call_count)
        self.assertEqual(2, len(obj.created_cells))
        self.assertEqual(1, self.cell_profile.add_error_as_exception.call_count)

    def test_createdeletecellsobject_get_relations_to_create__include_existing_cells(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None

        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.profile.RELATIONS_TO_EXISTING_CELLS = 2
        obj.created_cells = ['cell1', 'cell2']
        obj.existing_cells = ['cell3', 'cell4']
        obj.external_cells = ['cell5', 'cell6']
        obj.get_relations_to_create()
        expected_output = [('cell1', 'cell3'), ('cell1', 'cell4'), ('cell1', 'cell2'), ('cell1', 'cell5'),
                           ('cell1', 'cell6'), ('cell2', 'cell3'), ('cell2', 'cell4'), ('cell2', 'cell1'),
                           ('cell2', 'cell5'), ('cell2', 'cell6')]

        self.assertEqual(expected_output, obj.relations_to_create)

    def test_createdeletecellsobject_get_relations_to_create__exclude_existing_cells(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        del self.cell_profile.RELATIONS_TO_EXISTING_CELLS
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.created_cells = ['cell1', 'cell2']
        obj.external_cells = ['cell3', 'cell4']
        obj.get_relations_to_create()
        expected_output = [('cell1', 'cell2'), ('cell1', 'cell3'), ('cell1', 'cell4'), ('cell2', 'cell1'),
                           ('cell2', 'cell3'), ('cell2', 'cell4')]

        self.assertEqual(expected_output, obj.relations_to_create)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.get_relations_to_create')
    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation',
           side_effect=['cell2_relation', 'cell3_relation'])
    def test_createdeletecellsobject_create_relations__successful(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.RELATION_TYPE = 'UtranCellRelation'
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.relations_to_create = [('cell1', 'cell2'), ('cell1', 'cell3')]
        obj.create_relations()
        self.assertEqual(['cell2_relation', 'cell3_relation'], obj.created_relations)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.get_relations_to_create')
    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation',
           side_effect=[HTTPError('error'), HTTPError('error')])
    def test_createdeletecellsobject_create_relations__fail(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.RELATION_TYPE = 'UtranCellRelation'
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.relations_to_create = [('cell1', 'cell2'), ('cell1', 'cell3')]
        obj.create_relations()
        self.assertEqual(2, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest')
    def test_createdeletecellsobject_delete_all_cells__successful(self, mock_delete_cell, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.cells_to_be_created = ['cell1', 'cell2']
        obj.delete_all_cells()
        self.assertEqual(2, mock_delete_cell.call_count)

    def test_lock_cells_for_deletion__successful(self):
        user = Mock()
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, user, node1)
        obj.cells_to_be_created = ['cell1', 'cell2']
        obj.lock_cells_for_deletion('cell1', user)
        self.assertTrue(user.enm_execute.called)

    def test_lock_cells_for_deletion__exception_raised(self, *_):
        mock_user = Mock()
        mock_user.enm_execute.side_effect = EnmApplicationError("Could not lock cell1 before deletion")
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, mock_user, node1)
        obj.cells_to_be_created = ['cell1', 'cell2']
        obj.lock_cells_for_deletion('cell1', mock_user)
        self.assertEqual(1, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.time.sleep')
    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest', side_effect=HTTPError('error'))
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.lock_cells_for_deletion')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.cmedit_clean_up')
    def test_createdeletecellsobject_delete_all_cells__retry(self, mock_cmedit_clean_up,
                                                             mock_lock_cells, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.cells_to_be_created = ['cell1', 'cell2']
        obj.delete_all_cells(attempts=1)
        self.assertEqual(2, mock_lock_cells.call_count)
        self.assertEqual(2, self.cell_profile.add_error_as_exception.call_count)
        self.assertEqual(2, mock_cmedit_clean_up.call_count)

    @patch('enmutils_int.lib.cell_management.time.sleep')
    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest', side_effect=HTTPError('error'))
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.cmedit_clean_up')
    def test_createdeletecellsobject_delete_all_cells__attempt_less_than_attempts_try_again(self,
                                                                                            mock_cmedit_clean_up, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.cells_to_be_created = ['cell1', 'cell2']
        obj.delete_all_cells(attempts=3)
        self.assertEqual(2, self.cell_profile.add_error_as_exception.call_count)
        self.assertEqual(2, mock_cmedit_clean_up.call_count)

    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest',
           side_effect=HTTPError('Invalid or non existing FDN'))
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_createdeletecellsobject_delete_all_cells__non_existing_cell(self, mock_debug, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.cells_to_be_created = ['cell1']
        obj.delete_all_cells()
        mock_debug.assert_called_with('Cell was already deleted/never created: {0}'.format('cell1'))

    def test_createdeletecellsobject_reset(self):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        obj.external_cells = ['cell2']
        obj.created_cells = ['cell1']
        obj.relations_to_create = [('cell1', 'cell2')]
        obj.created_relations = ['cell4_relation']
        obj._setup_passed = True
        obj.reset()
        self.assertEqual([], obj.external_cells)
        self.assertEqual([], obj.created_cells)
        self.assertEqual([], obj.relations_to_create)
        self.assertEqual([], obj.created_relations)
        self.assertEqual(False, obj.setup_completed)

    def test_createdeletecellsobject__not_equal(self):
        node1 = Mock(lte_cell_type=None)
        node1.node_id = "RNC12"
        obj = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        node1.node_id = "RNC13"
        obj1 = CreateDeleteCellsObject(self.cell_profile, Mock(), node1)
        self.assertTrue(obj != obj1)

    @patch('enmutils_int.lib.cell_management.cellmgt.get_utran_network')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.fetch_existing_cells')
    def test_rnccreatedeletecells_setup__successful(self, *_):
        node1 = Mock(node_id="RNC12", poid="1234", lte_cell_type=None)
        self.cell_profile.NUM_RELATIONS_PER_NODE = 2
        self.cell_profile.NUM_CELLS_PER_NODE = 2
        self.cell_profile.CELL_TYPE = "UtranCell"
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        obj.setup()
        self.assertEqual(True, obj.setup_completed)

    @patch('enmutils_int.lib.cell_management.cellmgt.get_utran_network', side_effect=[HTTPError('error')])
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup_completed', new_callable=PropertyMock)
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup')
    def test_rnccreatedeletecells_setup__fail(self, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.NUM_RELATIONS_PER_NODE = 2
        self.cell_profile.NUM_CELLS_PER_NODE = 2
        self.cell_profile.CELL_TYPE = "UtranCell"
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        obj.setup()
        self.assertEqual(1, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup_completed', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.cell_management.cellmgt.get_utran_network')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup')
    def test_rnccreatedeletecells_setup__doesnt_get_utran_network_if_setup_is_not_completed(
            self, mock_add_error, mock_get_utran_network, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.NUM_RELATIONS_PER_NODE = 2
        self.cell_profile.NUM_CELLS_PER_NODE = 2
        self.cell_profile.CELL_TYPE = "UtranCell"
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        obj.setup()
        self.assertEqual(1, mock_add_error.call_count)
        self.assertFalse(mock_get_utran_network.called)

    @patch('enmutils_int.lib.cell_management.IurLink')
    def test_rnccreatedeletecells_check_iurlink_exists(self, mock_iurlink):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        mock_obj = Mock()
        mock_obj.rnc_id = 11
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        mock_iurlink.iurlink_exists.return_value = True
        obj.check_if_iurlink_exists(mock_obj)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.create_relations')
    @patch('enmutils_int.lib.cell_management.RncCreateDeleteCells.__init__', return_value=None)
    @patch('enmutils_int.lib.cell_management.RncCreateDeleteCells.check_if_iurlink_exists', return_value=True)
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_rnccreatedeletecells_create_relations__iurlink_created(self, mock_debug, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        self.cell_profile.RELATION_TYPE = 'UtranCellRelation'
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        obj.external_cells = [Mock()]
        mock_obj = Mock()
        mock_obj.created_cells = ['cell1']
        obj.create_relations(target_objs=[mock_obj, mock_obj])
        self.assertEqual(0, mock_debug.call_count)
        self.assertEqual(len(obj.external_cells), 3)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.create_relations')
    @patch('enmutils_int.lib.cell_management.RncCreateDeleteCells.check_if_iurlink_exists', return_value=False)
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_rnccreatedeletecells_create_relations__iurlink_not_created(self, mock_debug, *_):
        node1 = Mock()
        node1.node_id = "RNC12"
        node1.lte_cell_type = None
        self.cell_profile.RELATION_TYPE = 'UtranCellRelation'
        obj = RncCreateDeleteCells(self.cell_profile, Mock(), node1)
        mock_obj = Mock()
        mock_obj.created_cells = ['cell1']
        obj.create_relations(target_objs=[mock_obj])
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_create_delete_cells_object_summary_report__logs_correctly(self, mock_logger, *_):
        CreateDeleteCellsObject(Mock(), Mock(), Mock()).summary_report()
        self.assertEqual(4, mock_logger.call_count)

    def test_get_available_cell_ids(self):
        create_delete = CreateDeleteCellsObject(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        create_delete.existing_cells = ["Cell-1", "Cell-2", "Cell-NAN"]
        create_delete.profile.CELL_ID_RANGE = (0, 10)
        ids = create_delete.get_available_cell_ids()
        self.assertEqual(8, len(ids))
        self.assertTrue(2 not in ids)

    @patch('enmutils_int.lib.cell_management.cellmgt.delete_cell_via_rest')
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.lock_cells_for_deletion')
    def test_clean_up_cells(self, *_):
        create_delete = CreateDeleteCellsObject(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        create_delete.profile.NAME = "TEST_CELLMGT_PROFILE"
        create_delete.existing_cells = ["Cell-1", "Cell-2", "TEST_CELLMGT_PROFILE-3"]
        create_delete.clean_up_cells()
        self.assertEqual(2, len(create_delete.existing_cells))

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.get_available_cell_ids', return_value=[1, 2, 5])
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup')
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_erbscreatedeletecells_setup(self, mock_debug, *_):
        self.cell_profile.NAME = 'CellManagement'
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.setup()
        self.assertEqual(0, mock_debug.call_count)

        erbs_create_delete._setup_completed = True
        erbs_create_delete.existing_cells = ["SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-103_LTE17ERBS00009,"
                                             "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE17ERBS00009-3",
                                             "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-103_LTE17ERBS00009,"
                                             "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE17ERBS00009-4"]
        erbs_create_delete.profile.CELL_TYPE = "EUtranCellFDD"
        erbs_create_delete.profile.NUM_CELLS_PER_NODE = 3
        erbs_create_delete.setup()
        expected_cells = ["SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-103_LTE17ERBS00009,ManagedElement=1,"
                          "ENodeBFunction=1,EUtranCellFDD=CellManagement-1",
                          "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-103_LTE17ERBS00009,ManagedElement=1,"
                          "ENodeBFunction=1,EUtranCellFDD=CellManagement-2",
                          "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv7004-103_LTE17ERBS00009,ManagedElement=1,"
                          "ENodeBFunction=1,EUtranCellFDD=CellManagement-5"]
        self.assertEqual(expected_cells, erbs_create_delete.cells_to_be_created)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.get_available_cell_ids', return_value=[1, 2, 5])
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.fetch_existing_cells', side_effect=[[], ["cell-1"]])
    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.setup')
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_erbscreatedeletecells_setup__raises_EnvironError(self, *_):
        self.cell_profile.NAME = 'CellManagement'
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.existing_cells = []
        erbs_create_delete.MAX_RETRIES = 2
        erbs_create_delete._setup_completed = True
        erbs_create_delete.setup()
        self.assertEqual(1, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.create_relations')
    @patch('enmutils_int.lib.cell_management.ERBSCreateDeleteCells.create_eutran_relations')
    @patch('enmutils_int.lib.cell_management.ERBSCreateDeleteCells.create_utran_relation')
    def test_erbscreatedeletecells_create_relations(self, mock_utran, mock_eutran, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        mock_created_cells = Mock()
        mock_created_cells.created_cells = ["Cell-1", "Cell-2"]
        erbs_create_delete.create_relations(target_objs=[mock_created_cells])
        self.assertEqual(1, mock_utran.call_count)
        self.assertEqual(1, mock_eutran.call_count)

    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation')
    def test_erbscreatedeletecells_create_utran_relation__successful(self, create_cell_relation, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.profile.UTRAN_RELATION = {'relation_type': 'UtranCellRelation',
                                                     'external_cell_type': 'ExternalUtranCellFDD',
                                                     'num_to_create': 2, 'frequency': 50, 'cell_start_id': 50}
        erbs_create_delete.created_cells = ["Cell-1", "Cell-2"]
        erbs_create_delete.create_utran_relation()
        self.assertEqual(4, create_cell_relation.call_count)

    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation', side_effect=HTTPError("Error"))
    def test_erbscreatedeletecells_create_utran_relation__fails(self, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.profile.UTRAN_RELATION = {'relation_type': 'UtranCellRelation',
                                                     'external_cell_type': 'ExternalUtranCellFDD',
                                                     'num_to_create': 2, 'frequency': 50, 'cell_start_id': 50}
        erbs_create_delete.created_cells = ["Cell-1", "Cell-2"]
        erbs_create_delete.create_utran_relation()
        self.assertEqual(4, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.ERBSCreateDeleteCells.create_target_lte_cgi_proxy_objects',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation')
    def test_erbscreatedeletecells_create_eutran_relation__successful(self, mock_create_relations, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.profile.EUTRAN_RELATION = {'relation_type': 'EUtranCellRelation',
                                                      'external_cell_type': 'ExternalEUtranCellFDD',
                                                      'num_to_create': 28, 'frequencies': (5, 6), 'cell_start_id': 50,
                                                      'enode_id': 100}
        erbs_create_delete.created_cells = ["Cell-1", "Cell-2"]
        erbs_create_delete.create_eutran_relations()
        self.assertEqual(4, mock_create_relations.call_count)

    @patch('enmutils_int.lib.cell_management.ERBSCreateDeleteCells.create_target_lte_cgi_proxy_objects',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.cell_management.cellmgt.create_external_cell_relation', side_effect=HTTPError("Error"))
    def test_erbscreatedeletecells_create_eutran_relation__fails(self, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.profile.EUTRAN_RELATION = {'relation_type': 'EUtranCellRelation',
                                                      'external_cell_type': 'ExternalEUtranCellFDD',
                                                      'num_to_create': 28, 'frequencies': (5, 6), 'cell_start_id': 50,
                                                      'enode_id': 100}
        erbs_create_delete.created_cells = ["Cell-1", "Cell-2"]
        erbs_create_delete.create_eutran_relations()
        self.assertEqual(4, self.cell_profile.add_error_as_exception.call_count)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.reset')
    def test_erbscreatedeletecells_reset(self, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, Mock(), Mock(lte_cell_type="FDD"))
        erbs_create_delete.reset()
        self.assertEqual(0, erbs_create_delete.created_eutran_relations)
        self.assertEqual(0, erbs_create_delete.created_utran_relations)

    @patch('enmutils_int.lib.cell_management.CreateDeleteCellsObject.summary_report')
    @patch('enmutils_int.lib.cell_management.log.logger.debug')
    def test_erbscreatedeletecells_summary_report__successful(self, mock_debug, *_):
        erbs_create_delete = ERBSCreateDeleteCells(self.cell_profile, user=Mock(), node=Mock(lte_cell_type="FDD"))
        erbs_create_delete.profile.EUTRAN_RELATION = {"num_to_create": 2}
        erbs_create_delete.profile.UTRAN_RELATION = {"num_to_create": 2}
        erbs_create_delete.summary_report()
        self.assertEqual(2, mock_debug.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
