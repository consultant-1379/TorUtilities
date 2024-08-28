import unittest2
from mock import patch, Mock, PropertyMock

from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow import DynamicCrud02Flow
from testslib import unit_test_utils


class DynamicCrud02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.profile = DynamicCrud02Flow()
        self.profile.USER_ROLES = 'ADMINISTRATOR'
        self.profile.NUM_USERS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow.time.sleep", return_value=None)
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.state',
           new_callable=PropertyMock, return_value="RUNNING")
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.sleep',
           return_value=0)
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow'
           '.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow'
           '.create_and_execute_threads')
    def test_execute_flow__success(self, mock_create_and_execute_threads, *_):
        self.profile.execute_flow()
        self.assertEqual(1, mock_create_and_execute_threads.call_count)

    @patch("enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.get_given_url")
    def test_tasks_set__success(self, mock_get, *_):
        worker = ['url', 1]
        self.profile.tasks_set(worker, self.profile, self.user)
        self.assertEqual(mock_get.call_count, 1)

    def test_get_given_url__is_successful(self):
        self.profile.get_given_url(self.user, "abc")
        self.assertEqual(self.user.get.call_count, 1)

    @patch(
        "enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow.DynamicCrud02Flow.add_error_as_exception")
    def test_get_given_url__adds_exception_when_get_raises_exception(self, mock_add_error_as_exception):
        self.user.get.side_effect = Exception
        self.profile.get_given_url(self.user, "abc")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
