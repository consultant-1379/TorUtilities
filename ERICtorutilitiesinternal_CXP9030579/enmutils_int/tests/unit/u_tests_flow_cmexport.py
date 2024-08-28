#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow
from testslib import unit_test_utils


class CmExportFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CmExportFlow()
        self.flow.FILETYPE = "3GPP"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Test"]
        self.flow.MAX_RETENTION_TIME = "4"
        self.flow.RETENTION_ENABLED = True

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.set_pib_parameters_to_required_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.validate_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.common_utils.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_existing_pib_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_profile_users')
    def test_execute_flow_with_filetype_list_is_successful(self, mock_create_users, mock_get_existing_pib_values, *_):
        mock_get_existing_pib_values.return_value = (Mock(), Mock())
        mock_create_users.return_value = [Mock()]
        self.flow.FILETYPE = ['3GPP', 'dynamic']
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.set_pib_parameters_to_required_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.state')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_existing_pib_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.validate_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_export_objects')
    def test_execute_flow__with_assertion_values_is_successful(self, mock_create_export_objects, mock_create_exports,
                                                               mock_validate_exports, mock_get_existing_pib_values, *_):
        mock_get_existing_pib_values.return_value = (Mock(), Mock())
        self.flow.execute_flow()
        self.assertEqual(mock_create_export_objects.call_count, 1)
        self.assertEqual(mock_create_exports.call_count, 1)
        self.assertEqual(mock_validate_exports.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.set_pib_parameters_to_required_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.validate_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_exports')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.common_utils.get_internal_file_path_for_import')
    @patch(
        'enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_existing_pib_values')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_profile_users')
    def test_execute_flow_max_retention_time_is_successful(self, mock_create_users, mock_get_existing_pib_values, *_):
        mock_get_existing_pib_values.return_value = (Mock(), Mock())
        mock_create_users.return_value = [Mock()]
        self.flow.MAX_RETENTION_TIME = Mock()
        delattr(self.flow, "MAX_RETENTION_TIME")
        self.flow.FILETYPE = ['3GPP', 'dynamic']
        self.assertFalse(hasattr(self, "MAX_RETENTION_TIME"))
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport', return_value=None)
    def test_create_export_objects(self, mock_export):
        self.assertEqual(3, len(self.flow.create_export_objects(Mock(), [Mock()], file_type=self.flow.FILETYPE, num_of_exports=3)))
        self.assertEqual(mock_export.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport', return_value=None)
    def test_create_export_objects_with_node_regex_is_successful(self, mock_export):
        self.flow.NODE_REGEX = '*'
        self.assertEqual(3, len(self.flow.create_export_objects(Mock(), [Mock()], num_of_exports=3, file_type=self.flow.FILETYPE,)))
        self.assertEqual(mock_export.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.common_utils.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport', return_value=None)
    def test_create_export_objects_with_file_in_is_successful(self, mock_export, mock_get_file_path):
        self.flow.FILE_IN = 'CMEXPORT_05_SON_userFilter_v1.txt'
        self.assertEqual(3, len(self.flow.create_export_objects(Mock(), [Mock()], num_of_exports=3, file_type=self.flow.FILETYPE,)))
        self.assertEqual(mock_export.call_count, 3)
        mock_get_file_path.assert_called_with('etc', 'data', 'CMEXPORT_05_SON_userFilter_v1.txt')

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    def test_create_exports_adds_error_on_exception(self, mock_add_error, mock_debug):
        export = Mock()
        export._create.side_effect = [Exception, None]
        self.flow.create_exports([export, export])
        self.assertEqual(mock_add_error.call_count, 1)
        mock_debug.assert_called_with("Successfully created 1/2 export(s).")

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    def test_create_exports(self, mock_add_error, mock_debug):
        export = Mock()
        export._create.side_effect = [None, None]
        self.flow.create_exports([export, export])
        self.assertEqual(mock_add_error.call_count, 0)
        mock_debug.assert_called_with("Successfully created 2/2 export(s).")

    def test_filter_cran_node_filter_cran_nodes(self):
        """
        Deprecated 24.09 and to be Deleted in 25.04 ENMRTD-25426
        """

    def test_filter_cran_node_filter_other_cran_nodes(self):
        """
        Deprecated 24.09 and to be Deleted in 25.04 ENMRTD-25426
        """

    def test_filter_cran_node_filter_nodes_add_error(self):
        """
        Deprecated 24.09 and to be Deleted in 25.04 ENMRTD-25426
        """

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    def test_validate_exports_adds_error_on_exception(self, mock_add_error):
        export = Mock()
        export._validate.side_effect = [Exception, None]
        self.flow.validate_exports([export, export])
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.generate_node_list_for_exports')
    def test_execute_parallel_flow_is_successful(self, mock_node_list, mock_create_users, *_):
        self.flow.NUMBER_OF_EXPORTS = 1
        self.flow.THREAD_QUEUE_TIMEOUT = 0.1
        mock_node_list.return_value = [Mock(), Mock()]
        mock_create_users.return_value = [Mock()]
        self.flow.execute_parallel_flow()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.generate_node_list_for_exports')
    def test_execute_parallel_flow_adds_error_as_exception(self, mock_node_list, mock_create_users,
                                                           mock_add_error, *_):
        self.flow.NUMBER_OF_EXPORTS = 3
        self.flow.THREAD_QUEUE_TIMEOUT = 0.1
        mock_node_list.return_value = [Mock(), Mock()]
        mock_create_users.return_value = [Mock()]
        self.flow.execute_parallel_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.random.randint', return_value=2)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.generate_basic_dictionary_from_list_of_objects')
    def test_generate_node_list_for_exports_is_successful(self, mock_nodes, *_):
        mock_nodes.return_value = {'ERBS': ['node1', 'node2', 'node3'], 'RadioNode': ['node1', 'node2']}
        self.flow.NUMBER_OF_EXPORTS = 2
        node_lists = self.flow.generate_node_list_for_exports()
        self.assertEqual(len(node_lists), 2)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.generate_basic_dictionary_from_list_of_objects')
    def test_generate_node_list_for_exports_returns_empty_nodes_list(self, mock_nodes, _):
        mock_nodes.return_value = {'ERBS': []}
        self.assertEqual(self.flow.generate_node_list_for_exports(), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.update_pib_parameter_on_enm")
    def test_update_pib_values__success(self, mock_update_pib_parameter_on_enm, mock_add_error):
        mock_update_pib_parameter_on_enm.return_value = True
        self.flow.update_pib_values("hai", "hello")
        self.assertEquals(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.update_pib_parameter_on_enm")
    def test_enabling_schedule_cleanup_export__exception(self, mock_update_pib_parameter_on_enm,
                                                         mock_add_error):
        mock_update_pib_parameter_on_enm.side_effect = Exception
        self.flow.update_pib_values("hai", "hello")
        self.assertEquals(mock_add_error.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.get_pib_value_on_enm")
    def test_get_existing_pib_values(self, mock_get_pib_parameter_on_enm):
        mock_get_pib_parameter_on_enm.side_effect = ["4", "True"]
        self.assertEqual(self.flow.get_existing_pib_values(), ("4", "True"))

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.update_pib_values')
    def test_set_pib_parameters_to_required_values__success(self, mock_update_pib_values):
        self.flow.set_pib_parameters_to_required_values()
        self.assertTrue(mock_update_pib_values.called)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow.CmExportFlow.update_pib_values')
    def test_reset_pib_parameters__success(self, mock_update_pib_values):
        self.flow.reset_pib_parameters("4", "True")
        self.assertTrue(mock_update_pib_values.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
