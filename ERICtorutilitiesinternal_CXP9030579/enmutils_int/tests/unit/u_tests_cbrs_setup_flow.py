import unittest2
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip
from mock import patch, Mock, PropertyMock
from parameterizedtestcase import ParameterizedTestCase
from enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow import (CbrsSetupFlow,
                                                                       DEVICE_2208, DEVICE_NR_4408,
                                                                       DEVICE_RADIODOT, DEVICE_4408, DEVICE_6488,
                                                                       DEVICE_PASSIVE_DAS_4408)
from enmutils.lib.exceptions import EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError

SAMPLE_CMEDIT_RESPONSE = ["FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE32dg2ERBS00020,ENodeBFunction=1,EUtranCellTDD=LTE32dg2ERBS00020-5",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-10",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-9",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-11",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-8",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-7",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-4",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-6",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-5",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-2",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-1",
                          "FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
                          "LTE26dg2ERBS00014,ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-3",
                          "12 instance(s)"]
SAMPLE_CMEDIT_RESPONSE2 = ["FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=8",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=2",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=7",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=9",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=4",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=1",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=11",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=5",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=12",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=10",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=3",
                           "FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement="
                           "NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=6",
                           "12 instance(s)"]


class CBRSUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.profile = CbrsSetupFlow()
        self.profile.NUM_DEVICES = 500
        self.profile.NUM_USERS = 1
        self.profile.DEVICES_REQUIRED = {"2208": 1, "RadioDot": 8, "4408": 1, "6488": 1, "DEVICE_NR_4408": 1, "PassiveDas_4408": 10}
        self.profile.USER_ROLES = ['ADMINISTRATOR']
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.SAS_URL = generate_configurable_ip()
        self.profile.CBRS_PAL_PERCENTAGE = 0.10
        self.profile.MIXPALGAA_PERCENTAGE = 0.50

    def tearDown(self):
        self.profile.DEVICES_REQUIRED = {}
        self.profile.product_data_dict = {}

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.'
           'update_profile_persistence_nodes_list')
    def test_update_nodes_used_by_profile__is_successful(self, mock_update_nodes_list, _):
        mock_nodes = [Mock(node_id='node_{0}'.format(_ + 1)) for _ in range(5)]
        self.profile.lite_nodes = mock_nodes
        used_nodes = {'node_1', 'node_4', 'node_5'}
        self.profile.update_nodes_used_by_profile(used_nodes)
        mock_update_nodes_list.assert_called_once_with([mock_nodes[1], mock_nodes[2]])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_cells_numerical_order')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_by_cell_size__correct(self, *_):
        self.profile.cbrs_cell_fdns = [
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
            'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-1',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00015,'
            'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-2',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00016,'
            'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-3', ]
        self.profile.cell_size = {1: [], 12: []}
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00016": []}
        self.profile.sort_by_cell_size()
        self.assertEqual(3, len(self.profile.cell_size[1]))

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_cells_numerical_order')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_by_cell_size__invalid_cell_size(self, *_):
        self.profile.cell_size = {2: [], 3: [], 6: [], 12: []}
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00016": ['cell1']}
        self.profile.sort_by_cell_size()
        self.assertTrue('LTE26dg2ERBS00016' not in self.profile.sorted_cbrs_cells)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_by_product_data")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_radiodots_and_get_device_counts')
    def test_sort_device_type__correct(self, mock_sort_radiodots, *_):
        self.profile.fru_dict = {"LTE29dg2ERBS00059": 1, "LTE29dg2ERBS00054": 1, "LTE26dg2ERBS00014": 2,
                                 "LTE26dg2ERBS00015": 2, "LTE26dg2ERBS00016": 40,
                                 "LTE26dg2ERBS00017": 1, "LTE26dg2ERBS00018": 41}
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00014": 2, "LTE26dg2ERBS00015": 2, "LTE26dg2ERBS00016": 2,
                                          "LTE26dg2ERBS00017": 1, "LTE29dg2ERBS00054": 1, "LTE26dg2ERBS00018": 12,
                                          "LTE29dg2ERBS00059": 3}
        self.profile.cell_size = {2: ["NR12gNodeBRadio00022"],
                                  3: ["LTE29dg2ERBS00059"],
                                  6: ["LTE26dg2ERBS00014", "LTE26dg2ERBS00017"],
                                  12: ["LTE26dg2ERBS00015", "LTE26dg2ERBS00016", "LTE26dg2ERBS00018",
                                       "LTE29dg2ERBS00054"]}
        self.profile.sort_device_type()
        self.assertTrue(mock_sort_radiodots.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_radiodots_and_get_device_counts__4x4_radiodot(self, *_):
        mock_device_count_dict_per_node = {"LTE44dg2ERBS00003": 48}
        self.profile.rf_branch_count_dict = {"LTE44dg2ERBS00003": 4}
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productName=RD 4442 B48"]}
        self.profile.sort_radiodots_and_get_device_counts("LTE44dg2ERBS00003")
        self.assertEqual(mock_device_count_dict_per_node, self.profile.device_count_dict_per_node)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_radiodots_and_get_device_counts__radiodot_not_in_dict(self, *_):
        mock_device_count_dict_per_node = {}
        self.profile.rf_branch_count_dict = {"LTE44dg2ERBS00096": 4}
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productName=RD 4442 B48"]}
        self.profile.sort_radiodots_and_get_device_counts("LTE44dg2ERBS00003")
        self.assertDictEqual(mock_device_count_dict_per_node, self.profile.device_count_dict_per_node)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_radiodots_and_get_device_counts__rf_count_not_2_or_4(self, mock_log):
        self.profile.rf_branch_count_dict = {"LTE44dg2ERBS00003": 3}
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productName=RD 4442 B48"]}
        self.profile.sort_radiodots_and_get_device_counts("LTE44dg2ERBS00003")
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_radiodots_and_get_device_counts__2x2_radiodot(self, *_):
        mock_device_count_dict_per_node = {"LTE44dg2ERBS00003": 24}
        self.profile.rf_branch_count_dict = {"LTE44dg2ERBS00003": 2}
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productName=testing"]}
        self.profile.sort_radiodots_and_get_device_counts("LTE44dg2ERBS00003")
        self.assertEqual(mock_device_count_dict_per_node, self.profile.device_count_dict_per_node)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_rf_data_per_node_id')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.count_all_rf_branches')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_node_ids_from_rf_data')
    def test_get_rf_branch__successful(self, mock_get_node_ids_from_rf_data, mock_count_all_rf_branches, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = (
            "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03dg2ERBS00025,"
            "NodeSupport=1,SectorEquipmentFunction=1', u'rfBranchRef  [SubNetwork=Europe,SubNetwork=Ireland,"
            "SubNetwork=NETSimW,ManagedElement=LTE03dg2ERBS00025,Equipment=1,AntennaUnitGroup=1,RfBranch=1,"
            " SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03dg2ERBS00025,Equipment=1,"
            "AntennaUnitGroup=1,RfBranch=2]")
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_rf_branch(mock_user)
        self.assertEqual(mock_get_node_ids_from_rf_data.call_count, 1)
        self.assertEqual(mock_count_all_rf_branches.call_count, 1)

    @patch('enmutils.lib.exceptions.EnvironError')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.count_all_rf_branches')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_rf_data_per_node_id')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_node_ids_from_rf_data')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_rf_branch__environ_error_raised(self, mock_log, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = ["error 0 instance(s)"]
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_rf_branch(user=mock_user)
        mock_log.assert_called_with("Could not use node, error encountered: [No RfBranchRef data found: [['error 0 instance(s)']]].")

    def test_count_all_rf_branches__successful(self):
        self.profile.rf_data_dict = {'LTE47dg2ERBS00035': ["SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                           "ManagedElement=LTE47dg2ERBS00035,NodeSupport=1,SectorEquipmentFunction=1',"
                                                           " u'rfBranchRef  [SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                           "ManagedElement=LTE47dg2ERBS00035,Equipment=1,AntennaUnitGroup=1,RfBranch=1,"
                                                           " SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE47dg2ERBS00035,"
                                                           "Equipment=1,AntennaUnitGroup=1,RfBranch=2, SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                           "ManagedElement=LTE47dg2ERBS00035,Equipment=1,AntennaUnitGroup=1,RfBranch=3, "
                                                           "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE47dg2ERBS00035,"
                                                           "Equipment=1,AntennaUnitGroup=1,RfBranch=4]', u'', u'"],
                                     'LTE14dg2ERBS00096': ["SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                           " ManagedElement=LTE14dg2ERBS00006,NodeSupport=1,SectorEquipmentFunction=1',"
                                                           "u'rfBranchRef  [SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                           " ManagedElement=LTE14dg2ERBS00006,Equipment=1,AntennaUnitGroup=1,RfBranch=1]"]}
        self.profile.rf_branch_count_dict = {"LTE14dg2ERBS00096": 4}
        mock_expected_rf_branch_count_dict = {'LTE47dg2ERBS00035': 4, "LTE14dg2ERBS00096": 4}
        self.profile.count_all_rf_branches()
        self.assertDictEqual(self.profile.rf_branch_count_dict, mock_expected_rf_branch_count_dict)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_node_ids_from_rf_data__successful(self, _):
        mock_split_dict = ["FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE02dg2ERBS00041,"
                           "NodeSupport=1,SectorEquipmentFunction=4 rfBranchRef : 1",
                           "FDN: SubNetwork=Europe,SubNetwork=Ireland, SubNetwork=NETSimW,ManagedElement=LTE02dg2ERBS00042,]", "'u"]
        self.profile.rf_data_dict = {"LTE02dg2ERBS00042": []}
        mock_rf_data_dict = {'LTE02dg2ERBS00042': [],
                             'LTE02dg2ERBS00041': []}
        self.profile.get_node_ids_from_rf_data(mock_split_dict)
        self.assertDictEqual(self.profile.rf_data_dict, mock_rf_data_dict)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_rf_data_per_node_id(self, _):
        self.profile.rf_data_dict = {"LTE02dg2ERBS00042": []}
        mock_rf_data_dict_after_iteration = {"LTE02dg2ERBS00042": ["SubNetwork=NETSimW,ManagedElement=LTE02dg2ERBS00042"]}
        mock_rf_data_split = ["data node1", "SubNetwork=NETSimW,ManagedElement=LTE02dg2ERBS00042"]
        self.profile.get_rf_data_per_node_id(mock_rf_data_split)
        self.assertDictEqual(self.profile.rf_data_dict, mock_rf_data_dict_after_iteration)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_by_product_data")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_sort_device_type__no_nodes_having_right_number_cells(self, *_):
        self.profile.fru_dict = {"LTE29dg2ERBS00059": 1, "LTE29dg2ERBS00054": 1, "LTE26dg2ERBS00014": 2,
                                 "LTE26dg2ERBS00015": 2, "LTE26dg2ERBS00016": 40,
                                 "LTE26dg2ERBS00017": 1, "LTE26dg2ERBS00018": 41}
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00014": 2, "LTE26dg2ERBS00015": 2, "LTE26dg2ERBS00016": 2,
                                          "LTE26dg2ERBS00017": 1, "LTE29dg2ERBS00054": 1, "LTE26dg2ERBS00018": 12,
                                          "LTE29dg2ERBS00059": 3}
        self.profile.cell_size = {2: [""],
                                  3: [""],
                                  6: ["", ""],
                                  12: ["", "", "", ""]}
        self.profile.sort_device_type()
        self.assertFalse(self.profile.sort_by_product_data.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.validate_frus")
    def test_get_device_count_based_on_frus__no_devices(self, mock_device_count_node, *_):
        mock_node = "LTE26dg2ERBS00014"
        mock_device_count_node.return_value = 0
        self.profile.get_device_count_based_on_frus(mock_node, Mock(), Mock())
        self.assertTrue(mock_node not in self.profile.device_count_dict_per_node.keys())

    def test_get_device_count_based_on_nr_nodes_6_devices(self):
        mock_values = "NR118gNodeBRadio00011"
        self.profile.cell_size = {2: [], 3: [], 6: [], 12: [mock_values]}
        self.assertEqual(self.profile.get_device_count_based_on_nr_nodes(node_id=mock_values), 6)

    def test_get_device_count_based_on_nr_nodes_3_devices(self):
        mock_values = "NR118gNodeBRadio00011"
        self.profile.cell_size = {2: [], 3: [], 6: [mock_values], 12: []}
        self.assertEqual(
            self.profile.get_device_count_based_on_nr_nodes(node_id=mock_values), 3)

    def test_get_device_count_based_on_nr_nodes_1_devices(self):
        mock_values = "NR118gNodeBRadio00011"
        self.profile.cell_size = {2: [], 3: [mock_values], 6: [], 12: []}
        self.assertEqual(
            self.profile.get_device_count_based_on_nr_nodes(node_id=mock_values), 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils.lib.exceptions.EnvironError')
    def test_get_all_product_data__correct(self, *_):
        mock_user = Mock()
        mock_node = "LTE26dg2ERBS00014"
        mock_response = Mock()
        mock_response.get_output.return_value = ("u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                 "ManagedElement=LTE26dg2ERBS00014,Equipment=1,"
                                                 "FieldReplaceableUnit=2', u'productData : {productionDate=20180301, "
                                                 "serialNumber=D829144004, productNumber=KRC 161 746/1, "
                                                 "productName=Radio 4408 B48, productRevision=R1B}', u'', "
                                                 "u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                 "ManagedElement=LTE44dg2ERBS00003,Equipment=1,"
                                                 "FieldReplaceableUnit=1', u'productData : {productionDate=20180301, "
                                                 "serialNumber=D829144003, productNumber=KRC 161 746/1, "
                                                 "productName=Radio 4408 B48, productRevision=R1B}', u'', u'', "
                                                 "u'2 instance(s)'")
        mock_user.enm_execute.return_value = mock_response
        self.profile.lite_nodes = [Mock(node_id="LTE26dg2ERBS00014")]
        self.profile.get_all_product_data(mock_user)
        self.assertTrue(mock_node in self.profile.node_ids)

    @patch(
        "enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.build_product_data_dict_per_nodes_chunk")
    @patch("enmutils.lib.log.logger.debug")
    def test_build_product_data_dict__is_successful(self, mock_debug, *_):
        self.profile.node_ids = ["LTE26dg2ERBS00022", "NR118gNodeBRadio00011", "LTE24dg2ERBS00022", "LTE55dg2ERBS00036"]
        self.profile.build_product_data_dict()
        self.assertEqual(mock_debug.call_count, 5)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_build_product_data_dict_per_nodes_chunk__node_and_product_data_added_correctly(self, *_):
        self.profile.node_ids = ["LTE26dg2ERBS00022", "NR118gNodeBRadio00011", "LTE24dg2ERBS00022", "LTE55dg2ERBS00036"]
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00022": 0, "LTE24dg2ERBS00022": 0}
        self.profile.product_data_split = ["SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW "
                                           "ManagedElement=LTE26dg2ERBS00022,Equipment=1, "
                                           "FieldReplaceableUnit=2', u'productData : {productionDate=20180301, "
                                           "serialNumber=D829144004, productNumber=KRC 161 746/1, "
                                           "productName=Radio 4408 B48, productRevision=R1B}', u'', ",
                                           "u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                           "ManagedElement=LTE24dg2ERBS00022,Equipment=1,"
                                           "FieldReplaceableUnit=1', u'productData : {productionDate=20180301, "
                                           "serialNumber=D829144003, productNumber=KRC 161 746/1, "
                                           "productName=Radio 4408 B48, productRevision=R1B",
                                           "u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                           "ManagedElement=LTE55dg2ERBS00036,Equipment=1,"
                                           "FieldReplaceableUnit=1', u'productData : {productionDate=20180301, "
                                           "serialNumber=D829144003, productNumber=KRC 161 746/1, "
                                           "productName=Radio 4408 B48, productRevision=R1B"]
        self.profile.build_product_data_dict_per_nodes_chunk(self.profile.node_ids)
        self.assertTrue(len(self.profile.product_data_dict) == 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch(
        "enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.build_product_data_dict_for_validating_device_count")
    def test_build_product_data_dict_per_nodes_chunk__call_build_product_data_dict_for_validating_device_count_success(
            self, mock_build_product_dict_for_validation, *_):
        self.profile.node_ids = ["LTE26dg2ERBS00022"]
        self.profile.sorted_cbrs_cells = {"LTE26dg2ERBS00022": 0}
        self.profile.product_data_split = []
        self.profile.build_product_data_dict_per_nodes_chunk(self.profile.node_ids)
        self.assertTrue(mock_build_product_dict_for_validation.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_mock_build_product_dict_for_validation__lenth_of_product_data_dict_values_is_forty_eight(self, *_):
        self.profile.sorted_cbrs_cells = {"LTE15dg2ERBS00055": 3}
        mock_product_data = self.profile.product_data_split = ["LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1"
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1"
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1",
                                                               "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1", "LTE15dg2ERBS00055 serialNumber=D82911555002, productNumber=KRC 161 746/1"]
        self.profile.build_product_data_dict_for_validating_device_count("LTE15dg2ERBS00055", mock_product_data)
        self.assertTrue(len(self.profile.product_data_dict["LTE15dg2ERBS00055"]) == 120)

    def test_get_all_product_data__node_not_in_product_data_dict(self):
        mock_user = Mock()
        self.profile.product_data_dict = {"node1": "productdata"}
        mock_node = "node1"
        mock_response = Mock()
        mock_response.get_output.return_value = ("u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                 "ManagedElement=node1,Equipment=1,"
                                                 "FieldReplaceableUnit=2', u'productData : {productionDate=20180301, "
                                                 "serialNumber=D829144004, productNumber=KRC 161 746/1, "
                                                 "productName=Radio 4408 B48, productRevision=R1B}', u'', "
                                                 "u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,"
                                                 "ManagedElement=node1,Equipment=1,"
                                                 "FieldReplaceableUnit=1', u'productData : {productionDate=20180301, "
                                                 "serialNumber=D829144003, productNumber=KRC 161 746/1, "
                                                 "productName=Radio 4408 B48, productRevision=R1B}', u'', u'', "
                                                 "u'2 instance(s)'")
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_all_product_data(mock_user)
        self.assertTrue(mock_node in self.profile.product_data_dict.keys())

    def test_validate_frus_2_device(self):
        mock_values = ["KRD 901 160/11", "KRD 901 160/11"]
        self.assertEqual(self.profile.validate_frus(product_data_per_node=mock_values, device_type=DEVICE_6488), 2)

    def test_validate_frus_0_device(self):
        mock_values = ["Test", "KYR 030 405/12"]
        self.assertEqual(self.profile.validate_frus(product_data_per_node=mock_values, device_type=DEVICE_6488), 0)

    def test_sort_by_product_data__incorrect_product_data(self):
        mock_node_id = "LTE44dg2ERBS00003"
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productNumber=ABC 123/456"]}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertTrue(mock_node_id not in self.profile.device_type[DEVICE_4408])

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_device_count_based_on_frus")
    def test_sort_by_product_data__values_is_none(self, mock_get_device_count_based_on_frus):
        mock_node_id = "LTE44dg2ERBS00003"
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": []}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertFalse(mock_get_device_count_based_on_frus.called)

    def test_sort_by_product_data__4408_device(self):
        mock_node_id = "LTE44dg2ERBS00003"
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productNumber=KRC 161 746/1"]}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertTrue(mock_node_id in self.profile.device_type[DEVICE_4408])

    def test_sort_by_product_data__nr_4408_device(self):
        mock_node_id = "NR20gNodeBRadio00027"
        self.profile.product_data_dict = {"NR20gNodeBRadio00027": ["productNumber=KRC 161 746/1"]}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertTrue(mock_node_id in self.profile.device_type[DEVICE_NR_4408])

    def test_sort_by_product_data__6488_device(self):
        mock_node_id = "LTE44dg2ERBS00009"
        self.profile.product_data_dict = {"LTE44dg2ERBS00009": ["productNumber=KRD 901 160/11"]}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertTrue(mock_node_id in self.profile.device_type[DEVICE_6488])

    def test_sort_by_product_data__2208_device(self, *_):
        mock_node_id = "LTE44dg2ERBS00003"
        self.profile.product_data_dict = {"LTE44dg2ERBS00003": ["productNumber=KRC 161 711/1"]}
        self.profile.sort_by_product_data(mock_node_id)
        self.assertTrue(mock_node_id in self.profile.device_type[DEVICE_2208])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_fru_count__node_not_in_node_ids_list(self, *_):
        self.profile.node_ids = []
        self.profile.get_fru_count()
        self.assertTrue(len(self.profile.fru_dict) == 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_fru_count___runs_correct(self, *_):
        self.profile.node_ids = ["node1"]
        self.profile.product_data_split = [u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                                           u'ManagedElement=node1,Equipment=1,FieldReplaceableUnit=2'u'productData : '
                                           u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                                           u'ManagedElement=LTE44dg2ERBS00003,Equipment=1,FieldReplaceableUnit=1',
                                           u'productData : {productionDate=20180301, serialNumber=D829144003, '
                                           u'productNumber=KRC 161 746/1, productName=Radio 4408 B48, '
                                           u'productRevision=R1B}'u'',
                                           u'2 instance(s)', u'u']
        self.profile.get_fru_count()
        self.assertTrue(len(self.profile.fru_dict) == 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_fru_count__instances_not_last_value(self, *_):
        mock_node = "node1"
        self.profile.product_data_dict = {mock_node: [
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE44dg2ERBS00003,'
            u'Equipment=1,FieldReplaceableUnit=2',
            u'productData : {productionDate=20180301, serialNumber=D829144004, productNumber=KRC 161 746/1, '
            u'productName=Radio 4408 B48, productRevision=R1B}',
            u'',
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE44dg2ERBS00003,'
            u'Equipment=1,FieldReplaceableUnit=1',
            u'productData : {productionDate=20180301, serialNumber=D829144003, productNumber=KRC 161 746/1, '
            u'productName=Radio 4408 B48, productRevision=R1B}',
            u'', u'2 instance(s)', u'u']}
        self.profile.get_fru_count()
        self.assertTrue(mock_node not in self.profile.fru_dict.keys())

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_fru_count__product_data_dict_empty(self, *_):
        mock_node = "node1"
        self.profile.product_data_dict = {}
        self.profile.get_fru_count()
        self.assertTrue(mock_node not in self.profile.fru_dict.keys())

    @patch('enmutils.lib.exceptions.EnvironError')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_all_product_data__environ_error_raised(self, mock_log, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = ["error 0 instance(s)"]
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_all_product_data(user=mock_user)
        mock_log.assert_any_call("Could not use node, error encountered: [No Product data found: [['error 0 instance("
                                 "s)']]].")

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_required_number_of_devices__correct(self, *_):
        self.profile.DEVICES_REQUIRED = {"2208": 1, "RadioDot": 8, "4408": 1, "6488": 1, "DEVICE_NR_4408": 1, "PassiveDas_4408": 10}
        self.profile.device_type = {DEVICE_2208: ["Node1"], DEVICE_RADIODOT: ["Node2"], DEVICE_4408: [],
                                    DEVICE_6488: ["Node3", "Node4"], DEVICE_PASSIVE_DAS_4408: ["passive_das_4408_1", "passive_das_4408_2"]}
        self.profile.device_count_dict_per_node = {"Node1": 2, "Node2": 1, "Node3": 1, "Node4": 1, "passive_das_4408_1": 2, "passive_das_4408_2": 2}
        self.profile.get_required_number_of_devices()
        self.assertListEqual(self.profile.used_nodes, ["Node2", "Node1", "passive_das_4408_1", "Node3"])

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.update_nodes_used_by_profile")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow"
           ".determine_num_cells_to_add_and_groups_required_for_nr_nodes", return_value=(2, 3))
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow"
           ".determine_num_cells_to_add_and_groups_required", return_value=(3, 2))
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.select_cells")
    def test_generate_cbrs_add_commands__successfully_generates_groups(self, mock_select_cells, *_):
        self.profile.sorted_cbrs_cells = {
            "node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00015,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00015-{0}'.format(i) for i in range(1, 7)],
            "NR20gNodeBRadio00027": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,'
                                     'ManagedElement=NR20gNodeBRadio00027, '
                                     'GNBDUFunction=1,NRSectorCarrier={0}'.format(i) for i in range(1, 7)]}
        mock_select_cells.side_effect = [["cell1", "cell2", "cell3"], ["cell4", "cell5", "cell6"], ["cell7", "cell8"],
                                         ["cell3", "cell4"], ["cell1", "cell2"]]
        self.profile.used_nodes = ["NR20gNodeBRadio00027", "node1"]
        self.profile.generate_cbrs_add_commands()
        self.assertEqual(5, len(self.profile.add_group_commands))

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.update_nodes_used_by_profile")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow"
           ".determine_num_cells_to_add_and_groups_required", return_value=(3, 2))
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.select_cells")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    def test_generate_cbrs_add_commands__number_of_groups_by_cells_doesnt_equal_number_of_cells_available(self,
                                                                                                          mock_log, *_):
        self.profile.sorted_cbrs_cells = {"node1": ["Test"]}
        self.profile.used_nodes = ["node1"]
        self.profile.generate_cbrs_add_commands()
        self.assertEqual(mock_log.call_count, 3)
        self.assertEqual(0, len(self.profile.add_group_commands))

    def test_determine_num_cells_to_add_and_groups_required_for_nr_nodes__2cell_1_group(self):
        mock_node_id = "NR20gNodeBRadio00027"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: [mock_node_id]}
        self.profile.device_count_dict_per_node = {mock_node_id: 2}
        self.profile.cell_size = {2: [mock_node_id], 3: [], 6: [], 12: []}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required_for_nr_nodes(node_id=mock_node_id), (2, 1))

    def test_determine_num_cells_to_add_and_groups_required_for_nr_nodes__2cell_3_group(self):
        mock_node_id = "NR20gNodeBRadio00027"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: [mock_node_id]}
        self.profile.device_count_dict_per_node = {mock_node_id: 3}
        self.profile.cell_size = {2: [], 3: [], 6: [mock_node_id], 12: []}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required_for_nr_nodes(node_id=mock_node_id), (2, 3))

    def test_determine_num_cells_to_add_and_groups_required_for_nr_nodes__2cell_6_group(self):
        mock_node_id = "NR20gNodeBRadio00027"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: [mock_node_id]}
        self.profile.device_count_dict_per_node = {mock_node_id: 6}
        self.profile.cell_size = {2: [], 3: [], 6: [], 12: [mock_node_id]}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required_for_nr_nodes(node_id=mock_node_id), (2, 6))

    def test_determine_num_cells_to_add_and_groups_required__3cells_2_groups(self):
        mock_node_id = "Node1"
        self.profile.device_type = {DEVICE_2208: [mock_node_id], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 2}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (3, 2))

    def test_determine_num_cells_to_add_and_groups_required__4cells_3_groups(self):
        mock_node_id = "LTE26dg2ERBS00015"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [mock_node_id], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 24}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (4, 3))

    def test_determine_num_cells_to_add_and_groups_required__2cells_6_groups(self):
        mock_node_id = "LTE26dg2ERBS00015"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [mock_node_id], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 48}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (2, 6))

    def test_determine_num_cells_to_add_and_groups_required__6cells_1_group(self):
        mock_node_id = "LTE26dg2ERBS00019"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [mock_node_id], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 1}
        self.profile.cell_size = {2: [], 3: [], 6: [mock_node_id], 12: []}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (6, 1))

    def test_determine_num_cells_to_add_and_groups_required__6cells_2_group(self):
        mock_node_id = "LTE26dg2ERBS00019"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [mock_node_id],
                                    DEVICE_6488: [], DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 2}
        self.profile.cell_size = {2: [], 3: [], 6: [], 12: [mock_node_id]}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (6, 2))

    def test_determine_num_cells_to_add_and_groups_required__3cells_1_group(self):
        mock_node_id = "LTE26dg2ERBS00019"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [mock_node_id],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 1}
        self.profile.cell_size = {2: [], 3: [mock_node_id], 6: [], 12: []}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (3, 1))

    def test_determine_num_cells_to_add_and_groups_required__6cell_nodes_with_2_devices(self):
        mock_node_id = "LTE26dg2ERBS00019"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [mock_node_id], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 2}
        self.profile.cell_size = {2: [], 3: [], 6: [mock_node_id], 12: []}
        self.assertTupleEqual(self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id), (0, 0))

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_determine_num_cells_to_add_and_groups_required__else_statement_logged(self, mock_log, *_):
        mock_node_id = "LTE26dg2ERBS00019"
        self.profile.device_type = {DEVICE_2208: [], DEVICE_RADIODOT: [], DEVICE_4408: [], DEVICE_6488: [],
                                    DEVICE_NR_4408: []}
        self.profile.device_count_dict_per_node = {mock_node_id: 1}
        self.profile.cell_size = {2: [], 3: [], 6: [], 12: [mock_node_id]}
        self.profile.determine_num_cells_to_add_and_groups_required(node_id=mock_node_id)
        mock_log.assert_called_with("Unable to get correct groups for LTE26dg2ERBS00019 and 1 devices")

    def test_sort_cells_numerically_successful(self, *_):
        self.profile.sorted_cbrs_cells = {'LTE55dg2ERBS00017': [
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-2',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-3',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-1',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-10'], 'NR20gNodeBRadio00027': [
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=8',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=2',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=7',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=9']}
        mock_sorted_cells = {'LTE55dg2ERBS00017': [
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-1',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-2',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-3',
            'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE55dg2ERBS00017,'
            'ENodeBFunction=1,EUtranCellTDD=LTE55dg2ERBS00017-10'], 'NR20gNodeBRadio00027': [
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=2',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=7',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=8',
                'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,ManagedElement='
                'NR20gNodeBRadio00027,GNBDUFunction=1,NRSectorCarrier=9']}
        self.profile.sort_cells_numerical_order()
        self.assertEqual(self.profile.sorted_cbrs_cells, mock_sorted_cells)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.'
           'update_profile_persistence_nodes_list')
    def test_update_nodes_used_by_profile__no_nodes_to_remove(self, mock_update_nodes_list):
        mock_nodes = [Mock(node_id='node_{0}'.format(_ + 1)) for _ in range(3)]
        self.profile.lite_nodes = mock_nodes
        used_nodes = {'node_1', 'node_2', 'node_3'}
        self.profile.update_nodes_used_by_profile(used_nodes)
        self.assertEqual(mock_update_nodes_list.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.cbrscpi_teardown')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.get_list_of_scripting_service_ips',
           return_value=['some_ip'])
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.remove_groups')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_initial_startup__not_cloud_native_env(self, *_):
        self.profile.initial_startup(Mock())
        self.assertEqual(self.profile.scripting_vms_without_ports, ['some_ip'])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.remove_groups')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.cbrscpi_teardown')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.get_cloud_native_service_ips',
           return_value=(['some_ip:4321'], ['some_ip']))
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.cache.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_initial_startup__on_cloud_native_env(self, *_):
        self.profile.initial_startup(Mock())
        self.assertEqual(self.profile.scripting_vms_without_ports, ['some_ip'])
        self.assertEqual(self.profile.scripting_vms_with_ports, ['some_ip:4321'])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_determine_device_type_for_groups__4408_and_6488_device_types(self, _):
        self.profile.used_nodes = ["Node1", "Node2"]
        self.profile.device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: ["Node1"],
                                    DEVICE_6488: ["Node2"]}
        self.profile.cell_grouping_for_pal_policies = ["Node1: cell1, cell2, cell3", "Node2: cell1, cell2, cell3"]
        self.profile.determine_device_type_for_groups()
        self.assertEqual(self.profile.groups_available_for_pal.get(DEVICE_4408), 1)
        self.assertEqual(self.profile.groups_available_for_pal.get(DEVICE_6488), 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_determine_device_type_for_groups__not_applicable_device_type(self, _):
        self.profile.used_nodes = ["Node2"]
        self.profile.device_type = {DEVICE_RADIODOT: ["Node2"], DEVICE_2208: [], DEVICE_4408: [],
                                    DEVICE_6488: []}
        self.profile.cell_grouping_for_pal_policies = ["Node2: cell1, cell2, cell3"]
        self.profile.determine_device_type_for_groups()
        self.assertEqual(self.profile.groups_available_for_pal.get(DEVICE_RADIODOT), 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_number_of_groups_required_for_device_type__gets_10_percent_of_available_groups(self, _):
        self.profile.groups_available_for_pal = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 100, DEVICE_6488: 81}
        self.profile.get_number_of_groups_required_for_device_type()
        self.assertEqual(self.profile.groups_wanted_for_pal_policies[DEVICE_4408], 10)
        self.assertEqual(self.profile.groups_wanted_for_pal_policies[DEVICE_6488], 8)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_required_amount_of_groups_mixpalgaa__gets_50_percent_of_available_groups(self, _):
        self.profile.groups_wanted_for_pal_policies = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 10,
                                                       DEVICE_6488: 7}
        self.profile.get_required_amount_of_groups_mixpalgaa()
        self.assertEqual(self.profile.groups_wanted_for_mixpalgaa[DEVICE_4408], 5)
        self.assertEqual(self.profile.groups_wanted_for_mixpalgaa[DEVICE_6488], 4)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_groups_for_mixpalgaa__for_4408_and_6488_devices_sucessfully(self, _):
        self.profile.groups_wanted_for_mixpalgaa = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 5, DEVICE_6488: 70}
        self.profile.groups_for_each_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [],
                                                    DEVICE_4408: ["Node2", "Node5"], DEVICE_6488: ["Node5"]}
        self.profile.pal_4408_groups_used = ["Node1:cell1, cell2, cell3", "Node2:cell1, cell2, cell3"]
        self.profile.pal_6488_groups_used = ["Node5"]
        self.profile.get_groups_for_mixpalgaa()
        self.assertTrue("Node1:cell1, cell2, cell3" in self.profile.mixpalgaa_4408_groups_used and
                        "Node5" in self.profile.mixpalgaa_6488_groups_used)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_groups_for_pal_policies(self, _):
        self.profile.groups_for_each_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: ["Node2"],
                                                    DEVICE_6488: ["Node5"]}
        self.profile.groups_wanted_for_pal_policies = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 3,
                                                       DEVICE_6488: 2}
        self.profile.get_groups_for_pal_policies()
        self.assertTrue("Node2" in self.profile.pal_4408_groups_used and
                        "Node5" in self.profile.pal_6488_groups_used)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_get_groups_for_pal_policies_groups_is_more_than_required(self, _):
        self.profile.groups_for_each_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: ["Node2"],
                                                    DEVICE_6488: ["Node5", "Node6", "Node7"]}
        self.profile.groups_wanted_for_pal_policies = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 3,
                                                       DEVICE_6488: 2}
        self.profile.get_groups_for_pal_policies()
        self.assertTrue("Node2" in self.profile.pal_4408_groups_used and
                        "Node5" and "Node6" in self.profile.pal_6488_groups_used)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_set_4408_channel_mask_and_mixpal_channel_mask__success(self, mock_run_remode_cmd, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)],
            "Node2": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1", "Node2"]
        self.profile.pal_4408_groups_used = ["Node1: cell1, cell2, cell3"]
        self.profile.set_4408_channel_mask_and_mixpal_channel_mask(admin_user=Mock())
        self.assertEqual(mock_run_remode_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=EnmApplicationError)
    def test_set_4408_channel_mask_and_mixpal_channel_mask__Environ_error_raised(self, mock_run_cmd, mock_error, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.pal_4408_groups_used = ["Node1: cell1, cell2, cell3"]
        self.profile.set_4408_channel_mask_and_mixpal_channel_mask(admin_user=Mock())
        self.assertRaises(EnmApplicationError, mock_run_cmd)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_set_6488_channel_mask_and_mixpal_channel_mask__success(self, mock_run_remode_cmd, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)],
            "Node2": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1", "Node2"]
        self.profile.pal_6488_groups_used = ["Node1: cell1, cell2, cell3"]
        self.profile.set_6488_channel_mask_and_mixpal_channel_mask(admin_user=Mock())
        self.assertEqual(mock_run_remode_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=EnmApplicationError)
    def test_set_6488_channel_mask_and_mixpal_channel_mask__Environ_error_raised(self, mock_run_cmd, mock_error, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.pal_6488_groups_used = ["Node1: cell1, cell2, cell3"]
        self.profile.set_6488_channel_mask_and_mixpal_channel_mask(admin_user=Mock())
        self.assertRaises(EnmApplicationError, mock_run_cmd)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=EnmApplicationError)
    def test_set_mixpalgaa_policies__Environ_error_raised(self, mock_run_cmd, mock_error, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.lists_mixpalgaa_groups_used = [["Node1: cell1"], ["cell2, cell3"]]
        self.profile.set_mixpalgaa_policies(admin_user=Mock())
        self.assertRaises(EnmApplicationError, mock_run_cmd)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_unset_channel_mask_and_mixpal_channel_mask_on_teardown_policies__success(self, mock_run_remode_cmd, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)],
            "Node2": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1", "Node2"]
        self.profile.lists_pal_groups_used = [["Node1: cell1"], []]
        self.profile.unset_channel_mask_and_mixpal_channel_mask_on_teardown(admin_user=Mock())
        self.assertEqual(mock_run_remode_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=EnmApplicationError)
    def test_unset_channel_mask_and_mixpal_channel_mask_on_teardown__Environ_error_raised(self, mock_run_cmd,
                                                                                          mock_error, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.lists_pal_groups_used = [["Node1: cell1], [Node1: cell3"]]
        self.profile.unset_channel_mask_and_mixpal_channel_mask_on_teardown(admin_user=Mock())
        self.assertRaises(EnmApplicationError, mock_run_cmd)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_unset_mixpalgaa_policies_on_teardown__success(self, mock_run_remode_cmd, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)],
            "Node2": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1", "Node2"]
        self.profile.lists_mixpalgaa_groups_used = [["Node1: cell1"], ["Node1: cell3"]]
        self.profile.unset_mixpalgaa_policies_on_teardown(admin_user=Mock())
        self.assertEqual(mock_run_remode_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_unset_mixpalgaa_policies_on_teardown__fail(self, mock_run_remode_cmd, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.lists_mixpalgaa_groups_used = []
        self.profile.unset_mixpalgaa_policies_on_teardown(admin_user=Mock())
        self.assertEqual(mock_run_remode_cmd.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=EnmApplicationError)
    def test_unset_mixpalgaa_policies_on_teardown__Environ_error_raised(self, mock_run_cmd, mock_error, _):
        self.profile.sorted_cbrs_cells = {
            "Node1": ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE26dg2ERBS00014,'
                      'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-{0}'.format(i) for i in range(1, 7)]}
        self.profile.used_nodes = ["Node1"]
        self.profile.lists_mixpalgaa_groups_used = [["Node1: cell1"], ["Node1: cell3"]]
        self.profile.unset_mixpalgaa_policies_on_teardown(admin_user=Mock())
        self.assertRaises(EnmApplicationError, mock_run_cmd)
        self.assertTrue(mock_error.called)

    @patch(
        'enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.unset_channel_mask_and_mixpal_channel_mask_on_teardown')
    @patch(
        'enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.unset_mixpalgaa_policies_on_teardown')
    def test_teardown_pal_policies__successfully(self, mock_unset_mixpalgaa_policies_on_teardown, *_):
        self.profile.teardown_pal_policies(user=Mock())
        self.assertTrue(mock_unset_mixpalgaa_policies_on_teardown.assert_called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_required_number_of_devices")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_device_type")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_rf_branch")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_fru_count")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_all_product_data")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_by_cell_size")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nr_cbrs_cells_via_cmedit")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_cbrs_cells_via_cmedit")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.execute_cpi_flow")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.generate_cbrs_add_commands")
    @ParameterizedTestCase.parameterize(
        'is_on_cenm',
        [
            ([True, ]),
            ([False, ])
        ]
    )
    def test_sort_select_cells_and_build_add_commands__no_errors(self, is_on_cenm, mock_generate_cbrs_add_group_commands, *_):
        mock_user = Mock()
        self.profile.is_on_cenm = is_on_cenm
        self.profile.sort_select_cells_and_build_add_commands(user=mock_user)
        self.assertTrue(mock_generate_cbrs_add_group_commands.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_maintenance_user_mo_on_node')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.map_nodes_to_standalone_domain_coordinator')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_standalone_domain_coordinator')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.cert_and_trust_distribution_on_nodes')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_pal_policies_for_cbrs_groups')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.execute_cbrs_add_commands')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.build_summary')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.state', new_callable=PropertyMock,
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nr_cbrs_cells_via_cmedit")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_cbrs_cells_via_cmedit')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.initial_startup')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_users')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_select_cells_and_build_add_commands')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    def test_execute_flow__successful_on_pENM(self, mock_add_error, *_):
        self.profile.is_on_cenm = False
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_maintenance_user_mo_on_node')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.map_nodes_to_standalone_domain_coordinator')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_standalone_domain_coordinator')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.cert_and_trust_distribution_on_nodes')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_pal_policies_for_cbrs_groups')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.execute_cbrs_add_commands')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.build_summary')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.state', new_callable=PropertyMock,
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nr_cbrs_cells_via_cmedit")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_cbrs_cells_via_cmedit')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.initial_startup')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_users')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.sort_select_cells_and_build_add_commands')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    def test_execute_flow__successful_on_cENM(self, mock_add_error, *_):
        self.profile.is_on_cenm = True
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_build_summary__successful(self, mock_log):
        self.profile.build_summary()
        self.assertEqual(mock_log.call_count, 12)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_4408_channel_mask_and_mixpal_channel_mask')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_6488_channel_mask_and_mixpal_channel_mask')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_groups_for_mixpalgaa')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_groups_for_pal_policies')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_required_amount_of_groups_mixpalgaa')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_number_of_groups_required_for_device_type')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.determine_device_type_for_groups')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.set_mixpalgaa_policies')
    def test_set_pal_policies_for_cbrs_groups__successful(self, *_):
        mock_user = Mock()
        self.profile.set_pal_policies_for_cbrs_groups(mock_user)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.update_nodes_used_by_profile')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.initial_startup',
           side_effect=EnvironError('No CBRS cells on deployment'))
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_users')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    def test_execute_flow__initial_startup_fails(self, mock_add_error, mock_debug, *_):
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        mock_debug.assert_called_with("Due to failure the profile will now go to completed.")

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.update_nodes_used_by_profile')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.is_nr_cbrs_cells_required_for_iteration")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_cbrs_cells_via_cmedit',
           side_effect=EnvironError('Could not find any cbrs enabled cells on deployment'))
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.initial_startup')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_users')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    def test_execute_flow__get_cbrs_cells_via_cmedit_fails(self, mock_add_error, mock_debug, *_):
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)
        mock_debug.assert_called_with("Profile could not get cbrs cells. Profile will now go to completed.")

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_cbrs_cells_via_cmedit__available_cells(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = SAMPLE_CMEDIT_RESPONSE
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(len(self.profile.cbrs_cell_fdns), 12)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_cbrs_cells_via_cmedit__no_cbrs_cells_available_on_deployment(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = ['0 instance(s)']
        mock_user.enm_execute.return_value = mock_response
        with self.assertRaises(EnvironError) as e:
            self.profile.get_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(str(e.exception), 'Could not find any cbrs enabled cells on deployment')

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_cbrs_cells_via_cmedit__cmedit_fails(self, *_):
        mock_user = Mock()
        mock_user.enm_execute.side_effect = NoOuputFromScriptEngineResponseError('No output', Mock())
        with self.assertRaises(NoOuputFromScriptEngineResponseError) as e:
            self.profile.get_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(str(e.exception), 'No output')

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nr_cbrs_cells_via_cmedit")
    def test_is_nr_cbrs_cells_required_for_iteration__nr_device_greater_than_zero(self, mock_get_nr_cbrs_cells_via_cmedit, _):
        self.profile.DEVICES_REQUIRED = {"2208": 1, "RadioDot": 8, "4408": 1, "6488": 1, "DEVICE_NR_4408": 1}
        self.profile.is_nr_cbrs_cells_required_for_iteration(user=Mock())
        self.assertTrue(mock_get_nr_cbrs_cells_via_cmedit.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.get_nr_cbrs_cells_via_cmedit")
    def test_is_nr_cbrs_cells_required_for_iteration__nr_device_equal_to_zero(self, mock_get_nr_cbrs_cells_via_cmedit, _):
        self.profile.DEVICES_REQUIRED = {"2208": 1, "RadioDot": 8, "4408": 1, "6488": 1, "DEVICE_NR_4408": 0}
        self.profile.is_nr_cbrs_cells_required_for_iteration(user=Mock())
        self.assertFalse(mock_get_nr_cbrs_cells_via_cmedit.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_nr_cbrs_cells_via_cmedit__available_cells(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = SAMPLE_CMEDIT_RESPONSE2
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_nr_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(len(self.profile.cbrs_cell_fdns), 12)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_nr_cbrs_cells_via_cmedit__no_cbrs_cells_available_on_deployment(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = ['0 instance(s)']
        mock_user.enm_execute.return_value = mock_response
        self.profile.get_nr_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(mock_user.enm_execute.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_get_nr_cbrs_cells_via_cmedit__cmedit_fails(self, *_):
        mock_user = Mock()
        mock_user.enm_execute.side_effect = NoOuputFromScriptEngineResponseError('No output', Mock())
        with self.assertRaises(NoOuputFromScriptEngineResponseError) as e:
            self.profile.get_nr_cbrs_cells_via_cmedit(mock_user)
        self.assertEqual(str(e.exception), 'No output')

    def test_select_cells__correct(self):
        mock_fdn_list = ['FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                         'ManagedElement=LTE26dg2ERBS00014 '
                         'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-1',
                         'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                         'ManagedElement=LTE26dg2ERBS00015, '
                         'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-2',
                         'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
                         'ManagedElement=LTE26dg2ERBS00016, '
                         'ENodeBFunction=1,EUtranCellTDD=LTE26dg2ERBS00014-3',
                         'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,'
                         'ManagedElement=NR20gNodeBRadio00027, '
                         'GNBDUFunction=1,NRSectorCarrier=8',
                         'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,'
                         'ManagedElement=NR20gNodeBRadio00027, '
                         'GNBDUFunction=1,NRSectorCarrier=9',
                         'FDN : SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR20gNodeBRadio00027,'
                         'ManagedElement=NR20gNodeBRadio00027, '
                         'GNBDUFunction=1,NRSectorCarrier=10']
        self.profile.select_cells(0, 7, mock_fdn_list)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.Command')
    def test_remove_groups__all_groups_on_penm(self, mock_command, *_):
        self.profile.SA_DC_CLUSTER_IP_LIST = ''
        self.profile.remove_groups(Mock(username='admin', password='admin123'), ['some_ip'])
        mock_command.assert_called_with('cbrs remove --deregister all --quiet')

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.Command')
    def test_remove_groups__all_groups_on_cenm(self, mock_command, *_):
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.remove_groups(Mock(username='admin', password='admin123'), ['some_ip'])
        mock_command.assert_called_with('cbrs remove --deregister all --cbrsfunction {0} --quiet'.format(self.profile.SA_DC_CLUSTER_IP_LIST))

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_cmd_on_vm',
           side_effect=[RuntimeError('Unable to obtain a connection from the connection pool'), Mock()])
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.Command')
    def test_remove_groups__retry_on_run_time_error(self, mock_command, *_):
        self.profile.SA_DC_CLUSTER_IP_LIST = ''
        self.profile.remove_groups(Mock(username='admin', password='admin123'), ['some_ip'])
        mock_command.assert_called_with('cbrs remove --deregister all --quiet')
        self.assertEqual(mock_command.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_sec_admin_command_on_nodes')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.create_xml_file')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_cert_and_trust_distribution_on_nodes(self, mock_log, *_):
        self.profile.cert_and_trust_distribution_on_nodes(user=Mock())
        self.assertEqual(mock_log.call_count, 2)

    @patch("__builtin__.open")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    def test_create_xml_file__successful(self, mock_log, *_):
        self.profile.used_nodes = ["LTE_01", "NR36"]
        self.profile.create_xml_file()
        self.assertTrue(mock_log.called)

    @patch("__builtin__.open")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    def test_create_xml_file__batch_node_count_greater_than_end_range(self, mock_log, *_):
        self.profile.used_nodes = ["LTE_01", "NR36"]
        self.profile.batch_node_count = 1600
        self.profile.create_xml_file()
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    def test_run_sec_admin_command_on_nodes__successful(self, mock_log, _):
        self.profile.trust_cert_xml_list = ['file1']
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.side_effect = [["Successfully started a job to issue certificates for nodes. Perform 'secadm job get -j 12345' to get progress info."],
                                                ['IN PROGRESS'], ["COMPLETED"]]
        mock_user.enm_execute.return_value = mock_response
        self.profile.run_sec_admin_command_on_nodes(mock_user)
        self.assertEqual(mock_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug")
    def test_run_sec_admin_command_on_nodes__no_result_in_cert_poll_num(self, mock_log, _):
        self.profile.trust_cert_xml_list = ['file1']

        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.side_effect = [["Successfully started a job to issue certificates for nodes. Perform 'secadm job get -j 12345' to get progress info."],
                                                ['1'], ["2"], ['3'], ["4"], ['5'], ["6"], ['7'], ["8"], ['9'], ["10"],
                                                ['11'], ["12"], ['13'], ["14"], ['15'], ["16"]]
        mock_user.enm_execute.return_value = mock_response
        self.profile.run_sec_admin_command_on_nodes(mock_user)
        self.assertTrue(mock_log.called_with('Failed_trust_cert_status on: file1'))

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_local_cmd')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_remove_trust_cert_xml_on_teardown__successful(self, mock_log, _):
        self.profile.trust_cert_xml_list = ['file1', 'file2']
        self.profile.remove_trust_cert_xml_on_teardown()
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_create_maintenance_user_mo_on_node__successful_for_LTE_and_NR(self, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.used_nodes = ["LTE23dg200006", "NR26gNodeBRadio00001"]
        self.profile.create_maintenance_user_mo_on_node(mock_user)
        self.assertEqual(mock_user.enm_execute.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_create_maintenance_user_mo_on_node__nothing_set_for_sa_dc_cluster_list(self, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = ""
        self.profile.used_nodes = ["LTE23dg200006", "NR26gNodeBRadio00001"]
        self.profile.create_maintenance_user_mo_on_node(mock_user)
        self.assertEqual(mock_user.enm_execute.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_create_maintenance_user_mo_on_node__enm_application_error_raised(self, mock_log):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.used_nodes = ["LTE23dg200006", "NR26gNodeBRadio00001"]
        mock_user.enm_execute.side_effect = EnmApplicationError
        self.profile.create_maintenance_user_mo_on_node(mock_user)
        self.assertEqual(mock_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd")
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_map_nodes_to_standalone_domain_coordinator__nodes_mapped_successfully(self, *_):
        mock_user = Mock()
        self.profile.used_nodes = ["LTE_10", "LTE_26", "NR_20gNodeBRadio"]
        self.profile.map_nodes_to_standalone_domain_coordinator(mock_user)
        self.assertEqual(self.profile.mapped_paths_for_nodes, ['SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_10',
                                                               'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_26',
                                                               'SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR_20gNodeBRadio,ManagedElement=NR_20gNodeBRadio'])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd")
    def test_map_nodes_to_standalone_domain_coordinator__sa_dc_ip_not_set(self, mock_run_remote_cbrs_add, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = ""
        self.profile.used_nodes = ["LTE_10", "LTE_26"]
        self.profile.map_nodes_to_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_cbrs_add.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd",
           side_effect=[EnmApplicationError])
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    def test_map_nodes_to_standalone_domain_coordinator__run_remote_cmd_raises_error(self, *_):
        mock_user = Mock()
        self.profile.used_nodes = ["LTE_10", "LTE_26"]
        self.profile.map_nodes_to_standalone_domain_coordinator(mock_user)
        self.assertEqual(self.profile.mapped_paths_for_nodes, [])

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_set_standalone_domain_coordinator__set_sas_url_and_sa_dc(self, mock_run_remote_add, mock_log):
        mock_user = Mock()
        self.profile.set_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_add.call_count, 1)
        self.assertEqual(mock_log.call_count, 4)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_set_standalone_domain_coordinator__sas_url_not_set(self, mock_run_remote_add, _):
        mock_user = Mock()
        self.profile.SAS_URL = ""
        self.profile.set_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_add.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=[EnmApplicationError])
    def test_set_standalone_domain_coordinator__first_run_remote_command_raises_error(self, mock_run_remote_add, mock_add_error, _):
        mock_user = Mock()
        self.profile.set_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_add.call_count, 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_set_standalone_domain_coordinator__no_sa_dc_ips(self, mock_run_remote_add, mock_log):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = ""
        self.profile.SAS_URL = generate_configurable_ip()
        self.profile.set_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_add.call_count, 1)
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=[EnmApplicationError])
    def test_set_standalone_domain_coordinator__second_run_remote_command_raises_error(self, mock_run_remote_add, mock_add_error, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = ""
        self.profile.SAS_URL = generate_configurable_ip()
        self.profile.set_standalone_domain_coordinator(mock_user)
        self.assertEqual(mock_run_remote_add.call_count, 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_cleanup_mapped_nodes_on_teardown__successful(self, mock_run_remote, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.mapped_paths_for_nodes = [
            'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_10',
            'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_26']
        self.profile.cleanup_mapped_nodes_on_teardown(mock_user)
        self.assertEqual(mock_run_remote.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_cleanup_mapped_nodes_on_teardown__ip_list_not_set(self, mock_run_remote, _):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = ""
        self.profile.cleanup_mapped_nodes_on_teardown(mock_user)
        self.assertEqual(mock_run_remote.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd',
           side_effect=[EnmApplicationError])
    def test_cleanup_mapped_nodes_on_teardown__error_raised(self, mock_run_remote, mock_add_error, *_):
        mock_user = Mock()
        self.profile.SA_DC_CLUSTER_IP_LIST = generate_configurable_ip()
        self.profile.mapped_paths_for_nodes = [
            'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_10',
            'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE_26']
        self.profile.cleanup_mapped_nodes_on_teardown(mock_user)
        self.assertEqual(mock_run_remote.call_count, 2)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.run_remote_cbrs_add_cmd')
    def test_execute_cbrs_add_commands__adds_error(self, mock_run_cmd, mock_error):
        self.profile.scripting_vms = ["vm", "vm1"]
        mock_user = Mock()
        self.profile.add_group_commands = ["cmd"]
        mock_run_cmd.side_effect = EnmApplicationError
        self.profile.execute_cbrs_add_commands(mock_user)
        self.assertEqual(1, mock_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep')
    def test_run_remote_cbrs_add_cmd__is_successful(self, mock_sleep, *_):
        self.profile.scripting_vms_without_ports = ["vm", "vm1"]
        self.profile.add_group_commands = ["cmd"]
        self.profile.run_remote_cbrs_add_cmd(Mock(), Mock(), Mock())
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.CbrsSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow.run_remote_cmd')
    def test_run_remote_cbrs_add_cmd__raises_error(self, mock_run_cmd, *_):
        mock_run_cmd.return_value.ok = False
        mock_run_cmd.return_value.rc = 1
        self.profile.scripting_vms_without_ports = ["vm", "vm1"]
        self.profile.add_group_commands = ["cmd"]
        with self.assertRaisesRegexp(EnmApplicationError,
                                     "Cbrs add command returned status code 1 and no output. Check logs for more details"):
            self.profile.run_remote_cbrs_add_cmd(Mock(), Mock(), Mock())


if __name__ == '__main__':
    unittest2.main(verbosity=2)
