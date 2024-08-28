#!/usr/bin/env python
import unittest2

from enmutils.lib import log
from enmutils_int.lib import cellmgt
from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import CreateAndDeleteCells
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import func_dec


class CellMgtAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 2}
    EXCLUSIVE = True

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ['ADMINISTRATOR']

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.user = self.fixture.users[0]
        self.nodes = self.fixture.nodes
        self.profile = CreateAndDeleteCells()
        self.fdns = ['{1},MeContext={0},ManagedElement=1,ENodeBFunction=1,'
                     'EUtranCellFDD={0}-CELLMGT-1'.format(self.nodes[0].node_id, self.nodes[0].subnetwork),
                     '{1},MeContext={0},ManagedElement=1,ENodeBFunction=1,'
                     'EUtranCellFDD={0}-CELLMGT-2'.format(self.nodes[0].node_id, self.nodes[0].subnetwork)]

    def tearDown(self):
        func_test_utils.tear_down(self)

    def delete_cells_cleanup_via_rest(self):

        for cell_fdn in self.fdns:
            if cell_fdn in cellmgt.get_all_fdn_list_of_cells_on_node(self.user, self.nodes[0], "EUtrancellFDD"):
                cellmgt.delete_cell_via_rest(self.user, cell_fdn)

    def delete_cells_cleanup(self):
        for cell_fdn in self.fdns:
            response = self.user.enm_execute('cmedit delete {0} -ALL'.format(cell_fdn))
            log.logger.debug("{0}".format(".".join([line for line in response.get_output()])[-24:]))

    @func_dec('CellMgt', 'Determine existing cells on list of nodes')
    def test_determine_existing_cells_on_list_of_nodes_is_successful(self):
        existing_cells = cellmgt.determine_existing_cells_on_list_of_nodes(
            user=self.user, source_cell_type='EUtranCellFDD', nodes=self.nodes)
        self.assertEqual(len(self.nodes), len(existing_cells.values()))

    @func_dec('CellMgt', 'Create cells')
    def test_create_cells_is_successful(self):
        self.delete_cells_cleanup()
        existing_cells = {'{0}'.format(self.nodes[0].node_id): [u'{1},MeContext={0},'
                                                                u'ManagedElement=1,ENodeBFunction=1,'
                                                                u'EUtranCellFDD={0}-1'.format(self.nodes[0].node_id,
                                                                                              self.nodes[0].subnetwork)]}
        expected_new_cells = {'{0}'.format(self.nodes[0].node_id):
                              {'EUtranCellFDD':
                               ['{1},MeContext={0},ManagedElement=1,'
                                'ENodeBFunction=1,EUtranCellFDD={0}-CELLMGT-1'.format(self.nodes[0].node_id,
                                                                                      self.nodes[0].subnetwork),
                                '{1},MeContext={0},ManagedElement=1,'
                                'ENodeBFunction=1,EUtranCellFDD={0}-CELLMGT-2'.format(self.nodes[0].node_id,
                                                                                      self.nodes[0].subnetwork)]}}
        new_cells = cellmgt.create_cells(self.user, 'EUtranCellFDD', existing_cells, "FDD")
        self.assertEqual(new_cells, expected_new_cells)
        self.delete_cells_cleanup()

    @func_dec('CellMgt', 'Delete cells')
    def test_delete_cells_is_successful(self):
        existing_cells = {'netsim_LTE03ERBS00001': [u'{1},MeContext={0},'
                                                    u'ManagedElement=1,ENodeBFunction=1,'
                                                    u'EUtranCellFDD={0}-1'.format(self.nodes[0].node_id,
                                                                                  self.nodes[0].subnetwork)]}
        new_cells = cellmgt.create_cells(self.user, 'EUtranCellFDD', existing_cells, "FDD")
        self.assertTrue(cellmgt.delete_cells(self.user, new_cells))

    @func_dec('CellMgt', 'Create cells via rest')
    def test_create_cell_via_rest_is_successful(self):
        self.delete_cells_cleanup_via_rest()
        _, failed_cells = cellmgt.create_cell_via_rest(self.user, self.profile, self.fdns, "EUtranCellFDD", unicode("FDD"))
        self.assertEqual(len(failed_cells), 0)
        self.delete_cells_cleanup_via_rest()

    @func_dec('CellMgt', 'Delete cells via rest')
    def test_delete_cell_via_rest_is_successful(self):
        cellmgt.create_cell_via_rest(self.user, self.profile, self.fdns, "EUtranCellFDD", unicode("FDD"))
        for fdn in self.fdns:
            cellmgt.delete_cell_via_rest(self.user, fdn)
            self.assertTrue(fdn not in cellmgt.get_all_fdn_list_of_cells_on_node(self.user, self.nodes[0],
                                                                                 "EUtranCellFDD"))

    @func_dec('CellMgt', 'Create and delete cell relations')
    def test_create_delete_cell_relation_is_successful(self):
        fdn = ['{1},MeContext={0},ManagedElement=1,ENodeBFunction=1,'
               'EUtranCellFDD={0}-CELLMGT-1'.format(self.nodes[0].node_id, self.nodes[0].subnetwork)]
        cgi_obj = {
            "frequency": "11",
            "cellGlobalIdentity": {"mcc": "999", "mnc": "90", "eNBId": "100", "cellId": "50"},
            "externalCellType": "ExternalEUtranCellFDD",
            "attributes": {
                "ExternalEUtranCellFDD": {"physicalLayerCellIdGroup": "1", "physicalLayerSubCellId": "1", "tac": "1"}}}
        relation_type = ("INCOMING", "readRelations", "LTE", "EUtranCellRelation")
        cellmgt.create_cell_via_rest(self.user, self.profile, fdn, "EUtranCellFDD", unicode("FDD"))
        relation_created = cellmgt.create_external_cell_relation(self.user, str(fdn[0]), cgi_obj, "EUtranCellRelation")
        cellmgt.delete_cell_relation(self.user, fdn[0])
        self.assertTrue(relation_created not in str(cellmgt.get_cell_relations((self.user, fdn), relation_type)))
        self.delete_cells_cleanup_via_rest()
