#!/usr/bin/env python
import unittest2

from testslib import unit_test_utils
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils_int.lib import network_mo_info

from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, NoRequestedMoInfoOnEnm, NoNodesWithReqMosOnEnm


get_network_mo_info_response = {'EUtranCellFDD': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 1',
                                                  u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 2',
                                                  u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 3',
                                                  u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00002 - 1',
                                                  u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00002 - 2',
                                                  u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00003 - 1']}

group_mos_by_node_resp = {'netsim_LTE02ERBS00001': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 1',
                                                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 2',
                                                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00001 - 2'],
                          'netsim_LTE02ERBS00002': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00002 - 1',
                                                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00002 - 2'],
                          'netsim_LTE02ERBS00003': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD = LTE02ERBS00003 - 1']}


class NetworkMoInfoUnitTests(ParameterizedTestCase):
    maxDiff = None

    def setUp(self):
        unit_test_utils.setup()
        self.user = User(username="network_mo_info")
        self.network_mo_info = network_mo_info.NetworkMoInfo(self.user)
        self.network_mo_info.network_mo_count = 61230

        self.network_mo_info.mediator_dict = {
            "MSCM": {"EUtranCellFDD": 3840, "EUtranCellTDD": 0, "UtranCell": 14442},
            "MSCMCE": {"EUtranCellFDD": 21390, "EUtranCellTDD": 1000, "UtranCell": 20558}
        }
        self.network_element_response = [
            u'FDN : NetworkElement=netsim_LTE102ERBS00001', u'neType : ERBS', u'', u'', u'1 instance(s)']
        self.eutrancellfdd = [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00001-1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00001-2', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00001-3', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00002,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00002-1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00003-1', u'',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD=LTE102ERBS00003-2', u'', u'', u'6 instance(s)']

        self.eutrancelltdd = []

        self.utrancell = [u'FDN : SubNetwork=RNC05,MeContext=netsim_RNC05,ManagedElement=1,RncFunction=1,'
                          u'UtranCell=RNC05-1-1', u'',
                          u'FDN : SubNetwork=RNC23,MeContext=netsim_RNC23,ManagedElement=1,RncFunction=1,'
                          u'UtranCell=RNC23-1-1', u'',
                          u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1,'
                          u'UtranCell=RNC24-1-1', u'',
                          u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1,'
                          u'UtranCell=RNC24-2-1', u'', u'', u'4 instance(s)']

        self.gerancell = [u'FDN : SubNetwork=NETSimG,MeContext=MSC010BSC16,ManagedElement=MSC010BSC16,BscFunction=1,'
                          u'BscM=1,GeranCellM=1,GeranCell=1004938', u'',
                          u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,'
                          u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1005467', u'',
                          u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,'
                          u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1001729', u'',
                          u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,'
                          u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1004467', u'',
                          u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,BscFunction=1,'
                          u'BscM=1,GeranCellM=1,GeranCell=1001171', u'', u'', u'5 instance(s)']

        self.nrcellcu = []

        self.cells_dict = {'EUtranCellFDD': [u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00001-1',
                                             u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00001-2',
                                             u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00001-3',
                                             u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00002,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00002-1',
                                             u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00003-1',
                                             u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,'
                                             u'ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE102ERBS00003-2'],
                           'EUtranCellTDD': [],
                           'UtranCell': [u'FDN : SubNetwork=RNC05,MeContext=netsim_RNC05,ManagedElement=1,RncFunction=1'
                                         u',UtranCell=RNC05-1-1',
                                         u'FDN : SubNetwork=RNC23,MeContext=netsim_RNC23,ManagedElement=1,RncFunction=1'
                                         u',UtranCell=RNC23-1-1',
                                         u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1'
                                         u',UtranCell=RNC24-1-1',
                                         u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1'
                                         u',UtranCell=RNC24-2-1'],
                           'GeranCell': [u'FDN : SubNetwork=NETSimG,MeContext=MSC010BSC16,ManagedElement=MSC010BSC16,'
                                         u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1004938',
                                         u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,'
                                         u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1005467',
                                         u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,'
                                         u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1001729',
                                         u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,'
                                         u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1004467',
                                         u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,'
                                         u'BscFunction=1,BscM=1,GeranCellM=1,GeranCell=1001171']}
        self.sorted_dict = {
            'EUtranCellFDD': {
                'netsim_LTE102ERBS00001': [
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00001-1',
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00001-2',
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00001,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00001-3'],
                'netsim_LTE102ERBS00003': [
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00003-1',
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00003,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00003-2'],
                'netsim_LTE102ERBS00002': [
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE102ERBS00002,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD=LTE102ERBS00002-1']},
            'EUtranCellTDD': {},
            'UtranCell': {
                'netsim_RNC05': [
                    u'FDN : SubNetwork=RNC05,MeContext=netsim_RNC05,ManagedElement=1,RncFunction=1,'
                    u'UtranCell=RNC05-1-1'],
                'netsim_RNC24': [
                    u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1,'
                    u'UtranCell=RNC24-1-1',
                    u'FDN : SubNetwork=RNC24,MeContext=netsim_RNC24,ManagedElement=1,RncFunction=1,'
                    u'UtranCell=RNC24-2-1'],
                'netsim_RNC23': [
                    u'FDN : SubNetwork=RNC23,MeContext=netsim_RNC23,ManagedElement=1,RncFunction=1,'
                    u'UtranCell=RNC23-1-1']},
            'GeranCell': {
                'MSC03BSC06': [
                    u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=1001729',
                    u'FDN : SubNetwork=NETSimG,MeContext=MSC03BSC06,ManagedElement=MSC03BSC06,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=1001171'],
                'MSC08BSC15': [
                    u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=1005467',
                    u'FDN : SubNetwork=NETSimG,MeContext=MSC08BSC15,ManagedElement=MSC08BSC15,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=1004467'],
                'MSC010BSC16': [
                    u'FDN : SubNetwork=NETSimG,MeContext=MSC010BSC16,ManagedElement=MSC010BSC16,BscFunction=1,BscM=1,'
                    u'GeranCellM=1,GeranCell=1004938']}}

    def tearDown(self):
        unit_test_utils.tear_down()

    def assign_mock_values_to_cells(self):
        eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp, gerancell_resp, nrcellcu_resp = Mock(), Mock(), Mock(), Mock(), Mock()
        eutrancellfdd_resp.get_output.return_value = self.eutrancellfdd
        eutrancelltdd_resp.get_output.return_value = self.eutrancelltdd
        utrancell_resp.get_output.return_value = self.utrancell
        gerancell_resp.get_output.return_value = self.gerancell
        nrcellcu_resp.get_output.return_value = self.nrcellcu

        return utrancell_resp, eutrancellfdd_resp, eutrancelltdd_resp, gerancell_resp, nrcellcu_resp

    # get_nodes_with_required_num_of_mos_on_enm ########################################################################

    @patch('enmutils_int.lib.network_mo_info.get_workload_admin_user')
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo')
    def tests_get_nodes_with_required_num_of_mos_on_enm_successfully_returns_expected_node_names(
            self, mock_network_mo_info, *_):

        mock_network_mo_info.return_value.get_network_mos_info.return_value = get_network_mo_info_response
        mock_network_mo_info.return_value.group_mos_by_node.return_value = group_mos_by_node_resp

        self.assertEqual(['netsim_LTE02ERBS00001', 'netsim_LTE02ERBS00002'],
                         network_mo_info.get_nodes_with_required_num_of_mos_on_enm({"EUtranCellFDD": 2}))

    @patch('enmutils_int.lib.network_mo_info.get_workload_admin_user')
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo')
    def tests_get_nodes_with_required_num_of_mos_on_enm_raises_exception_when_no_mo_info_is_available(
            self, mock_network_mo_info, *_):

        mock_network_mo_info.return_value.get_network_mos_info.return_value = {}

        self.assertRaises(NoRequestedMoInfoOnEnm, network_mo_info.get_nodes_with_required_num_of_mos_on_enm, {"EUtranCellFDD": 1})

    @patch('enmutils_int.lib.network_mo_info.get_workload_admin_user')
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo')
    def tests_get_nodes_with_required_num_of_mos_on_enm_raises_exception_when_no_nodes_contain_req_num_of_mos(
            self, mock_network_mo_info, *_):
        mock_network_mo_info.return_value.get_network_mos_info.return_value = get_network_mo_info_response

        self.assertRaises(NoNodesWithReqMosOnEnm, network_mo_info.get_nodes_with_required_num_of_mos_on_enm,
                          {"EUtranCellFDD": 5})

    # get_network_mos_info #############################################################################################

    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_mos_info_successfully_returns_the_expected_result(self, mock_enm_execute, *_):
        utrancell_resp, eutrancellfdd_resp, eutrancelltdd_resp, gerancell_resp, nrcellcu_resp = self.assign_mock_values_to_cells()

        mock_enm_execute.side_effect = [utrancell_resp, eutrancellfdd_resp, eutrancelltdd_resp, gerancell_resp,
                                        nrcellcu_resp]
        response = self.network_mo_info.get_network_mos_info()

        self.assertEqual(5, len(response.keys()))
        self.assertEqual(response.get("EUtranCellTDD"), [])
        self.assertEqual(len(response.get("EUtranCellFDD")), 6)
        self.assertEqual(len(response.get("UtranCell")), 4)

    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_mos_info__successfully_logs_an_error_when_0_instances_are_found_for_a_cell_type(
            self, mock_enm_execute, mock_debug):

        eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp, gerancell_resp, nrcellcu_resp = self.assign_mock_values_to_cells()
        gerancell_resp.get_output.return_value = ["0 instance(s)"]

        # .iteritems() in the code arranges the commands alphabetically so the order of the side effect is necessary
        mock_enm_execute.side_effect = [gerancell_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp, nrcellcu_resp]

        self.network_mo_info.get_network_mos_info()

        self.assertEqual(mock_debug.call_count, 4)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_mos_info__retry_if_got_error(self, mock_enm_execute, mock_debug):

        eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp, gerancell_resp, nrcellcu_resp = self.assign_mock_values_to_cells()
        gerancell_resp.get_output.return_value = ["Error 9999"]

        # .iteritems() in the code arranges the commands alphabetically so the order of the side effect is necessary
        mock_enm_execute.side_effect = [gerancell_resp, gerancell_resp, gerancell_resp, gerancell_resp, gerancell_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp]

        self.network_mo_info.get_network_mos_info()

        self.assertEqual(mock_debug.call_count, 12)

    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_get_network_mos_info__retry_reaches_5(self, mock_enm_execute, mock_debug):

        eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp, gerancell_resp, nrcellcu_resp = self.assign_mock_values_to_cells()
        gerancell_resp.get_output.return_value = ["Error 9999"]

        # .iteritems() in the code arranges the commands alphabetically so the order of the side effect is necessary
        mock_enm_execute.side_effect = [gerancell_resp, gerancell_resp, gerancell_resp, gerancell_resp, gerancell_resp, gerancell_resp,
                                        eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp, eutrancellfdd_resp, eutrancelltdd_resp, utrancell_resp,
                                        nrcellcu_resp]

        self.network_mo_info.get_network_mos_info()

        self.assertEqual(mock_debug.call_count, 13)

    # get_mo_network_info_subgrouped_by_node TESTS ###################################################################################

    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.get_network_mos_info')
    def test_get_mo_network_info_subgrouped_by_node(self, mock_get_network_mos_info):
        mock_get_network_mos_info.return_value = self.cells_dict
        response = self.network_mo_info.get_mo_network_info_subgrouped_by_node()
        self.assertListEqual(sorted(response.get("UtranCell").keys()), ["netsim_RNC05", "netsim_RNC23", "netsim_RNC24"])
        self.assertListEqual(response.get("EUtranCellTDD").keys(), [])
        self.assertListEqual(sorted(response.get("EUtranCellFDD").keys()), ["netsim_LTE102ERBS00001",
                                                                            "netsim_LTE102ERBS00002",
                                                                            "netsim_LTE102ERBS00003"])

    # group_cells_by_node TESTS ########################################################################################

    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    def test_group_total_cells_by_node__successfully_returns_the_expected_result(self, *_):
        for cell_type in self.sorted_dict:
            self.assertDictEqual(self.sorted_dict.get(cell_type),
                                 network_mo_info.group_mos_by_node(self.cells_dict.get(cell_type)))

    # group_ne_type_per_mo_type_and_count TESTS ################################################################################

    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.generate_and_update_gsm_relation_file')
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.build_ne_type_dict')
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.get_mo_network_info_subgrouped_by_node')
    def test_group_ne_type_per_mo_type_and_count_successfully_returns_the_expected_result(
            self, mock_get_mo_network_info_subgrouped_by_node, mock_build_ne_type_dict, *_):

        mock_build_ne_type_dict.return_value = {
            'netsim_LTE102ERBS00001': 'ERBS',
            'netsim_LTE102ERBS00003': 'ERBS',
            'netsim_LTE102ERBS00002': 'ERBS',
            'netsim_RNC05': 'RNC',
            'netsim_RNC24': 'RNC',
            'netsim_RNC23': 'RNC',
            'MSC03BSC06': 'BSC',
            'MSC08BSC15': 'BSC',
            'MSC010BSC16': 'BSC'}
        mock_get_mo_network_info_subgrouped_by_node.return_value = self.sorted_dict

        response = self.network_mo_info.group_ne_type_per_mo_type_and_count()

        self.assertEqual(response.keys(), ['ERBS', 'RNC', 'BSC'])
        self.assertDictEqual(response.get("ERBS"), {'EUtranCellFDD': 6})
        self.assertDictEqual(response.get("RNC"), {'UtranCell': 4})
        self.assertDictEqual(response.get("BSC"), {'GeranCell': 5})

    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.group_ne_type_per_mo_type_and_count')
    def test_map_ne_types_to_mediator_and_update_cell_count(self, mock_ne_type_per_cell_count):
        expected = {
            'MSCMCE': {'EUtranCellFDD': 6, 'EUtranCellTDD': 5, 'UtranCell': 5},
            'MSCM': {'EUtranCellFDD': 22, 'EUtranCellTDD': 2, 'UtranCell': 11}
        }
        mock_ne_type_per_cell_count.return_value = {
            "ERBS": {'EUtranCellFDD': 6, 'UtranCell': 4},
            "RNC": {'EUtranCellFDD': 6, 'UtranCell': 4},
            "RadioNode": {'EUtranCellFDD': 6, 'UtranCell': 4}
        }
        self.network_mo_info.mediator_dict = {
            'MSCMCE': {'EUtranCellFDD': 0, 'EUtranCellTDD': 5, 'UtranCell': 1},
            'MSCM': {'EUtranCellFDD': 10, 'EUtranCellTDD': 2, 'UtranCell': 3}
        }
        self.network_mo_info.map_ne_types_to_mediator_and_update_mo_count()
        self.assertDictEqual(self.network_mo_info.mediator_dict, expected)

    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.group_ne_type_per_mo_type_and_count')
    def test_map_ne_types_to_mediator_and_update_cell_count__ignores_none_type(self, mock_ne_type_per_cell_count):
        expected = {
            'MSCMCE': {'EUtranCellFDD': 0, 'EUtranCellTDD': 0, 'UtranCell': 0},
            'MSCM': {'EUtranCellFDD': 6, 'EUtranCellTDD': 0, 'UtranCell': 4}
        }
        mock_ne_type_per_cell_count.return_value = {
            "None": {'EUtranCellFDD': 6, 'UtranCell': 4},
            "RNC": {'EUtranCellFDD': 6, 'UtranCell': 4}
        }
        self.network_mo_info.mediator_dict = {
            'MSCMCE': {'EUtranCellFDD': 0, 'EUtranCellTDD': 0, 'UtranCell': 0},
            'MSCM': {'EUtranCellFDD': 0, 'EUtranCellTDD': 0, 'UtranCell': 0}
        }
        self.network_mo_info.map_ne_types_to_mediator_and_update_mo_count()
        self.assertDictEqual(self.network_mo_info.mediator_dict, expected)

    def test_update_mediation_cell_count_values(self):
        existing_cell_count = {"EutrancCellFDD": 60, "UtranCell": 18, "EUtranCellTDD": 2}
        cell_count = {"EutrancCellFDD": 12, "UtranCell": 8}
        expected = {"EutrancCellFDD": 72, "UtranCell": 26, "EUtranCellTDD": 2}
        result = self.network_mo_info.update_mediation_mo_count_values(existing_cell_count, cell_count)
        self.assertDictEqual(expected, result)

    @ParameterizedTestCase.parameterize(
        ("ne_type", "mediator"),
        [
            ("ERBS", "MSCM"),
            ("RNC", "MSCM"),
            ("RadioNode", "MSCMCE"),
            ("RKI", None),
        ]
    )
    def test_match_to_mediatior(self, ne_type, mediator):
        self.assertEqual(self.network_mo_info.match_to_mediatior(ne_type), mediator)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_build_ne_type_dict(self, mock_execute):
        response = Mock()
        response.get_output.return_value = [u'FDN : NetworkElement=LTE40dg2ERBS00001', u'neType : RadioNode', u'',
                                            u'FDN : NetworkElement=LTE40dg2ERBS00002', u'neType : RadioNode', u'',
                                            u'', u'2 instance(s)']
        mock_execute.return_value = response
        expected = {"LTE40dg2ERBS00001": "RadioNode", "LTE40dg2ERBS00002": "RadioNode"}
        self.assertDictEqual(expected, self.network_mo_info.build_ne_type_dict())

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_build_ne_type_dict_raises_script_engine_response_error(self, mock_execute):
        response = Mock()
        response.get_output.return_value = [u'', u'0 Instance(s)']
        mock_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.network_mo_info.build_ne_type_dict)
        response.get_output.return_value = [u'ErroR']
        mock_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.network_mo_info.build_ne_type_dict)

    @patch('enmutils_int.lib.network_mo_info.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.retrieve_list_of_rnc_nodes_from_enm', return_value=["RNC01"])
    @patch('enmutils_int.lib.network_mo_info.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.touch_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.delete_file')
    def test_generate_and_update_gsm_relation_file__writes_to_file(self, mock_delete_file, mock_touch_file,
                                                                   mock_write_data_to_file, *_):
        user = Mock()
        user.enm_execute.return_value.get_output.return_value = [u'FDN : ManagedElement=RNC1,UtranCell-1,GsmRelation=1']
        self.network_mo_info.user = user
        self.network_mo_info.generate_and_update_gsm_relation_file()
        self.assertEqual(mock_delete_file.call_count, 1)
        self.assertEqual(mock_touch_file.call_count, 1)
        self.assertEqual(mock_write_data_to_file.call_count, 2)

    @patch('enmutils_int.lib.network_mo_info.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.retrieve_list_of_rnc_nodes_from_enm', return_value=[])
    @patch('enmutils_int.lib.network_mo_info.filesystem.touch_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.delete_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.write_data_to_file')
    def test_generate_and_update_gsm_relation_file__only_adds_rncs_on_enm(self, mock_write_data_to_file, *_):
        self.network_mo_info.generate_and_update_gsm_relation_file()
        self.assertEqual(mock_write_data_to_file.call_count, 0)

    @patch('enmutils_int.lib.network_mo_info.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.network_mo_info.NetworkMoInfo.retrieve_list_of_rnc_nodes_from_enm', return_value=["RNC01"])
    @patch('enmutils_int.lib.network_mo_info.filesystem.touch_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.delete_file')
    @patch('enmutils_int.lib.network_mo_info.filesystem.write_data_to_file', )
    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    def test_generate_and_update_gsm_relation_file__write_data_failure_logs_exception(self, mock_debug, *_):
        user = Mock()
        user.enm_execute.return_value.get_output.side_effect = Exception("Error")
        self.network_mo_info.user = user
        self.network_mo_info.generate_and_update_gsm_relation_file()
        self.assertEqual(mock_debug.call_count, 3)

    def test_retrieve_list_of_rnc_nodes_from_enm__success(self):
        user = Mock()
        user.enm_execute.return_value.get_output.return_value = [u'FDN : NetworkElement=RNC1',
                                                                 u'FDN : NetworkElement=RNC2', u'', u'2 instance(s)']
        self.network_mo_info.user = user
        self.assertEqual(2, len(self.network_mo_info.retrieve_list_of_rnc_nodes_from_enm()))

    def test_retrieve_list_of_rnc_nodes_from_enm__scope_error(self):
        user = Mock()
        user.enm_execute.return_value.get_output.return_value = [u'Error : 1111 Scope issue']
        self.network_mo_info.user = user
        self.assertListEqual([], self.network_mo_info.retrieve_list_of_rnc_nodes_from_enm())

    @patch('enmutils_int.lib.network_mo_info.log.logger.debug')
    def test_retrieve_list_of_rnc_nodes_from_enm__logs_exception(self, mock_debug):
        user = Mock()
        user.enm_execute.return_value.get_output.side_effect = Exception("Error")
        self.network_mo_info.user = user
        self.network_mo_info.retrieve_list_of_rnc_nodes_from_enm()
        self.assertEqual(1, mock_debug.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
