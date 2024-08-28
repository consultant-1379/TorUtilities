#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import Mock, patch
from enmutils_int.lib.profile_flows.doc_flows.doc_flow import Doc01Flow


class DocFlowUnitTest(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Doc01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "MOCK"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.sleep")
    def test_execute_flow__success(self, mock_sleep, mock_handler, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_handler.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.random.randint")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.get_doc_url")
    def test_task_set__is_successful(self, mock_get_doc_url, *_):
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_get_doc_url.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.random.randint")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.get_doc_url", side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.doc_flows.doc_flow.Doc01Flow.add_error_as_exception")
    def test_task_set__adds_error_when_doc_url_raises_exception(self, mock_add_error_as_exception, *_):
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
