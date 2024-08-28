#!/usr/bin/env python
from datetime import datetime
import unittest2
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.netview_flows.netview_01_flow import Netview01Flow


class Netview01FlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.mock_node = Mock()
        self.mock_node.node_id = "LTE06dg2ERBS00014"
        self.flow = Netview01Flow()
        self.flow.NUM_USERS = 1
        self.flow.TIME_INTERVAL = 15 * 60
        self.flow.USER_ROLES = ["NetworkViewer_Administrator"]

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_execute_flow__success(self):
        with patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow._sleep_until"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.state", new_callable=PropertyMock), \
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.timedelta"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.datetime") as mock_datetime,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.add_error_as_exception"
                      "") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.filter_nodes_having_poid_set"
                      "") as mock_filter_nodes_having_poid_set,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.update_node_location_by_rest"
                      "") as mock_update_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.get_node_location_by_rest"
                      "") as mock_get_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.keep_running"
                      "") as mock_keep_running,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.create_profile_users"
                      "") as mock_create_users,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.get_nodes_list_by_attribute"
                      "") as mock_get_allocated_nodes:
            mock_get_allocated_nodes.return_value = [self.mock_node]
            mock_filter_nodes_having_poid_set.return_value = [Mock(node_id="node1", poid="1234")]
            mock_create_users.return_value = [self.user]
            mock_keep_running.side_effect = [True, False]
            mock_current_time = Mock()
            mock_current_time.hour = 0
            mock_current_time.minute = 8
            mock_datetime.now.return_value = mock_current_time

            self.flow.execute_flow()
            self.assertTrue(mock_filter_nodes_having_poid_set.called)
            self.assertTrue(mock_get_allocated_nodes.called)
            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_keep_running.called)
            self.assertTrue(mock_get_location.called)
            self.assertTrue(mock_update_location.called)
            self.assertFalse(mock_add_error_as_exception.called)
            mock_get_location.assert_called_with(self.user, "node1", "1234")

    def test_execute_flow__success_minute_before_seven(self):
        with patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow._sleep_until"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.state", new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.timedelta"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.datetime") as mock_datetime,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.filter_nodes_having_poid_set"
                      "") as mock_filter_nodes_having_poid_set,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow."
                      "add_error_as_exception") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.update_node_location_by_rest"
                      "") as mock_update_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.get_node_location_by_rest"
                      "") as mock_get_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.keep_running"
                      "") as mock_keep_running,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.create_profile_users"
                      "") as mock_create_users,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.get_nodes_list_by_attribute"
                      "") as mock_get_allocated_nodes:

            mock_get_allocated_nodes.return_value = [self.mock_node]
            mock_filter_nodes_having_poid_set.return_value = [Mock(node_id="node1", poid="1234")]
            mock_create_users.return_value = [self.user]
            mock_keep_running.side_effect = [True, False]
            mock_current_time = Mock()
            mock_current_time.hour = 0
            mock_current_time.minute = 6
            mock_datetime.now.return_value = mock_current_time

            self.flow.execute_flow()
            self.assertTrue(mock_filter_nodes_having_poid_set.called)
            self.assertTrue(mock_get_allocated_nodes.called)
            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_keep_running.called)
            self.assertTrue(mock_get_location.called)
            self.assertTrue(mock_update_location.called)
            self.assertFalse(mock_add_error_as_exception.called)

    def test_execute_flow__no_nodes(self):
        with patch("enmutils_int.lib.profile.Profile._sleep_until"),\
                patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.timedelta"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.datetime"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.add_error_as_exception"
                      "") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.filter_nodes_having_poid_set"
                      "") as mock_filter_nodes_having_poid_set,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.update_node_location_by_rest"
                      "") as mock_update_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.get_node_location_by_rest"
                      "") as mock_get_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.keep_running"
                      "") as mock_keep_running,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.create_profile_users"
                      "") as mock_create_users,\
                patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute"
                      "") as mock_get_allocated_nodes:
            mock_get_allocated_nodes.return_value = []
            mock_filter_nodes_having_poid_set.return_value = []
            mock_create_users.return_value = [self.user]
            mock_keep_running.side_effect = [True, False]

            self.flow.execute_flow()
            self.assertTrue(mock_get_allocated_nodes.called)
            self.assertTrue(mock_filter_nodes_having_poid_set.called)
            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertFalse(mock_get_location.called)
            self.assertFalse(mock_update_location.called)
            self.assertFalse(mock_keep_running.called)

    def test_execute_flow__get_node_locations_raises_exception(self):
        with patch("enmutils_int.lib.profile.Profile._sleep_until"),\
                patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.timedelta"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.datetime"),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.add_error_as_exception"
                      "") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.filter_nodes_having_poid_set"
                      "") as mock_filter_nodes_having_poid_set,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.update_node_location_by_rest"
                      "") as mock_update_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.get_node_location_by_rest"
                      "", side_effect=Exception()) as mock_get_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.keep_running"
                      "") as mock_keep_running,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.Netview01Flow.create_profile_users"
                      "") as mock_create_users,\
                patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute"
                      "") as mock_get_allocated_nodes:
            mock_get_allocated_nodes.return_value = [self.mock_node]
            mock_filter_nodes_having_poid_set.return_value = [Mock(node_id="node1", poid="1234")]
            mock_create_users.return_value = [self.user]
            mock_keep_running.side_effect = [True, False]

            self.flow.execute_flow()
            self.assertTrue(mock_get_allocated_nodes.called)
            self.assertTrue(mock_filter_nodes_having_poid_set.called)
            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertTrue(mock_keep_running.called)
            self.assertTrue(mock_get_location.called)
            self.assertFalse(mock_update_location.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_01_flow.datetime")
    def test_set_start_time_increments_time_by_one_hour_after_23_hours(self, mock_datetime):
        night_hour_time = datetime.now().replace(hour=23, minute=10)
        mock_datetime.now.return_value = night_hour_time
        self.assertEqual(self.flow._set_start_time(), night_hour_time.replace(hour=0, minute=7))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
