import unittest2

from testslib import unit_test_utils
from mock import patch, Mock
from enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi import CbrsCpi, rm_cpi_file_from_scripting_vm, cbrs_cpi_cleanup_import, \
    cbrscpi_teardown, cleanup_wlvm_cpi_file, generic_pexpect_for_cpi_signing
from enmutils.lib.exceptions import EnvironError

CBRS_DEFAULT_DIR = "/home/enmutils/cbrs/"
PATH_CPI_CSV = CBRS_DEFAULT_DIR + "CpiSortedData.csv"
PRIVATE_KEY = "CPI_private_key.pem"
PATH_PRIVATE_KEY = CBRS_DEFAULT_DIR + PRIVATE_KEY
CBRS_JAR_DIR = "/home/enmutils/cbrs/opt/ericsson/ERICcpisigningtool_CXP9035592/"
JAR_FILE_EXPECTED = "cpi-signing-tool-2.18.12.jar"

DEVICE_RADIODOT = "RadioDot"
DEVICE_2208 = "2208"
DEVICE_4408 = "4408"
DEVICE_6488 = "6488"
DEVICE_NR_4408 = "NR_4408"
DEVICE_PASSIVE_DAS_4408 = "PassiveDas_4408"
DEVICE_6488_NEW = "6488_NEW"
DEVICE_6488_OLD = "6488_OLD"
SAMPLE_CMEDIT_RESPONSE = [" FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE32dg2ERBS00022"
                          ",ENodeBFunction=1,SectorCarrier=8 maxAllowedEirpPsd : -1 FDN : SubNetwork=Europe,"
                          "SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE32dg2ERBS00022,ENodeBFunction=1,"
                          "SectorCarrier=7 maxAllowedEirpPsd : -1 "]


class CBRSCpiUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.profile = CbrsCpi()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.import_signed_csv_file_to_db")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.put_signed_csv_file_to_scripting_cluster")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.sign_cpi_csv_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.creating_unsigned_csv_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.build_lines_for_cpi_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.get_node_serial_numbers")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.get_node_location")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.replace_product_number_with_fcc_ids")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.check_private_key_exists")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.check_jar_file_exists")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.random.choice")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.cmedit_check_max_allowed_eirp_for_all_nodes")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cbrscpi_teardown")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.set_cpi_registration_pib_values")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_create_and_sign_cpi_data__successful_on_penm(self, mock_log, mock_cpi_pib_registration, *_):
        mock_user = Mock()
        self.profile.execute_cpi_flow(Mock(), Mock(), Mock(), Mock(), Mock(), mock_user)
        mock_log.assert_called_with("Starting the Creation of CPI signed Data")
        self.assertTrue(mock_cpi_pib_registration.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.import_signed_csv_file_to_db")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.put_signed_csv_file_to_scripting_cluster")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.sign_cpi_csv_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.creating_unsigned_csv_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.build_lines_for_cpi_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.get_node_serial_numbers")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.get_node_location")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.replace_product_number_with_fcc_ids")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.check_private_key_exists")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.check_jar_file_exists")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.random.choice")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.cmedit_check_max_allowed_eirp_for_all_nodes")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cbrscpi_teardown")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.set_cpi_registration_pib_values")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_create_and_sign_cpi_data__successful_on_cenm(self, mock_log, mock_cpi_pib_registration, *_):
        mock_user = Mock()
        self.profile.execute_cpi_flow(Mock(), Mock(), Mock(), Mock(), Mock(), mock_user)
        self.assertEqual(mock_log.call_count, 2)
        self.assertFalse(mock_cpi_pib_registration.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist")
    def test_check_jar_file_exists__jar_file_present(self, mock_does_file_exist, mock_log):
        self.profile.check_jar_file_exists()
        mock_does_file_exist.assert_called_with(CBRS_JAR_DIR + JAR_FILE_EXPECTED)
        mock_log.assert_called_with("Jar is present on the deployment")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_check_jar_file_exists__download_successful_rpm_extraction_failed(self, *_):
        with self.assertRaises(EnvironError) as e:
            self.profile.check_jar_file_exists()
            self.assertEqual(str(e.exception), "Jar failed to download and extract")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist", side_effect=[False, True])
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_check_jar_file_exists__download_successful_rpm_extraction_successful(self, mock_log, *_):
        self.profile.check_jar_file_exists()
        mock_log.assert_called_with("Jar downloaded and rpm extracted correctly")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_check_private_key_exists__key_present_on_deployment(self, mock_log, _):
        self.profile.check_private_key_exists()
        mock_log.assert_called_with("Private key is present for cbrs cpi functionality")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.download")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_check_private_key_exists__key_not_present_on_deployment(self, mock_log, *_):
        self.profile.check_private_key_exists()
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.filesystem.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.download", side_effect=EnvironError)
    def test_check_private_key_exists__error_downloading_key(self, *_):
        with self.assertRaises(EnvironError) as e:
            self.profile.check_private_key_exists()
        self.assertEqual(str(e.exception), "Unable to download file: .")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_replace_product_number_with_fcc_ids__successful(self, _):
        product_data_dict = {"node_6488": "KRD 901 160/11", "node_4408": "KRC 161 746/1", "NR20gNodeBRadio00027": "KRC 161 746/1", "node_2208": "KRC 161 711/1",
                             "Node_radiodot": "KRY 901 385/1", "Test_node": "wrong_Product_id"}
        self.profile.replace_product_number_with_fcc_ids(product_data_dict)
        self.assertTrue(len(self.profile.fcc_id_dict.keys()) == 5)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.add_decimals_to_long_lat")
    def test_get_node_location__successful(self, mock_add_decimals, _):
        product_data_dict = {"node_6488": ["latitude=1000001, longitude=-100}"],
                             "node_4408": ["latitude=-1000, longitude=100020}"]}
        mock_used_nodes = ["node_6488", "node_4408"]
        self.profile.get_node_location(product_data_dict, mock_used_nodes)
        self.assertTrue(mock_add_decimals.called)

    def test_add_decimals_to_long_lat__negative_values(self):
        mock_lat = "-1000001"
        mock_long = "-100"
        mock_node_id = "node_4408"
        self.profile.add_decimals_to_long_lat(mock_lat, mock_long, mock_node_id)
        self.assertDictEqual(self.profile.long_lat_dict, {'node_4408': '-10.00001, -10.0'})

    def test_add_decimals_to_long_lat__postive_values(self):
        mock_lat = "1000001"
        mock_long = "100"
        mock_node_id = "node_4408"
        self.profile.add_decimals_to_long_lat(mock_lat, mock_long, mock_node_id)
        self.assertDictEqual(self.profile.long_lat_dict, {'node_4408': '10.00001, 10.0'})

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_get_node_serial_numbers__successful(self, _):
        product_data_dict = {"node_6488": ["serialNumber=D19058373,"]}
        used_nodes = ["node_6488", "node_4408"]
        self.profile.get_node_serial_numbers(product_data_dict, used_nodes)
        self.assertTrue("node_6488" in self.profile.serial_number_dict.keys())

    def test_build_lines_for_cpi_file__successful(self, *_):
        self.profile.fcc_id_dict = {"TestNode1": "TA8BKRD901160", "TestNode2": "TA8AKRC161746-1",
                                    "TestNode3": "TA8BKRD901160", "TestNode4": "TA8AKRY901385-1",
                                    "TestNode5": "Testing", "TestNodeNew": "TA8BKRD901160",
                                    "TestNodeOld": "TA8BKRD901160", "NR20gNodeBRadio00027": "TA8AKRC161746-1"}
        self.profile.serial_number_dict = {"TestNode1": ["d19020"], "TestNode2": ["b1234"], "TestNode3": ["c5678"],
                                           "TestNode4": ["D160740"], "TestNodeNew": ["New6488"],
                                           "TestNodeOld": ["Old6488"], "NR20gNodeBRadio00027": ["D160840"]}
        self.profile.long_lat_dict = {"TestNode1": "10.002 , -18.0", "TestNode2": "-15.71 , 12.3",
                                      "TestNode3": "36.0, -90.0", "TestNode4": "16.0, 15.0", "TestNodeOld": "12.5, -19.0",
                                      "TestNodeNew": "-67.4, -15.0", "NR20gNodeBRadio00027": "15.4, -4.002"}
        mock_used_nodes = ["TestNode1", "TestNode2", "TestNode3", "TestNode4", "TestNode5",
                           "TestNodeOld", "TestNodeNew", "NR20gNodeBRadio00027"]
        mock_device_type = {DEVICE_RADIODOT: ["TestNode4"], DEVICE_2208: ["TestNode1"], DEVICE_4408: ["TestNode2"],
                            DEVICE_6488: ["TestNodeOld", "TestNodeNew"], DEVICE_NR_4408: ["NR20gNodeBRadio00027"],
                            DEVICE_PASSIVE_DAS_4408: []}
        mock_rf_branch_dict = {"LTE35dg2ERBS0009": 4}
        self.profile.old_new_6488_dict = {DEVICE_6488_OLD: ["TestNodeOld"], DEVICE_6488_NEW: ["TestNodeNew"]}
        self.profile.build_lines_for_cpi_file(mock_used_nodes, mock_device_type, mock_rf_branch_dict)
        self.assertListEqual(self.profile.cpi_data_list,
                             [['TA8BKRD901160,d19020,10.002,-18.0,0,AGL,FALSE,0,0,0,0,12,47,0,Ericsson_Antenna'],
                              ['TA8AKRC161746-1,b1234,-15.71,12.3,0,AGL,FALSE,0,0,0,0,12.5,47,0,Ericsson_Antenna'],
                              ['TA8AKRY901385-1,D160740,16.0,15.0,0,AGL,TRUE,0,0,0,0,3,25,0,Ericsson_Antenna'],
                              ['TA8BKRD901160,Old6488,12.5,-19.0,0,AGL,FALSE,0,0,0,0,17,44.5,0,Ericsson_Antenna'],
                              ['TA8BKRD901160,New6488,-67.4,-15.0,0,AGL,FALSE,0,0,0,0,11,44.5,0,Ericsson_Antenna'],
                              ['TA8AKRC161746-1,D160840,15.4,-4.002,0,AGL,FALSE,0,0,0,0,12.5,47,0,Ericsson_Antenna']])

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.CbrsCpi.determine_old_or_new_6488")
    def test_cmedit_check_max_allowed_eirp_for_all_nodes__successful_execution(self, mock_determine_old_new_6488, _):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = SAMPLE_CMEDIT_RESPONSE
        mock_user.enm_execute.return_value = mock_response
        self.profile.cmedit_check_max_allowed_eirp_for_all_nodes(mock_user, Mock())
        self.assertEqual(mock_determine_old_new_6488.called, 1)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep", return_value=0)
    def test_cmedit_check_max_allowed_eirp_for_all_nodes__raises_error(self, *_):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = ['0 instance(s)']
        mock_user.enm_execute.return_value = mock_response
        with self.assertRaises(EnvironError) as e:
            self.profile.cmedit_check_max_allowed_eirp_for_all_nodes(mock_user, Mock())
        self.assertEqual(str(e.exception), 'Could not find any Eirp data to confirm 6488 new or old')

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_determine_old_or_new_6488__succesful(self, _):
        mock_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: [], DEVICE_6488: ["New6488", "Old6488", "TestNodeNewShouldntBeHere"]}
        self.profile.old_new_6488_dict = {DEVICE_6488_OLD: [], DEVICE_6488_NEW: ["TestNodeNewShouldntBeHere"]}
        mock_old_new_6488_dict = {DEVICE_6488_NEW: ["TestNodeNewShouldntBeHere", "New6488"], DEVICE_6488_OLD: ["Old6488"]}
        mock_node_ids = ["New6488"]
        self.profile.determine_old_or_new_6488(mock_device_type, mock_node_ids)
        self.assertDictEqual(self.profile.old_new_6488_dict, mock_old_new_6488_dict)

    def test_serial_number_iteration__successful_for_4_rf_branch(self):
        mock_rf_branch_dict = {"LTE35dg2ERBS0009": 4}
        mock_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: [], DEVICE_6488: [], DEVICE_PASSIVE_DAS_4408: ["LTE35dg2ERBS0009"]}
        self.profile.serial_number_dict = {"LTE35dg2ERBS0009": ["D82918523002"], "LTE35dg2ERBS007": ["MOCK"]}
        self.profile.fcc_id_dict = {"LTE35dg2ERBS0009": "TA8AKRC161746-1"}
        self.profile.long_lat_dict = {"LTE35dg2ERBS0009": "17.23 ,38.5"}
        return_list = self.profile.iterate_serial_numbers("LTE35dg2ERBS0009", mock_device_type, mock_rf_branch_dict)
        self.assertListEqual(return_list, ['TA8AKRC161746-1,D82918523002:p1p2p3p4:1,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2p3p4:2,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2p3p4:3,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2p3p4:4,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2p3p4:5,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2p3p4:6,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2p3p4:7,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2p3p4:8,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2p3p4:9,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2p3p4:10,17.23 ,38.5'])

    def test_serial_number_iteration__successful(self):
        mock_rf_branch_dict = {"LTE35dg2ERBS0009": 4}
        mock_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: ["LTE35dg2ERBS0009"], DEVICE_4408: [], DEVICE_6488: [], DEVICE_PASSIVE_DAS_4408: []}
        self.profile.serial_number_dict = {"LTE35dg2ERBS0009": ["D82918523001", "D82918523002"], "LTE35dg2ERBS007": ["MOCK"]}
        self.profile.fcc_id_dict = {"LTE35dg2ERBS0009": "TA8BKRD901160"}
        self.profile.long_lat_dict = {"LTE35dg2ERBS0009": "10.002 ,-18.0"}
        return_list = self.profile.iterate_serial_numbers("LTE35dg2ERBS0009", mock_device_type, mock_rf_branch_dict)
        self.assertListEqual(return_list, ['TA8BKRD901160,D82918523001,10.002 ,-18.0', 'TA8BKRD901160,D82918523002,10.002 ,-18.0'])

    def test_serial_number_iteration__successful_for_2_rf_branch(self):
        mock_rf_branch_dict = {"LTE35dg2ERBS0009": 2}
        mock_device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: [], DEVICE_6488: [], DEVICE_PASSIVE_DAS_4408: ["LTE35dg2ERBS0009"]}
        self.profile.serial_number_dict = {"LTE35dg2ERBS0009": ["D82918523002"], "LTE35dg2ERBS007": ["MOCK"]}
        self.profile.fcc_id_dict = {"LTE35dg2ERBS0009": "TA8AKRC161746-1"}
        self.profile.long_lat_dict = {"LTE35dg2ERBS0009": "17.23 ,38.5"}
        return_list = self.profile.iterate_serial_numbers("LTE35dg2ERBS0009", mock_device_type, mock_rf_branch_dict)
        self.assertListEqual(return_list, ['TA8AKRC161746-1,D82918523002:p1p2:1,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2:2,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2:3,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2:4,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2:5,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2:6,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2:7,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2:8,17.23 ,38.5',
                                           'TA8AKRC161746-1,D82918523002:p1p2:9,17.23 ,38.5', 'TA8AKRC161746-1,D82918523002:p1p2:10,17.23 ,38.5'])

    @patch("__builtin__.open")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_creating_unsigned_csv_file__successful(self, mock_log, *_):
        self.profile.cpi_data_list = [['TA8BKRD901160,d19020,100.02,-180,0,AGL,FALSE,0,0,0,0,12,47,0,Ericsson_Antenna'],
                                      ['TA8AKRC161746-1,b1234,-157.1,123,0,AGL,FALSE,0,0,0,0,12.5,47,0,Ericsson_Antenna'],
                                      ['TA8BKRD901160,c5678,360,-90,0,AGL,FALSE,0,0,0,0,11,44.5,0,Ericsson_Antenna'],
                                      ['TA8AKRY901385-1,D160740,160,150,0,AGL,TRUE,0,0,0,0,3,25,0,Ericsson_Antenna']]
        self.profile.creating_unsigned_csv_file()
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.get_ms_host", return_value="LMS")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.generic_pexpect_for_cpi_signing")
    def test_sign_cpi_csv_file__successful_physical_deployment(self, mock_generic_pexpect_for_cpi_signing, mock_log, *_):
        self.profile.sign_cpi_csv_file()
        self.assertTrue(mock_generic_pexpect_for_cpi_signing.called)
        mock_log.assert_called_with("Finished signing CBRS data")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.get_ms_host", return_value="localhost")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.generic_pexpect_for_cpi_signing")
    def test_sign_cpi_csv_file__successful_cENM_deployment(self, mock_generic_pexpect_for_cpi_signing, mock_log, *_):
        self.profile.sign_cpi_csv_file()
        self.assertTrue(mock_generic_pexpect_for_cpi_signing.called)
        mock_log.assert_called_with("Finished signing CBRS data")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.get_ms_host", return_value="localhost")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.generic_pexpect_for_cpi_signing")
    def test_sign_cpi_csv_file__successful_vio_deployment(self, mock_generic_pexpect_for_cpi_signing, mock_log, *_):
        self.profile.sign_cpi_csv_file()
        self.assertTrue(mock_generic_pexpect_for_cpi_signing.called)
        mock_log.assert_called_with("Finished signing CBRS data")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_generic_pexpect_for_cpi_signing__successful(self, mock_pexpect, mock_log, _):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 0
        mock_spawn.expect.side_effect = [0, 0, 0, 0, 0, 0, 0, 0]
        generic_pexpect_for_cpi_signing(mock_spawn)
        mock_log.assert_called_with("Correctly signed data")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_generic_pexpect_for_cpi_signing__wrong_return_code_first_if(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 1
        with self.assertRaises(EnvironError):
            generic_pexpect_for_cpi_signing(mock_spawn)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.upload")
    def test_put_signed_csv_file_to_scripting_cluster__upload_successful(self, mock_upload, _):
        self.profile.put_signed_csv_file_to_scripting_cluster(scripting_vm="Testing_ip")
        self.assertTrue(mock_upload.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.upload", side_effect=IOError)
    def test_put_signed_csv_file_to_scripting_cluster__upload_failed_runtime_error(self, *_):
        with self.assertRaises(RuntimeError) as e:
            self.profile.put_signed_csv_file_to_scripting_cluster("mock_ip -p 4312")
            self.assertEqual(str(e.exception), "Unable to download file: .")

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.update_pib_value")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_set_cpi_registration_pib_values__successful_for_all(self, mock_log, _):
        self.profile.set_cpi_registration_pib_values()
        self.assertEqual(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.update_pib_value", side_effect=[EnvironError])
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    def test_set_cpi_registration_pib_values__exception_raised(self, mock_log, _):
        self.profile.set_cpi_registration_pib_values()
        self.assertEqual(mock_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.run_local_cmd")
    def test_cleanup_wlvm_cpi_file__successful(self, mock_run_local_cmd, _):
        cleanup_wlvm_cpi_file()
        self.assertEqual(mock_run_local_cmd.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.random")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cleanup_wlvm_cpi_file")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.cbrs_cpi_cleanup_import")
    def test_cbrscpi_teardown__all_functions_called(self, mock_cleanup_import, mock_clean_wlvm_cpi_file, *_):
        cbrscpi_teardown(Mock())
        self.assertTrue(mock_clean_wlvm_cpi_file.called, mock_cleanup_import.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_import_signed_csv_file_to_db__successful(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 0
        self.profile.import_signed_csv_file_to_db(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_import_signed_csv_file_to_db__wrong_return_code_first_if(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 1
        with self.assertRaises(EnvironError):
            self.profile.import_signed_csv_file_to_db(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_import_signed_csv_file_to_db__wrong_return_code_second_if(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.sendline.return_value = 0
        mock_spawn.expect.side_effect = [0, 1]
        with self.assertRaises(EnvironError):
            self.profile.import_signed_csv_file_to_db(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_import_signed_csv_file_to_db__wrong_return_code_third_if(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.sendline.return_value = 0
        mock_spawn.expect.side_effect = [0, 0, 1]
        with self.assertRaises(EnvironError):
            self.profile.import_signed_csv_file_to_db(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_import_signed_csv_file_to_db__wrong_return_code_fourth_if(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.sendline.return_value = 0
        mock_spawn.expect.side_effect = [0, 0, 0, 1]
        with self.assertRaises(EnvironError):
            self.profile.import_signed_csv_file_to_db(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.rm_cpi_file_from_scripting_vm")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.EnvironError")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_cbrs_cpi_cleanup_import__successful(self, mock_pexpect, mock_error, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.side_effect = [0, 0, 0]
        cbrs_cpi_cleanup_import(Mock())
        self.assertFalse(mock_error.called)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.rm_cpi_file_from_scripting_vm")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_cbrs_cpi_cleanup_import__wrong_return_code(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 1
        with self.assertRaises(EnvironError):
            cbrs_cpi_cleanup_import(Mock())

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_rm_cpi_file_from_scripting_vm__successful(self, mock_pexpect, mock_log, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.side_effect = [0]
        rm_cpi_file_from_scripting_vm(mock_spawn)
        self.assertEqual(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.time.sleep")
    @patch("enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi.pexpect")
    def test_rm_cpi_file_from_scripting_vm__raises_error(self, mock_pexpect, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.side_effect = [1]
        with self.assertRaises(EnvironError):
            rm_cpi_file_from_scripting_vm(Mock())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
