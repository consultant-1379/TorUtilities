#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import patch, Mock, PropertyMock
from enmutils_int.lib.profile_flows.plm_flows.plm_01_flow import Plm01Flow, EnmApplicationError


class PLM01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Plm01Flow()
        self.flow.delete_file = ['PLM_deletable_links1.csv']
        self.flow.MAX_LINKS = 400
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "LinkManagement_Administrator"
        self.flow.NODE_TYPES = ["SGSN-MME", "MINI-LINK-6352"]
        self.flow.SCHEDULE_SLEEP = 5 * 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.perform_pre_startup_steps")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.PhysicalLinkMgt")
    def test_execute_flow__deletes_links_if_all_files_imported(self, mock_physical_link_mgt, mock_prestartup_steps, *_):
        mock_prestartup_steps.return_value = ["PLMimport1.csv", "PLMimport2.csv"]
        mock_physical_link_mgt.return_value.files_imported = ["PLMimport1.csv", "PLMimport2.csv"]
        self.flow.execute_flow()
        self.assertTrue(self.flow.FILE_FLAG)
        self.assertEqual(mock_physical_link_mgt.return_value.delete_links_using_id.call_count, 1)

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.perform_pre_startup_steps")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.PhysicalLinkMgt")
    def test_execute_flow__creates_links_deleted_when_all_files_were_imported(self, mock_physical_link_mgt,
                                                                              mock_prestartup_steps, *_):
        mock_prestartup_steps.return_value = ["PLMimport1.csv", "PLMimport2.csv"]
        mock_physical_link_mgt.return_value.files_imported = ["PLMimport1.csv", "PLMimport2.csv"]
        self.flow.delete_file = "/home/enmutils/dynamic_content/PLM_deletable_links1.csv"
        self.flow.FILE_FLAG = True
        self.flow.execute_flow()
        self.assertEqual(mock_physical_link_mgt.return_value.create_links.call_count, 1)
        mock_physical_link_mgt.return_value.create_links.assert_called_with([self.flow.delete_file])

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.perform_pre_startup_steps")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.PhysicalLinkMgt")
    def test_execute_flow__creates_links_if_not_all_files_were_imported(self, mock_physical_link_mgt,
                                                                        mock_prestartup_steps, *_):
        import_files = ["PLMimport1.csv", "PLMimport2.csv"]
        mock_prestartup_steps.return_value = import_files
        mock_physical_link_mgt.return_value.files_imported = ["PLMimport1.csv"]
        self.flow.execute_flow()
        self.assertEqual(mock_physical_link_mgt.return_value.create_links.call_count, 1)
        mock_physical_link_mgt.return_value.create_links.assert_called_with(import_files)

    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.perform_pre_startup_steps", return_value=[])
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.PhysicalLinkMgt")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.add_error_as_exception")
    def test_execute_flow__adds_error_as_exception_if_no_import_files(self, mock_add_error_as_exception, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_files_set_max_links")
    def test_perform_pre_startup_steps__is_successful(self, mock_create_files, *_):
        files_list = ["PLMimport1.csv", "PLMimport2.csv"]
        mock_create_files.return_value = files_list
        plm = Mock()
        import_files = self.flow.perform_pre_startup_steps(plm)
        self.assertEqual(import_files, files_list)
        self.assertEqual(plm.delete_links_on_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.sleep")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.plm_flows.plm_01_flow.Plm01Flow.create_files_set_max_links")
    def test_perform_pre_startup_steps__adds_error_as_exception(self, mock_create_files, mock_add_error_as_exception,
                                                                *_):
        mock_create_files.side_effect = Exception
        plm = Mock()
        self.flow.perform_pre_startup_steps(plm)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_create_files_set_max_links__is_successful(self):
        plm = Mock()
        plm.validate_nodes_for_import.return_value = {Mock()}
        plm.prepare_delete_links_dict.return_value = {Mock()}
        plm.write_to_csv_file.side_effect = [["PLMimport1.csv"], ["PLM_deletable_links1.csv"]]
        self.flow.create_files_set_max_links(plm)
        self.assertTrue(plm.get_normalized_nodes_from_enm.called)
        self.assertTrue(plm.validate_nodes_for_import.called)
        self.assertTrue(plm.write_to_csv_file.call_count, 2)

    def test_create_files_set_max_links__updates_max_links(self):
        plm = Mock()
        plm.validate_nodes_for_import.return_value = {Mock()}
        plm.prepare_delete_links_dict.return_value = {Mock()}
        plm.write_to_csv_file.side_effect = [["PLMimport1.csv"], ["PLM_deletable_links1.csv"]]
        plm.get_max_links_limit.return_value = 200
        self.flow.create_files_set_max_links(plm)
        self.assertTrue(plm.get_normalized_nodes_from_enm.called)
        self.assertTrue(plm.validate_nodes_for_import.called)
        self.assertTrue(plm.write_to_csv_file.call_count, 2)
        self.assertEqual(self.flow.MAX_LINKS, 200)

    def test_create_files_set_max_links__raises_exception(self):
        plm = Mock()
        plm.get_normalized_nodes_from_enm.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.flow.create_files_set_max_links, plm)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
