#!/usr/bin/env python

import json

import responses
import unittest2
from enmutils.lib.exceptions import EnvironError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils_int.lib import cellmgt
from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import CreateAndDeleteCells
from enmutils_int.lib.cellmgt import view_cell_relations, verify_nodes_on_enm_and_return_mo_cell_fdn_dict
from enmutils_int.lib.load_node import ERBSLoadNode as Node
from mock import patch, Mock, PropertyMock
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError
from testslib import unit_test_utils

URL = 'http://locahost/'

MO_TYPE = 'EUtranCellFDD'

MO_ATTRIBUTE_DATA = {
    MO_TYPE: [
        # ["attribute_name", attribute_min_value, attribute_max_value]
        ["physicalLayerCellIdGroup", 0, 65535],
        ["tac", 0, 65535],
        ["physicalLayerSubCellId", 0, 2],
        ["lbEUtranCellOffloadCapacity", 0, 1000000]
    ]
}

BATCH_MO_SIZE = 50
REQUIRED_NUMBER_OF_NODES = 1
REQUIRED_NUMBER_OF_CELLS_PER_NODE = 4

CELL_FDN_CPP = "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6064-01_LTE01ERBS00048,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00048-12"
CELL_NAME_CPP = "LTE01ERBS00048-12"
NODE_NAME_CPP = "ieatnetsimv6064-01_LTE01ERBS00048"

CELL_FDN_RadioNode = "SubNetwork=NETSimW,ManagedElement=LTE45dg2ERBS00015,ENodeBFunction=1,EUtranCellFDD=LTE45dg2ERBS00015-12"
CELL_NAME_RadioNode = "LTE45dg2ERBS00015-12"
NODE_NAME_RadioNode = "LTE45dg2ERBS00015"

CELL_FDN_RNC = "SubNetwork=RNC10,MeContext=ieatnetsimv7004-27_RNC10,ManagedElement=1,RncFunction=1,UtranCell=RNC10-19-1"
CELL_FDN_RNC2 = "SubNetwork=RNC10,ieatnetsimv7004-27_RNC10,1,RncFunction=1,UtranCell=RNC10-19-1"
CELL_NAME_RNC = "RNC10-19-1"
NODE_NAME_RNC = "ieatnetsimv7004-27_RNC10"

RNC_FUNCTION = "SubNetwork=RNC10,MeContext=ieatnetsimv7004-27_RNC10,ManagedElement=1,RncFunction=1"
UTRAN_NETWORK = "SubNetwork=RNC10,MeContext=ieatnetsimv7004-27_RNC10,ManagedElement=1,RncFunction=1,UtranNetwork=6"

RANDOM_FDN = "MeContext,SubNetwork=RNC10,ieatnetsimv7004-27_RNC10"
RANDOM_FDN_2 = "SubNetwork=RNC10,ieatnetsimv7004-27_RNC10"

TARGET_FDNS = ["SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,ENodeBFunction=1",
               "SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00030,ManagedElement=1,ENodeBFunction=1"]

CELL_RANGE = [
    "SubNetwork=NETSimG,MeContext=MSC46BSC92,ManagedElement=MSC46BSC92,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1",
    "SubNetwork=NETSimG,MeContext=MSC46BSC92,ManagedElement=MSC46BSC92,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=50",
    "SubNetwork=NETSimG,MeContext=MSC46BSC92,ManagedElement=MSC46BSC92,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=99",
    "SubNetwork=NETSimG,MeContext=MSC46BSC92,ManagedElement=MSC46BSC92,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=150",
    "SubNetwork=NETSimG,MeContext=MSC46BSC92,ManagedElement=MSC46BSC92,BscFunction=1,BscM=1,GeranCellM=1,GeranCell=160"]

CMEDIT_GET_RESPONSE = ["FDN : SubNetwork=RNC07,MeContext=RNC07,ManagedElement=1,RncFunction=1,UtranNetwork=6",
                       "FDN : SubNetwork=RNC07,MeContext=RNC07,ManagedElement=1,RncFunction=1,UtranNetwork=7"]

POST_RESPONSE = """{
    "requestResult": "SUCCESS",
    "requestErrorMessage": "",
    "failedMoOperations": [],
    "successfulMoOperations": [
        {
            "fdn": "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6064-01_LTE01ERBS00048,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00048-12",
            "operationType": "UPDATE",
            "operationStatus": "SUCCESS",
            "attributes": {
                "physicalLayerSubCellId": 2,
                "physicalLayerCellIdGroup": 30,
                "lbEUtranCellOffloadCapacity": 1000,
                "tac": 1
            },
            "reasonForFailure": "",
            "actionName": ""
        },
        {
            "fdn": "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6064-01_LTE01ERBS00007,ManagedElement=1,ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=LTE01ERBS00048,ExternalEUtranCellFDD=LTE01ERBS00048-12",
            "operationType": "UPDATE",
            "operationStatus": "SUCCESS",
            "attributes": {
                "physicalLayerSubCellId": 2,
                "physicalLayerCellIdGroup": 30,
                "lbEUtranCellOffloadCapacity": 1000,
                "tac": 1
            },
            "reasonForFailure": "",
            "actionName": ""
        }],
    "executionMode": "EXECUTE"
}""".replace('\n', '').replace(' ', '')

node_name = "LTE01ERBS00000"

cell_fdn_basename1 = "SubNetwork=ERBS-SUBNW-1,MeContext="
cell_fdn_basename2 = ",ManagedElement=1,ENodeBFunction=1,EUtranCellFDD="

cell_fdn_A1 = "{0}{node_name}{1}{node_name}-1".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)
cell_fdn_A2 = "{0}{node_name}{1}{node_name}-2".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)
cell_fdn_A3 = "{0}{node_name}{1}{node_name}-3".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)

cell_fdn_B1 = "{0}{node_name}{1}{node_name}-1".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)
cell_fdn_B2 = "{0}{node_name}{1}{node_name}-2".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)
cell_fdn_B3 = "{0}{node_name}{1}{node_name}-3".format(cell_fdn_basename1, cell_fdn_basename2, node_name=node_name)

cell_fdn_list1 = [cell_fdn_A1, cell_fdn_A1, cell_fdn_A2, cell_fdn_A3]
cell_fdn_list2 = [cell_fdn_B1, cell_fdn_B1, cell_fdn_B2, cell_fdn_B3]

attribute_values_default = {'physicalLayerSubCellId': '2', 'lbEUtranCellOffloadCapacity': '100005',
                            'physicalLayerCellIdGroup': '68', 'tac': '1005'}
attribute_values_new = {'physicalLayerSubCellId': 0, 'lbEUtranCellOffloadCapacity': 100006,
                        'physicalLayerCellIdGroup': 69, 'tac': 1006}

NEW = "NEW"
DEFAULT = "DEFAULT"
READ_CELL_JSON = {
    "requestResult": "SUCCESS",
    "requestErrorMessage": "",
    "failedMoOperations": [],
    "successfulMoOperations": {
        "LTE": [{"cell": "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE415dg2ERBS00041,"
                         "ENodeBFunction=1,EUtranCellFDD=LTE415dg2ERBS00041-1", "neType": "RadioNode"},
                {"cell": "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE415dg2ERBS00041,"
                         "ENodeBFunction=1,EUtranCellFDD=LTE415dg2ERBS00041-10", "neType": "RadioNode"}]
    }}


