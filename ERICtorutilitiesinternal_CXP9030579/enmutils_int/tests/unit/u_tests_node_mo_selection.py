#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.node_mo_selection import (NodeMoSelection, byteify, CARDINALITY_FILE, MO_FILE)
from testslib import unit_test_utils

CARDINALITY_SAMPLE = {
    "LTE14ERBS00004": {
        "RetSubUnit": "6", "ExternalEUtranCellFDD": "773", "EUtranCellFDD": "3", "ExternalUtranCellFDD": "36",
        "UtranCellRelation": "198", "EUtranFreqRelation": "27", "SectorCarrier": "3", "TermPointToENB": "512",
        "GeranFrequency": "3", "UtranFreqRelation": "18", "GeranCellRelation": "3", "EUtranCellRelation": "1601",
        "GeranFreqGroupRelation": "3", "ExternalENodeBFunction": "512"},
    "LTE14ERBS00005": {
        "RetSubUnit": "2", "ExternalEUtranCellFDD": "512", "EUtranCellFDD": "1", "ExternalUtranCellFDD": "36",
        "UtranCellRelation": "66", "EUtranFreqRelation": "9", "SectorCarrier": "1", "TermPointToENB": "512",
        "GeranFrequency": "1", "UtranFreqRelation": "6", "GeranCellRelation": "1", "EUtranCellRelation": "726",
        "GeranFreqGroupRelation": "1", "ExternalENodeBFunction": "512"},
    "LTE14ERBS00006": {
        "RetSubUnit": "2", "ExternalEUtranCellFDD": "512", "EUtranCellFDD": "1", "ExternalUtranCellFDD": "36",
        "UtranCellRelation": "66", "EUtranFreqRelation": "9", "SectorCarrier": "1", "TermPointToENB": "512",
        "GeranFrequency": "1", "UtranFreqRelation": "6", "GeranCellRelation": "1", "EUtranCellRelation": "726",
        "GeranFreqGroupRelation": "1", "ExternalENodeBFunction": "512"}
}


class NodeMoSelectionUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.mo_selection = NodeMoSelection()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_mo_selection.filesystem.get_lines_from_file', return_value=["MO"])
    @patch('enmutils_int.lib.node_mo_selection.json.loads')
    @patch('enmutils_int.lib.node_mo_selection.log.logger.debug')
    def test_read_information_from_file(self, mock_debug, *_):
        self.mo_selection.read_information_from_file("FILE")
        mock_debug.assert_called_with("Completed read of node(s) cardinality file.")

    @patch('enmutils_int.lib.node_mo_selection.filesystem.get_lines_from_file', return_value=[])
    @patch('enmutils_int.lib.node_mo_selection.json.loads')
    def test_read_information_from_file_raises_environ_error_empty_file(self, *_):
        self.assertRaises(EnvironError, self.mo_selection.read_information_from_file, "FILE")

    @patch('enmutils_int.lib.node_mo_selection.filesystem.get_lines_from_file',
           side_effect=RuntimeError("File not found."))
    def test_read_information_from_file_raises_environ_error(self, _):
        self.assertRaises(EnvironError, self.mo_selection.read_information_from_file, "FILE")

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_information_from_file')
    def test_read_cardinality_information_from_file(self, mock_read):
        self.mo_selection.read_cardinality_information_from_file()
        mock_read.assert_called_with(CARDINALITY_FILE)

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_information_from_file')
    def test_read_mo_information_from_file(self, mock_read):
        self.mo_selection.read_mo_information_from_file()
        mock_read.assert_called_with(MO_FILE)

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_cardinality_information_from_file')
    def test_select_all_with_required_mo_cardinality(self, mock_read_cardinality):
        self.mo_selection.cardinality_information = {}
        mock_read_cardinality.return_value = CARDINALITY_SAMPLE
        node, node1 = Mock(), Mock()
        node.node_name = "LTE14ERBS00006"
        node1.node_name = "LTE14ERBS00004"
        nodes = [node, node1]
        result = self.mo_selection.select_all_with_required_mo_cardinality(mo_name="ExternalEUtranCellFDD",
                                                                           min_cardinality=0, max_cardinality=512,
                                                                           nodes=nodes)
        self.assertEqual(1, mock_read_cardinality.call_count)
        self.assertEqual(result, nodes[:0])

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_cardinality_information_from_file')
    def test_select_all_with_required_mo_cardinality_no_nodes(self, mock_read_cardinality):
        self.mo_selection.cardinality_information = CARDINALITY_SAMPLE
        mock_read_cardinality.return_value = CARDINALITY_SAMPLE
        result = self.mo_selection.select_all_with_required_mo_cardinality(mo_name="ExternalEUtranCellFDD",
                                                                           min_cardinality=600, max_cardinality=0)
        self.assertEqual(0, mock_read_cardinality.call_count)
        self.assertEqual(result, ["LTE14ERBS00004"])

    @ParameterizedTestCase.parameterize(
        ("values", "expected"),
        [
            ((65, 1, 64), False),
            ((65, 1, 0), True),
            ((0, 1, 66), False),
            ((65, 1, 65), True),
            ((65, 0, 65), True),
            ((0, 0, 65), True),
            ((0, 0, 0), True),
            ((0, 1, 0), False),
        ]
    )
    def test_check_cardinality_meets_requirement(self, values, expected):
        existing_mo, min_mo, max_mo = values
        self.assertEqual(self.mo_selection.check_cardinality_meets_requirement(mo_cardinality=existing_mo,
                                                                               min_cardinality=min_mo,
                                                                               max_cardinality=max_mo), expected)

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_mo_information_from_file')
    def test_get_available_mo_values(self, mock_read):
        self.mo_selection.mo_information = {
            "LTE01": {"MO1": ["FDN", "FDN1"]},
            "LTE02": {"MO2": ["FDN"]},
            "LTE03": {"MO1": ["FDN"]}
        }

        self.assertDictEqual({"LTE01": {"MO1": ["FDN", "FDN1"]}, "LTE03": {"MO1": ["FDN"]}},
                             self.mo_selection.get_available_mo_values("MO1"))
        node = Mock()
        node.node_name = "LTE01"
        self.assertDictEqual({"LTE01": {"MO1": ["FDN", "FDN1"]}},
                             self.mo_selection.get_available_mo_values("MO1", nodes=[node]))
        self.assertDictEqual({}, self.mo_selection.get_available_mo_values("MO2", nodes=[node]))
        self.assertEqual(0, mock_read.call_count)

    @patch('enmutils_int.lib.node_mo_selection.NodeMoSelection.read_mo_information_from_file')
    def test_get_available_mo_values_mo_info_created_if_node_available(self, mock_read):
        self.mo_selection.mo_information = {}
        self.mo_selection.get_available_mo_values("MO1")
        self.assertEqual(1, mock_read.call_count)

    @ParameterizedTestCase.parameterize(
        ("data_in", "expected"),
        [
            (u'Unicode string', "Unicode string"),
            ({u"Key": u'Unicode string'}, {"Key": "Unicode string"}),
            ([u'Unicode string'], ["Unicode string"]),
            (10, 10),
        ]
    )
    def test_byteify(self, data_in, expected):
        self.assertEqual(byteify(data_in), expected)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
