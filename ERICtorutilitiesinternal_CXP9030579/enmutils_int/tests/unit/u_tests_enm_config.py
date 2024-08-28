#!/usr/bin/env python
import unittest2
from enmscripting.exceptions import TimeoutException
from enmutils.lib.exceptions import (TimeOutError, ENMJobStatusError, ScriptEngineResponseValidationError,
                                     ENMJobDetailStatusError)
from enmutils_int.lib.cm_import import CmImportLive
from mock import patch, Mock
from testslib import unit_test_utils


class EnmConfigUnitTests(unittest2.TestCase):

    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        self.nodes = [Mock()] * 2
        self.import_config_job = CmImportLive(
            nodes=self.nodes,
            template_name='cm_import_03.xml',
            flow='non_live_config1',
            file_type='3GPP',
            expected_num_mo_changes=1,
            config_name='UNIT_TEST',
            user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def get_mock_response(status):
        response = Mock()
        mock_groups = Mock()
        mock_groups.return_value = (450, status, '2019-08-28T11:28:29', None, 'cm_import_03.xml', 'Live', 'CMIMPORT_03_0828-11195145_u0')
        mock_status_group = Mock()
        mock_status_group.value.return_value = status
        mock_status = Mock()
        mock_status.return_value = [mock_status_group]
        mock_groups.find_by_label.side_effect = mock_status
        response.get_output.return_value.groups.return_value = ((mock_groups,),)

        return response

    # EnmJob Tests ##########

    def test_create_sets_job_id_if_successful(self):
        self.import_config_job.user.enm_execute.return_value = Mock(
            get_output=lambda: ['job setup successful with job ID 121'])
        self.import_config_job.create(validate=False)
        self.assertEqual(self.import_config_job.id, '121')

    def test_create_raises_validation_error_if_unsuccessful(self):
        self.import_config_job.user.enm_execute.return_value = Mock(get_output=lambda: ['job setup failed to create'])
        self.assertRaises(ScriptEngineResponseValidationError, self.import_config_job.create)

    @patch('enmutils_int.lib.enm_config.EnmJob.wait_for_finish')
    def test_create_successful_when_validate_is_true(self, mock_wait_for_finish):
        response = Mock()
        response.get_output.return_value = [u'{"output":"Successfully created with job ID 121\\n","v":"2"}']
        self.import_config_job.user.enm_execute.return_value = response
        self.import_config_job.create(validate=True)
        self.assertEqual(self.import_config_job.id, '121')
        self.assertTrue(mock_wait_for_finish.called)

    def test_get_status_is_successful(self):
        response = Mock()
        response.get_output.return_value.has_groups.return_value = True
        self.user.enm_execute.return_value = response
        self.import_config_job.get_status('command')

    def test_get_status_raises_scriptengine_error(self):
        response = Mock()
        response.get_output.return_value.has_groups.return_value = False
        self.user.enm_execute.return_value = response
        with self.assertRaises(ScriptEngineResponseValidationError):
            self.import_config_job.get_status('command')

    def test_get_status_raises_timeout_exception(self):
        self.user.enm_execute.side_effect = TimeoutException
        with self.assertRaises(TimeoutException):
            self.import_config_job.get_status('command')

    @patch('enmutils_int.lib.enm_config.log.logger.debug')
    @patch('enmutils_int.lib.enm_config.EnmJob.get_status')
    def test_wait_for_finish_is_successful(self, mock_get_status, mock_debug):
        mock_get_status.return_value = self.get_mock_response(status='COMPLETED')
        self.import_config_job.wait_for_finish(detailed_validation=True)
        mock_debug.assert_called_with(
            'Job cmedit import -f file:cm_import_03.xml --filetype 3GPP -t UNIT_TEST -nc  was completed successfully')

    @patch('enmutils_int.lib.enm_config.log.logger.debug')
    @patch('enmutils_int.lib.enm_config.EnmJob.get_status')
    def test_wait_for_finish_is_successful_no_detailed_validation(self, mock_get_status, mock_debug):
        mock_get_status.return_value = self.get_mock_response(status='COMPLETED')
        self.import_config_job.wait_for_finish()
        mock_debug.assert_called_with(
            'Job cmedit import -f file:cm_import_03.xml --filetype 3GPP -t UNIT_TEST -nc  was completed successfully')

    @patch('enmutils_int.lib.enm_config.timedelta')
    @patch('enmutils_int.lib.enm_config.datetime')
    @patch('enmutils_int.lib.enm_config.time.sleep')
    @patch('enmutils_int.lib.enm_config.EnmJob.get_status')
    def test_wait_for_finish_raises_timeouterror(self, mock_get_status, mock_sleep, mock_datetime, mock_timedelta):
        mock_datetime.now.side_effect = [0, 0, 1]
        mock_timedelta.return_value = 0.001
        mock_get_status.return_value = self.get_mock_response(status='IN PROGRESS')
        with self.assertRaises(TimeOutError):
            self.import_config_job.wait_for_finish()
            self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.enm_config.EnmJob.get_status')
    def test_wait_for_finish_raises_enmjobstatuserror(self, mock_get_status):
        mock_get_status.return_value = self.get_mock_response(status='ERROR')
        with self.assertRaises(ENMJobStatusError):
            self.import_config_job.wait_for_finish()

    @patch('enmutils_int.lib.enm_config.EnmJob.get_status')
    def test_wait_for_finish_raises_enmjobdetailstatuserror(self, mock_get_status):
        response = Mock()
        mock_groups = Mock()
        mock_groups.return_value = (450, 'COMPLETED', '2019-08-28T11:28:29', None, 'cm_import_03.xml', 'Live', 'CMIMPORT_03_0828-11195145_u0')
        mock_status_group = Mock()
        mock_status_group.value.side_effect = 'COMPLETED', 'ERROR'
        mock_status = Mock()
        mock_status.return_value = [mock_status_group]
        mock_groups.find_by_label.side_effect = mock_status
        response.get_output.return_value.groups.return_value = ((mock_groups,),)
        mock_get_status.return_value = response
        with self.assertRaises(ENMJobDetailStatusError):
            self.import_config_job.wait_for_finish(detailed_validation=True)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
