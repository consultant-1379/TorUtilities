#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow import ParMgt04Flow


class ParMgt04UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = ParMgt04Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.get_nodes_list_by_attribute",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.create_profile_users")
    def test_execute_flow_is_successful(self, mock_create_profile_users, mock_keep_running,
                                        mock_create_and_execute_threads, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.temporary_query_for_mo_class_mapping")
    def test_task_set_is_successful(self, mock_temporary_query_for_mo_class_mapping, *_):
        self.flow.task_set([self.user, Mock()], self.flow)
        self.assertTrue(mock_temporary_query_for_mo_class_mapping.called)

    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.ParMgt04Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow.temporary_query_for_mo_class_mapping")
    def test_task_set_raises_exception(self, mock_temporary_query_for_mo_class_mapping,
                                       mock_add_error_as_exception, *_):
        mock_temporary_query_for_mo_class_mapping.side_effect = Exception
        self.flow.task_set([self.user, Mock()], self.flow)
        self.assertTrue(mock_temporary_query_for_mo_class_mapping.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
