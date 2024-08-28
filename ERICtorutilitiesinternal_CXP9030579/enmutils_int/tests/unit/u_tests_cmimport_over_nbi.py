#!/usr/bin/env python
import unittest2
from mock import Mock, patch, mock_open
from testslib import unit_test_utils
from requests.exceptions import HTTPError
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import (TimeOutError, EnmApplicationError, FileDoesNotExist, RemoveUndoConfigFilesError,
                                     RemoveUndoJobError)
from enmutils_int.lib.cm_import import CmImportLive, CmImportOverNbiV2
from enmutils_int.lib.cm_import_over_nbi import UndoOverNbi, ValidationWarning


class CmImportOverNbiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = User(username='import_test_user')
        self.nodes = unit_test_utils.get_nodes(2)
        self.import_nbi_job = CmImportLive(
            name='import_nbi_job',
            user=self.user,
            nodes=self.nodes,
            template_name='import_nbi_job.xml',
            flow='live_config',
            file_type='3GPP',
            interface='NBIv1',
            expected_num_mo_changes=1
        )

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_is_successful(self, mock_post, *_):
        post_request_body = {
            'type': 'IMPORT',
            'fileName': self.import_nbi_job.template_name,
            'configName': 'Live',
            'fileFormat': '3GPP',
        }
        mock_post.return_value = Mock()
        setattr(mock_post.return_value, 'status_code', 201)
        self.import_nbi_job.create_import_over_nbi(post_endpoint='mock_endpoint')
        mock_post.assert_called_with('mock_endpoint', json=post_request_body, headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_is_successful_on__interface_version_2(self, mock_post, *_):
        post_request_body = {
            'type': 'IMPORT',
            'fileName': self.import_nbi_job.template_name,
            'configName': 'Live',
            'fileFormat': '3GPP',
            'executionPolicy': ['stop-on-error']
        }
        self.import_nbi_job.interface = 'NBIv2'
        self.import_nbi_job.create_import_over_nbi(post_endpoint='mock_endpoint')
        mock_post.assert_called_with('mock_endpoint', json=post_request_body,
                                     headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_log_error(self, mock_post, *_):
        post_request_body = {
            'type': 'IMPORT',
            'fileName': self.import_nbi_job.template_name,
            'configName': 'Live',
            'fileFormat': '3GPP',
        }
        mock_post.return_value = Mock()
        setattr(mock_post.return_value, 'status_code', 500)
        self.import_nbi_job.create_import_over_nbi(post_endpoint='mock_endpoint')
        mock_post.assert_called_with('mock_endpoint', json=post_request_body,
                                     headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_error_handling_as_list(self, mock_post, *_):
        post_request_body = {
            'type': 'IMPORT',
            'fileName': self.import_nbi_job.template_name,
            'configName': 'Live',
            'fileFormat': '3GPP',
            'executionPolicy': ['continue-on-error-node', 'parallel']
        }
        self.import_nbi_job.interface = 'NBIv2'
        self.import_nbi_job.error_handling = ['continue-on-error-node', 'parallel']
        self.import_nbi_job.create_import_over_nbi(post_endpoint='mock_endpoint')
        mock_post.assert_called_with('mock_endpoint', json=post_request_body,
                                     headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_with_file_is_successful(self, mock_post, *_):
        post_request_body = {
            'type': 'IMPORT',
            'fileName': 'tmp_cmimport_00',
            'configName': 'Live',
            'fileFormat': 'dynamic',
        }
        self.import_nbi_job.create_import_over_nbi(post_endpoint='mock_endpoint', file_in='tmp/cmimport_00')
        mock_post.assert_called_with('mock_endpoint', json=post_request_body, headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_raises_http_error(self, mock_post, *_):
        mock_post.return_value = HTTPError
        self.assertRaises(HTTPError, self.import_nbi_job.create_import_over_nbi, post_endpoint='mock_endpoint')


class CmImportOverNbiV2UnitTests(CmImportOverNbiUnitTests):

    def setUp(self):

        super(CmImportOverNbiV2UnitTests, self).setUp()

        self.import_live_nbi_v2_job = CmImportLive(
            name='nbi_v2',
            user=self.user,
            nodes=self.nodes,
            template_name='test_example',
            flow='live_config',
            file_type='3GPP',
            interface='NBIv2',
            expected_num_mo_changes=1,

        )

    def tearDown(self):

        super(CmImportOverNbiV2UnitTests, self).tearDown()
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.add_file_to_import_job')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbi.create_import_over_nbi')
    def test_create_import_over_nbi_v2_success(self, mock_create, mock_add, *_):
        self.import_live_nbi_v2_job.create_import_over_nbi_v2()
        mock_create.assert_called_with('/bulk-configuration/v1/import-jobs/jobs', None)
        self.assertTrue(mock_add.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbi.create_import_over_nbi')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.add_file_to_import_job')
    def test_create_import_over_nbi_v2_success_with_file_in(self, mock_add, mock_create, *_):
        file_in = '/tmp/wl_storage/profile_undo_configs/undo_over_nbi/PZundo177.txt'
        self.import_live_nbi_v2_job.create_import_over_nbi_v2(file_in=file_in)
        mock_create.assert_called_with('/bulk-configuration/v1/import-jobs/jobs', file_in)
        self.assertTrue(mock_add.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_import_over_nbi_v2_http_error(self, mock_post, _):
        mock_post.return_value = HTTPError
        self.assertRaises(HTTPError, self.import_live_nbi_v2_job.create_import_over_nbi_v2)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.validation_flow')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_add_file_to_import_job_success(self, mock_post, mock_validation_flow, *_):
        self.import_live_nbi_v2_job.id = 316
        mock_open_file = mock_open()
        file_body = {
            'file': (None, mock_open_file()),
            'filename': (None, 'test_example')
        }
        with patch('__builtin__.open', mock_open_file):
            self.import_live_nbi_v2_job.add_file_to_import_job()
        mock_post.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316/files', files=file_body)
        self.assertTrue(mock_validation_flow.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.validation_flow')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_add_file_to_import_job_with_file_in_success(self, mock_post, mock_validation_flow, *_):
        self.import_live_nbi_v2_job.id = 316
        file_in = '/tmp/wl_storage/profile_undo_configs/undo_over_nbi/PZundo177.txt'
        mock_open_file = mock_open()
        file_body = {
            'file': (None, mock_open_file()),
            'filename': (None, '_tmp_wl_storage_profile_undo_configs_undo_over_nbi_PZundo177.txt')
        }
        with patch('__builtin__.open', mock_open_file):
            self.import_live_nbi_v2_job.add_file_to_import_job(file_in=file_in)
        mock_post.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316/files', files=file_body)
        self.assertTrue(mock_validation_flow.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.validation_flow', side_effect=ValidationWarning)
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_add_file_to_import_job__skips_history_check_if_validation_warning(self, mock_post, *_):
        self.import_live_nbi_v2_job.id = 316
        self.import_live_nbi_v2_job.skip_history_check = False
        mock_open_file = mock_open()
        file_body = {
            'file': (None, mock_open_file()),
            'filename': (None, 'test_example')
        }
        with patch('__builtin__.open', mock_open_file):
            self.import_live_nbi_v2_job.add_file_to_import_job()
        mock_post.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316/files', files=file_body)
        self.assertTrue(self.import_live_nbi_v2_job.skip_history_check)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_add_file_to_import_job_raises_http_error(self, mock_post, *_):
        with patch('__builtin__.open', mock_open()):
            mock_post.return_value = HTTPError
            self.assertRaises(HTTPError, self.import_live_nbi_v2_job.add_file_to_import_job)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.no_valid_operations', return_value=False)
    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.execution_flow')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.poll_until_flow_is_complete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_validation_flow_is_successful(self, mock_post, mock_poll_until_flow_is_complete, mock_execution_flow, *_):
        self.import_live_nbi_v2_job.id = 316
        validate_json = {'invocationFlow': 'validate'}
        self.import_live_nbi_v2_job.validation_flow()
        mock_post.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316/invocations', json=validate_json,
                                     headers={'Content-Type': 'application/json'})
        mock_poll_until_flow_is_complete.assert_called_with(end_status='VALIDATED')
        self.assertTrue(mock_execution_flow.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.no_valid_operations', return_value=1)
    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.execution_flow')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.poll_until_flow_is_complete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_validation_flow_raises_http_error(self, mock_post, mock_poll_until_flow_is_complete, mock_execution_flow, *_):
        mock_post.return_value = HTTPError
        self.assertRaises(HTTPError, self.import_live_nbi_v2_job.validation_flow)
        self.assertFalse(mock_execution_flow.called)
        self.assertFalse(mock_poll_until_flow_is_complete.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.no_valid_operations', return_value=True)
    @patch('enmutils.lib.enm_user_2.User.post')
    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=None)
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.execution_flow')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.poll_until_flow_is_complete')
    def test_validation_flow__raises_validation_warning_if_no_valid_operations(self, mock_poll_until_flow_is_complete,
                                                                               mock_execution_flow, *_):
        self.assertRaises(ValidationWarning, self.import_live_nbi_v2_job.validation_flow)
        self.assertFalse(mock_execution_flow.called)
        self.assertTrue(mock_poll_until_flow_is_complete.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.poll_until_flow_is_complete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_execution_flow_is_successful(self, mock_post, mock_poll_until_flow_is_complete, *_):
        self.import_live_nbi_v2_job.id = 316
        execute_json = {'invocationFlow': 'execute'}
        self.import_live_nbi_v2_job.execution_flow()
        mock_post.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316/invocations', json=execute_json,
                                     headers={'Content-Type': 'application/json'})
        mock_poll_until_flow_is_complete.assert_called_with(end_status='EXECUTED')

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.poll_until_flow_is_complete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_execution_flow_raises_http_error(self, mock_post, mock_poll_until_flow_is_complete, *_):
        mock_post.return_value = HTTPError
        self.assertRaises(HTTPError, self.import_live_nbi_v2_job.execution_flow)
        self.assertFalse(mock_poll_until_flow_is_complete.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_is_successful(self, mock_get_import_job_by_id):
        json_response_validate_success = {
            "id": 255,
            "name": "1503580499822_cm_import_11_default_values.xml",
            "status": "VALIDATED",
            "configuration": "Live",
            'executionPolicy': 'stop-on-error'
        }

        mock_get_import_job_by_id.return_value = json_response_validate_success

        try:
            self.import_live_nbi_v2_job.poll_until_flow_is_complete(end_status='VALIDATED')
        except Exception:
            self.fail('Test should fail if error is encountered')

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_detects_cmimport_13(self, mock_get_import_job_by_id, mock_sleep):
        json_response_get_status_timeout_error = {
            "id": 255,
            "name": "1503580499822_cm_import_13_default_values.xml",
            "status": "VALIDATING",
            "configuration": "Live",
        }

        mock_get_import_job_by_id.return_value = json_response_get_status_timeout_error
        self.import_live_nbi_v2_job.timeout = 0.01
        self.import_live_nbi_v2_job.name = "cmimport_13"
        with self.assertRaises(TimeOutError):
            self.import_live_nbi_v2_job.poll_until_flow_is_complete(end_status='EXECUTED')
        mock_sleep.assert_called_with(0.5)

    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_raises_enm_application_error(self, mock_get_import_job_by_id):
        json_response_execute_failure = {
            "id": '255',
            "name": "1503580499822_cm_import_22_default_values.xml",
            "status": "EXECUTED",
            "configuration": "Live",
            "failureReason": "Error 7025 : Schema validation failed."
        }
        mock_get_import_job_by_id.return_value = json_response_execute_failure
        with self.assertRaises(EnmApplicationError):
            self.import_live_nbi_v2_job.poll_until_flow_is_complete(end_status='EXECUTED')

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_raises_timeout_error(self, mock_get_import_job_by_id, *_):
        json_response_get_status_timeout_error = {
            "id": 255,
            "name": "1503580499822_cm_import_11_default_values.xml",
            "status": "VALIDATING",
            "configuration": "Live",
        }

        mock_get_import_job_by_id.return_value = json_response_get_status_timeout_error
        self.import_live_nbi_v2_job.timeout = 0.00001
        with self.assertRaises(TimeOutError):
            self.import_live_nbi_v2_job.poll_until_flow_is_complete(end_status='EXECUTED')

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_import_job_by_id_is_successful(self, mock_get, *_):
        self.import_live_nbi_v2_job.id = 316
        self.import_live_nbi_v2_job.get_import_job_by_id()
        mock_get.assert_called_with('/bulk-configuration/v1/import-jobs/jobs/316',
                                    headers={'Content-Type': 'application/json'})

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.get', return_value=HTTPError)
    def test_get_import_job_by_id_raises_http_error(self, *_):
        with self.assertRaises(HTTPError):
            self.import_live_nbi_v2_job.get_import_job_by_id()

    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_summary_by_id')
    def test_no_valid_operations(self, mock_get_job):
        mock_get_job.return_value = {
            "id": 87323,
            "name": "Test",
            "summary": {
                "total": {
                    "type": "total",
                    "parsed": 1,
                    "valid": 0,
                    "invalid": 1,
                    "executed": 0,
                    "executionErrors": 0
                },
                "delete": {
                    "type": "delete",
                    "parsed": 1,
                    "valid": 0,
                    "invalid": 1,
                    "executed": 0,
                    "executionErrors": 0
                }
            }
        }
        self.assertEqual(True, self.import_live_nbi_v2_job.no_valid_operations())

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_summary_by_id')
    def test_no_valid_operations_attribute_error(self, mock_get_job, mock_debug):
        mock_get_job.return_value = {
            "id": 87323,
            "name": "Test",
            "summary": {
            }
        }
        self.assertEqual(False, self.import_live_nbi_v2_job.no_valid_operations())
        msg = ("Failed to retrieve valid operations from response: [{0}].\nFlow will continue and attempt operations."
               .format(mock_get_job.return_value))
        mock_debug.assert_called_with(msg)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_summary_by_id',
           side_effect=HTTPError("Error"))
    def test_no_valid_operations_http_error(self, *_):
        self.assertEqual(False, self.import_live_nbi_v2_job.no_valid_operations())

    def test_get_import_job_summary_by_id(self):
        user = Mock()
        response = Mock()
        response.status_code = 200
        user.get.return_value = response
        self.import_live_nbi_v2_job.user = user
        self.import_live_nbi_v2_job.get_import_job_summary_by_id()

    @patch('enmutils.lib.enm_user_2.build_user_message', return_value="error")
    def test_get_import_job_summary_by_id_raises_http_error(self, _):
        user = Mock()
        response = Mock()
        response.status_code = 504
        user.get.return_value = response
        self.import_live_nbi_v2_job.user = user
        self.assertRaises(HTTPError, self.import_live_nbi_v2_job.get_import_job_summary_by_id)


class CmImportOverNbiV1UnitTests(CmImportOverNbiUnitTests):

    def setUp(self):

        super(CmImportOverNbiV1UnitTests, self).setUp()
        self.import_live_nbi_v1_job = CmImportLive(
            name='nbi_v1',
            user=self.user,
            nodes=self.nodes,
            template_name='test_example',
            flow='live_config',
            file_type='dynamic',
            interface='NBIv1',
            expected_num_mo_changes=1
        )

    def tearDown(self):

        super(CmImportOverNbiV1UnitTests, self).tearDown()
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.add_file_to_import_job_v1')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbi.create_import_over_nbi')
    def test_create_import_over_nbi_v1_success(self, mock_create, mock_add, *_):
        self.import_live_nbi_v1_job.create_import_over_nbi_v1()
        mock_create.assert_called_with('/bulk/import/jobs', None)
        self.assertTrue(mock_add.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.add_file_to_import_job_v1')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbi.create_import_over_nbi')
    def test_create_import_over_nbi_v1_with_file_in_is_successful(self, mock_create, mock_add, *_):
        file_in = '/tmp/wl_storage/profile_undo_configs/undo_over_nbi/PZundo177.txt'
        self.import_live_nbi_v1_job.create_import_over_nbi_v1(file_in=file_in)
        mock_create.assert_called_with('/bulk/import/jobs', file_in)
        self.assertTrue(mock_add.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.add_file_to_import_job_v1')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbi.create_import_over_nbi', side_effect=HTTPError)
    def test_create_import_over_nbi_v1_raises_http_error(self, mock_create, mock_add, *_):
        self.assertRaises(HTTPError, self.import_live_nbi_v1_job.create_import_over_nbi_v1)
        self.assertFalse(mock_add.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.poll_until_completed')
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_add_file_to_import_is_successful(self, mock_put, mock_poll, *_):
        file_uri = '/bulk/import/jobs/Live/3GPP/test_example/true/STOP/default'
        with patch('__builtin__.open', mock_open()):
            self.import_live_nbi_v1_job.add_file_to_import_job_v1(file_uri)
        self.assertTrue(mock_put.called)
        self.assertTrue(mock_poll.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_add_file_to_import_raises_http_error(self, mock_put, *_):
        file_uri = '/bulk/import/jobs/Live/3GPP/test_example/true/STOP/default'
        with patch('__builtin__.open', mock_open()):
            mock_put.return_value = HTTPError
            self.assertRaises(HTTPError, self.import_live_nbi_v1_job.add_file_to_import_job_v1, file_uri)

    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.get_job_details_by_id')
    def test_poll_until_completed_is_successful(self, mock_get_job_details_by_id):
        json_response_get_job_details_success = {
            "id": 255,
            "status": "COMPLETED",
            "statusReason": "COMPLETED"
        }
        mock_get_job_details_by_id.return_value = json_response_get_job_details_success
        try:
            self.import_live_nbi_v1_job.poll_until_completed(255)
        except Exception:
            self.fail('Test should fail if error is encountered')

    @patch('enmutils_int.lib.cm_import_over_nbi.get_download_job_details_by_id')
    def test_poll_until_completed_when_undo_is_true_success(self, mock_get_download_job_details_by_id):
        json_response_get_job_details_success = {
            "id": 255,
            "status": "COMPLETED",
            "statusReason": "COMPLETED"
        }
        mock_get_download_job_details_by_id.return_value = json_response_get_job_details_success
        try:
            self.import_live_nbi_v1_job.poll_until_completed(255, undo=True)
        except Exception:
            self.fail('Test should fail if error is encountered')
        self.assertTrue(mock_get_download_job_details_by_id.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.get_job_details_by_id')
    def test_poll_until_completed_raises_enm_application_error(self, mock_get_job_details_by_id):
        json_response_get_job_details_failure = {
            "id": 255,
            "status": "FAILED",
            "statusReason": "Error 7042 : There are validation failures. Please consult the description of the errors reported in the import verbose job status.",
        }

        mock_get_job_details_by_id.return_value = json_response_get_job_details_failure
        self.assertRaises(EnmApplicationError, self.import_live_nbi_v1_job.poll_until_completed, 255)

    @patch('time.sleep')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV1.get_job_details_by_id')
    def test_poll_until_completed_raises_timeout_error(self, mock_get_job_details_by_id, *_):
        json_response_get_job_details_timeout = {
            "id": 255,
            "status": "IN PROGRESS"
        }

        mock_get_job_details_by_id.return_value = json_response_get_job_details_timeout
        self.import_live_nbi_v1_job.timeout = 0.001
        with self.assertRaises(TimeOutError):
            self.import_live_nbi_v1_job.poll_until_completed(255)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_job_details_by_id_success(self, mock_get, *_):
        self.import_live_nbi_v1_job.id = 255
        self.import_live_nbi_v1_job.get_job_details_by_id(self.import_live_nbi_v1_job.id)
        mock_get.assert_called_with('/bulk/import/jobs/255')

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils.lib.enm_user_2.User.get', return_value=HTTPError)
    def test_get_import_job_by_id_raises_http_error(self, *_):
        self.assertRaises(HTTPError, self.import_live_nbi_v1_job.get_job_details_by_id, 255)

    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_success(self, mock_get_job, mock_debug):
        nbiv2_import = CmImportOverNbiV2()
        nbiv2_import.timeout = 120
        nbiv2_import.id = 1234
        nbiv2_import.name = "cm_import_12"
        nbiv2_import.continue_on_operation_errors = False
        mock_get_job.return_value = {"status": "COMPLETED", "failureReason": []}
        nbiv2_import.poll_until_flow_is_complete("COMPLETED")
        mock_debug.assert_called_with('Job 1234 has COMPLETED successfully')

    @patch('time.sleep', return_value=0)
    @patch('datetime.timedelta')
    @patch('datetime.datetime')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_does_not_raise_enm_error_if_continue_on_op(self, mock_get_job, mock_datetime,
                                                                                    mock_timedelta, *_):
        nbiv2_import = CmImportOverNbiV2()
        nbiv2_import.timeout = 1
        nbiv2_import.id = 1234
        mock_timedelta.return_value = 1
        nbiv2_import.name = "cm_import_12"
        nbiv2_import.continue_on_operation_errors = True
        mock_datetime.now.side_effect = [0, 0, 1]
        mock_get_job.return_value = {"status": "VALIDATING", "failureReason": ["Error"]}
        self.assertRaises(TimeOutError, nbiv2_import.poll_until_flow_is_complete, "COMPLETED")

    @patch('time.sleep', return_value=0)
    @patch('datetime.timedelta')
    @patch('datetime.datetime')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_does_not_raise_enm_error_if_continue_on_op_import_13(self, mock_get_job,
                                                                                              mock_datetime,
                                                                                              mock_timedelta, *_):
        nbiv2_import = CmImportOverNbiV2()
        nbiv2_import.timeout = 1
        nbiv2_import.id = 1234
        mock_timedelta.return_value = 1
        nbiv2_import.name = "cm_import_13"
        nbiv2_import.continue_on_operation_errors = True
        mock_datetime.now.side_effect = [0, 0, 1]
        mock_get_job.return_value = {"status": "VALIDATING", "failureReason": ["Error"]}
        self.assertRaises(TimeOutError, nbiv2_import.poll_until_flow_is_complete, "COMPLETED")

    @patch('time.sleep', return_value=0)
    @patch('datetime.timedelta', return_value=0)
    @patch('datetime.datetime')
    @patch('enmutils_int.lib.cm_import_over_nbi.CmImportOverNbiV2.get_import_job_by_id')
    def test_poll_until_flow_is_complete_raises_enm_error_if_continue_on_op(self, mock_get_job, mock_datetime,
                                                                            mock_timedelta, *_):
        nbiv2_import = CmImportOverNbiV2()
        nbiv2_import.timeout = 1
        nbiv2_import.id = 1234
        mock_timedelta.return_value = 1
        nbiv2_import.name = "cm_import_12"
        nbiv2_import.continue_on_operation_errors = False
        mock_datetime.now.side_effect = [0, 0, 1]
        mock_get_job.return_value = {"status": "FAILED", "failureReason": ["Error"]}
        self.assertRaises(EnmApplicationError, nbiv2_import.poll_until_flow_is_complete, "COMPLETED")


class UndoOverNbiUnitTests(CmImportOverNbiUnitTests):

    def setUp(self):
        super(UndoOverNbiUnitTests, self).setUp()
        self.undo_import_job = UndoOverNbi(
            name='undo_over_nbi',
            user=self.user,
            file_type='dynamic',
        )

    def tearDown(self):
        super(UndoOverNbiUnitTests, self).tearDown()
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status')
    @patch('enmutils_int.lib.cm_import_over_nbi.get_download_file', return_value=("file", "Content"))
    @patch('enmutils_int.lib.cm_import_over_nbi.UndoOverNbi.poll_until_completed')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_undo_job_over_nbi_is_successful(self, mock_post, mock_poll_until_completed, mock_get_download_file, *_):
        self.undo_import_job.undo_job_over_nbi(id_of_job_to_undo=255)
        mock_post.assert_called_with('/configuration/jobs?type=UNDO_IMPORT_TO_LIVE',
                                     headers={'Content-Type': 'application/json'},
                                     json={'id': 255, 'type': 'UNDO_IMPORT_TO_LIVE'})
        self.assertTrue(mock_poll_until_completed.called)
        self.assertTrue(mock_get_download_file.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import_over_nbi.get_download_file')
    @patch('enmutils_int.lib.cm_import_over_nbi.UndoOverNbi.poll_until_completed')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_undo_job_over_nbi_raises_http_error(self, mock_post, mock_poll_until_completed, mock_get_download_file, *_):
        mock_post.return_value = HTTPError
        with self.assertRaises(HTTPError):
            self.undo_import_job.undo_job_over_nbi(id_of_job_to_undo=255)
        self.assertFalse(mock_poll_until_completed.called)
        self.assertFalse(mock_get_download_file.called)

    @patch('enmutils_int.lib.cm_import_over_nbi.filesystem.get_files_in_directory')
    def test_get_undo_config_file_path_is_successful(self, mock_get_files):
        mock_get_files.return_value = ['/tmp/wl_storage/profile_undo_configs/undo_over_nbi/undo_2017-12-18T11-20-00_177.txt']
        self.undo_import_job.id = 177
        self.assertEqual(self.undo_import_job.get_undo_config_file_path(),
                         '/tmp/wl_storage/profile_undo_configs/undo_over_nbi/undo_2017-12-18T11-20-00_177.txt')

    @patch('enmutils.lib.filesystem.get_files_in_directory')
    def test_get_undo_config_file_path_raises_file_does_not_exist_error(self, mock_get_files):
        mock_get_files.return_value = [
            '/tmp/wl_storage/profile_undo_configs/undo_over_nbi/undo_2017-12-18T11-20-00_177.txt']
        self.undo_import_job.id = 200
        self.assertRaises(FileDoesNotExist, self.undo_import_job.get_undo_config_file_path)

    @patch('enmutils.lib.filesystem.get_files_in_directory', side_effect=Exception)
    def test_get_undo_config_file_path_raises_exception(self, _):
        self.undo_import_job.id = 177
        self.assertRaises(Exception, self.undo_import_job.get_undo_config_file_path)

    @patch('enmutils.lib.filesystem.remove_dir')
    def test_remove_undo_config_files_is_successful(self, mock_remove_dir):
        self.undo_import_job.remove_undo_config_files()
        self.assertTrue(mock_remove_dir.called)

    @patch('enmutils.lib.filesystem.remove_dir', side_effect=Exception)
    def test_remove_undo_config_files_raises_remove_undo_config_files_error(self, _):
        self.assertRaises(RemoveUndoConfigFilesError, self.undo_import_job.remove_undo_config_files)

    @patch('enmutils.lib.log.logger.debug')
    def test_remove_undo_job__is_successful(self, mock_debug):
        user = Mock()
        self.undo_import_job.remove_undo_job(user, 12)
        user.enm_execute()
        self.assertEqual(3, mock_debug.call_count)

    @patch('enmutils.lib.enm_user_2.User.enm_execute', side_effect=Exception)
    @patch('enmutils.lib.log.logger.debug')
    def test_remove_undo_job__raises_RemoveUndoJobError(self, mock_debug, _):
        self.assertRaises(RemoveUndoJobError, self.undo_import_job.remove_undo_job, "user", 12)
        self.assertEqual(2, mock_debug.call_count)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
