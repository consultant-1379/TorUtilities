#!/usr/bin/env python

from testslib import unit_test_utils
from mock import patch, Mock
from enmutils_int.lib.profile_flows.fm_flows.fm_21_flow import Fm21
from enmutils.lib.exceptions import EnmApplicationError

import unittest2


class Fm21UnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(), Mock()]
        self.flow = Fm21()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "TEST1"
        self.flow.SCHEDULED_TIMES_STRINGS = ["05:20:00"]
        self.error_response = EnmApplicationError

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.FmManagement.synchronize")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.create_users')
    def test_execute_flow_fm_21_success(self, mock_create_user, mock_keep_running, mock_synchronize, mock_sleep):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_21()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_synchronize.called)
        self.assertTrue(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.FmManagement.synchronize")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.create_users')
    def test_execute_flow_fm_21_continues_with_errors(self, mock_create_user, mock_keep_running, mock_synchronize,
                                                      mock_sleep, *_):
        response = [False, True]
        mock_create_user.return_value = [self.user]
        mock_sleep.side_effect = response
        mock_synchronize.side_effect = response + [response[1]]
        mock_keep_running.side_effect = response + [response[1], response[1]]
        self.assertFalse(self.flow.execute_flow_fm_21())

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.FmManagement.synchronize")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.keep_running")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.create_users')
    def test_execute_flow_fm_21_throws_exception(self, mock_create_user, mock_keep_running, mock_synchronize,
                                                 mock_add_error_as_exception, *_):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_synchronize.side_effect = self.error_response
        self.flow.execute_flow_fm_21()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_synchronize.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
