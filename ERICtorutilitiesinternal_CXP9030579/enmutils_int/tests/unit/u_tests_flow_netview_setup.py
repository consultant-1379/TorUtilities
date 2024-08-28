#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock

from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow import NetviewSetupFlow


class NetviewSetupFlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.mock_node = Mock()
        self.mock_node.node_id = "LTE06dg2ERBS00014"
        self.flow = NetviewSetupFlow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Cmedit_Administrator"]
        self.flow.TOTAL_NODES = 250
        self.mock_location = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations", return_value=[])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.create_profile_users")
    def test_execute_flow__in_netview_setup_flow_success_no_existing_locations(
            self, mock_create_users, mock_nodes_list, mock_node_location, mock_add_error_as_exception, mock_log, *_):
        mock_location = Mock()
        mock_node_location.return_value = mock_location
        mock_nodes_list.return_value = [self.mock_node]
        self.flow.execute_flow()

        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_location.create_geo_location.called)
        self.assertTrue(mock_location.create_geo_point.called)
        self.assertTrue(self.flow.number_of_locations_created == 1)
        self.assertTrue(mock_log.logger.info.called)
        self.assertFalse(mock_add_error_as_exception.called)

    def test_execute_flow__in_netview_setup_flow_success_with_existing_locations(self):
        with patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations",
                   return_value=[Mock()]),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
                      new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.delete_location_on_node")\
                as mock_delete,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log") as mock_log,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation")\
                as mock_node_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
                      "get_nodes_list_by_attribute") as mock_nodes_list,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow"
                      ".create_profile_users") as mock_create_users:
            mock_location = Mock()
            mock_node_location.return_value = mock_location
            mock_nodes_list.return_value = [self.mock_node]
            self.flow.execute_flow()

            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_location.create_geo_location.called)
            self.assertTrue(mock_location.create_geo_point.called)
            self.assertTrue(self.flow.number_of_locations_created == 1)
            self.assertTrue(mock_log.logger.info.called)
            self.assertTrue(mock_delete.called)
            self.assertFalse(mock_add_error_as_exception.called)

    def test_execute_flow__in_netview_setup_flow_get_location_raises_exception(self):
        with patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations",
                   side_effect=Exception()),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
                      new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.delete_location_on_node")\
                as mock_delete,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log") as mock_log,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation")\
                as mock_node_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
                      "get_nodes_list_by_attribute") as mock_nodes_list,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow"
                      ".create_profile_users") as mock_create_users:
            mock_location = Mock()
            mock_node_location.return_value = mock_location
            mock_nodes_list.return_value = [self.mock_node]
            self.flow.execute_flow()

            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_location.create_geo_location.called)
            self.assertTrue(self.flow.number_of_locations_created == 1)
            self.assertTrue(mock_log.logger.info.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertTrue(mock_location.create_geo_point.called)
            self.assertFalse(mock_delete.called)

    def test_execute_flow__in_netview_setup_flow_delete_location_raises_exception(self):
        with patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations",
                   return_value=[Mock()]),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
                      new_callable=PropertyMock),\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.delete_location_on_node"
                      "", side_effect=Exception()) as mock_delete,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log"
                      "") as mock_log,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception") as mock_add_error_as_exception,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation"
                      "") as mock_node_location,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
                      "get_nodes_list_by_attribute") as mock_nodes_list,\
                patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow"
                      ".create_profile_users") as mock_create_users:
            mock_location = Mock()
            mock_node_location.return_value = mock_location
            mock_nodes_list.return_value = [self.mock_node]
            self.flow.execute_flow()

            self.assertTrue(mock_create_users.called)
            self.assertTrue(mock_location.create_geo_location.called)
            self.assertTrue(self.flow.number_of_locations_created == 1)
            self.assertTrue(mock_log.logger.info.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertTrue(mock_location.create_geo_point.called)
            self.assertTrue(mock_delete.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations", return_value=[])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.create_profile_users")
    def test_execute_flow__in_netview_setup_flow_create_latitude_and_longitude_raises_exception(
            self, mock_create_users, mock_nodes_list, mock_node_location, mock_add_error_as_exception, mock_log, *_):
        mock_location = Mock()
        mock_node_location.return_value = mock_location
        mock_location.create_latitude_and_longitude.side_effect = Exception()
        mock_nodes_list.return_value = [self.mock_node]
        self.flow.execute_flow()

        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_location.create_geo_location.called)
        self.assertTrue(self.flow.number_of_locations_created == 0)
        self.assertTrue(mock_log.logger.info.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_location.create_geo_point.called)

    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.get_existing_locations",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.log")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NodeLocation")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow.NetviewSetupFlow.create_profile_users")
    def test_execute_flow__in_netview_setup_flow_create_geo_point_raises_exception(
            self, mock_create_users, mock_nodes_list, mock_node_location, mock_add_error_as_exception, mock_log, *_):
        mock_location = Mock()
        mock_location.create_geo_point.side_effect = Exception()
        mock_node_location.return_value = mock_location
        mock_nodes_list.return_value = [self.mock_node]
        self.flow.execute_flow()

        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_location.create_geo_location.called)
        self.assertTrue(self.flow.number_of_locations_created == 0)
        self.assertTrue(mock_log.logger.info.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_location.create_geo_point.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
