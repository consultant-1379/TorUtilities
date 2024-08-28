#!/usr/bin/env python

import unittest2
from mock import patch, Mock
from testslib import unit_test_utils

from enmutils_int.lib.profile_flows.fm_flows.fm_27_flow import Fm27


class Fm27UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Fm27()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["FM_Administrator"]
        self.flow.NUMBER_OF_ROUTING_FILES = 20

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.Fm27.get_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.load_mgr.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.Fm27.create_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.FmAlarmRoute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.split_list_into_sublists")
    def test_execute_flow_success(self, mock_split_list_into_sublists, mock_log, mock_fm_route, *_):
        mock_split_list_into_sublists.return_value = [Mock()]
        self.flow.execute_flow()

        self.assertTrue(mock_fm_route.called)
        self.assertTrue(mock_split_list_into_sublists.called)
        self.assertTrue(mock_log.logger.info.call_count, 3)

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.Fm27.get_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.load_mgr.wait_for_setup_profile")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.sleep_until_profile_persisted")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.Fm27.create_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.FmAlarmRoute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.split_list_into_sublists")
    def test_execute_flow_throws_exception(self, mock_split_list_into_sublists, mock_log, mock_fm_route, *_):
        mock_split_list_into_sublists.return_value = [Mock()]
        mock_route_object = Mock()
        mock_route_object.create.side_effect = Exception()
        mock_fm_route.return_value = mock_route_object
        self.flow.execute_flow()

        self.assertTrue(mock_fm_route.called)
        self.assertTrue(mock_split_list_into_sublists.called)
        self.assertTrue(mock_log.logger.info.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