class CellMgtUnitTests(ParameterizedTestCase):

    def setUp(self):
        self.user = Mock()
        self.mock_user = Mock()
        unit_test_utils.setup()
        self.profile = Mock()
        self.profile.NAME = "TEST_CELLMGT_PROFILE"
        self.profile.USER_ROLES = "TEST_USER"
        self.profile.REQUIRED_NUMBER_OF_NODES = "1"
        self.profile.REQUIRED_NUMBER_OF_CELLS_PER_NODE = "1"
        self.profile.MO_TYPE = MO_TYPE
        self.profile.MO_ATTRIBUTE_DATA = MO_ATTRIBUTE_DATA
        node_name = "LTE01ERBS00000"
        node_poid = "23134512411"

        self.number_of_erbs_nodes = 3
        self.dummy_erbs_nodes = []
        for _ in range(1, self.number_of_erbs_nodes + 1):
            self.dummy_erbs_nodes.append(Node(node_id="{}".format(node_name), profiles=[self.profile.NAME],
                                              primary_type='ERBS', poid="{}".format(node_poid)))

        self.dummy_rnc_nodes = [Node(node_id="RNC01", profiles=[self.profile.NAME], primary_type='RNC')]

        self.cell = CreateAndDeleteCells()
        self.cell.USER_ROLES = "TEST_USER"

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_modify_cell_parameters(self):
        response = Mock(status_code=200)
        response.json.return_value = json.loads(POST_RESPONSE)
        self.user.post.return_value = response
        expected_result = ["ieatnetsimv6064-01_LTE01ERBS00048", "ieatnetsimv6064-01_LTE01ERBS00007"]
        attribute_data = {'physicalLayerSubCellId': 2, 'lbEUtranCellOffloadCapacity': 100005,
                          'physicalLayerCellIdGroup': 68, 'tac': 1005}
        self.assertEqual(expected_result, cellmgt.modify_cell_parameters(
            self.user, CELL_FDN_CPP, attribute_data))
        self.assertEqual(expected_result, cellmgt.modify_cell_parameters(
            self.user, CELL_FDN_RadioNode, attribute_data))
        self.assertEqual(expected_result, cellmgt.modify_cell_parameters(
            self.user, CELL_FDN_RNC, attribute_data))

    def test_modify_cell_parameters_raise_error(self):
        response = Mock()
        response.ok = False
        self.mock_user.post.return_value = response

        with self.assertRaises(HTTPError):
            cellmgt.modify_cell_parameters(self.mock_user, CELL_FDN_CPP, attribute_values_default)

    @patch('enmutils_int.lib.cellmgt.modify_cell_parameters')
    @patch('enmutils_int.lib.cellmgt.get_cell_name')
    def test_revert_cell_attributes(self, mock_cell_name, mock_modify_para):
        mock_cell_name.return_value = 'name'
        mock_modify_para.side_effect = HTTPError

        cellmgt.revert_cell_attributes(12, cell_fdn_A1, attribute_values_default, self.user)

    @patch('enmutils_int.lib.cellmgt.modify_cell_parameters')
    @patch('enmutils_int.lib.cellmgt.get_cell_name')
    def test_update_cells_attributes_via_cell_management(self, mock_cell_name, mock_modify_para):
        mock_cell_name.return_value = 'name'
        mock_modify_para.return_value = None
        data = {node_name: {cell_fdn_A1: {'new': 'something'}}, node_name: {cell_fdn_B1: {'new': 'something'}}}
        cellmgt.update_cells_attributes_via_cell_management(self.user, 'new', 3, data)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.cellmgt.modify_cell_parameters')
    @patch('enmutils_int.lib.cellmgt.get_cell_name')
    def test_update_cells_attributes_via_cell_management__raises_enm_application_error(self, mock_cell_name,
                                                                                       mock_modify_para, mock_debug):
        mock_cell_name.return_value = 'name'
        mock_modify_para.side_effect = Exception("Error")
        data = {node_name: {cell_fdn_A1: {'new': 'something'}}, node_name: {cell_fdn_B1: {'new': 'something'}}}
        self.assertRaises(EnmApplicationError, cellmgt.update_cells_attributes_via_cell_management, self.user, 'new',
                          3, data)
        self.assertEqual(3, mock_debug.call_count)

    def test_get_cell_name(self):
        self.assertEqual(CELL_NAME_CPP, cellmgt.get_cell_name(CELL_FDN_CPP))
        self.assertEqual(CELL_NAME_RadioNode, cellmgt.get_cell_name(CELL_FDN_RadioNode))
        self.assertEqual(CELL_NAME_RNC, cellmgt.get_cell_name(CELL_FDN_RNC))

    def test_get_nodename_for_mo(self):
        self.assertEqual(NODE_NAME_CPP, cellmgt.get_nodename_for_mo(CELL_FDN_CPP))
        self.assertEqual(NODE_NAME_RadioNode, cellmgt.get_nodename_for_mo(CELL_FDN_RadioNode))
        self.assertEqual(NODE_NAME_RNC, cellmgt.get_nodename_for_mo(CELL_FDN_RNC))
        self.assertEqual(None, cellmgt.get_nodename_for_mo(RANDOM_FDN))
        self.assertEqual(None, cellmgt.get_nodename_for_mo(RANDOM_FDN_2))

    def test_get_all_fdn_list_of_cells_on_node__successful(self, *_):
        mock_user = Mock()
        cell_fdn_basename = "SubNetwork=ERBS-SUBNW-1,MeContext=ieatnetsimv6064-01_LTE01ERBS00001,ManagedElement=1," \
                            "ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001 "
        mock_response = Mock(**{"get_output.return_value": ["FDN : {0}-1".format(cell_fdn_basename),
                                                            "FDN : {0}-2".format(cell_fdn_basename), "", "",
                                                            "2 instance(s)"]})
        mock_user.enm_execute.return_value = mock_response
        expected_result = ["{0}-1".format(cell_fdn_basename), "{0}-2".format(cell_fdn_basename)]
        self.assertEqual(expected_result, cellmgt.get_all_fdn_list_of_cells_on_node(mock_user,
                                                                                    self.dummy_erbs_nodes[0].node_id,
                                                                                    MO_TYPE))

    # configure_new_attribute_values TESTS #############################################################################
    @patch('enmutils_int.lib.cellmgt._get_new_attribute_value')
    def test_configure_new_attribute_values__successfully_returns_expected_results(self, mock_get_new_attr_values):

        mock_get_new_attr_values.side_effect = [0, 1, 0, 100006]

        current_attribute_values = {'physicalLayerSubCellId': '2', 'lbEUtranCellOffloadCapacity': '100005',
                                    'physicalLayerCellIdGroup': 'null', 'tac': '0'}

        expected_attribute_values = {'physicalLayerSubCellId': 0, 'lbEUtranCellOffloadCapacity': 100006,
                                     'physicalLayerCellIdGroup': 0, 'tac': 1}

        self.assertEqual(expected_attribute_values, cellmgt.configure_new_attribute_values(MO_ATTRIBUTE_DATA[MO_TYPE],
                                                                                           current_attribute_values))

    # _get_new_attribute_value #########################################################################################

    @ParameterizedTestCase.parameterize(
        ('attribute_name', 'attribute_value', 'attribute_data', 'set_new_attributes_to_zero', "value"),
        [
            ('physicalLayerSubCellId', '2', ['physicalLayerSubCellId', 0, 2], False, 0),
            ('lbEUtranCellOffloadCapacity', '100005', ["lbEUtranCellOffloadCapacity", 0, 1000000], True, 0),
            ('physicalLayerCellIdGroup', 'null', ['physicalLayerCellIdGroup', 0, 167], False, 0),
            ('tac', '0', ["tac", 0, 65535], False, 1),
            ('primaryScramblingCode', '126', ['primaryScramblingCode', 0, 127], False, 127),
            ('primaryScramblingCode', '127', ['primaryScramblingCode', 0, 127], False, 0),
            ('primaryScramblingCode', '128', ['primaryScramblingCode', 0, 127], False, 0)
        ]
    )
    def test__get_new_attribute_value__successfully_returns_expected_values(
            self, mock_attribute_name, mock_attribute_value, mock_attribute_data, mock_set_new_attributes_to_zero,
            mock_value):
        value = cellmgt._get_new_attribute_value(mock_attribute_name, mock_attribute_value, mock_attribute_data,
                                                 mock_set_new_attributes_to_zero)
        self.assertEqual(value, mock_value)

    # populate_node_cell_data TESTS ##################################################################################

    @patch('time.sleep')
    @patch('enmutils_int.lib.cellmgt.get_cell_attributes')
    @patch('enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node')
    def test_populate_node_cell_data(self, mock_get_all_fdn_list_of_cells_on_node, mock_get_cell_attributes, *_):
        mock_get_cell_attributes.return_value = attribute_values_default

        mock_get_all_fdn_list_of_cells_on_node.side_effect = [cell_fdn_list1, cell_fdn_list2]

        expected_node_cell_data = \
            {
                node_name:
                    {
                        cell_fdn_A1: {DEFAULT: attribute_values_default, NEW: attribute_values_new},
                        cell_fdn_A2: {DEFAULT: attribute_values_default, NEW: attribute_values_new},
                        cell_fdn_A3: {DEFAULT: attribute_values_default, NEW: attribute_values_new}
                    },
                node_name:
                    {
                        cell_fdn_B1: {DEFAULT: attribute_values_default, NEW: attribute_values_new},
                        cell_fdn_B2: {DEFAULT: attribute_values_default, NEW: attribute_values_new},
                        cell_fdn_B3: {DEFAULT: attribute_values_default, NEW: attribute_values_new}
                    },
            }
        self.assertEqual(expected_node_cell_data, cellmgt.populate_node_cell_data(
            self.user, REQUIRED_NUMBER_OF_CELLS_PER_NODE, MO_TYPE, self.dummy_erbs_nodes[:2], MO_ATTRIBUTE_DATA))

    @patch('time.sleep')
    @patch('enmutils_int.lib.cellmgt.get_cell_attributes')
    @patch('enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node')
    def test_populate_node_cell_data_have_no_attribute_data(self, mock_get_all_fdn_list_of_cells_on_node,
                                                            mock_get_cell_attributes, *_):
        mock_get_cell_attributes.return_value = None

        mock_get_all_fdn_list_of_cells_on_node.side_effect = [cell_fdn_list1, cell_fdn_list2]

        cellmgt.populate_node_cell_data(
            self.user, REQUIRED_NUMBER_OF_CELLS_PER_NODE, MO_TYPE, self.dummy_erbs_nodes[:2], MO_ATTRIBUTE_DATA)

    @patch('enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node', return_value="TestNode")
    @patch('enmutils.lib.log.logger')
    def test_get_required_cell_fdn_list__is_successful(self, mock_logger, _):
        node_cell_data = {}
        required_cell_fdn_list = cellmgt.get_required_cell_fdn_list(node_name, 1, Mock(), Mock(),
                                                                    REQUIRED_NUMBER_OF_CELLS_PER_NODE, node_cell_data)
        self.assertEqual(required_cell_fdn_list, {'LTE01ERBS00000': 'Test'})
        mock_logger.debug.assert_any_call("# Fetching list of Cell FDN's for node 1: LTE01ERBS00000")
        mock_logger.debug.assert_any_call("# Full List of Cells for node LTE01ERBS00000 (1): ['T', 'e', 's', 't', 'N', "
                                          "'o', 'd', 'e']")

    @patch('enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node', return_value=None)
    @patch('enmutils.lib.log.logger')
    def test_get_required_cell_fdn_list__raises_errors(self, mock_logger, _):
        node_cell_data = {}
        self.assertRaises(EnvironError, cellmgt.get_required_cell_fdn_list, node_name, 1, Mock(), Mock(),
                          REQUIRED_NUMBER_OF_CELLS_PER_NODE, node_cell_data)
        mock_logger.debug.assert_called_with("# Fetching list of Cell FDN's for node 1: LTE01ERBS00000")

    def test_log_config_error(self):
        self.assertTrue(cellmgt.log_config_error(2, 2))

    @patch('enmutils_int.lib.cellmgt.extract_cell_fdns',
           return_value=[['MeContext=LTE01ERBS00000,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE05ERBS00002-6',
                          'MeContext=LTE01ERBS00000,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE05ERBS00002-6',
                          'MeContext=LTE01ERBS00000,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE05ERBS00002-6']])
    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_124a_test_124b_fetch_cell_fdns_rest_response_status_ok_with_complete_response(self, *_):
        post_response_read_data = """
        {{
             "requestResult":"SUCCESS",
             "requestErrorMessage":"",
             "failedMoOperations":[],
             "successfulMoOperations":
             {{
             "LTE":[
                {{
             "fdn":"NetworkElement=LTE05ERBS00002",
             "neType":"ERBS",
             "cells":["MeContext={node1}, ManagedElement=1, ENodeBFunction=1, EUtranCellFDD=LTE05ERBS00002-6",
                      "MeContext={node2}, ManagedElement=1, ENodeBFunction=1, EUtranCellFDD=LTE05ERBS00002-6",
                      "MeContext={node3}, ManagedElement=1, ENodeBFunction=1, EUtranCellFDD=LTE05ERBS00002-6"
                     ]
                }}
                   ]
            }}
        }}
        """.replace('\n', '').replace(' ', '').format(node1=self.dummy_erbs_nodes[0].node_id,
                                                      node2=self.dummy_erbs_nodes[1].node_id,
                                                      node3=self.dummy_erbs_nodes[2].node_id)
        response = Mock(status_code=200)
        response.json.return_value = json.loads(post_response_read_data)
        self.user.post.return_value = response

        node_fdn_data = ["NetworkElement={}".format(self.dummy_erbs_nodes[0].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[1].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[2].node_id)]

        cell_list = []
        fdn = "MeContext={node_name},ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE05ERBS00002-6"
        for node in self.dummy_erbs_nodes[0:3]:
            node_name = node.node_id
            cell_list += ["{0}".format(fdn.format(node_name=node_name))]
        self.assertEqual(cell_list, cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self.user,
                                                                                                 node_fdn_data))

    @patch('enmutils_int.lib.cellmgt.extract_cell_fdns', return_value=[])
    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_124b_fetch_cell_fdns_rest_response_status_ok_with_incomplete_response(self, *_):
        post_response_read_data = {"requestResult": "SUCCESS",
                                   "requestErrorMessage": "",
                                   "failedMoOperations": [],
                                   "successfulMoOperations": {"LTE": [{'notFdn': 'yes'}]}}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_data
        self.user.post.return_value = response
        node_fdn_data = ["NetworkElement={}".format(self.dummy_erbs_nodes[0].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[1].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[2].node_id)]
        cell_list = []

        self.assertEqual(cell_list, cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self.user,
                                                                                                 node_fdn_data))

    @patch('enmutils_int.lib.cellmgt.read_cells_for_specified_poid_list_via_cell_mgt', side_effect=HTTPError())
    def test_124c_fetch_cell_fdns_rest_response_status_nok_with_incomplete_response(self, _):
        node_fdn_data = ["NetworkElement={}".format(self.dummy_erbs_nodes[0].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[1].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[2].node_id)]

        self.assertRaises(HTTPError,
                          cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt, self.user, node_fdn_data)

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    @patch('json.dumps')
    def test_124d_fetch_cell_fdns_rest_response_status_ok_with_incomplete_response2(self, *_):
        response = Mock(status_code=200)
        response.json.return_value = {}
        self.user.post.return_value = response
        cell_list = []
        self.assertEqual(cell_list, cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self.user,
                                                                                                 cell_list))

    @patch('enmutils_int.lib.cellmgt.extract_cell_fdns', return_value=[])
    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_124e_fetch_cell_fdns_rest_response_status_ok_with_incomplete_response3(self, *_):
        post_response_read_data = {"requestResult": "SUCCESS",
                                   "requestErrorMessage": "",
                                   "failedMoOperations": [],
                                   "successfulMoOperations": {}}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_data
        self.user.post.return_value = response
        node_fdn_data = ["NetworkElement={}".format(self.dummy_erbs_nodes[0].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[1].node_id),
                         "NetworkElement={}".format(self.dummy_erbs_nodes[2].node_id)]

        cell_list = []
        self.assertEqual(cell_list, cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self.user,
                                                                                                 node_fdn_data))

    def test_125a_get_list_of_poids_in_network(self):
        output = {u'treeNodes': [{'poId': '{}'.format(self.dummy_erbs_nodes[0].poid)},
                                 {'poId': '{}'.format(self.dummy_erbs_nodes[1].poid)},
                                 {'poId': '{}'.format(self.dummy_erbs_nodes[2].poid)}]}
        response = Mock()
        response.json.return_value = output
        response.status_code = 200

        node_fdn_data = ["{}".format(self.dummy_erbs_nodes[0].poid),
                         "{}".format(self.dummy_erbs_nodes[1].poid),
                         "{}".format(self.dummy_erbs_nodes[2].poid)]

        self.user.get.return_value = response

        self.assertEqual(node_fdn_data, cellmgt.get_list_of_poids_in_network(self.user))

    def test_125b_get_empty_list_of_poids_if_nothing_is_on_network(self):
        response = Mock()
        output = {u'treeNodes': [{'Some': 'more'}]}
        response.json.return_value = output
        response.status_code = 200
        node_fdn_data = []
        self.user.get.return_value = response
        self.assertEqual(node_fdn_data, cellmgt.get_list_of_poids_in_network(self.user))
        output = {}
        response.json.return_value = output
        self.assertEqual(node_fdn_data, cellmgt.get_list_of_poids_in_network(self.user))

    @patch('time.sleep')
    @patch('enmutils_int.lib.cellmgt.fetch_and_display_attribute_values')
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    def test_127_read_cell_data_ui_flow(self, mock_fetch_cell_fdns, mock_fetch_and_display_cell_attrs, *_):

        ui_display_limit = 2
        sleep_time = 120

        user_node_data = (self.user, ["NetworkElement={}".format(node.node_id)
                                      for node in self.dummy_erbs_nodes[0:self.number_of_erbs_nodes]])

        mock_fetch_cell_fdns.return_value = []
        self.assertFalse(cellmgt.read_cell_data_ui_flow(user_node_data, sleep_time, ui_display_limit))

        mock_fetch_cell_fdns.return_value = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        mock_fetch_and_display_cell_attrs.side_effect = [0, 0, 1, 1]
        self.assertFalse(cellmgt.read_cell_data_ui_flow(user_node_data, sleep_time, ui_display_limit))
        self.assertTrue(cellmgt.read_cell_data_ui_flow(user_node_data, sleep_time, ui_display_limit))

    @patch('enmutils_int.lib.cellmgt.filter_nodes_having_poid_set')
    def test_create_list_of_node_poids__is_successful(self, mock_filter_nodes_having_poid_set):
        nodes = [Mock(poid="1234"), Mock(poid="2345")]
        mock_filter_nodes_having_poid_set.return_value = nodes
        self.assertEqual(["1234", "2345"], cellmgt.create_list_of_node_poids(self.user, nodes))
        mock_filter_nodes_having_poid_set.assert_called_with(nodes)

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    @responses.activate
    def test_129a_fetch_cell_attrs_rest_response_status_ok_with_complete_response(self, _):

        post_response_read_cell_attr_data = """{{
         "requestResult":"SUCCESS",
         "requestErrorMessage":"",
         "failedMoOperations":[],
         "successfulMoOperations":{{
             "LTE":[
             {{
                 "fdn":"MeContext={node1},ManagedElement=1,ENodeBFunction=1,EUtranCellFDD={node1}-1",
                 "attributes": {{
                     "cellId": 1,
                     "administrativeState":"LOCKED",
                     "nodeName": "{node1}",
                     "neType": "ERBS",
                     "operationalState":"ENABLED",
                     "cellName":"{node1}-1",
                     "syncStatus":"SYNCHRONIZED",
                     "tac":1,
                     "eNodeBPlmnId":{{
                         "mncLength":2,
                         "mcc":353,
                         "mnc":57
                     }},
                 "duplexType":"FDD",
                 "eNBId":163
                    }}
             }},
             {{
                 "fdn":"MeContext={node1},ManagedElement=1,ENodeBFunction=1,EUtranCellFDD={node1}-2",
                 "attributes": {{
                     "cellId": 2,
                     "administrativeState":"LOCKED",
                     "nodeName": "{node1}",
                     "neType": "ERBS",
                     "operationalState":"ENABLED",
                     "cellName":"{node1}-2",
                     "syncStatus":"SYNCHRONIZED",
                     "tac":1,
                     "eNodeBPlmnId":{{
                         "mncLength":2,
                         "mcc":353,
                         "mnc":57
                     }},
                 "duplexType":"FDD",
                 "eNBId":163
                    }}
             }}
         ]
         }}
         }}""".replace('\n', '').replace(' ', '').format(node1=self.dummy_erbs_nodes[0].node_id)
        response = Mock(status_code=200)
        response.json.return_value = json.loads(post_response_read_cell_attr_data)
        self.user.post.return_value = response
        cell_fdn_list = []
        node_name = self.dummy_erbs_nodes[0].node_id

        cell_attribute_data = {}
        for cell_counter in range(1, 3):
            attributes = {"cellId": cell_counter, "administrativeState": "LOCKED", "nodeName": "{}".format(node_name),
                          "neType": "ERBS", "operationalState": "ENABLED",
                          "cellName": "{0}-{1}".format(node_name, cell_counter),
                          "syncStatus": "SYNCHRONIZED", "tac": 1,
                          "eNodeBPlmnId": {"mncLength": 2, "mcc": 353, "mnc": 57},
                          "duplexType": "FDD", "eNBId": 163}

            cell_attribute_data["{0}-{1}".format(node_name, cell_counter)] = attributes

        self.assertEqual(cell_attribute_data,
                         cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(self.user, cell_fdn_list))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_129b_fetch_cell_attrs_rest_response_status_ok_with_incomplete_response(self, _):
        response = Mock(status_code=200)
        response.json.return_value = {"requestResult": "FAILED", "successfulMoOperations": []}
        self.user.post.return_value = response
        cell_fdn_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        self.assertEqual(None,
                         cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(self.user, cell_fdn_list))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    @patch('enmutils_int.lib.cellmgt.timestamp.get_string_elapsed_time', return_value=0)
    @patch('enmutils_int.lib.cellmgt.timestamp.get_current_time', return_value=0)
    def test_129c_fetch_cell_attrs_rest_response_status_ok_with_incomplete_response2(self, *_):
        response = Mock(status_code=200)
        response.json.return_value = {}
        self.user.post.return_value = response
        cell_fdn_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        self.assertEqual({},
                         cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(self.user, cell_fdn_list))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_129d_fetch_cell_attrs_rest_response_status_ok_with_incomplete_response3(self, _):
        post_response_read_cell_attr_data = {"requestResult": "FAILED",
                                             "successfulMoOperations": {'LTE': [{'notFdn': 'None'}]}}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_cell_attr_data
        self.user.post.return_value = response
        cell_fdn_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        self.assertEqual({},
                         cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(self.user, cell_fdn_list))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_129e_fetch_cell_attrs_rest_response_status_ok_with_incomplete_response4(self, _):
        post_response_read_cell_attr_data = {"requestResult": "FAILED",
                                             "successfulMoOperations": {'LTE': [{'fdn': 'None'}]}}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_cell_attr_data
        self.user.post.return_value = response
        cell_fdn_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        self.assertEqual({}, cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(self.user, cell_fdn_list))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_129f_fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt__value_error(self, _):
        response = Mock(status_code=200)
        response.json.side_effect = ValueError("Error")
        self.user.post.return_value = response
        cell_fdn_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        self.assertRaises(EnmApplicationError, cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt,
                          self.user, cell_fdn_list)

    @patch('enmutils_int.lib.cellmgt.fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt')
    def test_130_fetch_and_display_attribute_values(self, mock_fetch_cell_attrs):
        cell_fdns_list = [cell_fdn_A1]
        cell_attr_data = {"cell1": {"attr1": 1, "attr2": 2, "attr3": 3}}
        mock_fetch_cell_attrs.side_effect = [{}, cell_attr_data]

        self.assertRaises(EnvironError, cellmgt.fetch_and_display_attribute_values, self.user, cell_fdns_list)
        self.assertEqual(1, cellmgt.fetch_and_display_attribute_values(self.user, cell_fdns_list))

    @patch('time.sleep')
    @patch('enmutils.lib.enm_user_2.User.post')
    @patch('enmutils_int.lib.cellmgt.create_list_of_node_poids')
    @patch('enmutils_int.lib.cellmgt.lock_unlock_cell_via_cell_mgt')
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    def test_133_lock_unlock_cells_flow(self, mock_fetch_cell_fdns, mock_lock_unlock_cell, mock_get_poid, *_):

        sleep_time = 120
        mock_get_poid.return_value = ['{}'.format(self.dummy_erbs_nodes[0].poid)]
        user_node_data = (self.user, self.dummy_erbs_nodes[0])

        dummy_cell_list = [cell_fdn_A1, cell_fdn_A2, cell_fdn_A3, cell_fdn_A1]
        mock_fetch_cell_fdns.side_effect = [[], dummy_cell_list, dummy_cell_list]
        self.assertFalse(cellmgt.lock_unlock_cells_flow(user_node_data, sleep_time))

        mock_lock_unlock_cell.side_effect = [True for _ in range(0, 8)]
        self.assertTrue(cellmgt.lock_unlock_cells_flow(user_node_data, sleep_time))

        mock_lock_unlock_cell.side_effect = [False for _ in range(0, 8)]
        self.assertFalse(cellmgt.lock_unlock_cells_flow(user_node_data, sleep_time))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_134a_lock_unlock_cell_rest_response_status_ok_with_complete_response(self, _):
        cell_fdn = cell_fdn_A1
        post_response_read_cell_attr_data = {"requestResult": "SUCCESS",
                                             "requestErrorMessage": "",
                                             "failedMoOperations": [],
                                             "successfulMoOperations": [
                                                 {"fdn": "{cell_fdn}".format(cell_fdn=cell_fdn),
                                                  "operationType": "UPDATE",
                                                  "operationStatus": "SUCCESS",
                                                  "attributes": {"administrativeState": "LOCKED"},
                                                  "reasonForFailure": "",
                                                  "actionName": "",
                                                  "relatedMos": []}],
                                             "executionMode": "EXECUTE"}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_cell_attr_data
        self.user.post.return_value = response
        self.assertTrue(cellmgt.lock_unlock_cell_via_cell_mgt(self.user, cell_fdn, "LOCKED"))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_134b_lock_unlock_cell_rest_response_status_ok_with_corrupt_response(self, _):
        post_response_read_cell_attr_data = {"requestErrorMessage": "", "failedMoOperations": []}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_cell_attr_data
        self.user.post.return_value = response
        self.assertFalse(cellmgt.lock_unlock_cell_via_cell_mgt(self.user, cell_fdn_A1, "LOCKED"))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    def test_134c_lock_unlock_cell_rest_response_status_ok_with_operation_unsuccessful(self, _):

        post_response_read_cell_attr_data = {"requestResult": "FAILURE",
                                             "requestErrorMessage": "",
                                             "failedMoOperations": [],
                                             "successfulMoOperations": [],
                                             "executionMode": "EXECUTE"}
        response = Mock(status_code=200)
        response.json.return_value = post_response_read_cell_attr_data
        self.user.post.return_value = response
        self.assertFalse(cellmgt.lock_unlock_cell_via_cell_mgt(self.user, cell_fdn_A1, "LOCKED"))

    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    @patch('enmutils_int.lib.cellmgt.timestamp.get_string_elapsed_time', return_value=0)
    @patch('enmutils_int.lib.cellmgt.timestamp.get_current_time', return_value=0)
    @patch('enmutils_int.lib.cellmgt.get_cell_name', return_value="Cell")
    def test_134e_lock_unlock_cell_rest_response_status_ok_with_operation_unsuccessful(self, *_):
        response = Mock()
        response.json.return_value = {"requestResult": "Failed"}
        self.user.post.return_value = response
        self.assertFalse(cellmgt.lock_unlock_cell_via_cell_mgt(self.user, cell_fdn_A1, "LOCKED"))

    def test_get_list_of_existing_cells_on_nodes_is_successful(self):
        response = Mock()
        response.get_output.return_value = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-1'
                                            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-2']
        self.mock_user.enm_execute.return_value = response

        expected_list_of_cells = [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,'
                                  u'ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-2']
        self.assertEqual(cellmgt.get_list_of_existing_cells_on_node(
            user=self.mock_user, node_name=node_name, cell_mo_type='EutranCelFDD'), expected_list_of_cells)

    def test_get_list_of_existing_cells_on_nodes_returns_empty_list_if_re_does_not_match(self):
        response = Mock()
        response.get_output.return_value = ['tester']
        self.mock_user.enm_execute.return_value = response
        self.assertEqual(cellmgt.get_list_of_existing_cells_on_node(user=self.mock_user, node_name=node_name,
                                                                    cell_mo_type='EutranCelFDD'), [])

    def test_determine_existing_cells_is_successful(self):
        node = Mock()
        node.node_id = node_name
        response = Mock()
        response.get_output.return_value = [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=LTE01ERBS00001,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1',
                                            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=LTE01ERBS00001,'
                                            u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-2']
        self.mock_user.enm_execute.return_value = response

        expected_existing_cells = {'LTE01ERBS00000':
                                   [u'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01ERBS00001,ManagedElement=1,'
                                    u'ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-1',
                                    u'SubNetwork=ERBS-SUBNW-1,MeContext=LTE01ERBS00001,ManagedElement=1,'
                                    u'ENodeBFunction=1,EUtranCellFDD=LTE01ERBS00001-2']}

        self.assertEqual(cellmgt.determine_existing_cells_on_list_of_nodes(
            user=self.mock_user, source_cell_type='EutranCelFDD', nodes=[node]), expected_existing_cells)

    @patch('enmutils_int.lib.cellmgt.sleep')
    def test_view_cell_relations_success(self, *_):
        user_node_data = [self.mock_user, 'test_node']
        relations = [('INCOMING', 'readRelations', 'LTE', 'EUtranCellRelation')]

        view_cell_relations(user_node_data, relations)

        self.assertTrue(self.mock_user.post.called)

    @patch('enmutils_int.lib.cellmgt.sleep')
    @patch('enmutils.lib.log.logger.error')
    def test_view_cell_relations_raises_http_error(self, mock_error, *_):
        self.mock_user.post.side_effect = HTTPError()
        user_node_data = [self.mock_user, 'test_node']
        relations = [('INCOMING', 'readRelations', 'LTE', 'EUtranCellRelation')]

        view_cell_relations(user_node_data, relations)

        self.assertTrue(mock_error.called)

    @patch("enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node")
    @patch('enmutils_int.lib.cellmgt.filter_nodes_having_poid_set')
    def test_verify_nodes_on_enm_mo_cell_fdn_dict(self, mock_filter_nodes_having_poid_set,
                                                  mock_get_all_fdn_list_of_cells_on_node):
        mock_filter_nodes_having_poid_set.return_value = [Mock()]

        verify_nodes_on_enm_and_return_mo_cell_fdn_dict(Mock(), [Mock()], [Mock(), Mock()])

        self.assertTrue(mock_filter_nodes_having_poid_set.called)
        self.assertTrue(mock_get_all_fdn_list_of_cells_on_node.called)

    @patch("enmutils_int.lib.cellmgt.get_all_fdn_list_of_cells_on_node")
    @patch('enmutils_int.lib.cellmgt.filter_nodes_having_poid_set')
    def test_verify_nodes_on_enm_mo_cell_fdn_dict_no_verified_nodes(self, mock_filter_nodes_having_poid_set,
                                                                    mock_get_all_fdn_list_of_cells_on_node):
        mock_filter_nodes_having_poid_set.return_value = []

        verify_nodes_on_enm_and_return_mo_cell_fdn_dict(Mock(), [Mock()], [Mock(), Mock()])

        self.assertTrue(mock_filter_nodes_having_poid_set.called)
        self.assertFalse(mock_get_all_fdn_list_of_cells_on_node.called)

    def test_get_fdn_of_node_b_function_is_successful(self):
        existing_cells = {'LTE01ERBS00002':
                          [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-2'],
                          'LTE01ERBS00001':
                          [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                           u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-2']}
        expected_fdn = 'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,ENodeBFunction=1'
        self.assertEqual(cellmgt.get_fdn_of_node_b_function('LTE01ERBS00001', existing_cells), expected_fdn)

    def test_get_fdn_of_node_b_function_is_unsuccessful(self):
        existing_cells = {'LTE01ERBS00001':
                          [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                           u'ManagedElement=1,ENodeBFunction=0,EUtranCellFDD=LTE02ERBS00029-2']}
        expected_fdn = ''
        self.assertEqual(cellmgt.get_fdn_of_node_b_function('LTE01ERBS00001', existing_cells), expected_fdn)

    def test_execute_cmedit_command_to_create_new_cell_is_successful(self):
        cmedit_command = ('cmedit create SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                          'EUtranCellFDD=LTE06dg2ERBS00021-CELLMGT-1 EUtranCellFDDId=LTE06dg2ERBS00021-CELLMGT-1,'
                          'cellId=0,earfcndl=1,earfcnul=18001,'
                          'pciConflictCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'pciDetectingCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'physicalLayerCellIdGroup=0,physicalLayerSubCellId=0,tac=0')
        cell_fdn = ('SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                    'EUtranCellFDD=LLTE06dg2ERBS00021-CELLMGT-1')
        response = Mock()
        response.get_output.return_value = ['1 instance(s) updated']
        self.mock_user.enm_execute.return_value = response
        new_cell = cellmgt.execute_cmedit_command_to_create_new_cell(
            self.mock_user, cmedit_command, 'LTE06dg2ERBS00021', cell_fdn)
        self.assertEqual(new_cell, cell_fdn)

    def test_execute_cmedit_command_to_create_new_cell_could_not_create_new_cell(self):
        cmedit_command = ('cmedit create SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                          'EUtranCellFDD=LTE06dg2ERBS00021-CELLMGT-1 EUtranCellFDDId=LTE06dg2ERBS00021-CELLMGT-1,'
                          'cellId=0,earfcndl=1,earfcnul=18001,'
                          'pciConflictCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'pciDetectingCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'physicalLayerCellIdGroup=0,physicalLayerSubCellId=0,tac=0')
        cell_fdn = ('SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                    'EUtranCellFDD=LLTE06dg2ERBS00021-CELLMGT-1')
        response = Mock()
        response.get_output.return_value = []
        self.mock_user.enm_execute.return_value = response
        with self.assertRaises(ScriptEngineResponseValidationError):
            cellmgt.execute_cmedit_command_to_create_new_cell(self.mock_user, cmedit_command, 'LTE06dg2ERBS00021',
                                                              cell_fdn)

    def test_execute_cmedit_command_to_create_new_cell_catches_exception(self):
        cmedit_command = ('cmedit create SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                          'EUtranCellFDD=LTE06dg2ERBS00021-CELLMGT-1 EUtranCellFDDId=LTE06dg2ERBS00021-CELLMGT-1,'
                          'cellId=0,earfcndl=1,earfcnul=18001,'
                          'pciConflictCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'pciDetectingCell=[{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}],'
                          'physicalLayerCellIdGroup=0,physicalLayerSubCellId=0,tac=0')
        cell_fdn = ('SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00021,ENodeBFunction=1,'
                    'EUtranCellFDD=LLTE06dg2ERBS00021-CELLMGT-1')
        self.mock_user.enm_execute.side_effect = Exception
        new_cell = cellmgt.execute_cmedit_command_to_create_new_cell(
            self.mock_user, cmedit_command, 'LTE06dg2ERBS00021', cell_fdn)
        self.assertIsNone(new_cell)

    def test_create_cells_is_successful(self):
        existing_cells = {'LTE01ERBS00002':
                          [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtranCellFDD=LTE02ERBS00029-2']}
        expected_newly_created_cells = {'LTE01ERBS00002':
                                        {'EutranCelFDD': ['SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                                          'ManagedElement=1,ENodeBFunction=1,'
                                                          'EutranCelFDD=LTE01ERBS00002-CELLMGT-1',
                                                          'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                                          'ManagedElement=1,ENodeBFunction=1,'
                                                          'EutranCelFDD=LTE01ERBS00002-CELLMGT-2']}}
        response = Mock()
        response.get_output.return_value = ['1 instance(s) updated']
        self.mock_user.enm_execute.return_value = response
        self.assertEqual(cellmgt.create_cells(self.mock_user, 'EutranCelFDD', existing_cells, "FDD"),
                         expected_newly_created_cells)

    def test_create_cells_is_successful_tdd(self):
        existing_cells = {'LTE01ERBS00002':
                          [u'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,'
                           u'ENodeBFunction=1,EUtranCellTDD=LTE02ERBS00029-2']}
        expected_newly_created_cells = {'LTE01ERBS00002':
                                        {'EutranCelTDD': ['SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                                          'ManagedElement=1,ENodeBFunction=1,'
                                                          'EutranCelTDD=LTE01ERBS00002-CELLMGT-1',
                                                          'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                                          'ManagedElement=1,ENodeBFunction=1,'
                                                          'EutranCelTDD=LTE01ERBS00002-CELLMGT-2']}}
        response = Mock()
        response.get_output.return_value = ['1 instance(s) updated']
        self.mock_user.enm_execute.return_value = response
        result = cellmgt.create_cells(self.mock_user, 'EutranCelTDD', existing_cells, "TDD")
        self.assertEqual(result, expected_newly_created_cells)

    def test_execute_cmedit_command_to_delete_cells_is_successful(self):
        response = Mock()
        response.get_output.return_value = [u'20 instance(s) deleted']
        self.mock_user.enm_execute.return_value = response
        expected_num_instances_deleted = 20
        cell_fdn = ('SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,ENodeBFunction=1,'
                    'EutranCelFDD=LTE01ERBS00002-CELLMGT-1')
        self.assertEqual(
            expected_num_instances_deleted, cellmgt.execute_cmedit_command_to_delete_cells(self.mock_user, cell_fdn))

    def test_execute_cmedit_command_to_delete_cells_raises_environ_error(self):
        self.mock_user.enm_execute.side_effect = HTTPError
        cell_fdn = ('SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,ENodeBFunction=1,'
                    'EutranCelFDD=LTE01ERBS00002-CELLMGT-1')
        with self.assertRaises(EnvironError):
            cellmgt.execute_cmedit_command_to_delete_cells(self.mock_user, cell_fdn)

    def test_execute_cmedit_command_to_delete_cells_returns_0_if_no_instances_in_output(self):
        response = Mock()
        response.get_output.return_value = [u'Error: Internal Error']
        self.mock_user.enm_execute.return_value = response
        expected_num_instances_deleted = 0
        cell_fdn = ('SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,ManagedElement=1,ENodeBFunction=1,'
                    'EutranCelFDD=LTE01ERBS00002-CELLMGT-1')
        self.assertEqual(
            expected_num_instances_deleted, cellmgt.execute_cmedit_command_to_delete_cells(self.mock_user, cell_fdn))

    def test_delete_cells_is_successful(self):
        response = Mock()
        response.get_output.return_value = [u'20 instance(s) deleted']
        self.mock_user.enm_execute.return_value = response
        newly_created_cells = {'LTE01ERBS00002':
                               {'EutranCelFDD':
                                ['SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                 'ManagedElement=1,ENodeBFunction=1,EutranCelFDD=LTE01ERBS00002-CELLMGT-1',
                                 'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                 'ManagedElement=1,ENodeBFunction=1,EutranCelFDD=LTE01ERBS00002-CELLMGT-2']}}
        self.assertTrue(cellmgt.delete_cells(self.mock_user, newly_created_cells))

    def test_delete_cells_returns_false_if_no_instances_deleted(self):
        response = Mock()
        response.get_output.return_value = [u'Error: Internal Error']
        self.mock_user.enm_execute.return_value = response
        newly_created_cells = {'LTE01ERBS00002':
                               {'EutranCelFDD':
                                ['SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                 'ManagedElement=1,ENodeBFunction=1,EutranCelFDD=LTE01ERBS00002-CELLMGT-1',
                                 'SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00029,'
                                 'ManagedElement=1,ENodeBFunction=1,EutranCelFDD=LTE01ERBS00002-CELLMGT-2']}}
        self.assertFalse(cellmgt.delete_cells(self.mock_user, newly_created_cells))

    @patch('enmutils_int.lib.cellmgt.timestamp', return_value=0)
    @patch('enmutils_int.lib.cellmgt.log_and_truncate_json_response')
    @patch('enmutils_int.lib.cellmgt.raise_for_status', return_value=None)
    @patch('enmutils.lib.log.logger.debug')
    def test_fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(self, mock_debug, *_):
        poids_data = ["1234", "1235"]
        user = Mock()
        user.post.return_value.json.side_effect = ValueError("error")
        cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, poids_data)
        mock_debug.assert_called_with("The response to the HTTP request doesnt contain expected information "
                                      "(successfulMoOperations)")

    @patch('enmutils_int.lib.cellmgt.lock_unlock_cell_via_cell_mgt', side_effect=["LOCKED", "UNLOCKED"])
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt')
    def test_lock_unlock_cells_flow_applies_limit(self, mock_fetch_fdns, mock_lock_unlock):
        user = Mock()
        user.username = "Test"
        user_node_data = (user, "1234")
        mock_fetch_fdns.return_value = ["ManagedElement=1", "ManagedElement=2", "ManagedElement=3", "ManagedElement=4"]
        cellmgt.lock_unlock_cells_flow(user_node_data, 0, 1)
        self.assertEqual(mock_lock_unlock.call_count, 2)

    def test_filter_cells_on_cell_type(self):
        cells = [u"EUTranCell=1", u"GeranCell=1"]
        filtered_cells = cellmgt.filter_cells_on_cell_type(cells, "GeranCell")
        self.assertEqual([u"GeranCell=1"], filtered_cells)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.cellmgt.create_external_cell_relation', side_effect=[Exception("Error"), "Cell1", None])
    def test_create_flow(self, *_):
        user = Mock()
        profile = Mock()
        profile.RELATIONS_TO_DELETE = []
        cgi_obj = {
            "frequency": "6",
            "cellGlobalIdentity": {"mcc": "999", "mnc": "999", "lac": "9998", "cellIdentity": "3"},
            "attributes": {"ExternalGeranCell": {"externalGeranCellId": "TEST1", "cSysType": "GSM900"}},
            "targetMscId": "MSC1"}
        user_node_tuple = (user, [["FDN1", "FDN2", "FDN5"], [cgi_obj] * 3])
        cellmgt.create_flow(user_node_tuple, profile, "ExternalGeranCellRelation")
        self.assertEqual(profile.add_error_as_exception.call_count, 1)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.cellmgt.delete_cell_relation', side_effect=[Exception("Error"), None])
    def test_delete_flow_adds_exception_delete_failure(self, mock_delete_cell, *_):
        user = Mock()
        profile = Mock()
        user_node_tuple = (user, [["FDN1", "FDN2", "FDN5"], ["FDN3", "FDN4", "FDN6"]])
        cellmgt.delete_flow(user_node_tuple, profile)
        self.assertEqual(mock_delete_cell.call_count, 2)
        self.assertEqual(profile.add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_create_cell_relation(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"successfulMoOperations": [{u'fdn': u'ExternalGeranCellRelation=1027151',
                                                                  u'operationStatus': u'SUCCESS'}]}
        user.post.return_value = response
        cgi = {"FDN2": ["1"]}
        cellmgt.create_external_cell_relation(user, "FDN1", cgi, "GeranCell")
        mock_debug.assert_called_with("Successfully created cell relation: ExternalGeranCellRelation=1027151")

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_create_cell_relation_logs_failed_create(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"successfulMoOperations": []}
        user.post.return_value = response
        cgi = {"FDN2": ["1"]}
        cellmgt.create_external_cell_relation(user, "FDN1", cgi, "GeranCell")
        mock_debug.assert_called_with("Cell relation did not create successfully, "
                                      "response: [{'successfulMoOperations': []}].")

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_relation(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = None
        user.post.return_value = response
        cellmgt.delete_cell_relation(user, "FDN1")
        mock_debug.assert_called_with("Successfully deleted cell relation.")

    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_relation_no_json(self, mock_debug):
        user = Mock()
        response = Mock()
        response.status_code = 503
        response.text = None
        user.post.return_value = response
        cellmgt.delete_cell_relation(user, "FDN1")
        mock_debug.assert_called_with("ENM service failed to return a valid response, unable to determine deletion "
                                      "status.")

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_relation_logs_failed_delete(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"requestResult": "Error"}
        user.post.return_value = response
        cellmgt.delete_cell_relation(user, "FDN1")
        mock_debug.assert_called_with("Successfully deleted cell relation.")
        self.assertEqual(3, mock_debug.call_count)

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_relation_invalid_mo_raises_no_exception(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "requestResult": "ERROR",
            "requestErrorMessage": "Invalid or non existing FDN [MSC24BSC48].",
            "failedMoOperations": [],
            "successfulMoOperations": [],
            "failedMmlOperations": [],
            "successfulMmlOperations": [],
            "executionMode": "EXECUTE"
        }
        user.post.return_value = response
        cellmgt.delete_cell_relation(user, "FDN1")
        self.assertEqual(2, mock_debug.call_count)
        mock_debug.assert_called_with("FDN invalid or not found, nothing to delete.")

    @patch('enmutils.lib.log.logger.debug')
    def test_get_cell_relations(self, mock_debug, *_):
        user = Mock()
        user_node_data = (user, ["FDN1", "FDN2"])
        cellmgt.get_cell_relations(user_node_data, ("IN", "read", "GSM", "GeranCell"))
        mock_debug.assert_called_with("Successfully queried ENM for cell relations.")

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_via_rest_success(self, mock_debug, *_):
        target = CELL_FDN_CPP
        user = Mock()
        response = Mock()
        user.post.return_value = response
        cellmgt.delete_cell_via_rest(user, target)
        mock_debug.assert_called_with("Successfully deleted cell: {0}".format(target))

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_cell_via_rest_fail(self, mock_debug, *_):
        target_fdn = CELL_FDN_CPP
        json_data = {
            "executionMode": "EXECUTE",
            "responseLevel": "HIGH",
            "name": "deleteCell",
            "fdn": target_fdn,
            "force": "true"
        }
        user = Mock()
        response = Mock()
        response.status_code = 400
        response.json.return_value = {'requestResult': 'Error'}
        user.post.return_value = response
        cellmgt.delete_cell_via_rest(user, target_fdn)
        mock_debug.assert_called_with("Cell failed to delete cell correctly.\nRequest made: \t[{0}]\nResponse: \t[{1}]"
                                      .format(json.dumps(json_data), response.json()))

    @patch('enmutils_int.lib.cellmgt.generate_cell_id_for_utrancell', return_value=1)
    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    def test_create_cell_via_rest__is_successful(self, mock_debug, *_):
        user = Mock()
        response = Mock()
        user.post.return_value = response
        target_fdn = [TARGET_FDNS[0]]
        cell_id = 1
        cell_type = "EUtranCellFDD"
        unique_cell_name = target_fdn[0] + ",{0}={1}-{2}".format(cell_type, self.profile.NAME, cell_id)
        self.assertEqual(cellmgt.create_cell_via_rest(user, self.profile, [unique_cell_name], cell_type, unicode("FDD")),
                         ([unique_cell_name], {}))

        cell_type = "UtranCell"
        unique_cell_name = target_fdn[0] + ",{0}={1}-{2}".format(cell_type, self.profile.NAME, cell_id)
        self.assertEqual(cellmgt.create_cell_via_rest(user, self.profile, [unique_cell_name], cell_type, "FDD",
                                                      node_name="RNC01"),
                         ([unique_cell_name], {}))

        mock_debug.assert_called_with("Created 1/1 cell(s) of type 'UtranCell'.")

    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    @patch('enmutils_int.lib.cellmgt.generate_cell_id_for_utrancell', return_value=1)
    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch('enmutils_int.lib.cellmgt.raise_for_status', side_effect=HTTPError("Error"))
    def test_create_cell_via_rest__returns_failed_fdns_with_error_msg_when_failed_due_to_http_error(self, *_):

        target_fdns = TARGET_FDNS
        user = Mock()
        response = Mock()
        response.status_code = 400
        response.json.return_value = {"requestResult": "Error"}
        user.post.return_value = response

        expected_output = ([], {target_fdns[0]: 'Error', target_fdns[1]: 'Error'})
        self.assertEqual(cellmgt.create_cell_via_rest(user, self.profile, target_fdns, "EUtranCellFDD", unicode("FDD")),
                         expected_output)

    @patch('enmutils_int.lib.cellmgt.random.randrange', return_value=1)
    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    def test_generate_cell_id_for_utrancell__returns_first_unused_cid_from_utran_cid_range_when_successful(self,
                                                                                                           mock_debug, _):
        self.user.enm_execute.return_value.get_output.return_value = [
            "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=RNC02,MeContext=RNC02,ManagedElement=1,RncFunction=1,UtranCell=CELLMGT_05-2",
            "",
            "cId : 2",
            "",
            "",
            "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=RNC02,MeContext=RNC02,ManagedElement=1,RncFunction=1,UtranCell=CELLMGT_05-1",
            "",
            "cId : 1",
            "",
            "",
            "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=RNC02,MeContext=RNC02,ManagedElement=1,RncFunction=1,UtranCell=RNC02-92-3",
            "",
            "cId : 7162",
            "",
            ""
        ]
        self.assertEqual(cellmgt.generate_cell_id_for_utrancell(self.profile, self.user, node_name="RNC01"), 3)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.cellmgt.random.randrange', return_value=123)
    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    def test_generate_cell_id_for_utrancell__returns_random_cid_when_enm_execute_raises_error(self, mock_debug, _):
        self.user.enm_execute.side_effect = EnmApplicationError
        self.assertEqual(cellmgt.generate_cell_id_for_utrancell(self.profile, self.user, node_name="RNC01"), 123)
        self.assertEqual(self.profile.add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 3)

    def test_build_create_json_data_utran_cell(self):
        target_fdn = TARGET_FDNS[0]
        cell_type = "UtranCell"
        cell_id = '100'

        unique_cell_name = target_fdn + ",{0}={1}-{2}".format(cell_type, self.profile.NAME, cell_id)

        json_data = {
            "executionMode": "EXECUTE",
            "responseLevel": "HIGH",
            "name": "createCell",
            "fdn": unique_cell_name,
            "attributes": {
                "UtranCell": {
                    'iubLinkRef': '{0},IubLink=1'.format(target_fdn),
                    "cId": cell_id,
                    "localCellId": cell_id,
                    "primaryScramblingCode": "0",
                    "sib1PlmnScopeValueTag": "0",
                    "tCell": "0",
                    "uarfcnDl": "10",
                    "uarfcnUl": "10"},
                "LocationArea": {
                    "lac": "1"},
                "ServiceArea": {
                    "sac": "1"}},
        }
        self.assertEqual(cellmgt.build_create_cell_json(unique_cell_name, cell_type, cell_id, "FDD"), json_data)

    def test_build_create_json_data__eutrancellfdd(self):
        target_fdn = TARGET_FDNS[0]
        cell_type = "EUtranCellFDD"
        cell_id = '1'
        unique_cell_name = target_fdn + ",{0}={1}-{2}".format(cell_type, self.profile.NAME, cell_id)

        json_data = {
            "executionMode": "EXECUTE",
            "responseLevel": "HIGH",
            "name": "createCell",
            "fdn": unique_cell_name,
            "attributes": {
                "EUtranCellFDD": {
                    "cellId": unique_cell_name.split('-')[-1],
                    "EUtranCellFDDId": unique_cell_name.split('=')[-1],
                    "physicalLayerCellIdGroup": "1",
                    "physicalLayerSubCellId": "1",
                    "tac": "1",
                    "earfcndl": "2",
                    "earfcnul": "18002"}}
        }
        self.assertEqual(cellmgt.build_create_cell_json(unique_cell_name, cell_type, cell_id, unicode("FDD")), json_data)

    @patch('enmutils_int.lib.cellmgt.extract_cell_fdns', return_value=[CELL_FDN_RNC, CELL_FDN_RNC])
    @patch('enmutils.lib.log.logger.debug')
    def test_read_cells_network_element__successful(self, *_):

        network_element = 'ieatnetsimv7004-27_RNC10'
        read_cells = [CELL_FDN_RNC, CELL_FDN_RNC]
        standard = "WCDMA"
        cell_type = "UtranCell"
        user = Mock()
        response = Mock()
        response.json.return_value = {"successfulMoOperations": {"WCDMA": read_cells}}
        user.post.return_value = response

        self.assertEqual(cellmgt.read_cells_network_element(user, network_element, standard, cell_type), read_cells)

    def test_create_eutran_attributes_returns_lowercase_eutrancell_for_dg2_nodes(self):
        self.assertEqual(cellmgt.create_eutran_attributes('SWdg2-89=0089', unicode("TDD")), {"EUtranCellTDD": {
            "cellId": "89=0089",
            "eUtranCellTDDId": "0089",
            "physicalLayerCellIdGroup": "1",
            "physicalLayerSubCellId": "1",
            "tac": "1",
            "subframeAssignment": "1",
            "earfcn": "262100"}})

    def test_create_eutran_attributes_returns_uppercase_eutrancell(self):
        self.assertEqual(cellmgt.create_eutran_attributes('SWERBS-89=0089', unicode("FDD")), {"EUtranCellFDD": {
            "cellId": "89=0089",
            "EUtranCellFDDId": "0089",
            "physicalLayerCellIdGroup": "1",
            "physicalLayerSubCellId": "1",
            "tac": "1",
            "earfcndl": "2",
            "earfcnul": "18002"}})

    def test_create_eutran_attributes__raises_environ_error(self):
        self.assertRaises(EnvironError, cellmgt.create_eutran_attributes, "hello", 989)

    @patch('enmutils_int.lib.cellmgt.raise_for_status')
    @patch('enmutils.lib.log.logger.debug')
    def test_read_cells_network_element__fails(self, mock_debug, *_):

        network_element = 'ieatnetsimv7004-27_RNC10'
        standard = "WCDMA"
        cell_type = "UtranCell"
        user = Mock()
        user.post.side_effect = Exception("Errors")

        self.assertEqual(cellmgt.read_cells_network_element(user, network_element, standard, cell_type), [])
        mock_debug.assert_called_with('Error occurred retrieving cell relations: Errors')

    @patch('enmutils_int.lib.cellmgt.remove_gerancell_in_range', return_value=CELL_RANGE[-2:])
    @patch('enmutils_int.lib.cellmgt.fetch_cell_fdns_for_specified_poid_list_via_cell_mgt', return_value=CELL_RANGE)
    @patch('enmutils_int.lib.cellmgt.lock_unlock_cell_via_cell_mgt', return_value=True)
    def test_lock_unlock_cells_flow__remove_reserved_gerancells(self, mock_lock_unlock, *_):
        user = Mock()
        user.username = "Test"
        user_node_data = (user, "1234")
        cellmgt.lock_unlock_cells_flow(user_node_data, 0, remove_reserved_gerancells=True)
        self.assertEqual(mock_lock_unlock.call_count, 4)

    def test_get_utran_network__is_successful(self):

        utran_network_fdns = ["SubNetwork=RNC07,MeContext=RNC07,ManagedElement=1,RncFunction=1,UtranNetwork=6",
                              "SubNetwork=RNC07,MeContext=RNC07,ManagedElement=1,RncFunction=1,UtranNetwork=7"]
        user = Mock()
        response = Mock()
        response.get_output.return_value = CMEDIT_GET_RESPONSE
        user.enm_execute.return_value = response

        self.assertEqual(cellmgt.get_utran_network(user, 'RNC07'), utran_network_fdns)

    def test_get_utran_network__raises_EnmApplicationError(self):

        user = Mock()
        response = Mock()
        response.get_output.return_value = ['No FDN']
        user.enm_execute.return_value = response

        with self.assertRaises(EnmApplicationError):
            cellmgt.get_utran_network(user, 'RNC07')

    def test_get_utran_network__raises_Exception(self):

        user = Mock()
        user.enm_execute.side_effect = Exception

        with self.assertRaises(Exception):
            cellmgt.get_utran_network(user, 'RNC07')

    @patch('enmutils_int.lib.cellmgt.IurLink.iurlink_exists', new_callable=PropertyMock,
           side_effect=[True, False, True])
    @patch('enmutils_int.lib.cellmgt.IurLink.check_if_iurlink_exists', side_effect=[None, None, HTTPError])
    @patch('enmutils_int.lib.cellmgt.IurLink.create_iurlink')
    def test_iurlink_execute_flow(self, *_):
        profile = Mock()
        user = Mock()
        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        for _ in range(3):
            iurlink.execute()

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_check_if_iurlink_exists__iurlink_already_exists(self, mock_debug):
        profile = Mock()
        user = Mock()
        response = Mock()
        response.get_output.return_value = ['1 instance(s)']
        user.enm_execute.return_value = response
        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        iurlink.check_if_iurlink_exists()
        mock_debug.assert_called_with("IurLink already exists for {0} to RNC with Id {1}".format(iurlink.rnc_function,
                                                                                                 iurlink.rnc_id))
        self.assertEqual(iurlink.iurlink_exists, True)

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_check_if_iurlink_exists__iurlink_does_not_already_exist(self, mock_debug):
        profile = Mock()
        response = Mock()
        response.get_output.return_value = ['0 instance(s)']
        user = Mock()
        user.enm_execute.return_value = response
        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        iurlink.check_if_iurlink_exists()
        mock_debug.assert_called_with(
            "IurLink does not already exist for {0} to RNC with Id {1}.".format(iurlink.rnc_function,
                                                                                iurlink.rnc_id))
        self.assertEqual(iurlink.iurlink_exists, False)

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_check_if_iurlink_exists__raises_scriptengineresponsevalidationerror(self, *_):
        profile = Mock()
        user = Mock()
        response = Mock()
        response.get_output.return_value = ['Something went wrong']
        user.enm_execute.return_value = response

        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        with self.assertRaises(ScriptEngineResponseValidationError):
            iurlink.check_if_iurlink_exists()

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_create_iurlink__successful(self, mock_debug):
        profile = Mock()
        user = Mock()
        response = Mock()
        response.get_output.return_value = ['1 instance(s) updated']
        user.enm_execute.return_value = response

        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        iurlink.create_iurlink()
        mock_debug.assert_called_with(
            "IurLink successfully created for {0} to RNC with Id {1}".format(iurlink.rnc_function,
                                                                             iurlink.rnc_id))

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_create_iurlink__raises_scriptengineresponsevalidationerror(self, *_):
        profile = Mock()
        user = Mock()
        response = Mock()
        response.get_output.return_value = ["Error with cmedit command"]
        user.enm_execute.return_value = response

        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        with self.assertRaises(ScriptEngineResponseValidationError):
            iurlink.create_iurlink()

    @patch('enmutils.lib.log.logger.debug')
    def test_iurlink_create_iurlink__raises_httperror(self, *_):
        profile = Mock()
        user = Mock()
        user.enm_execute.side_effect = [HTTPError("Error")]

        iurlink = cellmgt.IurLink(profile, user, RNC_FUNCTION, 5, UTRAN_NETWORK)

        with self.assertRaises(HTTPError):
            iurlink.create_iurlink()

    @patch("enmutils_int.lib.cellmgt.create_external_cell_relation")
    def test_create_geran_freq_group_relation__builds_correct_json_data(self, mock_create_relation):
        user = Mock()
        source_fdn = TARGET_FDNS[0]
        freq_group_id = 6
        frequencies = ["10"]
        relation_type = "GeranFreqGroupRelation"
        expected_json_data = {
            "frequencyGroupId": freq_group_id,
            "frequencies": frequencies,
            "bandIndicator": "PCS_1900"
        }
        cellmgt.create_geran_freq_group_relation(user, source_fdn, freq_group_id, frequencies)
        mock_create_relation.assert_called_with(user, source_fdn, expected_json_data, relation_type)

    @patch('enmutils.lib.log.logger.debug')
    def test_log_and_truncate_json_response__truncates(self, mock_debug):
        json_value = u"{0}{1}{2}".format("s" * 2001, "should not be logged", "s" * 3000)
        json_data = {u"key": json_value}
        cellmgt.log_and_truncate_json_response(json_data, "operation")
        mock_debug.assert_called_with('The operation operation is being performed on the Cell Mgt Service with the '
                                      'following data:: {"key": "sssssssssssssssssssssssssssssssssssssssssssssssssss'
                                      'ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss'
                                      'ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss ... sssssssssss'
                                      'sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss'
                                      'sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss'
                                      'sssssssssssssssssssssssssssss"}')

    @patch('enmutils.lib.log.logger.debug')
    def test_log_and_truncate_json_response__does_not_truncate(self, mock_debug):
        json_value = u"should be logged."
        json_data = {u"key": json_value}
        cellmgt.log_and_truncate_json_response(json_data, "operation")
        mock_debug.assert_called_with('The operation operation is being performed on the Cell Mgt Service with the '
                                      'following data:: {"key": "should be logged."}')

    @patch('enmutils_int.lib.cellmgt.filter_cells_on_cell_type')
    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    def test_extract_cell_fdns__breaks_on_empty_mo_operations(self, mock_debug, _):
        cellmgt.extract_cell_fdns({"LTE": [{"fdn": "FDN", "neType": "RadioNode"}]})
        mock_debug.assert_called_with("The response to the HTTP request doesnt contain expected information (cells)")

    @patch('enmutils_int.lib.cellmgt.filter_cells_on_cell_type')
    @patch('enmutils_int.lib.cellmgt.log.logger.debug')
    def test_extract_cell_fdns__wrong_technology_type(self, mock_debug, _):
        self.assertListEqual([], cellmgt.extract_cell_fdns({"successfulMoOperations": {"GRAT": []}}))
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils_int.lib.cellmgt.filter_cells_on_cell_type')
    def test_extract_cell_fdns__selects_cell(self, mock_filter):
        cellmgt.extract_cell_fdns(READ_CELL_JSON.get('successfulMoOperations'))
        mock_filter.assert_any_cell([READ_CELL_JSON.get('successfulMoOperations').get('LTE')[0]], "EUtranCell")

    def test_cells_on_cell_type__returns_cell(self):
        result = cellmgt.filter_cells_on_cell_type(['SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                                                    'ManagedElement=LTE415dg2ERBS00041,ENodeBFunction=1,'
                                                    'EUtranCellFDD=LTE415dg2ERBS00041-6',
                                                    'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                                                    'ManagedElement=LTE415dg2ERBS00041,ENodeBFunction=1,'
                                                    'UtranCell=LTE415dg2ERBS00041-6'], 'EUtranCell')
        self.assertEqual(1, len(result))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
