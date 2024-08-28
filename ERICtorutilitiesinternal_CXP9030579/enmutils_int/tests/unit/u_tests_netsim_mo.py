#!/usr/bin/env python

import unittest2
from mock import Mock, patch

from enmutils.lib import shell
from enmutils.lib.enm_user_2 import User
from enmutils_int.lib import netsim_mo
from enmutils_int.lib.load_node import ERBSLoadNode
from enmutils_int.lib.netsim_mo import MOType, MOTree, FailedNetsimOperation
from testslib import unit_test_utils


class MOTreeUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        user = User("Mockuser")
        self.mock_node = ERBSLoadNode(
            "netsimlin704_LTE01", "255.255.255.255", "5.1.120", "1094-174-285", security_state='ON', normal_user='test',
            normal_password='test', secure_user='test', secure_password='test', subnetwork='subnetwork', netsim="netsimlin704", simulation="LTE01", user=user)

        self.tree = MOTree(self.mock_node)

    def tearDown(self):
        unit_test_utils.tear_down()
        shell.connection_mgr = None

    def test__validate_response_returns_true(self):
        response = "Number of MOs: '5', ManagedElement=1': {}"
        self.assertTrue(self.tree._validate_response(response))

    def test_get_mo_path_with_no_name_param_returns_first_mo_of_correct_type_found(self):
        self.tree.mo_tree = {'Number of MOs': '5', 'ManagedElement=1': {
            'ENodeBFunction=1': {'EUtranCellFDD=LTE03ERBS00016-1': {}, 'EUtranCellFDD=LTE03ERBS00016-2': {},
                                 'EUtranCellFDD=LTE03ERBS00016-3': {}}}}
        path = self.tree.get_mo_path(self.tree.mo_tree, "EUtranCellFDD")

        self.assertEqual(path, "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00016-1")

    def test_get_mo_path_with_name_param_returns_correct_mo_type(self):
        self.tree.mo_tree = {'Number of MOs': '5', 'ManagedElement=1': {
            'ENodeBFunction=1': {'EUtranCellFDD=LTE03ERBS00016-1': {}, 'EUtranCellFDD=LTE03ERBS00016-2': {},
                                 'EUtranCellFDD=LTE03ERBS00016-3': {}}}}
        path = self.tree.get_mo_path(self.tree.mo_tree, "EUtranCellFDD", "LTE03ERBS00016-2")

        self.assertEqual(path, "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00016-2")

    def test_motree_parses_dumpmotree_correctly(self):
        response = """>> dumpmotree:motypes="ManagedElement,ENodeBFunction,EUtranCellFDD,UtranFreqRelation,UtranCellRelation";\nManagedElement=1\n   ENodeBFunction=1\n      EUtranCellFDD=LTE25ERBS00097-1\n         UtranFreqRelation=1\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=2\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=3\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=4\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=5\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=6\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n      EUtranCellFDD=LTE25ERBS00097-2\n         UtranFreqRelation=1\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=2\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=3\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=4\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=5\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=6\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n      EUtranCellFDD=LTE25ERBS00097-3\n         UtranFreqRelation=1\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=2\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=3\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=4\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=5\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n         UtranFreqRelation=6\n            UtranCellRelation=1\n            UtranCellRelation=2\n            UtranCellRelation=3\n            UtranCellRelation=4\n\nNumber of MOs: 95\n\n"""
        expected_tree = {'ManagedElement=1': {'ENodeBFunction=1': {'EUtranCellFDD=LTE25ERBS00097-1': {'UtranFreqRelation=1': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=2': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=3': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=4': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=5': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=6': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}}, 'EUtranCellFDD=LTE25ERBS00097-2': {'UtranFreqRelation=1': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=2': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=3': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=4': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=5': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=6': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}}, 'EUtranCellFDD=LTE25ERBS00097-3': {'UtranFreqRelation=1': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=2': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=3': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=4': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=5': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}, 'UtranFreqRelation=6': {'UtranCellRelation=1': {}, 'UtranCellRelation=2': {}, 'UtranCellRelation=3': {}, 'UtranCellRelation=4': {}}}}}, 'Number of MOs:': '95'}
        mo_tree = self.tree._parse_dump_tree_response(response)
        self.assertEqual(1, cmp(expected_tree, mo_tree))

    def test_motree_parses_dumpmotree_correctly_II(self):
        response = """>> dumpmotree:motypes="ManagedElement,ENodeBFunction,EUtraNetwork,ExternalENodeBFunction,TermPointToENB";\nManagedElement=1\n   ENodeBFunction=1\n      EUtraNetwork=1\n         ExternalENodeBFunction=LTE04ERBS00088\n            TermPointToENB=1\n         ExternalENodeBFunction=LTE04ERBS00089\n            TermPointToENB=1\n         ExternalENodeBFunction=LTE04ERBS00090\n            TermPointToENB=1\n\nNumber of MOs: 9\n\n"""
        expected_tree = {'Number of MOs:': '9', 'ManagedElement=1': {'ENodeBFunction=1': {"EUtraNetwork=1": {"ExternalENodeBFunction=LTE04ERBS00088": {"TermPointToENB=1": {}}, "ExternalENodeBFunction=LTE04ERBS00089": {"TermPointToENB=1": {}}, "ExternalENodeBFunction=LTE04ERBS00090": {"TermPointToENB=1": {}}}}}}
        mo_tree = self.tree._parse_dump_tree_response(response)
        self.assertEqual(1, cmp(expected_tree, mo_tree))

    def test_parse_dump_tree_response__raises_mo_name_run_time_error(self):
        response = ('>> \n'
                    ':MO not defined:motypes="ManagedElement,ENodeBFunction,EUtraNetwork,ExternalENodeBFunction,'
                    'TermPointToENB";\n'
                    'ManagedElement=1\n'
                    '   ENodeBFunction=1\n'
                    '      EUtraNetwork=1\n'
                    'ExternalENodeBFunction=LTE04ERBS00088\n'
                    '            TermPointToENB=1\n'
                    'ExternalENodeBFunction=LTE04ERBS00089\n'
                    '            TermPointToENB=1\n'
                    'ExternalENodeBFunction=LTE04ERBS00090\n'
                    '            TermPointToENB=1\n\nNumber of MOs: 9\n\n')
        self.assertRaises(RuntimeError, self.tree._parse_dump_tree_response, response)

    def test_validate_response__no_dump_mo_tree_validation_set(self):
        self.assertFalse(self.tree._validate_response("return False"))

    @patch('enmutils_int.lib.netsim_mo.MOTree._validate_response', return_value=True)
    @patch('enmutils_int.lib.netsim_mo.netsim_executor.run_cmd')
    def test_set_mo_tree_for_specific_types__sets_tree_as_expected(self, mock_run_cmd, _):
        response = Mock(rc=0, stdout='>> dumpmotree:motypes="ManagedElement,ENodeBFunction,EUtranCellFDD";'
                                     '\nManagedElement=1\n   ENodeBFunction=1\n      EUtranCellFDD=LTE03ERBS00016-1\n'
                                     '      EUtranCellFDD=LTE03ERBS00016-2\n'
                                     '      EUtranCellFDD=LTE03ERBS00016-3\n\nNumber of MOs: 5\n\n')
        mock_run_cmd.return_value = response
        expected_mo_tree = {'Number of MOs': '5', 'ManagedElement=1': {
            'ENodeBFunction=1': {'EUtranCellFDD=LTE03ERBS00016-1': {}, 'EUtranCellFDD=LTE03ERBS00016-2': {},
                                 'EUtranCellFDD=LTE03ERBS00016-3': {}}}}
        self.tree.set_mo_tree_for_specific_types(mo_types=["ManagedElement", "ENodeBFunction", "EUtranCellFDD"])
        self.assertEqual(self.tree.mo_tree, expected_mo_tree)

    @patch('enmutils_int.lib.netsim_mo.MOTree._validate_response', return_value=False)
    @patch('enmutils_int.lib.netsim_mo.netsim_executor.run_cmd')
    def test_set_mo_tree_for_specific_types__raises_failed_netsim_operation(self, mock_run_cmd, _):
        response = Mock(rc=1)
        mock_run_cmd.return_value = response

        self.assertRaises(FailedNetsimOperation, self.tree.set_mo_tree_for_specific_types,
                          mo_types=["ManagedElement", "ENodeBFunction", "EUtranCellFDD"])

    @patch('enmutils_int.lib.netsim_mo.MOTree._validate_response', return_value=True)
    @patch('enmutils_int.lib.netsim_mo.netsim_executor.run_cmd')
    def test_set_mo_tree_from_specific_point__sets_tree_as_expected(self, mock_run_cmd, _):
        response = Mock(rc=0, stdout='>> dumpmotree:moid="ManagedElement=1,ENodeBFunction=1,'
                                     'EUtranCellFDD=LTE01ERBS00001-1,EUtranFreqRelation=1";\nEUtranFreqRelation=1\n   '
                                     'EUtranCellRelation=1\n   EUtranCellRelation=2\n   EUtranCellRelation=3\n   '
                                     'EUtranCellRelation=4\n   EUtranCellRelation=5\n\nNumber of MOs: 6\n\n')
        mock_run_cmd.return_value = response
        expected_mo_tree = {'Number of MOs': '6', 'EUtranFreqRelation=1': {
            'EUtranCellRelation=1': {}, 'EUtranCellRelation=2': {}, 'EUtranCellRelation=3': {},
            'EUtranCellRelation=4': {}, 'EUtranCellRelation=5': {}}}
        self.tree.set_mo_tree_from_specific_point(from_mo_path="ManagedElement=1,ENodeBFunction=1,"
                                                               "EUtranCellFDD=LTE01ERBS00001-1,EUtranFreqRelation=1")
        self.assertEqual(self.tree.mo_tree, expected_mo_tree)

    def test_get_mo_path__ignores_cmsync_mos(self):
        mo_tree = {"ENodeBFunction=1": {
            'EUtraNetwork=1': {
                'ExternalENodeBFunction=LTE01ERBS00030': {'TermPointToENB=CMSYNC': {}}
            }}}
        self.assertIsNone(self.tree.get_mo_path(mo_tree, 'TermPointToENB'))

        mo_tree = {"ENodeBFunction=2": {
            'EUtraNetwork=4': {
                'ExternalENodeBFunction=LTE01ERBS00001': {'TermPointToENB=CMSYNC': {}},
                'ExternalENodeBFunction=LTE01ERBS00029': {'TermPointToENB=1': {}}
            }}}
        self.assertEqual("ENodeBFunction=2,EUtraNetwork=4,ExternalENodeBFunction=LTE01ERBS00029,TermPointToENB=1",
                         self.tree.get_mo_path(mo_tree, 'TermPointToENB'))

    def test_get_mo_path__ignores_temporary_mos(self):
        mo_tree = {"ENodeBFunction=3": {
            'EUtraNetwork=2': {
                'ExternalENodeBFunction=LTE01ERBS00003': {'EUtranFreqRelation=E1234': {}}
            }}}
        self.assertIsNone(self.tree.get_mo_path(mo_tree, 'EUtranFreqRelation'))

        mo_tree = {"ENodeBFunction=4": {
            'EUtraNetwork=3': {
                'ExternalENodeBFunction=LTE01ERBS00031': {'EUtranFreqRelation=E1234': {}},
                'ExternalENodeBFunction=LTE01ERBS00029': {'EUtranFreqRelation=1234': {}}
            }}}
        self.assertEqual("ENodeBFunction=4,EUtraNetwork=3,ExternalENodeBFunction=LTE01ERBS00029,"
                         "EUtranFreqRelation=1234", self.tree.get_mo_path(mo_tree, 'EUtranFreqRelation'))

    def test_get_mo_path__ignores_cellmgt_mos(self):
        mo_tree = {"RncFunction=1": {'UtranCell=CELLMGT05-1': {}}}
        self.assertIsNone(self.tree.get_mo_path(mo_tree, 'Utrancell'))
        mo_tree = {'UtranCell': 'CELLMGT05-1'}
        self.assertIsNone(self.tree.get_mo_path(mo_tree, 'Utrancell'))

        mo_tree = {"RncFunction=1": {'UtranCell=ABC': {}}}
        self.assertEqual("RncFunction=1,UtranCell=ABC", self.tree.get_mo_path(mo_tree, 'UtranCell'))


class MOTypeUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.node = Mock()
        self.node.netsim = "Sim1"
        self.nodes = [self.node]
        self.mo_type = MOType(type_name="EUtranCellRelation", nodes=self.nodes,
                              mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00017-1,"
                                      "EUtranFreqRelation=1,EUtranCellRelation=42")

    def tearDown(self):
        unit_test_utils.tear_down()
        shell.connection_mgr = None

    def test__get_mo_tree__is_successful(self):
        motree = Mock()
        parent_types = ['type1', 'type2']
        netsim_mo._get_mo_tree(motree, parent_types)
        motree.set_mo_tree_for_specific_types.assert_called_with(parent_types)

    def test__get_mo_path_to_type__is_successful(self):
        motree = Mock()
        parent_types = ['type1', 'type2']
        netsim_mo._get_mo_path_to_type(motree, parent_types,)
        motree.get_mo_path.assert_called_with(motree.mo_tree, 'type2')

    def test__get_mo_path_to_type__is_successful_if_create_mo_from_parent_type(self):
        motree = Mock()
        motree.get_mo_path.return_value = 'existing_path'
        parent_types = ['type1', 'type2']
        mo_path = netsim_mo._get_mo_path_to_type(motree, parent_types, 'type2')
        self.assertEqual(mo_path, 'existing_path,type2=CMSYNC')

    @patch('enmutils_int.lib.netsim_mo.create_mo_types')
    @patch('enmutils_int.lib.netsim_mo._get_mo_path_to_type', return_value=None)
    @patch('enmutils_int.lib.netsim_mo._get_mo_tree')
    @patch('enmutils_int.lib.netsim_mo.MOTree')
    @patch('enmutils_int.lib.netsim_mo.thread_queue.ThreadQueue')
    def test_get_mo_types_on_nodes__no_mo_path(self, mock_tq, mock_mo_tree, *_):
        mo_tree = Mock()
        mock_mo_tree.return_value.mo_tree = mo_tree
        mock_mo_tree.return_value.node = self.node
        netsim_mo.get_mo_types_on_nodes("UtranCell", parent_types=["ManagedElement"], nodes=[self.node])
        self.assertEqual(mock_tq.call_count, 1)

    @patch('enmutils_int.lib.netsim_mo.create_mo_types')
    @patch('enmutils_int.lib.netsim_mo._get_mo_path_to_type', return_value=None)
    @patch('enmutils_int.lib.netsim_mo._get_mo_tree')
    @patch('enmutils_int.lib.netsim_mo.MOTree')
    @patch('enmutils_int.lib.netsim_mo.thread_queue.ThreadQueue')
    def test_get_mo_types_on_nodes__no_mo_tree(self, mock_tq, mock_mo_tree, *_):
        mock_mo_tree.return_value.mo_tree = None
        mock_mo_tree.return_value.node = self.node
        netsim_mo.get_mo_types_on_nodes("UtranCell", parent_types=["ManagedElement"], nodes=[self.node])
        self.assertEqual(mock_tq.call_count, 1)

    @patch('enmutils_int.lib.netsim_mo.create_mo_types')
    @patch('enmutils_int.lib.netsim_mo.MOTree')
    @patch('enmutils_int.lib.netsim_mo.log.logger.debug')
    @patch('enmutils_int.lib.netsim_mo.thread_queue.ThreadQueue')
    def test_get_mo_types_on_nodes__no_worklist(self, mock_tq, mock_debug, *_):
        netsim_mo.get_mo_types_on_nodes("UtranCell", parent_types=["ManagedElement"], nodes=[])
        self.assertEqual(0, mock_tq.call_count)
        mock_debug.assert_called_with("Could not create work list for nodes: [[]]")

    @patch('enmutils_int.lib.netsim_mo.thread_queue.ThreadQueue')
    @patch('enmutils_int.lib.netsim_mo._get_mo_tree')
    @patch('enmutils_int.lib.netsim_mo.create_mo_types')
    @patch('enmutils_int.lib.netsim_mo._get_mo_path_to_type')
    @patch('enmutils_int.lib.netsim_mo.MOTree')
    def test_get_mo_types_on_nodes__is_successful(self, mock_mo_tree, mock_get_mo_path, mock_create_mo_types, *_):
        mo_tree = Mock()
        mock_mo_tree.return_value.mo_tree = mo_tree
        mock_mo_tree.return_value.node = self.node
        mock_get_mo_path.return_value = 'mo_path'
        nodes = [self.node, self.node]
        netsim_mo.get_mo_types_on_nodes("UtranCell", parent_types=["ManagedElement"], nodes=nodes)
        mock_create_mo_types.assert_called_with({'Sim1': {'mo_path': [self.node, self.node]}}, False, 'UtranCell', None, [])

    @patch('enmutils_int.lib.netsim_mo.MOType')
    def test_create_mo_types__is_successful(self, mock_mo_type):
        mock_motype_obj = Mock()
        mock_mo_type.return_value = mock_motype_obj
        node_mo_paths = {'Sim1': {'mo_path': [self.node, self.node]}}
        mo_types = netsim_mo.create_mo_types(node_mo_paths=node_mo_paths, new_mo=False, type_name='UtranCell',
                                             create_mo_from_parent_type=None, mo_types=[])
        self.assertEqual(mo_types, [mock_motype_obj])

    @patch('enmutils_int.lib.netsim_mo.NewMOType')
    def test_create_mo_types__is_successful_if_new_mo(self, mock_new_mo_type):
        mock_motype_obj = Mock()
        mock_new_mo_type.return_value = mock_motype_obj
        node_mo_paths = {'Sim1': {'mo_path': [self.node, self.node]}}
        mo_types = netsim_mo.create_mo_types(node_mo_paths=node_mo_paths, new_mo=True, type_name='UtranCell',
                                             create_mo_from_parent_type=None, mo_types=[])
        self.assertEqual(mo_types, [mock_motype_obj])

    def test_mos_to_create_property_with_create_from_parent_mo_attribute_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,EUtranFreqRelation=1",
                                          create_from_parent_mo="EUtranFreqRelation")
        self.assertEqual(new_mo_type.mos_to_create, ["EUtranFreqRelation", "EUtranCellRelation"])

    def test_mos_to_create_property_without_create_from_parent_mo_attribute_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                                  "EUtranFreqRelation=1")
        self.assertEqual(new_mo_type.mos_to_create, None)

    def test_delete_commands__property_in_motype_class_returns_expected_result(self):
        new_mo_type = netsim_mo.MOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                       mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                               "EUtranFreqRelation=1")
        self.assertEqual(new_mo_type.delete_commands,
                         ['deletemo:moid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,'
                          'EUtranFreqRelation=1";'])

    def test_delete_commands__property_with_create_from_parent_mo_argument_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                                  "EUtranFreqRelation=1",
                                          create_from_parent_mo="EUtranCellFDD")
        self.assertEqual(new_mo_type.delete_commands,
                         ['deletemo:moid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1";'])

    def test_delete_commands__property_with_no_create_from_parent_mo_argument_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                                  "EUtranFreqRelation=1",
                                          create_from_parent_mo=None)
        self.assertEqual(new_mo_type.delete_commands,
                         ['deletemo:moid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,'
                          'EUtranFreqRelation=1,EUtranCellRelation=new";'])

    def test_create_commands__property_in_motype_class_returns_expected_result(self):
        mo_type = netsim_mo.MOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                   mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                           "EUtranFreqRelation=1")
        self.assertEqual(mo_type.create_commands,
                         ['createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1",'
                          'type="EUtranCellRelation",name="1";'])

    def test_create_commands_property_with_create_from_parent_mo_argument_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,EUtranFreqRelation=1",
                                          create_from_parent_mo="EUtranFreqRelation")
        self.assertEqual(new_mo_type.create_commands,
                         ['createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1",type="EUtranFreqRelation",name="1";',
                          'createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,EUtranFreqRelation=1",type="EUtranCellRelation",name="new";'])

    def test_create_commands__property_with_no_create_from_parent_mo_argument_set(self):
        new_mo_type = netsim_mo.NewMOType(type_name="EUtranCellRelation", nodes=self.nodes,
                                          mo_path="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,"
                                                  "EUtranFreqRelation=1",
                                          create_from_parent_mo=None)
        self.assertEqual(new_mo_type.create_commands,
                         ['createmo:parentid="ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1,'
                          'EUtranFreqRelation=1",type="EUtranCellRelation",name="new";'])

    @patch('enmutils_int.lib.netsim_mo.log.logger.debug')
    @patch('enmutils_int.lib.netsim_mo.determine_mo_types_required')
    def test_determine_mo_types_required_with_mcd_burst_info__returns_one_mo_type_when_mo_path_is_set(
            self, mock_determine_mo_types_required, mock_debug):
        mo_burst_info = {"notification_percentage_rate": 0.45, "node_type": "ERBS", "mo_type_name": "EUtranCellFDD",
                         "mo_path": "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=%NENAME%-1",
                         "parent_mo_names": None, "mo_attribute": "userLabel", "mo_values": ["abc", "def", "ghi"]}

        mock_determine_mo_types_required.return_value = [self.mo_type]

        mo_types = netsim_mo.determine_mo_types_required_with_mcd_burst_info(mo_burst_info, self.nodes, 20)
        self.assertEqual(mo_types, [self.mo_type])
        mock_debug.assert_called_with(('MO TYPE: type: EUtranCellRelation, MO path: ManagedElement=1,ENodeBFunction=1,'
                                       'EUtranCellFDD=LTE01ERBS00017-1,EUtranFreqRelation=1,EUtranCellRelation=42,'
                                       ' # nodes: 1, burst rate: 9.0'))

    def test_determine_mo_types_required_with_avc_burst_info_returns_one_mo_type_when_mo_path_is_set(self):
        mo_burst_info = {"notification_percentage_rate": 0.45, "node_type": "ERBS", "mo_type_name": "EUtranCellFDD",
                         "mo_path": "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=%NENAME%-1",
                         "parent_mo_names": None, "mo_attribute": "userLabel", "mo_values": ["abc", "def", "ghi"]}

        nodes = [Mock()] * 2

        mo_types = netsim_mo.determine_mo_types_required_with_avc_burst_info(mo_burst_info, nodes, 20)
        self.assertEqual(len(mo_types), 1)

    @patch("enmutils_int.lib.netsim_mo.get_mo_types_on_nodes", return_value=[Mock()])
    def test_determine_mo_types_required__common_path_to_mo_return_false(self, mock_get_mo_types_on_nodes):
        mo_burst_info = {"notification_percentage_rate": 0.45, "node_type": "ERBS", "mo_type_name": "EUtranCellFDD",
                         "parent_mo_names": None, "mo_attribute": "userLabel", "mo_values": ["abc", "def", "ghi"]}

        nodes = Mock()

        mo_types = netsim_mo.determine_mo_types_required(mo_burst_info, nodes, Mock())
        self.assertEqual(mo_types, mock_get_mo_types_on_nodes.return_value)
        mock_get_mo_types_on_nodes.assert_called_with(nodes=nodes,
                                                      type_name="EUtranCellFDD",
                                                      parent_types=None,
                                                      new_mo=False)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
