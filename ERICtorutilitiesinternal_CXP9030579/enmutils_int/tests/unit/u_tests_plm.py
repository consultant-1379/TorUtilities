#!/usr/bin/env python
from collections import OrderedDict
import unittest2
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils
from mock import patch, Mock, mock_open
from enmutils_int.lib.plm import PhysicalLinkMgt, EnmApplicationError


sgsn_oss_id_response = [u'FDN : NetworkElement=CORE01SGSN001', u'ossModelIdentity : 16A-CP09', u'', u'',
                        u'1 instance(s)']
file_path = "/home/enmutils/dynamic_content/{}"


class PLMUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.plm = PhysicalLinkMgt(self.user, ["SGSN-MME", "MINI-LINK-6352"])

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_convert_string__returns_integer_value_from_given_alphanumeric_string(self):
        self.assertEqual(self.plm.convert_string("PLMimport_25.csv"), 25)

    @patch("enmutils.lib.persistence.has_key")
    @patch("enmutils.lib.persistence.get")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_normalized_nodes_from_enm__is_successful(self, mock_execute_cmedit_cmd, mock_persistence, mock_has_key):
        self.plm.node_types = ["SGSN-MME", "MINI-LINK-6352", "RadioNode"]
        expected_output = OrderedDict()
        expected_output['SGSN-MME'] = ['CORESGSN01', 'CORESGSN02']
        expected_output['MINI-LINK-6352'] = ['CORE01ML6352-2-8-0001', 'CORE01ML6352-2-8-00010']
        mock_execute_cmedit_cmd.side_effect = [['CORESGSN02', 'CORESGSN01'],
                                               ['CORE01ML6352-2-8-00010', 'CORE01ML6352-2-8-0001'],
                                               ['LTE01dg2', 'LTE02dg2'], ['BSC82MSRBS-V224', 'BSC66MSRBS-V204']]
        mock_has_key.return_value = True
        mock_persistence.return_value = Mock(_is_exclusive=False)
        actual_output = self.plm.get_normalized_nodes_from_enm()
        self.assertEqual(actual_output, expected_output)

    @patch("enmutils.lib.persistence.has_key")
    @patch("enmutils.lib.persistence.get")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_normalized_nodes_from_enm__if_exclusive(self, mock_execute_cmedit_cmd, mock_persistence,
                                                         mock_has_key):
        self.plm.node_types = ["SGSN-MME", "MINI-LINK-6352", "RadioNode"]
        expected_output = OrderedDict()
        expected_output['SGSN-MME'] = ['CORESGSN01', 'CORESGSN02']
        expected_output['MINI-LINK-6352'] = ['CORE01ML6352-2-8-0001', 'CORE01ML6352-2-8-00010']
        mock_execute_cmedit_cmd.side_effect = [['CORESGSN02', 'CORESGSN01'],
                                               ['CORE01ML6352-2-8-00010', 'CORE01ML6352-2-8-0001'],
                                               ['LTE01dg2', 'LTE02dg2'], ['BSC82MSRBS-V224', 'BSC66MSRBS-V204']]
        mock_has_key.return_value = True
        mock_persistence.return_value = Mock(_is_exclusive=True)
        self.assertRaises(EnmApplicationError, self.plm.get_normalized_nodes_from_enm)

    @patch("enmutils.lib.persistence.has_key")
    @patch("enmutils.lib.persistence.get")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_normalized_nodes_from_enm_for_not_has_key(self, mock_execute_cmedit_cmd, mock_persistence,
                                                           mock_has_key):
        self.plm.node_types = ["SGSN-MME", "MINI-LINK-6352", "RadioNode"]
        expected_output = OrderedDict()
        expected_output['SGSN-MME'] = ['CORESGSN01', 'CORESGSN02']
        expected_output['MINI-LINK-6352'] = ['CORE01ML6352-2-8-0001', 'CORE01ML6352-2-8-00010']
        mock_execute_cmedit_cmd.side_effect = [['CORESGSN02', 'CORESGSN01'],
                                               ['CORE01ML6352-2-8-00010', 'CORE01ML6352-2-8-0001'],
                                               ['LTE01dg2', 'LTE02dg2'], ['BSC82MSRBS-V224', 'BSC66MSRBS-V204']]
        mock_has_key.return_value = False
        self.assertRaises(EnmApplicationError, self.plm.get_normalized_nodes_from_enm)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_normalized_nodes_from_enm__raises_exception(self, mock_execute_cmedit_cmd):
        mock_execute_cmedit_cmd.side_effect = [[], []]
        self.assertRaises(EnmApplicationError, self.plm.get_normalized_nodes_from_enm)

    def test_prepare_model_id_and_node_names_dict__is_successful(self):
        model_id_list = [('CORE01SGSN001', '16A-CP09'), ('CORE01SGSN002', '16A-CP09'),
                         ('CORE10SGSN001', '16A-CP06'), ('CORE10SGSN002', '16A-CP06')]
        expected_output = OrderedDict()
        expected_output['16A-CP09'] = ['CORE01SGSN001', 'CORE01SGSN002']
        expected_output['16A-CP06'] = ['CORE10SGSN001', 'CORE10SGSN002']
        actual_output = self.plm.prepare_model_id_and_node_names_dict(model_id_list)
        self.assertEqual(actual_output, expected_output)

    def test_sort_interfaces_list_according_to_hierarchy__is_successful(self):
        interface_list = ["1/13", "1/19", "1/2", "1/20", "1/3", "1/4", "1/5", "1/8", "1/9", "1/1", "management"]
        inf_to_ignore = ['management']
        expected_output = ["1/1", "1/2", "1/3", "1/4", "1/5", "1/8", "1/9", "1/13", "1/19", "1/20"]
        actual_output = self.plm.sort_interfaces_list_according_to_hierarchy(interface_list, inf_to_ignore)
        self.assertEqual(actual_output, expected_output)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.sort_interfaces_list_according_to_hierarchy")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_interfaces_on_node__is_successful(self, mock_execute_cmedit_cmd, mock_sort_inf_list):
        model_id_node_dict = OrderedDict()
        expected_output = OrderedDict()
        sorted_list = ['100/1', '100/11', '100/16', '100/17']
        model_id_node_dict["16A-CP09"] = ["CORE01SGSN001", "CORE01SGSN002"]
        model_id_node_dict["16A-CP06"] = ["CORE10SGSN001", "CORE10SGSN002"]
        expected_output["16A-CP09"] = (sorted_list, ["CORE01SGSN001", "CORE01SGSN002"])
        mock_execute_cmedit_cmd.side_effect = [['100/11', '100/16', '100/1', '100/17'], []]
        mock_sort_inf_list.return_value = sorted_list
        actual_output = self.plm.get_interfaces_on_node(model_id_node_dict)
        self.assertEqual(actual_output, expected_output)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.sort_interfaces_list_according_to_hierarchy")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_interfaces_on_node__ML_is_successful(self, mock_execute_cmedit_cmd, mock_sort_inf_list):
        model_id_node_dict = OrderedDict()
        expected_output = OrderedDict()
        sorted_list = ['100/1', '100/11', '100/16', '100/17']
        model_id_node_dict["16A-CP09"] = ["CORE01ML001", "CORE01ML002"]
        model_id_node_dict["16A-CP06"] = ["CORE10ML001", "CORE10ML002"]
        expected_output["16A-CP09"] = (sorted_list, ["CORE01ML001", "CORE01ML002"])
        mock_execute_cmedit_cmd.side_effect = [['LAN', 'RLIME', 'CT', 'RLT'], []]
        mock_sort_inf_list.return_value = sorted_list
        actual_output = self.plm.get_interfaces_on_node(model_id_node_dict)
        self.assertEqual(actual_output, expected_output)

    @patch("enmutils_int.lib.plm.log.logger.debug")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.sort_interfaces_list_according_to_hierarchy")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_get_interfaces_on_node__ML669_is_successful(self, mock_execute_cmedit_cmd, mock_sort_inf_list, mock_log):
        model_id_node_dict = OrderedDict()
        expected_output = OrderedDict()
        sorted_list = ['100/1', '100/11', '100/16', '100/17']
        model_id_node_dict["16A-CP09"] = ["CORE01ML669001", "CORE01ML669002"]
        model_id_node_dict["16A-CP06"] = ["CORE10ML669001", "CORE10ML669002"]
        expected_output["16A-CP09"] = (sorted_list, ["CORE01ML669001", "CORE01ML669002"])
        mock_execute_cmedit_cmd.side_effect = [['LAN', 'RLIME', 'CT', 'RLT'], []]
        mock_sort_inf_list.return_value = sorted_list
        actual_output = self.plm.get_interfaces_on_node(model_id_node_dict)
        self.assertEqual(actual_output, expected_output)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd")
    def test_fetch_nodes_model_id__is_successful(self, mock_execute_cmd, *_):
        node_names_list = ["CORE01SGSN0001"] * 600
        self.plm.fetch_nodes_model_id(node_names_list)
        self.assertEqual(mock_execute_cmd.call_count, 2)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.consolidate_data_for_import", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.get_interfaces_on_node", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.prepare_model_id_and_node_names_dict", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_nodes_model_id")
    def test_prepare_node_details_for_import_files__is_successful_if_nodes_less_than_500(self, mock_fetch_model_id, *_):
        normalized_nodes = OrderedDict()
        normalized_nodes['SGSN-MME'] = ['CORESGSN01', 'CORESGSN02']
        result = self.plm.prepare_node_details_for_import_files(normalized_nodes)
        self.assertIsInstance(result, dict)
        self.assertFalse(mock_fetch_model_id.called)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.consolidate_data_for_import", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.get_interfaces_on_node", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.prepare_model_id_and_node_names_dict", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.execute_cmedit_cmd", return_value=Mock())
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_nodes_model_id")
    def test_prepare_node_details_for_import_files__is_successful_if_nodes_greater_than_500(self, mock_fetch_model_id,
                                                                                            *_):
        normalized_nodes = OrderedDict()
        normalized_nodes['SGSN-MME'] = ['CORESGSN01'] * 619
        result = self.plm.prepare_node_details_for_import_files(normalized_nodes)
        self.assertIsInstance(result, dict)
        self.assertTrue(mock_fetch_model_id.called)

    @patch("enmutils_int.lib.plm.re")
    def test_execute_cmedit_cmd__is_successful(self, mock_re):
        response = Mock()
        response.get_output.return_value = sgsn_oss_id_response
        cmd = "cmedit get CORE01SGSN001 NetworkElement.ossModelIdentity"
        self.user.enm_execute.return_value = response
        mock_re.compile.return_value.findall.return_value = [('CORE01SGSN001', '16A-CP09')]
        result = self.plm.execute_cmedit_cmd(cmd, "FDN : NetworkElement=(.*)\nossModelIdentity : (.*)")
        self.assertTrue(self.user.enm_execute.called)
        self.assertTrue(mock_re.compile.called)
        self.assertIsInstance(result, list)

    @patch("enmutils_int.lib.plm.re")
    @patch("enmutils_int.lib.plm.log")
    def test_execute_cmedit_cmd__logs_exception(self, mock_log, *_):
        cmd = "cmedit get CORE01SGSN001 NetworkElement.ossModelIdentity"
        self.user.enm_execute.side_effect = Exception
        self.plm.execute_cmedit_cmd(cmd, "FDN : NetworkElement=(.*)\nossModelIdentity : (.*)")
        self.assertTrue(mock_log.logger.debug.call_count, 1)

    def test_consolidate_data_for_import__is_succesful(self):
        model_id_inf_dict = OrderedDict()
        model_id_inf_dict["16A-CP09"] = (['100/1', '100/11'], ["CORE01SGSN004", "CORE01SGSN002", "CORE01SGSN005",
                                                               "CORE01SGSN001", "CORE01SGSN003"])
        model_id_inf_dict["16A-CP06"] = (["100/1"], ["CORE10SGSN002", "CORE10SGSN001"])
        expected_output = [("CORE01SGSN001", "100/1", "CORE01SGSN002"), ("CORE01SGSN003", "100/1", "CORE01SGSN004"),
                           ("CORE01SGSN001", "100/11", "CORE01SGSN002"), ("CORE01SGSN003", "100/11", "CORE01SGSN004"),
                           ("CORE10SGSN001", "100/1", "CORE10SGSN002")]
        actual_output = self.plm.consolidate_data_for_import(model_id_inf_dict)
        self.assertEqual(actual_output, expected_output)

    @patch("enmutils_int.lib.plm.filesystem")
    def test_write_to_csv_file__is_successful(self, mock_filesystem):
        file_paths = [file_path.format("PLMimport1.csv")]
        mock_filesystem.does_dir_exist.return_value = False
        mock_filesystem.create_dir.return_value = True
        import_dict = {"PLMimport1.csv": "link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1"}
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            self.plm.write_to_csv_file(import_dict)
            mock_open_file.assert_called_once_with(file_paths[0], 'w')

    @patch("enmutils_int.lib.plm.filesystem")
    def test_write_to_csv_file__does_not_create_directory_if_already_exists(self, mock_filesystem):
        file_paths = [file_path.format("PLMimport1.csv")]
        mock_filesystem.does_dir_exist.return_value = True
        import_dict = {"PLMimport1.csv": "link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1"}
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            self.plm.write_to_csv_file(import_dict)
            mock_open_file.assert_called_once_with(file_paths[0], 'w')

    def test_write_to_csv_file__raises_enmapplication_error(self):
        self.assertRaises(EnmApplicationError, self.plm.write_to_csv_file, {})

    @patch("enmutils_int.lib.plm.log.logger.debug")
    def test_validate_nodes_for_import_is_successful(self, mock_log):
        nodes_to_import = OrderedDict()
        self.plm.num_lines = 2
        nodes_to_import["SGSN-MME"] = [("CORE01SGSN001", "100/1", "CORE01SGSN002"),
                                       ("CORE01SGSN003", "100/1", "CORE01SGSN004"),
                                       ("CORE01SGSN001", "100/11", "CORE01SGSN002"),
                                       ("CORE01SGSN003", "100/11", "CORE01SGSN004"),
                                       ("CORE10SGSN001", "100/1", "CORE10SGSN002")]
        nodes_to_import['MINI-LINK-6352'] = [("CORE01ML6352-2-8-0001", "ct-1/1/1", "CORE01ML6352-2-8-00010"),
                                             ("CORE01ML6352-2-8-0001", "rlt-1/1/1", "CORE01ML6352-2-8-00010")]
        actual_result = self.plm.validate_nodes_for_import(nodes_to_import, max_links=1000)
        expected_result = {'PLMimport1.csv': ['link1,CORE01SGSN001,100/1,CORE01SGSN002,100/1',
                                              'link2,CORE01SGSN003,100/1,CORE01SGSN004,100/1'],
                           'PLMimport2.csv': ['link3,CORE01SGSN001,100/11,CORE01SGSN002,100/11',
                                              'link4,CORE01SGSN003,100/11,CORE01SGSN004,100/11'],
                           'PLMimport3.csv': ['link5,CORE10SGSN001,100/1,CORE10SGSN002,100/1',
                                              'link6,CORE01ML6352-2-8-0001,ct-1/1/1,CORE01ML6352-2-8-00010,ct-1/1/1'],
                           'PLMimport4.csv': ['link7,CORE01ML6352-2-8-0001,rlt-1/1/1,CORE01ML6352-2-8-00010,rlt-1/1/1']}
        self.assertEqual(actual_result, expected_result)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.plm.log.logger.debug")
    def test_validate_nodes_for_import_is_successful_max(self, mock_log):
        nodes_to_import = OrderedDict()
        self.plm.num_lines = 2
        nodes_to_import["SGSN-MME"] = [("CORE01SGSN001", "100/1", "CORE01SGSN002"),
                                       ("CORE01SGSN003", "100/1", "CORE01SGSN004"),
                                       ("CORE01SGSN001", "100/11", "CORE01SGSN002"),
                                       ("CORE01SGSN003", "100/11", "CORE01SGSN004"),
                                       ("CORE10SGSN001", "100/1", "CORE10SGSN002")]
        nodes_to_import['MINI-LINK-6352'] = [("CORE01ML6352-2-8-0001", "ct-1/1/1", "CORE01ML6352-2-8-00010"),
                                             ("CORE01ML6352-2-8-0001", "rlt-1/1/1", "CORE01ML6352-2-8-00010")]
        actual_result = self.plm.validate_nodes_for_import(nodes_to_import, max_links=7)
        expected_result = {'PLMimport1.csv': ['link1,CORE01SGSN001,100/1,CORE01SGSN002,100/1',
                                              'link2,CORE01SGSN003,100/1,CORE01SGSN004,100/1'],
                           'PLMimport2.csv': ['link3,CORE01SGSN001,100/11,CORE01SGSN002,100/11',
                                              'link4,CORE01SGSN003,100/11,CORE01SGSN004,100/11'],
                           'PLMimport3.csv': ['link5,CORE10SGSN001,100/1,CORE10SGSN002,100/1',
                                              'link6,CORE01ML6352-2-8-0001,ct-1/1/1,CORE01ML6352-2-8-00010,ct-1/1/1'],
                           'PLMimport4.csv': ['link7,CORE01ML6352-2-8-0001,rlt-1/1/1,CORE01ML6352-2-8-00010,rlt-1/1/1']}
        self.assertEqual(actual_result, expected_result)
        self.assertTrue(mock_log.called)

    def test_prepare_delete_links_dict__is_successful(self):
        self.plm.num_lines = 2
        import_files = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv"),
                        file_path.format("PLMimport3.csv")]
        data = '\n'.join(["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                          "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1"])
        expected_result = {"PLM_deletable_links1.csv": ["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                                                        "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1"]}
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            with open(mock_open_file(spec=import_files), 'rb'):
                actual_result = self.plm.prepare_delete_links_dict(import_files)
                self.assertEqual(actual_result, expected_result)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.set_number_of_links_created")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.persist_files_imported")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.check_response_for_errors_after_file_import", return_value={})
    @patch("enmutils_int.lib.plm.import_multipart_file_to_plm")
    def test_create_links__is_successful(self, *_):
        file_paths = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        self.plm.files_imported = []
        self.plm.create_links(file_paths)
        self.assertEqual(self.plm.files_imported, [file_paths[0]])

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.set_number_of_links_created")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.persist_files_imported")
    @patch("enmutils_int.lib.plm.import_multipart_file_to_plm")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.check_response_for_errors_after_file_import")
    def test_create_links__raises_EnmApplicationError(self, mock_check_response, *_):
        file_paths = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        self.plm.files_imported = []
        mock_check_response.return_value = {'link1': 'invalid interface', 'link2': 'invalid interface'}
        self.assertRaises(EnmApplicationError, self.plm.create_links, file_paths)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.persist_files_imported")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.set_number_of_links_created")
    @patch("enmutils_int.lib.plm.import_multipart_file_to_plm")
    def test_create_links__does_not_append_deletable_links_file_to_imported_files_list(self, *_):
        file_paths = [file_path.format("PLM_deletable_links1.csv")]
        self.plm.files_imported = []
        self.plm.create_links(file_paths)
        self.assertFalse(hasattr(self.plm.files_imported, file_paths[0]))

    @patch("enmutils_int.lib.plm.import_multipart_file_to_plm")
    def test_create_links__does_not_create_links_if_all_files_are_already_imported(self, mock_multipart_import, *_):
        file_paths = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        self.plm.files_imported = file_paths
        self.plm.create_links(file_paths)
        self.assertFalse(mock_multipart_import.called)

    @patch('enmutils_int.lib.plm.log.logger.info')
    @patch("enmutils_int.lib.plm.run_local_cmd")
    def test_set_number_of_links_created__is_successful(self, mock_run_local_cmd, mock_logger_info):
        imported_file = file_path.format("PLMimport1.csv")
        response = Mock()
        response.ok = True
        response.stdout = "301 PLMimport1.csv"
        mock_run_local_cmd.return_value = response
        self.plm.set_number_of_links_created(imported_file, 130)
        self.assertEqual(mock_logger_info.call_count, 1)
        self.assertEqual(self.plm.links_created, 170)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.persist_files_imported")
    @patch("enmutils_int.lib.plm.log.logger.info")
    @patch("enmutils_int.lib.plm.run_local_cmd")
    def test_set_number_of_links_created__logs_if_response_is_not_ok(self, mock_run_local_cmd, mock_logger_info, *_):
        imported_file = file_path.format("PLMimport1.csv")
        response = Mock()
        response.ok = False
        mock_run_local_cmd.return_value = response
        self.plm.set_number_of_links_created(imported_file, 10)
        self.assertEqual(mock_logger_info.call_count, 2)
        self.assertEqual(self.plm.links_created, 290)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_content_from_files")
    def test_delete_links_using_id__deletes_links_successfully(self, mock_fetch_content):
        import_files = [file_path.format("PLMimport1.csv")]
        self.plm.files_imported.append(import_files[0])
        mock_fetch_content.return_value = ['link1', 'link2', 'link3', 'link4', 'link5', 'link6', 'link7', 'link8',
                                           'link9', 'link10']
        self.plm.links_created = 600
        response = Mock()
        response.get_output.return_value = [u'Link successfully deleted.']
        self.user.enm_execute.return_value = response
        self.plm.delete_links_using_id(import_files[0])
        self.assertEqual(self.user.enm_execute.call_count, 10)
        self.assertEqual(self.plm.links_created, 590)
        self.assertEqual(self.plm.files_imported, [])

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_content_from_files")
    def test_delete_links_using_id__raises_error_if_failed_to_delete_links(self, mock_fetch_content):
        import_files = [file_path.format("PLM_deletable_links1.csv")]
        self.plm.files_imported.append("PLMimport1.csv")
        mock_fetch_content.return_value = ['link1', 'link2']
        self.plm.links_created = 900
        response = Mock()
        response.get_output.side_effect = [[u'Link successfully deleted.'], [u'Error 5003 : Internal Server Error.']]
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.plm.delete_links_using_id, import_files[0])
        self.assertEqual(self.user.enm_execute.call_count, 2)
        self.assertEqual(self.plm.links_created, 899)
        self.assertEqual(self.plm.files_imported, ["PLMimport1.csv"])

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_content_from_files")
    def test_delete_links_using_id__logs_exception(self, mock_fetch_content):
        import_files = [file_path.format("PLMimport1.csv")]
        mock_fetch_content.return_value = ['link1', 'link2']
        self.user.enm_execute.side_effect = Exception
        self.plm.delete_links_using_id(import_files[0])
        self.assertTrue(self.user.enm_execute.call_count, 2)

    def test_get_max_links_limit__fetches_maximum_links_that_can_be_created_on_server(self):
        import_files = [file_path.format("PLMimport1.csv")]
        data = '\n'.join(["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                          "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1"])
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            with open(mock_open_file(spec=import_files[0]), 'rb'):
                actual_result = self.plm.get_max_links_limit(import_files)
                self.assertEqual(actual_result, 2)

    def test_fetch_content_from_files__return_list_of_nodes_from_file(self):
        imported_files = [file_path.format("PLMimport1.csv")]
        data = '\n'.join(["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                          "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1"])
        expected_result = ['CORE01SGSN002', 'CORE01SGSN001', 'CORE01SGSN004', 'CORE01SGSN003']
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            with open(mock_open_file(spec=imported_files[0]), 'rb'):
                actual_result = self.plm.fetch_content_from_files(imported_files)
                self.assertEqual(actual_result, expected_result)

    def test_fetch_content_from_files__return_list_of_links_from_file(self):
        imported_files = [file_path.format("PLMimport1.csv")]
        data = '\n'.join(["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                          "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1"])
        expected_result = ['link1', 'link2']
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            with open(mock_open_file(spec=imported_files[0]), 'rb'):
                actual_result = self.plm.fetch_content_from_files(imported_files, links=True)
                self.assertEqual(actual_result, expected_result)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.remove_files")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.delete_links_on_nodes")
    @patch("enmutils_int.lib.plm.persistence")
    def test_teardown__is_successful(self, mock_persistence, mock_delete_links, mock_remove_files):
        mock_persistence.has_key.return_value = True
        mock_persistence.remove.return_value = 1
        self.plm._teardown()
        self.assertTrue(mock_delete_links.called)
        self.assertTrue(mock_remove_files.called)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.remove_files")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.delete_links_on_nodes")
    @patch("enmutils_int.lib.plm.persistence")
    def test_teardown__does_not_remove_key_from_persistence_if_not_present(self, mock_persistence, mock_delete_links,
                                                                           mock_remove_files):
        mock_persistence.has_key.return_value = False
        self.plm._teardown()
        self.assertTrue(mock_delete_links.called)
        self.assertTrue(mock_remove_files.called)
        self.assertFalse(mock_persistence.remove.called)

    @patch("enmutils_int.lib.plm.persistence")
    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.delete_links_on_nodes")
    @patch('enmutils_int.lib.plm.log.logger.info')
    def test_teardown__logs_exception(self, mock_log, mock_delete_links, *_):
        mock_delete_links.side_effect = Exception
        self.assertRaises(Exception, self.plm._teardown)
        self.assertTrue(mock_delete_links.called)
        self.assertEqual(mock_log.call_count, 1)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_content_from_files")
    @patch('enmutils_int.lib.plm.log.logger.debug')
    def test_delete_links_on_nodes__logs_exception(self, mock_logger_debug, mock_fetch_content):
        import_files = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        mock_fetch_content.return_value = ['CORE01SGSN0001']
        self.user.enm_execute.side_effect = Exception
        self.plm.delete_links_on_nodes(import_files)
        self.assertEqual(mock_logger_debug.call_count, 1)

    @patch("enmutils_int.lib.plm.PhysicalLinkMgt.fetch_content_from_files")
    @patch('enmutils_int.lib.plm.log.logger.debug')
    def test_delete_links_on_nodes__logs_if_failed_to_delete_links_on_nodes(self, mock_logger_debug,
                                                                            mock_fetch_content):
        import_files = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        mock_fetch_content.return_value = ['CORE01SGSN0001', 'CORE01SGSN0002', 'CORE01SGSN0001']
        response = Mock()
        response.get_output.side_effect = [[u'Link successfully deleted.'], [u'Error 5003 : Internal Server Error.']]
        self.user.enm_execute.return_value = response
        self.plm.delete_links_on_nodes(import_files)
        self.assertEqual(mock_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.plm.log.logger.info')
    @patch("enmutils_int.lib.plm.os.remove")
    @patch("enmutils_int.lib.plm.os.path.isfile")
    def test_remove_files__removes_files_if_only_present(self, mock_os_path_file, mock_os_remove, mock_log):
        self.plm.file_paths = [file_path.format("PLMimport1.csv"), file_path.format("PLMimport2.csv")]
        mock_os_path_file.side_effect = [True, False]
        self.plm.remove_files()
        self.assertEqual(mock_os_path_file.call_count, 2)
        self.assertEqual(mock_os_remove.call_count, 1)
        self.assertEqual(mock_log.call_count, 5)

    @patch('enmutils_int.lib.plm.persistence')
    @patch('enmutils_int.lib.plm.mutexer')
    @patch('enmutils_int.lib.plm.log.logger.info')
    def test_persist_files_imported__removes_file_paths_if_flag_set_to_true(self, mock_logger_info, *_):
        import_file_path = "/home/enmutils/dynamic_content/PLMimport1.csv"
        self.plm.persist_files_imported(import_file_path, delete=True)
        self.assertEqual(mock_logger_info.call_count, 2)

    @patch('enmutils_int.lib.plm.persistence')
    @patch('enmutils_int.lib.plm.mutexer')
    @patch('enmutils_int.lib.plm.log.logger.info')
    def test_persist_files_imported__appends_file_paths_if_flag_set_to_false(self, mock_logger_info, *_):
        import_file_path = "/home/enmutils/dynamic_content/PLMimport1.csv"
        self.plm.persist_files_imported(import_file_path, delete=False)
        self.assertEqual(mock_logger_info.call_count, 2)

    @patch('enmutils_int.lib.plm.mutexer')
    @patch('enmutils_int.lib.plm.log.logger.info')
    @patch('enmutils_int.lib.plm.persistence')
    def test_persist_files_imported__persists_key_if_not_already_present_in_persistence(self, mock_persistence, *_):
        import_file_path = "/home/enmutils/dynamic_content/PLMimport1.csv"
        mock_persistence.has_key.return_value = False
        self.plm.persist_files_imported(import_file_path, delete=False)
        self.assertEqual(mock_persistence.set.call_count, 1)

    def test_check_response_for_errors_after_file_import__is_successful(self):
        self.plm.failed_links = {}
        response = Mock()
        response.json.return_value = [{'importResult': 'Imported', 'name': 'link1', 'errorMessage': ''},
                                      {'importResult': 'Failed', 'name': 'link2', 'errorMessage': 'Invalid Interface'}]
        failed_links = self.plm.check_response_for_errors_after_file_import(response)
        self.assertEqual(failed_links, {'link2': 'Invalid Interface'})

    def test_check_response_for_errors_after_file_import__raises_EnmApplicationError(self):
        self.plm.failed_links = {}
        response = Mock()
        response.json.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.plm.check_response_for_errors_after_file_import, response)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
