#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils.lib.enm_node import RBSNode as rbs
from enmutils.lib.enm_node import SGSNNode as sgsn
from enmutils.lib.exceptions import (EnmApplicationError, JobExecutionError,
                                     JobValidationError, TimeOutError)
from enmutils_int.lib.lkf import LkfJob
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP
from enmutils_int.lib.shm import (RestoreJob, SHMExport, UpgradeJob)
from enmutils_int.lib.shm_job import MultiUpgrade
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from enmutils_int.lib.shm_utilities import SoftwarePackage
from testslib import unit_test_utils

PACKAGE = 'ACCEPTANCE_TEST_UPGRADE_SHM'


class ShmJobUnitTests(ParameterizedTestCase):

    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        node = erbs(node_id='testNode', primary_type='ERBS')
        nodes = [node]
        time = "00:00:00"
        self.job = BackupJobCPP(user=self.user, nodes=nodes, description='testDescription', schedule_time=time)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.ShmJob.sleep_till_job_creation_time')
    @patch('time.sleep', return_value=lambda _: None)
    def test_create__backup_job_failure(self, *_):
        response = Mock(status_code=400, ok=False)
        response.json.return_value = {"jobConfigId": 90900, 'result': 'FAILURE'}
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_none_type_for_job_type_raise_runtime_error(self):
        self.job.job_type = None
        self.assertRaises(RuntimeError, self.job.create)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_sleep_till_job_creation_time__with_date_time_object(self, mock_log, _):
        time_now = datetime.now().replace(hour=22, minute=0, second=0)
        self.job.shm_schedule_time_strings = [time_now]
        job_creation_time = datetime.now().replace(hour=23, minute=0, second=0)
        self.job.sleep_till_job_creation_time(job_creation_time)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_sleep_till_job_creation_time__with_time_string(self, mock_log, _):
        self.job.shm_schedule_time_strings = ["22:30:00"]
        job_creation_time = "22:30:00"
        self.job.sleep_till_job_creation_time(job_creation_time)
        self.assertTrue(mock_log.call_count, 1)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_sleep_till_job_creation_time__with_profile_object(self, mock_log, _):
        self.job.shm_schedule_time_strings = ["22:00:00"]
        job_creation_time = "22:00:00"
        self.job.sleep_till_job_creation_time(job_creation_time, profile_object=Mock())
        self.assertTrue(mock_log.call_count, 1)

    def test_get_jobs_success(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"totalCount": 2,
                                      'result': [{'jobName': 'test', 'status': 'FAILED', 'startDate': '76745',
                                                  'endDate': '8098'},
                                                 {'jobName': 'test', 'status': 'COMPLETED', 'startDate': '345345',
                                                  'endDate': '678768'}]}
        self.user.post.return_value = response
        try:
            self.job.get_shm_jobs(self.user)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('time.sleep', side_effect=lambda _: None)
    def test_get_jobs_raises_job_validation_error_for_retry(self, *_):
        response = Mock(status_code=400, ok=False)
        response.json.return_value = {"totalCount": 0, "result": []}
        response.text = "Fail"
        self.user.post.return_value = response
        self.assertRaises(JobValidationError, self.job.get_shm_jobs, self.user)

    def test_get_jobs_results_with_match(self):
        response = Mock()
        response.json.return_value = {"totalCount": 2, 'result': [
            {'jobName': 'test1', 'status': 'FAILED', 'startDate': '76745', 'endDate': '8098'},
            {'jobName': 'test2', 'status': 'COMPLETED', 'startDate': '345345', 'endDate': '678768'}]}
        results = self.job._get_jobs_results(response, jobName="test1", status="FAILED")
        self.assertTrue(len(results), 1)

    def test_get_jobs_results_no_match(self):
        response = Mock()
        response.json.return_value = {"totalCount": 2, 'result': [
            {'jobName': 'test1', 'status': 'FAILED', 'startDate': '76745', 'endDate': '8098'},
            {'jobName': 'test2', 'status': 'COMPLETED', 'startDate': '345345', 'endDate': '678768'}]}
        results = self.job._get_jobs_results(response, jobName="shm_999", status="FAILED")
        self.assertFalse(results)

    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    def test_shm_job_exists(self, mock_job_status):
        response = Mock()
        response.json.return_value = {"result": [{"jobName": "shmJob1", "status": "success"}]}
        mock_job_status.return_value = response
        self.job.exists()

    def test_get_jobs_results(self):
        response = Mock()
        response.json.return_value = {"result": [{"jobName": "shmJob2", "status": "success"}]}
        self.job._get_jobs_results(response)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', return_value=["success"])
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs', return_value=["job1"])
    def test_validate(self, *_):
        self.job.validate()

    @patch('enmutils_int.lib.shm_job.ShmJob.cancel')
    @patch('enmutils_int.lib.shm_job.ShmJob.delete')
    def test_teardown_success(self, *_):
        self.job._teardown()

    @patch('enmutils_int.lib.shm_job.ShmJob.cancel', side_effect=Exception)
    @patch('enmutils_int.lib.shm_job.ShmJob.delete')
    def test_teardown_error(self, *_):
        self.job._teardown()

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_skipped_count_success(self, _):
        response = Mock()
        response.json.return_value = {"neDetails": {"result": [{"neResult": "SKIPPED"}, {"neResult": "SUCCESS"}]}}
        self.user.get.return_value = response
        self.job.get_skipped_count()

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_job.ShmJob._set_job_id')
    def test_get_skipped_count_value_error(self, *_):
        self.user.get.side_effect = ValueError
        self.job.get_skipped_count()

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_skipped_count_error(self, _):
        self.user.get.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.job.get_skipped_count)

    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results')
    def test_set_job_id__choose_successful_job_id(self, mock_job_result, mock_log, _):
        mock_job_result.return_value = [{"jobId": "1234"}]
        self.job._set_job_id()
        mock_log.assert_called_with("Job Id chosen is: 1234")

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results')
    def test_set_job_id__raises_enm_application_error(self, mock_job_result, *_):
        mock_job_result.return_value = []
        self.assertRaises(EnmApplicationError, self.job._set_job_id)

    def test_backup_delete_success(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {'status': 'success'}
        self.user.post.return_value = response
        self.job.job_id = "1234"
        try:
            self.job.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('time.sleep', return_value=lambda _: None)
    def test_backup_delete_status_200_failure(self, _):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {'status': 'failure'}
        self.user.post.return_value = response
        self.job.job_id = "1234"
        self.assertRaises(HTTPError, self.job.delete)

    def test_backup_delete_with_no_job_id(self):
        self.assertRaises(RuntimeError, self.job.delete)

    def test_cancel_with_verify_is_skipped_if_verify_cancelled_false(self, *_):
        self.job.job_id = "123"
        self.job.user = Mock()
        response = Mock()
        response.ok = True
        self.job.user.post.return_value = response
        self.job.cancel(verify_cancelled=False)

    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs', return_value=Mock())
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', side_effect=[[Mock()], []])
    def test_cancel_with_verify_is_successful_if_status_cancelled(self, *_):
        self.job.job_id = "123"
        self.job.user = Mock()
        response = Mock()
        response.ok = True
        self.job.user.post.return_value = response
        self.job.cancel()

    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs', return_value=Mock())
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', side_effect=[[], [Mock()]])
    def test_cancel_with_verify_is_successful_if_status_completed(self, *_):
        self.job.job_id = "123"
        self.job.user = Mock()
        response = Mock()
        response.ok = True
        self.job.user.post.return_value = response
        self.job.cancel()

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs', return_value=[])
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', return_value=[])
    def test_cancel_with_verify_raises_http_error(self, *_):
        self.assertRaises(HTTPError, self.job._verify_cancel)

    @patch('time.sleep', return_value=lambda _: None)
    def test_cancel_raises_http_error_if_response_fails(self, *_):
        self.job.job_id = "123"
        self.job.user = Mock()
        response = Mock()
        response.ok = False
        self.job.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.cancel)

    def test_cancel_with_no_job_id_raises_runtime_error(self):
        self.assertRaises(RuntimeError, self.job.cancel)

    def test_validate_raises_job_execution_error_if_result_is_not_success(self, *_):
        response = Mock(status_code=200, ok=True)
        self.user.post.return_value = response
        response.json.return_value = {"totalCount": 2, 'result': [
            {"jobId": "1234", "jobTemplateId": "45645", "jobName": "testJob", "jobType": "BACKUP",
             "createdBy": "user_1", "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED", "result": "FAILURE",
             "startDate": "1461234321601", "endDate": "1461234327288", "creationTime": "", "periodic": False,
             "totalNoOfNEs": "1", "jobTemplateIdAsLong": 45645, "jobIdAsLong": 45645, "comment": []},
            {"jobId": "281474984037012", "jobTemplateId": "123132", "jobName": "BACKUP_RtiC", "jobType": "BACKUP",
             "createdBy": "user_2", "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED", "result": "SUCCESS",
             "startDate": "12", "endDate": "13", "creationTime": "", "periodic": False, "totalNoOfNEs": "1",
             "jobTemplateIdAsLong": 123123, "jobIdAsLong": 123123, "comment": []}]}
        self.job.job_id = '1234'
        self.assertRaises(JobExecutionError, self.job.validate)

    def test_scheduler_returns_void_for_delete_job(self):
        self.job.job_type = "DELETEBACKUP"
        self.assertEqual(len(self.job.set_schedule()), 0)

    def test_scheduler_returns_single_dict_for_upgrade_job(self):
        self.job.job_type = "UPGRADE"
        self.assertEqual(len(self.job.set_schedule()), 1)

    def test_scheduler_returns_dict_for_job(self):
        self.job.job_type = "BACKUP"
        self.assertEqual(len(self.job.set_schedule()), 4)

    def test_scheduler_returns_weekly(self):
        self.job.repeat_frequency = "Weekly"
        self.assertEqual(len(self.job.set_schedule()), 5)

    def test_node_dictionary_correctly_sorts_multiple_node_types(self):
        self.assertEqual(self.job.node_types, ['ERBS'])
        self.job.nodes.append(sgsn(node_id='testNode1', primary_type='SGSN-MME'))
        self.job.nodes.append(rbs(node_id='testNode2', primary_type='RBS'))
        self.job.node_types = self.job.nodes_dictionary()
        self.assertItemsEqual(['ERBS', 'SGSN-MME', 'RBS'], [v for v in self.job.node_types])

    def test_set_ne_name_returns_dictionary_when_provided_nodes(self):
        ne_names = self.job.set_ne_names()
        self.assertEqual(list, type(ne_names))
        self.assertEqual(dict, type(ne_names[0]))
        self.assertEqual(1, len(ne_names))
        self.assertIn(self.job.nodes[0].node_id, ne_names[0].itervalues())

    def test_set_ne_name_correctly_handles_multi_node_types(self):
        self.job.nodes.append(sgsn(node_id='testNode1', primary_type='SGSN-MME'))
        self.job.nodes.append(rbs(node_id='testNode2', primary_type='RBS'))
        self.job.node_types = self.job.nodes_dictionary()
        ne_names = self.job.set_ne_names()
        self.assertEqual(3, len(ne_names))
        self.assertNotEqual(ne_names[0], ne_names[1] or ne_names[2])
        self.assertIn(self.job.nodes[1].node_id, ne_names[1].itervalues())

    def test_set_ne_name_returns_empty_list_with_no_nodes(self):
        self.job.nodes = []
        self.job.node_types = self.job.nodes_dictionary()
        ne_names = self.job.set_ne_names()
        self.assertEqual(0, len(ne_names))

    def test_wait_time_for_job_to_complete_raises_enm_application_error(self):
        self.assertRaises(EnmApplicationError, self.job.wait_time_for_job_to_complete)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_time_for_job_to_complete(self, mock_get_job_response):
        mock_get_job_response.return_value = {'status': 'STARTED'}
        self.job.job_id = 1234
        self.job.wait_time_for_job_to_complete(max_iterations=4, time_to_sleep=0.001)
        self.assertEqual(5, mock_get_job_response.call_count)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_time_for_job_to_complete_respone_enm_application_error(self, mock_get_job_response):
        mock_get_job_response.return_value = None
        self.job.job_id = 1234
        self.assertRaises(EnmApplicationError, self.job.wait_time_for_job_to_complete,
                          max_iterations=4, time_to_sleep=0.1)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', side_effect=IndexError)
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    def test_wait_time_for_job_to_complete_raises_index_error(self, *_):
        self.job.job_id = 1234
        self.assertRaises(EnmApplicationError, self.job.wait_time_for_job_to_complete, max_iterations=4,
                          time_to_sleep=0.1)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_time_for_job_to_complete_raises_enm_application_error2(self, mock_get_job_response, *_):
        self.job.job_id = 1234
        mock_get_job_response.side_effect = [{'status': 'STARTED'}, Exception]
        self.assertRaises(EnmApplicationError, self.job.wait_time_for_job_to_complete, max_iterations=4,
                          time_to_sleep=0.1)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob._get_jobs_results', side_effect=KeyError)
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    def test_wait_time_for_job_to_complete_raises_key_error(self, *_):
        self.job.job_id = 1234
        self.assertRaises(EnmApplicationError, self.job.wait_time_for_job_to_complete, max_iterations=4,
                          time_to_sleep=0.1)

    def test_convert_schedule_time_in_secs_success(self):
        self.job.convert_schedule_time_in_secs(scheduled_time=["02:05:00", "20:08:00", datetime(2020, 12, 11, 23, 0, 0), 123])

    def test_convert_schedule_time_in_secs_add_error_as_exception(self):
        self.assertRaises(Exception, self.job.convert_schedule_time_in_secs(scheduled_time=["1234"]))

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_upgrade_success(self, mock_get_job_response, *_):
        mock_get_job_response.return_value = {"status": "COMPLETED"}
        self.job.job_type = "UPGRADE"
        self.job._wait_job_to_complete()
        self.assertTrue(mock_get_job_response.called)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_mltn_success(self, mock_get_job_response, *_):
        mock_get_job_response.return_value = {"status": "COMPLETED"}
        self.job.nodes[0].primary_type = "MLTN"
        self.job._wait_job_to_complete()
        self.assertTrue(mock_get_job_response.called)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_ml669x_success(self, mock_get_job_response, *_):
        mock_get_job_response.return_value = {"status": "COMPLETED"}
        self.job.nodes[0].primary_type = "MINI-LINK-669x"
        self.job._wait_job_to_complete()
        self.assertTrue(mock_get_job_response.called)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_cleanup_success(self, mock_get_job_response, *_):
        mock_get_job_response.return_value = {"status": "COMPLETED"}
        self.job.name = "SHM_35"
        self.job.job_type = "Cleanup_job"
        self.job._wait_job_to_complete()
        self.assertTrue(mock_get_job_response.called)

    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_upgrade_raises_enm_error(self, mock_get_job_response, *_):
        mock_get_job_response.return_value = {"status": "STARTING"}
        self.assertRaises(EnmApplicationError, self.job._wait_job_to_complete)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('datetime.timedelta')
    @patch('datetime.datetime')
    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_wait_job_to_complete_upgrade_raises_timeout_error(self, mock_get_job_response,
                                                               mock_datetime, mock_timedelta, *_):
        mock_get_job_response.return_value = {"status": "RUNNING"}
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=60)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(0, 10)
        self.assertRaises(TimeOutError, self.job._wait_job_to_complete)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.convert_schedule_time_in_secs', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCPP._wait_job_to_complete', return_value="SCHEDULED")
    def test_fetch_job_status_success(self, *_):
        self.job.schedule_time_strings = ["06:30:00"]
        self.job.shm_schedule_time_strings = ["07:00:00"]
        self.job.fetch_job_status()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.convert_schedule_time_in_secs', return_value=0)
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobCPP._wait_job_to_complete', return_value="SCHEDULED")
    def test_fetch_job_status_fail(self, *_):
        self.job.fetch_job_status()

    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_construct_capacity_expansion_license_job_payload(self, mock_log):
        lkf_job = LkfJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='RadioNode')],
                         job_type="LICENSE_REQUEST", name="CapacityExpansionLicenseJob",
                         current_time="2020-12-11 00:00:00")
        lkf_job.construct_capacity_expansion_license_job_payload(limit=50)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.construct_capacity_expansion_license_job_payload', return_value=Mock())
    def test_get_shm_jobs__if_payload(self, mock_construct_payload):
        payload = mock_construct_payload.return_value()
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.return_value = {"totalCount": 1}
        self.user.post.return_value = response
        self.job.get_shm_jobs(self.user, 1, 50, payload=payload).return_value = response

    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.ShmJob.construct_capacity_expansion_license_job_payload', return_value=Mock())
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    def test_get_job_response__success_lkf_job(self, mock_get_shm_jobs, *_):
        lkf_job = LkfJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='RadioNode')],
                         job_type="LICENSE_REQUEST", name="CapacityExpansionLicenseJob",
                         current_time="2020-12-11 00:00:00")
        response = Mock()
        response.json.return_value = {"totalCount": 2, 'result': [
            {'jobName': 'test1', 'status': 'FAILED', 'startDate': '76745', 'endDate': '8098'},
            {'jobName': 'test2', 'status': 'COMPLETED', 'startDate': '345345', 'endDate': '678768'}]}
        mock_get_shm_jobs.return_value = response
        lkf_job.get_lkf_job()

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.ShmJob.construct_capacity_expansion_license_job_payload', return_value=Mock())
    @patch('enmutils_int.lib.shm_job.ShmJob.get_shm_jobs')
    def test_get_job_response__raises_enmapplication_error_lkf_job(self, mock_get_shm_jobs, *_):
        lkf_job = LkfJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='RadioNode')],
                         job_type="LICENSE_REQUEST", name="CapacityExpansionLicenseJob",
                         current_time="2020-12-11 00:00:00")
        mock_get_shm_jobs.return_value = None
        self.assertRaises(EnmApplicationError, lkf_job.get_lkf_job)

    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.ShmJob._get_job_response')
    def test_get_lkf_job__success(self, mock_get_job_response, _):
        self.job.get_lkf_job()
        self.assertTrue(mock_get_job_response.called)


