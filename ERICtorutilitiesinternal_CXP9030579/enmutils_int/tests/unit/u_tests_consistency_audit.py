import unittest2
from mock import Mock, patch

from enmutils_int.lib.consistency_audit import create_audit_job, invoke_audit_job, poll_job_status
from testslib import unit_test_utils


class ConsistencyAuditUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.mock_user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.consistency_audit.log.logger.debug")
    def test_create_audit_job_is_successful(self, mock_debug):
        create_audit_job(self.mock_user, "profile_node_time", "test")
        self.assertTrue(self.mock_user.post.return_value.json.called)
        self.assertEqual(2, mock_debug.call_count)
        mock_debug.assert_called_with('Successfully created audit job with name: profile_node_time')

    @patch("enmutils_int.lib.consistency_audit.log.logger.debug")
    def test_invoke_audit_job__success(self, mock_debug):
        mock_create_job_response = {u'status': u'CREATED', u'name': u'CA01_MSC02BSC03_1221-13120748', u'id': 11}
        invoke_audit_job(self.mock_user, mock_create_job_response)
        mock_debug.assert_called_with('Consistency Audit Job CA01_MSC02BSC03_1221-13120748 invoked successfully')

    @patch("enmutils_int.lib.consistency_audit.log.logger.debug")
    def test_invoke_audit_job__logs_if_unexpected_status(self, mock_debug):
        mock_create_job_response = {u'status': u'EXECUTING', u'name': u'CA01_MSC02BSC03_1221-13120748', u'id': 11}
        invoke_audit_job(self.mock_user, mock_create_job_response)
        mock_debug.assert_called_with('Status returned for creating audit job unexpected. Unable to invoke the job.'
                                      ' Create job name:CA01_MSC02BSC03_1221-13120748 Status: EXECUTING')

    @patch("enmutils_int.lib.consistency_audit.time.sleep")
    @patch("enmutils_int.lib.consistency_audit.log.logger.debug")
    def test_poll_job_status__success(self, mock_debug, _):
        mock_create_job_response = {u'status': u'COMPLETED', u'name': u'CA01_MSC02BSC03_1221-13120748', u'id': 11}
        self.mock_user.get.return_value.json.return_value = {u'status': u'FAILED'}
        poll_job_status(self.mock_user, mock_create_job_response, 6, 10)
        mock_debug.assert_called_with('Job CA01_MSC02BSC03_1221-13120748 completed. Job Status: FAILED')

    @patch("enmutils_int.lib.consistency_audit.time.sleep")
    @patch("enmutils_int.lib.consistency_audit.log.logger.debug")
    def test_poll_job_status__retries(self, mock_debug, _):
        mock_create_job_response = {u'status': u'COMPLETED', u'name': u'CA01_MSC02BSC03_1221-13120748', u'id': 11}
        self.mock_user.get.return_value.json.side_effect = [{u'status': u'CREATED'}, {u'status': u'EXECUTING'},
                                                            {u'status': u'EXECUTING'}, {u'status': u'EXECUTING'},
                                                            {u'status': u'EXECUTING'}, {u'status': u'EXECUTING'},
                                                            {u'status': u'EXECUTING'}]
        poll_job_status(self.mock_user, mock_create_job_response, 6, 10)
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 1/6')
        mock_debug.assert_any_call('Job CA01_MSC02BSC03_1221-13120748 not completed yet, polling status again in'
                                   ' 10 seconds')
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 2/6')
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 3/6')
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 4/6')
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 5/6')
        mock_debug.assert_any_call('Checking status of invoked audit job CA01_MSC02BSC03_1221-13120748. Retry: 6/6')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
