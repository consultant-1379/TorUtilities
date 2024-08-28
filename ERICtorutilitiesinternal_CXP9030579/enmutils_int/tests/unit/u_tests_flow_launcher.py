#!/usr/bin/env python
from datetime import datetime

import unittest2
from mock import Mock, patch, PropertyMock
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError

from enmutils_int.lib.profile_flows.launcher_flows.launcher_flow import LauncherFlow
from testslib import unit_test_utils


class LauncherFlowUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = LauncherFlow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "ADMINISTRATOR"
        self.flow.SCHEDULED_TIMES_STRINGS = ["09:00:00"]
        self.flow.RUN_UNTIL = ["18:00:00"]
        self.flow.requests = [("get", "url", {"json": "data"})]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.request_handler")
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.get_end_time",
           return_value=datetime.now().replace(hour=18, minute=0, second=0))
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.sleep")
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.create_profile_users")
    def test_launcher_flow__success(self, mock_create, mock_sleep, mock_datetime, *_):
        mock_datetime.now.side_effect = [datetime.now().replace(hour=9, minute=0, second=1),
                                         datetime.now().replace(hour=18, minute=0, second=1)]
        mock_create.return_value = [Mock()]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called_with(60))
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.raise_for_status")
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.log.logger.debug")
    def test_request_handler__success(self, mock_logger, *_):
        mock_user = [Mock()]
        mock_response = Mock()
        mock_response.ok = True
        mock_user[0].get = mock_response
        self.flow.request_handler(mock_user)
        mock_logger.assert_called_with("Successful requests: 1/1")

    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.raise_for_status",
           side_effect=HTTPError)
    @patch("enmutils_int.lib.profile_flows.launcher_flows.launcher_flow.LauncherFlow.add_error_as_exception")
    def test_request_handler__errors_when_NOK(self, mock_error, *_):
        mock_user = [Mock()]
        mock_get = Mock()
        mock_response = Mock()
        mock_get.return_value = mock_response
        mock_response.ok = False
        mock_user[0].get = mock_get
        self.flow.request_handler(mock_user)
        self.assertEqual(mock_error.call_count, 1)

    def test_get_attr__get(self):
        mock_user = [Mock()]
        self.flow.request_handler(mock_user)
        self.assertEqual(1, mock_user[0].get.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
