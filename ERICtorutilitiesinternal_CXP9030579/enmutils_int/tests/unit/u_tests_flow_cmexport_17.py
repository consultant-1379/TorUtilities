#!/usr/bin/env python
from datetime import datetime

import unittest2
from mock import Mock, patch
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow import CmExport17
from testslib import unit_test_utils


class CmExport17UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = CmExport17()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['Cmedit_Operator', 'CM_REST_Administrator']
        self.flow.FILE_RETENTION_TIME = 30 * 60
        self.flow.SCHEDULE_SLEEP = 15 * 60
        response = Mock()
        response.http_response_code.return_value = 200
        response.has_files.return_value = True
        self.response = response

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.sleep')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.download_files_over_cli')
    @ patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.download_files_over_nbi')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.create_profile_users')
    def test_execute_flow_is_successful(self, mock_create_profile_users, mock_download_nbi, mock_download_cli,
                                        mock_remove_local_files_over_certain_age, *_):
        mock_create_profile_users.return_value = [self.user]
        self.user.enm_execute.return_value = self.response
        self.flow.execute_flow()
        self.assertEqual(mock_download_nbi.call_count, 1)
        self.assertEqual(mock_download_cli.call_count, 1)
        self.assertEqual(mock_remove_local_files_over_certain_age.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli__is_successful(self, mock_get_job_ids):
        mock_get_job_ids.return_value = ["101"]
        self.response.http_response_code.return_value = 200
        self.user.enm_execute.return_value = self.response
        self.flow.download_files_over_cli(self.user)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli_adds_error_as_exception(self, mock_get_job_ids, mock_add_error_as_exception, *_):
        mock_get_job_ids.return_value = ["101"]
        self.response.http_response_code.return_value = 500
        self.user.enm_execute.return_value = self.response
        self.flow.download_files_over_cli(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli__no_job_ids_is_successful(self, mock_get_job_ids):
        mock_get_job_ids.return_value = []
        self.flow.download_files_over_cli(self.user)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli_has_no_files_to_download(self, mock_get_job_ids, mock_debug):
        mock_get_job_ids.return_value = []
        self.flow.download_files_over_cli(self.user)
        mock_debug.assert_called_with('No CMExports completed via CLI in the last 15 minutes. Nothing to download.')

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli_adds_script_engine_error(self, mock_get_job_ids, mock_add_error_as_exception, *_):

        mock_get_job_ids.return_value = ['1']
        self.response.http_response_code.return_value = 500
        self.user.enm_execute.return_value = self.response
        self.flow.download_files_over_cli(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_job_ids')
    def test_download_files_over_cli__get_job_ids_failure(self, mock_get_job_ids, mock_add_error_as_exception, *_):
        mock_get_job_ids.side_effect = Exception("Error")
        self.flow.download_files_over_cli(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_nbi_job_ids_in_last_fifteen_'
           'mins', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    def test_download_files_over_nbi_response_adds_error_as_exception(self, mock_add_error_as_exception, *_):
        self.flow.download_files_over_nbi(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.get_download_file')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_nbi_job_ids_in_last_fifteen'
           '_mins')
    def test_download_files_over_nbi_is_successful(self, mock_get_nbi_job_ids,
                                                   mock_get_download_file, *_):
        mock_file = Mock()
        mock_get_nbi_job_ids.return_value = ["101", '211']
        mock_get_download_file.return_value = [mock_file]
        self.flow.download_files_over_nbi(self.user)
        self.assertEqual(mock_get_download_file.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.get_download_file', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_nbi_job_ids_in_last_fifteen'
           '_mins')
    def test_download_files_over_nbi_download_files_adds_error(self, mock_get_nbi_job_ids, mock_add_error_as_exception, *_):
        mock_get_nbi_job_ids.return_value = ["101"]
        self.flow.download_files_over_nbi(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.get_nbi_job_ids_in_last_fifteen'
           '_mins')
    def test_download_export_files_has_no_files_to_download(self, mock_get_nbi_job_ids, mock_debug):
        mock_get_nbi_job_ids.return_value = []
        self.flow.download_files_over_nbi(self.user)
        mock_debug.assert_called_with('No CMExports completed via NBI in the last 15 minutes. Nothing to download.')

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_job_ids_is_successful(self, mock_datetime):
        self.response.get_output.return_value = [
            '12 CMEXPORT_01 COMPLETED 2019-04-04T23:55:00 2019-04-05T00:00:30 40 40']
        self.user.enm_execute.return_value = self.response
        mock_datetime.now.return_value = datetime(2019, 4, 5, 0, 10, 0)
        mock_datetime.strptime.return_value = datetime(2019, 4, 5, 0, 0, 30)

        self.assertEqual(self.flow.get_job_ids(self.user), ['12'])

    def test_get_job_ids_raises_script_engine_response_validation_error(self):
        self.response.http_response_code.return_value = 500
        self.user.enm_execute.return_value = self.response
        with self.assertRaises(ScriptEngineResponseValidationError):
            self.flow.get_job_ids(self.user)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_job_ids_no_match_with_date_time_format_returns_empty_list(self, mock_datetime):
        self.response.get_output.return_value = ['12 COMPLETED CMEXPORT_01_u0 ']
        self.user.enm_execute.return_value = self.response
        mock_datetime.now.return_value = datetime(2019, 4, 5, 14, 5, 0)
        self.assertEqual(self.flow.get_job_ids(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_job_ids_no_id_match_returns_empty_list(self, mock_datetime):
        self.response.get_output.return_value = ['- CMEXPORT_01 COMPLETED 2019-04-05T10:04:00 2019-04-05T10:05:30']
        self.user.enm_execute.return_value = self.response
        mock_datetime.now.return_value = datetime(2019, 4, 5, 10, 15, 0)
        mock_datetime.strptime.return_value = datetime(2019, 4, 5, 10, 5, 30)
        self.assertEqual(self.flow.get_job_ids(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_job_ids_no_cli_profile_name_match_returns_empty_list(self, mock_datetime):
        self.response.get_output.return_value = ['1 CMEXPORT_12 COMPLETED 2019-04-05T10:04:00 2019-04-05T10:05:30']
        self.user.enm_execute.return_value = self.response
        mock_datetime.now.return_value = datetime(2019, 4, 5, 10, 15, 0)
        mock_datetime.strptime.return_value = datetime(2019, 4, 5, 10, 5, 30)
        self.assertEqual(self.flow.get_job_ids(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_nbi_job_ids_in_last_fifteen_mins_is_successful(self, mock_datetime, *_):
        get_all_jobs = Mock()
        get_all_jobs.json.return_value = {'jobs': [
            {'id': 202,
             'endTime': '2019-06-20T09:12:00.000',
             'status': 'COMPLETED',
             'jobName': 'cmexport_03'}]}
        self.user.get.return_value = get_all_jobs
        mock_datetime.now.return_value = datetime(2019, 6, 20, 9, 15, 0)
        mock_datetime.strptime.return_value = datetime(2019, 6, 20, 9, 12, 30)
        self.assertEqual(self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user), [202])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_nbi_job_ids_in_last_fifteen_mins__returns_empty_list_job_not_completed(self, mock_datetime, *_):
        get_all_jobs = Mock()
        get_all_jobs.json.return_value = {'jobs': [
            {'id': 202,
             'endTime': ' ',
             'status': 'IN PROGRESS',
             'jobName': 'cmexport_12'}]}
        self.user.get.return_value = get_all_jobs
        mock_datetime.now.return_value = datetime(2019, 6, 20, 9, 15, 0)
        self.assertEqual(self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_nbi_job_ids_in_last_fifteen_mins_returns_empty_list_job_name_not_nbi_profile(self, mock_datetime, *_):
        get_all_jobs = Mock()
        get_all_jobs.json.return_value = {'jobs': [
            {'id': 202,
             'endTime': ' ',
             'status': 'COMPLETED',
             'jobName': 'cmexport_01'}]}
        self.user.get.return_value = get_all_jobs
        mock_datetime.now.return_value = datetime(2019, 6, 20, 9, 15, 0)
        self.assertEqual(self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    def test_get_nbi_job_ids_in_last_fifteen_mins__returns_empty_list_eniq_in_job_name(self, mock_datetime, *_):
        get_all_jobs = Mock()
        get_all_jobs.json.return_value = {'jobs': [
            {'id': 202,
             'endTime': '2019-06-20T09:12:00.000',
             'status': 'COMPLETED',
             'jobName': 'ENIQ_CMEXPORT_12'}]}
        self.user.get.return_value = get_all_jobs
        mock_datetime.now.return_value = datetime(2019, 6, 20, 9, 15, 0)
        mock_datetime.strptime.return_value = datetime(2019, 6, 20, 9, 12, 30)
        self.assertEqual(self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user), [])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.log.logger.debug')
    def test_get_nbi_job_ids_in_last_fifteen_mins__has_no_jobs(self, mock_debug, *_):
        get_all_jobs = Mock()
        get_all_jobs.json.return_value = {'jobs': []}
        self.user.get.return_value = get_all_jobs
        self.assertEqual(self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user), None)
        mock_debug.assert_called_with("There are no CMExport over NBI jobs. Nothing to download")

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17._get_nbi_job_ids')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    def test_get_nbi_job_ids_in_last_fifteen_mins__adds_error_as_exception(self, mock_add_error_as_exception, *_):
        self.user.get.side_effect = Exception
        self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.raise_for_status',
           side_effect=HTTPError("Error"))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow.CmExport17.add_error_as_exception')
    def test_get_nbi_job_ids_in_last_fifteen_mins__adds_error_as_exception_request_exception(
            self, mock_add_error_as_exception, _):
        self.user.get.return_value = Mock()
        self.flow.get_nbi_job_ids_in_last_fifteen_mins(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
