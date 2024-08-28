#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow import CmImport15Flow
from testslib import unit_test_utils


class CmImport15FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CmImport15Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = 'CM_REST_Administrator'
        self.flow.TIMEOUT = 0.0001
        self.nodes = [Mock(), Mock()]
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.datetime.timedelta', return_value=1)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.request_first_fifty_jobs')
    def test_execute_flow__is_successful(self, mock_first_fifty, mock_datetime, *_):
        mock_datetime.now.side_effect = [0, 0, 0, 1]
        self.flow.execute_flow()
        self.assertEqual(2, mock_first_fifty.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.datetime.timedelta', return_value=1)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.request_first_fifty_jobs')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.CmImport15Flow.add_error_as_exception')
    def test_execute_flow_adds_error(self, mock_add_error, mock_request, mock_datetime, *_):
        mock_datetime.now.side_effect = [0, 0, 0, 1]
        mock_request.side_effect = Exception
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow.raise_for_status')
    def test_request_first_fifty_jobs__successful(self, mock_raise_for_status):
        self.flow.request_first_fifty_jobs([self.user, self.user])
        self.user.get.assert_called_twice_with(
            'bulk-configuration/v1/import-jobs/jobs/?offset=0&limit=50&expand=summary&expand=failures&createdBy={user}')
        self.assertEqual(2, mock_raise_for_status.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