class SHMUpgradeJobUnitTests(unittest2.TestCase):

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    def setUp(self, _):  # pylint: disable=W0221

        unit_test_utils.setup()
        self.user = Mock()

        enode = Mock()
        enode.primary_type = 'ERBS'
        enode.node_version = '16A'
        enode.node_id = 'testNode'
        enode.mim_version = 'H.1.160'

        rnode = Mock()
        rnode.primary_type = 'RadioNode'
        rnode.node_version = '16A'
        rnode.node_id = 'testNode'
        rnode.mim_version = 'J.1.161'

        mnode = Mock()
        mnode.node_id = 'testNode'
        mnode.primary_type = 'MLTN'
        mnode.platform = "ECIM"
        mnode.mim_version = 'K.2.120'

        scunode = Mock()
        scunode.node_id = 'testNode'
        scunode.primary_type = 'SCU'
        scunode.platform = 'ECIM'
        scunode.mim_version = 'L.1.120'

        onode = Mock()
        onode.node_id = 'testNode'
        onode.primary_type = 'MINI-LINK-6352'
        onode.platform = 'MINI_LINK_OUTDOOR'

        snode = Mock()
        snode.node_id = 'testNode'
        snode.primary_type = 'Router_6672'
        snode.platform = "Router_6672"
        snode.mim_version = 'K.2.120'

        tnode = Mock()
        tnode.node_id = 'testNode'
        tnode.primary_type = 'TCU02'
        tnode.platform = "STN"

        sinode = Mock()
        sinode.node_id = 'testNode'
        sinode.primary_type = 'SIU02'
        sinode.platform = "STN"

        bscnode = Mock()
        bscnode.node_id = 'tesNode'
        bscnode.primary_type = 'BSC'
        bscnode.platform = "AXE"

        m6node = Mock()
        m6node.node_id = 'testNode'
        m6node.primary_type = 'MINI-LINK-669x'
        m6node.platform = 'MINI_LINK_INDOOR'

        software_package = SoftwarePackage([enode], self.user, mim_version="G1281", use_default=True,
                                           profile_name="SHM_TEST_PROFILE", existing_package="CXPL16BCP1_G1281")
        self.software_operator = SoftwareOperations(user=self.user, package=software_package)

        time = "00:00:00"
        self.job = UpgradeJob(user=self.user, nodes=[enode], software_package=software_package,
                              description='testDescription', schedule_time=time)
        self.install_verify_only_job_erbs = UpgradeJob(user=self.user, nodes=[enode],
                                                       software_package=software_package, schedule_time=time,
                                                       description='testDescription', install_verify_only=True)
        self.install_verify_only_job = UpgradeJob(user=self.user, nodes=[rnode], software_package=software_package,
                                                  install_verify_only=True, description='testDescription',
                                                  schedule_time=time)
        self.radio_job = UpgradeJob(user=self.user, nodes=[rnode], software_package=software_package,
                                    description='testDescription', schedule_time=time, platform='ECIM')
        self.multi = MultiUpgrade([self.job, self.radio_job], nodes=[enode, rnode], user=self.user,
                                  description='testDescription', schedule_time=time)
        mltn_software_package = SoftwarePackage([mnode], self.user, profile_name="SHM_06", use_default=True)
        self.mltn_job = UpgradeJob(user=self.user, nodes=[mnode], software_package=mltn_software_package,
                                   description='testDescription')

        scu_software_package = SoftwarePackage([scunode], self.user, profile_name="SHM_44", use_default=False)
        self.scu_job = UpgradeJob(user=self.user, nodes=[scunode], software_package=scu_software_package,
                                  description='testDescription')
        mini_link_6352_software_package = SoftwarePackage([onode], self.user, profile_name="SHM_31", use_default=True)
        self.minilink_6352_job1 = UpgradeJob(user=self.user, nodes=[onode], description='testDescription',
                                             software_package=mini_link_6352_software_package)

        mini_link_6352_software_package_additional = SoftwarePackage([onode], self.user, additional=True,
                                                                     profile_name="SHM_31", use_default=True)
        self.minilink_6352_job2 = UpgradeJob(user=self.user, nodes=[onode], description='testDescription',
                                             software_package=mini_link_6352_software_package_additional)

        spitfire_package = SoftwarePackage([snode], self.user)
        self.spitfire_job = UpgradeJob(user=self.user, nodes=[snode], software_package=spitfire_package,
                                       description='testDescription', upgrade_commit_only=True)
        tcu_package = SoftwarePackage([tnode], self.user, use_default=True, profile_name="SHM_27")
        siu_package = SoftwarePackage([sinode], self.user, use_default=True, profile_name="SHM_27")
        bsc_package = SoftwarePackage([bscnode], self.user, use_default=True)
        bsc_package_additional = SoftwarePackage([bscnode], self.user, use_default=True, additional=True)

        self.tcu_upgrade_job = UpgradeJob(user=self.user, nodes=[tnode], software_package=tcu_package,
                                          description='test_tcu_upgrade')
        self.siu_upgrade_job = UpgradeJob(user=self.user, nodes=[sinode], software_package=siu_package,
                                          description='test_tcu_upgrade')
        self.bsc_upgrade_job = UpgradeJob(user=self.user, nodes=[bscnode], software_package=bsc_package,
                                          description='test_bsc_upgrade')
        self.bsc_upgrade_job_additional = UpgradeJob(user=self.user, nodes=[bscnode],
                                                     software_package=bsc_package_additional,
                                                     description='test_bsc_upgrade')
        mini_link_669x_software_package_additional = SoftwarePackage([m6node], self.user, additional=True,
                                                                     profile_name="SHM_42", use_default=True)
        self.mini_link_669x_job = UpgradeJob(user=self.user, nodes=[m6node], description='testDescription',
                                             software_package=mini_link_669x_software_package_additional)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create__upgrade_job_success(self, mock_log, *_):
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.shm_schedule_time_strings = ["22:00:00"]
        self.job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create_job')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    @patch('enmutils_int.lib.shm_job.datetime.datetime')
    def test_create__with_profile_object(self, mock_datetime, mock_log, *_):
        time_now = datetime(2020, 12, 11, 23, 0, 0)
        mock_datetime.now.return_value = time_now
        self.user.post.return_value = Mock(status_code=201, ok=True)
        self.job.shm_schedule_time_strings = ["22:00:00", datetime(2020, 12, 11, 23, 0, 0)]
        self.job.create(profile_object=Mock())
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._set_job_id')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_multi_upgrade_job_success(self, mock_log, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.multi.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_radionode_upgrade_job_success(self, mock_log, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.radio_job.create()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_upgrade_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._set_job_id')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_multi_upgrade_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.multi.create)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_sgsn_upgrade_job_failure(self, *_):
        response = Mock()
        response.status_code = 200
        response.ok = False
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.radio_job.create)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._set_job_id')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade.update_configuration')
    def test_create_multi_upgrade_update_configuration_is_called(self, mock_update_configuration, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.multi.create()
        self.assertTrue(mock_update_configuration.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._set_job_id')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade._wait_job_to_complete')
    @patch('enmutils_int.lib.shm_job.MultiUpgrade.update_activities_schedule')
    def test_create_multi_upgrade_update_activities_is_called(self, mock_update_activities_schedule, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.multi.create()
        self.assertTrue(mock_update_activities_schedule.called)

    def test_set_install_verify_only_alters_activities_and_properties(self):
        self.assertEqual(len(self.job.set_properties()), 5)
        self.assertEqual(len(self.install_verify_only_job_erbs.set_properties()), 4)
        self.assertEqual(len(self.job.set_activities()), 4)
        self.assertEqual(len(self.install_verify_only_job_erbs.set_activities()), 2)
        self.assertNotEqual(self.radio_job.set_activities(), self.install_verify_only_job_erbs.set_activities())

    def test_set_upgrade_commit_only_only_alters_activities(self):
        self.assertEqual(len(self.spitfire_job.set_activities()), 2)

    def test_siu_tcu_activities(self):
        self.assertEqual(len(self.tcu_upgrade_job.set_activities()), 4)
        self.assertEqual(len(self.siu_upgrade_job.set_activities()), 4)

    def test_bsc_activities(self):
        self.assertEqual(len(self.bsc_upgrade_job.set_activities()), 1)
        self.assertEqual(len(self.bsc_upgrade_job_additional.set_activities()), 1)

    def test_set_activites__scu(self):
        self.assertEqual(len(self.scu_job.set_activities()), 3)

    def test_update_ne_type_and_platform(self):
        self.spitfire_job.update_ne_type_and_platform()
        self.assertEqual(self.spitfire_job.platform, "ECIM")
        self.scu_job.update_ne_type_and_platform()
        self.assertEqual(self.scu_job.platform, 'ECIM')
        self.mltn_job.update_ne_type_and_platform()
        self.minilink_6352_job1.update_ne_type_and_platform()
        self.minilink_6352_job2.update_ne_type_and_platform()
        self.mini_link_669x_job.update_ne_type_and_platform()
        self.assertEqual(self.mltn_job.ne_type, "MINI-LINK-Indoor")
        self.assertEqual(self.mltn_job.platform, "MINI_LINK_INDOOR")
        self.assertEqual(self.minilink_6352_job1.ne_type, "MINI-LINK-6352")
        self.assertEqual(self.minilink_6352_job1.platform, "MINI_LINK_OUTDOOR")
        self.assertEqual(self.minilink_6352_job2.ne_type, "MINI-LINK-6352")
        self.assertEqual(self.minilink_6352_job2.platform, "MINI_LINK_OUTDOOR")
        self.assertEqual(self.mini_link_669x_job.ne_type, "MINI-LINK-669x")
        self.assertEqual(self.mini_link_669x_job.platform, "MINI_LINK_INDOOR")

    def test_set_install_verify_only_alters_sgsn_activities(self):
        self.assertEqual(len(self.radio_job.set_activities()), 4)
        self.assertEqual(len(self.install_verify_only_job.set_activities()), 2)
        self.assertNotEqual(self.radio_job.set_activities(), self.install_verify_only_job.set_activities())

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    def test_create_mini_link_upgrade(self, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.mltn_job.create()
        self.assertEqual(3, len(self.mltn_job.set_activities()))

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    def test_create_mini_link_669x_upgrade(self, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.mini_link_669x_job.create()
        self.assertEqual(3, len(self.mini_link_669x_job.set_activities()))

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    def test_create_mini_link_6352_upgrade(self, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.minilink_6352_job1.create()
        self.minilink_6352_job2.create()
        self.assertEqual(3, len(self.minilink_6352_job1.set_activities()))
        self.assertEqual(3, len(self.minilink_6352_job2.set_activities()))

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    def test_create_bsc_upgrade(self, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.side_effect = [response, response, response]
        self.bsc_upgrade_job.create()
        self.bsc_upgrade_job_additional.create()
        self.assertEqual(1, len(self.bsc_upgrade_job.set_activities()))
        self.assertEqual(1, len(self.bsc_upgrade_job_additional.set_activities()))

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.UpgradeJob._set_job_id')
    @patch('enmutils_int.lib.shm.UpgradeJob._wait_job_to_complete')
    @patch('enmutils_int.lib.shm.UpgradeJob.update_ne_type_and_platform')
    def test_create_mini_link_upgrade_install_verify_only(self, *_):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        self.mltn_job.install_verify_only = True
        self.mltn_job.create()
        self.assertEqual(1, len(self.mltn_job.set_activities()))

    def test_multi_upgrade_set_properties(self):
        self.multi.set_properties()

    def test_multi_upgrade_set_activities(self):
        self.multi.set_activities()


class SHMRestoreJobUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()

        node = erbs(node_id='testNode', node_version='16A', primary_type='ERBS')
        nodes = [node]
        self.job = RestoreJob(user=self.user, nodes=nodes, description='testDescription')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.RestoreJob._set_job_id')
    @patch('enmutils_int.lib.shm.RestoreJob._wait_job_to_complete')
    def test_create_erbs_restore_job_success(self, *_):
        response = Mock(status_code=200, ok=True)
        self.user.post.return_value = response
        try:
            self.job.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    @patch('time.sleep', return_value=lambda _: None)
    def test_create_restore_job_failure(self, _):
        response = Mock(status_code=400, ok=False)
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.job.create)

    def test_set_activities_returns_correct_dict_size_and_type(self):
        self.assertIsInstance(self.job.set_activities(), list)
        self.assertIsInstance(self.job.set_activities()[0], dict)
        self.assertEqual(len(self.job.set_activities()), 4)


class ShmExportUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

        node = Mock()
        node.node_id = 'testNode'
        nodes = [node]
        self.export = SHMExport(user=self.user, nodes=nodes)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('time.sleep', return_value=lambda _: None)
    def test_create__export_failure(self, _):
        response = Mock(ok=False)
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.export.create)

    @patch('enmutils_int.lib.shm.SHMExport.verify_csv_created')
    def test_create_export__success(self, _):
        response = Mock()
        response.json.return_value = {'result': 'SUCCESS'}
        self.user.get.return_value = response
        self.export.create()

    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.shm.verify_json_response')
    def test_verify_csv_created(self, mock_json, *_):
        response = Mock()
        response.json.return_value = {"requestId": "id1"}
        response1 = Mock()
        response1.json.return_value = {"progressPercentage": 100}
        self.user.get.return_value = response1
        self.export.verify_csv_created(response=response)
        self.assertTrue(mock_json.called)

    @patch('enmutils_int.lib.shm.verify_json_response')
    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('time.sleep', return_value=0)
    def test_verify_csv_created_raises_enm_application_error(self, *_):
        response = Mock()
        response.json.return_value = {"requestId": "id2"}
        response1 = Mock()
        response1.json.return_value = {"progressPercentage": 0}
        self.user.get.return_value = response1
        self.assertRaises(EnmApplicationError, self.export.verify_csv_created, response=response)

    @patch('enmutils_int.lib.shm.verify_json_response')
    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('time.sleep', return_value=0)
    def test_verify_csv_created_raises_validation_error(self, *_):
        response = Mock()
        response.json.return_value = {"requestId": None}
        self.assertRaises(JobValidationError, self.export.verify_csv_created, response=response)

    @patch('enmutils_int.lib.shm.verify_json_response')
    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('time.sleep', return_value=0)
    def test_verify_csv_created__raises_validation_error_of_software_export(self, *_):
        response = Mock()
        response.json.return_value = {"requestId": None}
        test_node = Mock()
        test_node.node_id = 'testNode'
        test_nodes = [test_node]
        test_export_init = SHMExport(user=Mock(), nodes=test_nodes, export_type="SOFTWARE")
        self.assertRaises(JobValidationError, test_export_init.verify_csv_created, response=response)

    @patch('enmutils_int.lib.shm.verify_json_response')
    @patch('enmutils_int.lib.shm.log.logger.debug')
    @patch('time.sleep', return_value=0)
    def test_verify_csv_created__raises_validation_error_of_hardware_export(self, *_):
        response = Mock()
        response.json.return_value = {"requestId": None}
        test_node = Mock()
        test_node.node_id = 'testNode'
        test_nodes = [test_node]
        test_export_init = SHMExport(user=Mock(), nodes=test_nodes, export_type="HARDWARE")
        self.assertRaises(JobValidationError, test_export_init.verify_csv_created, response=response)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
