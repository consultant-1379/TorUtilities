#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow import CmImport08Flow
from testslib import unit_test_utils


class CmImport08FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nodes = [Mock(), Mock()]
        self.user = Mock()
        self.flow = CmImport08Flow()
        self.flow.USER_ROLES = ['Cmedit_Administrator']
        self.flow.FILETYPE = 'dynamic'
        self.flow.TIMEOUT = 0.001
        self.flow.teardown_list = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_calculate_num_imports_in_parallel__is_successful(self):
        self.assertEqual(self.flow.calculate_num_imports_in_parallel(len(self.nodes * 6)), 2)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImportUpdateLive')
    def test_create_reset_job_and_set_default_values__is_successful(self, mock_cmimport_update_live, *_):
        expected_num_mo_changes = 2
        cmimport_live_obj = mock_cmimport_update_live.return_value
        self.flow.create_reset_job_and_set_default_values(self.user, self.nodes, expected_num_mo_changes)
        mock_cmimport_update_live.assert_called_with(
            name='cmimport_08_reset',
            user=self.user,
            nodes=self.nodes,
            mos={'UtranFreqRelation': ('userLabel', 'cmimport_08_default'),
                 'EUtranFreqRelation': ('userLabel', 'cmimport_08_default')},
            template_name='cmimport_08_reset.txt',
            flow='live_config',
            file_type='dynamic',
            expected_num_mo_changes=expected_num_mo_changes,
            timeout=0.001)
        self.assertEqual(1, cmimport_live_obj.prepare_dynamic_file.call_count)
        self.assertEqual(1, cmimport_live_obj.create.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImportUpdateLive')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.add_error_as_exception')
    def test_create_reset_job_and_set_default_values__adds_error(self, mock_add_error, mock_cmimport_update_live, *_):
        cmimport_live_obj = mock_cmimport_update_live.return_value
        cmimport_live_obj.create.side_effect = Exception
        self.flow.create_reset_job_and_set_default_values(self.user, self.nodes, 2)
        self.assertEqual(1, cmimport_live_obj.prepare_dynamic_file.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.create_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.get_different_nodes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.'
           'calculate_num_imports_in_parallel', return_value=1)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImportUpdateLive')
    def test_create_import_jobs__is_successful(self, mock_cmimport_update_live, mock_calculate, mock_get_different, *_):
        mock_calculate.return_value = 1
        mock_get_different.return_value = iter(self.nodes)
        self.flow.create_import_jobs(self.nodes, 2, [Mock()])
        self.assertEqual(mock_cmimport_update_live.call_count, 2)

    def test_import_func(self):
        mock_import = Mock()
        self.flow.import_func(mock_import)
        self.assertEqual(1, mock_import._create.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.nodes_list')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.'
           'calculate_num_imports_in_parallel')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.create_import_jobs')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.'
           'create_reset_job_and_set_default_values')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow.CmImport08Flow.setup_flow')
    def test_execute_flow__is_successful(self, mock_setup_flow, mock_create_reset, mock_create_jobs, *_):
        cmimport_setup_object = Mock()
        cmimport_setup_object.nodes = self.nodes
        cmimport_setup_object.user = self.user
        cmimport_setup_object.expected_num_mo_changes = 2
        mock_setup_flow.return_value = cmimport_setup_object
        mock_create_jobs.return_value = [Mock()], [Mock()]
        self.flow.execute_flow()
        self.assertEqual(1, mock_setup_flow.call_count)
        self.assertEqual(1, mock_create_reset.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
