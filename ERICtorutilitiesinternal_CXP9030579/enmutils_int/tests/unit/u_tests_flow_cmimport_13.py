#!/usr/bin/env python
import datetime

import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow import CmImport13Flow
from testslib import unit_test_utils


class CmImport13FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CmImport13Flow()
        self.nodes = [Mock(), Mock()]
        self.user = Mock()
        self.flow.FILETYPE = '3GPP'
        self.flow.ITERATION_TIMEOUT = 0.001
        self.flow.POSTGRES_RETENTION_TIME_DAYS = "20"
        self.flow.TIMEOUT = 0.001
        self.flow.MOS_DEFAULT = {'UtranCellRelation': ('isRemoveAllowed', 'true'),
                                 'NRCellRelation': ('isRemoveAllowed', 'true')}
        self.flow.MOS_MODIFY = {'UtranCellRelation': ('isRemoveAllowed', 'false'),
                                'NRCellRelation': ('isRemoveAllowed', 'false')}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImportUpdateLive')
    def test_set_default_values__is_successful(self, mock_update_live, mock_teardown_list_append, mock_add_error,
                                               mock_picklable_boundmethod):
        expected_num_mo_changes = 20
        self.flow.set_default_values(self.nodes, self.user, expected_num_mo_changes)
        mock_update_live.assert_called_with(
            name='cmimport_13_reset',
            mos={'NRCellRelation': ('isRemoveAllowed', 'true'), 'UtranCellRelation': ('isRemoveAllowed', 'true')},
            nodes=self.nodes,
            user=self.user,
            template_name='cmimport_13_reset.xml',
            flow='live_config',
            file_type=self.flow.FILETYPE,
            interface='NBIv2',
            expected_num_mo_changes=expected_num_mo_changes,
            timeout=0.001
        )
        mock_teardown_list_append.assert_called_with(mock_picklable_boundmethod.return_value)
        mock_picklable_boundmethod.assert_called_with(mock_update_live.return_value.create_over_nbi)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImportUpdateLive')
    def test_set_default_values__adds_error(self, mock_update_live, mock_add_error):
        self.flow.teardown_list = Mock()
        mock_update = mock_update_live.return_value
        mock_update.create_over_nbi.side_effect = Exception
        self.flow.set_default_values(self.nodes, self.user, 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImportUpdateLive')
    def test_prepare_import_files__is_successful(self, mock_update_live, mock_teardown_list_append, mock_add_error):
        expected_num_mo_changes = 20
        self.flow.prepare_import_files(self.nodes, self.user, expected_num_mo_changes)
        self.assertEqual(mock_update_live.call_count, 4)
        self.assertEqual(mock_teardown_list_append.call_count, 4)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_lists',
           return_value=[4, []])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    def test_import_lists__is_successful(self, mock_set_default_values, mock_add_error, mock_debug, *_):
        expected_num_mo_changes = 20
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        self.flow.import_lists(self.nodes, self.user, expected_num_mo_changes, import_default_jobs, import_changes_jobs,
                               expected_job_count=3)
        self.assertFalse(mock_set_default_values.called)
        self.assertFalse(mock_debug.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_lists',
           return_value=[4, [Exception()]])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    def test_import_lists__error(self, mock_set_default_values, mock_add_error, mock_debug, *_):
        expected_num_mo_changes = 20
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        self.flow.import_lists(self.nodes, self.user, expected_num_mo_changes, import_default_jobs, import_changes_jobs,
                               expected_job_count=3)
        self.assertTrue(mock_set_default_values.called)
        self.assertEquals(2, mock_debug.call_count)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.create_list_of_imports',
           return_value=[1, [Exception(), Exception()]])
    def test_prepare_import_lists__un_successful(self, _):
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        self.flow.prepare_import_lists(import_default_jobs, import_changes_jobs, job_count=1,
                                       import_error_list=[], expected_job_count=0)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.create_list_of_imports',
           return_value=[1, [Exception(), Exception()]])
    def test_prepare_import_lists__successful(self, _):
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        self.flow.prepare_import_lists(import_default_jobs, import_changes_jobs, job_count=1,
                                       import_error_list=[], expected_job_count=1)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_lists',
           return_value=[3, []])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    def test_import_lists__successful(self, mock_set_default_values, mock_add_error, mock_debug, *_):
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", True)
        expected_num_mo_changes = 20
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        self.flow.import_lists(self.nodes, self.user, expected_num_mo_changes, import_default_jobs, import_changes_jobs,
                               expected_job_count=1)
        self.assertFalse(mock_set_default_values.called)
        self.assertFalse(mock_debug.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.datetime.timedelta',
           return_value=(datetime.timedelta(seconds=1)))
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_lists',
           return_value=[3, [Exception()]])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    def test_import_lists__import_error(self, mock_set_default_values, mock_add_error, mock_debug, *_):
        expected_num_mo_changes = 20
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", True)
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        for job in import_changes_jobs:
            job.create_over_nbi.side_effect = Exception
        self.flow.import_lists(self.nodes, self.user, expected_num_mo_changes, import_default_jobs,
                               import_changes_jobs)
        self.assertTrue(mock_set_default_values.called)
        self.assertEquals(2, mock_debug.call_count)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.datetime.timedelta',
           return_value=(datetime.timedelta(seconds=0)))
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_lists',
           return_value=[20, ["error"]])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.EnmApplicationError')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    def test_import_lists__timeout_error(self, mock_set_default_values, mock_add_error, mock_enmapplicationerror, mock_debug, *_):
        expected_num_mo_changes = 20
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", True)
        import_default_jobs = [Mock(), Mock()]
        import_changes_jobs = [Mock(), Mock()]
        for job in import_changes_jobs:
            job.create_over_nbi.side_effect = Exception
        self.flow.import_lists(self.nodes, self.user, expected_num_mo_changes, import_default_jobs,
                               import_changes_jobs)
        mock_add_error.assert_called_with(mock_enmapplicationerror(
            '{0} minute iteration has timed out before all jobs were successfully imported: '
            '{1} jobs completed out of 100'.format(self.flow.ITERATION_TIMEOUT / 60, 1)))
        self.assertTrue(mock_set_default_values.called)
        self.assertEqual(2, mock_debug.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.fetch_pib_parameter_value')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.setup_flow')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.import_lists')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    def test_execute_flow__adds_error(self, mock_add_error, mock_prepare_files, mock_import_lists, mock_setup, *_):
        mock_prepare_files.return_value = [], []
        self.user.open_session.side_effect = Exception
        mock_setup_object = mock_setup.return_value
        mock_setup_object.user = self.user
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)
        self.assertFalse(mock_import_lists.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.fetch_pib_parameter_value')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.import_lists')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.setup_flow')
    def test_execute_flow__is_successful(self, mock_setup_flow, mock_set_default, mock_prepare_files,
                                         mock_import_lists, mock_sleep, *_):
        mock_prepare_files.return_value = [], []
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", [""])
        self.flow.execute_flow()
        self.assertTrue(mock_setup_flow.called)
        self.assertTrue(mock_set_default.called)
        self.assertTrue(mock_prepare_files.called)
        self.assertEqual(mock_import_lists.call_count, 1)
        self.assertEqual(1, mock_sleep.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.fetch_pib_parameter_value')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.import_lists')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.prepare_import_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.set_default_values')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.setup_flow')
    def test_execute_flow__no_attr(self, mock_setup_flow, mock_set_default, mock_prepare_files,
                                   mock_import_lists, mock_sleep, *_):
        mock_prepare_files.return_value = [], []
        setattr(self.flow, "SCHEDULED_TIMES_STRINGS", [""])
        delattr(self.flow, "POSTGRES_RETENTION_TIME_DAYS")
        self.flow.execute_flow()
        self.assertTrue(mock_setup_flow.called)
        self.assertTrue(mock_set_default.called)
        self.assertTrue(mock_prepare_files.called)
        self.assertEqual(mock_import_lists.call_count, 1)
        self.assertEqual(1, mock_sleep.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.time.sleep', return_value=0)
    def test_create_list_of_imports__success(self, _):
        import_job = Mock()
        import_job.name = "Name"
        imports_list = [import_job]
        self.flow.create_list_of_imports(imports_list, 3, [])
        self.assertEqual(1, import_job.create_over_nbi.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    def test_create_list_of_imports__value_error(self, mock_add_error, _):
        import_job = Mock()
        import_job.name = "Name"
        import_job.create_over_nbi.side_effect = ValueError("No JSON could be decoded.")
        imports_list = [import_job]
        _, error_list = self.flow.create_list_of_imports(imports_list, 3, [])
        self.assertIn("EnmApplicationError", str(mock_add_error.call_args_list[0]))
        self.assertEqual(1, len(error_list))
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow.CmImport13Flow.add_error_as_exception')
    def test_create_list_of_imports__exception(self, mock_add_error, _):
        import_job = Mock()
        import_job.name = "Name"
        import_job.create_over_nbi.side_effect = Exception("Error.")
        imports_list = [import_job]
        _, error_list = self.flow.create_list_of_imports(imports_list, 3, [])
        self.assertEqual(1, len(error_list))
        self.assertEqual(1, mock_add_error.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
