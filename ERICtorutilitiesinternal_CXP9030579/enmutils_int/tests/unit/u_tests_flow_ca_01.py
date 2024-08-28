#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.ca_flows.ca_01_flow import CA01Flow
from testslib import unit_test_utils


class CA01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.node = Mock()
        self.flow = CA01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.RETRIES = 0
        self.flow.INTERVAL = 0

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.get_available_nodes")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.create_invoke_poll_jobs_for_available_nodes")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_create_invoke_pole, mock_sleep,
                                         mock_node, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_node.return_value = [self.node]
        self.flow.execute_flow()
        mock_create_invoke_pole.assert_called_once_with(self.user, self.node)
        mock_sleep.assert_called_once_with()

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.all_nodes_in_workload_pool",
           return_value=[Mock(node_id="RNC01"), Mock(node_id="MSC01BSC01"), Mock(node_id="M01B01"),
                         Mock(node_id="CHECK")])
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.log.logger.debug")
    def test_get_available_nodes_success(self, mock_log, _):
        self.assertEqual(["RNC01", "MSC01BSC01", "M01B01"], self.flow.get_available_nodes())
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.all_nodes_in_workload_pool",
           return_value=[Mock(node_id="RNC01"), Mock(node_id="CHECK")])
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.add_error_as_exception")
    def test_get_available_nodes_raises_warning_not_all_required_nodes_available(self, mock_add_error_as_exception, _):
        self.assertEqual(["RNC01"], self.flow.get_available_nodes())
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.get_timestamp_str")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.poll_job_status")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.invoke_audit_job")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.create_audit_job")
    def test_create_invoke_poll_jobs_for_available_nodes__success(self, mock_create, mock_invoke, mock_poll, *_):
        self.flow.create_invoke_poll_jobs_for_available_nodes(self.user, self.node)
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(1, mock_invoke.call_count)
        self.assertEqual(1, mock_poll.call_count)

    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.get_available_nodes",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.create_audit_job")
    @patch("enmutils_int.lib.profile_flows.ca_flows.ca_01_flow.CA01Flow.add_error_as_exception")
    def test_create_invoke_poll_jobs_for_available_nodes_adds_exception_create_audit_job(self,
                                                                                         mock_add_error_as_exception,
                                                                                         mock_create_audit_job, *_):
        mock_create_audit_job.side_effect = Exception
        self.flow.create_invoke_poll_jobs_for_available_nodes(self.user, self.node)
        self.assertEqual(mock_create_audit_job.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
