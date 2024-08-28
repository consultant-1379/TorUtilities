from datetime import datetime, timedelta

import unittest2
from mock import Mock, patch

from requests.exceptions import HTTPError
from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils_int.lib.shm_job import ShmJob, JobCreationError
from testslib import unit_test_utils


class ShmJobUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_shm_job_check_set_activities_properties(self):
        shm_job = ShmJob(user=self.user, nodes=[erbs(node_id='testNode', primary_type='ERBS')],
                         description='testDescription', schedule_time=datetime.now())
        self.assertIsNone(shm_job.set_activities())
        self.assertIsNone(shm_job.set_properties())

    @patch('enmutils_int.lib.shm_job.ShmJob.create_job')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_shm_job_create__with_shm_job_scheduled_time(self, mock_log, mock_create_job):
        shm_schedule_time1 = (datetime.now() + timedelta(seconds=1)).strftime("%H:%M:%S")
        shm_schedule_time2 = (datetime.now() + timedelta(seconds=2)).strftime("%H:%M:%S")
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type="up_back_lic_house",
                         shm_schedule_time_strings=[shm_schedule_time1, shm_schedule_time2])
        shm_job.create()
        self.assertTrue(mock_create_job.called)
        self.assertTrue(mock_log.call_count, 1)

    @patch('enmutils_int.lib.shm_job.ShmJob.create_job')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_shm_job_create__without_shm_job_scheduled_time(self, mock_log, mock_create_job):
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type="up_back_lic_house",
                         shm_schedule_time_strings=[])
        shm_job.create()
        self.assertTrue(mock_create_job.called)
        self.assertTrue(mock_log.call_count, 1)

    @patch('enmutils_int.lib.shm_job.ShmJob.create_job')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_shm_job_create__raise_runtimeerror(self, mock_log, mock_create_job):
        shm_schedule_time = datetime.now() + timedelta(seconds=1)
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type=None,
                         shm_schedule_time_strings=[shm_schedule_time.strftime("%H:%M:%S")])
        self.assertRaises(RuntimeError, shm_job.create)
        self.assertFalse(mock_create_job.called)
        self.assertTrue(mock_log.call_count, 1)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.fetch_job_status')
    @patch('enmutils_int.lib.shm_job.ShmJob._set_job_id')
    @patch('enmutils_int.lib.shm_job.ShmJob.generate_payload')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_job__successful(self, mock_log, mock_generate_payload, mock_set_jobid, mock_fetch_status, *_):
        shm_schedule_time = datetime.now() + timedelta(seconds=1)
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type="up_back_lic_house",
                         shm_schedule_time_strings=[shm_schedule_time.strftime("%H:%M:%S")])
        self.user.post.return_value = Mock(status_code=201, ok=True)
        shm_job.create_job(shm_schedule_time.strftime("%H:%M:%S"))
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_generate_payload.called)
        self.assertTrue(mock_set_jobid.called)
        self.assertTrue(mock_fetch_status.called)
        self.assertTrue(mock_log.call)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.fetch_job_status')
    @patch('enmutils_int.lib.shm_job.ShmJob._set_job_id')
    @patch('enmutils_int.lib.shm_job.ShmJob.generate_payload')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_job__raises_HTTPError(self, mock_log, mock_generate_payload, mock_set_jobid, mock_fetch_status, *_):
        shm_schedule_time = datetime.now() + timedelta(seconds=1)
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type="up_back_lic_house",
                         shm_schedule_time_strings=[shm_schedule_time.strftime("%H:%M:%S")])
        self.user.post.return_value = Mock(status_code=504, ok=True)
        self.assertRaises(HTTPError, shm_job.create_job, shm_schedule_time.strftime("%H:%M:%S"))
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_generate_payload.called)
        self.assertFalse(mock_set_jobid.called)
        self.assertFalse(mock_fetch_status.called)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    @patch('enmutils_int.lib.shm_job.ShmJob.fetch_job_status')
    @patch('enmutils_int.lib.shm_job.ShmJob._set_job_id')
    @patch('enmutils_int.lib.shm_job.ShmJob.generate_payload')
    @patch('enmutils_int.lib.shm_job.log.logger.debug')
    def test_create_job__raises_jobcreationerror(self, mock_log, mock_generate_payload, mock_set_jobid,
                                                 mock_fetch_status, *_):
        shm_schedule_time = datetime.now() + timedelta(seconds=1)
        shm_job = ShmJob(user=self.user, nodes=[Mock(node_id='shm_4444', primary_type='ERBS')],
                         description='basic_shm_job', job_type="up_back_lic_house",
                         shm_schedule_time_strings=[shm_schedule_time.strftime("%H:%M:%S")])
        self.user.post.return_value = Mock(status_code=403, ok=True)
        self.assertRaises(JobCreationError, shm_job.create_job, shm_schedule_time.strftime("%H:%M:%S"))
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_generate_payload.called)
        self.assertFalse(mock_set_jobid.called)
        self.assertFalse(mock_fetch_status.called)
        self.assertTrue(mock_log.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
