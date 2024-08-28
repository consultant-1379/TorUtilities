#!/usr/bin/env python
import unittest2
from requests.exceptions import HTTPError
from mock import patch, Mock, mock_open

from testslib import unit_test_utils

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.netview import (NodeLocation, update_node_location_by_rest, get_node_location_by_rest,
                                      get_existing_locations, delete_location_on_node, get_plm_dynamic_content,
                                      get_physical_links_on_nodes_by_rest_call, EnvironError)


class NetvizViewFlowUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.mock_node = Mock()
        self.mock_node.node_id = "LTE06dg2ERBS00014"
        self.mock_node.poid = 9456856834908
        self.location = NodeLocation(self.user, self.mock_node.node_id, 1.3456, 1.3456)

    def teardown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_node_location_create_geo_location(self, mock_log, mock_execute_command):

        self.location.create_geo_location()

        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_execute_command.called)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_node_location_create_geo_point(self, mock_log, mock_execute_command):

        self.location.create_geo_point()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_execute_command.called)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_create_latitude_and_longitude(self, mock_log, mock_execute_command):

        self.location.create_latitude_and_longitude()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_execute_command.called)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_delete_location(self, mock_log, mock_execute_command):

        self.location.delete()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_execute_command.called)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_node_location_teardown_success(self, mock_log, mock_execute_command):

        self.location._teardown()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_execute_command.called)
        self.assertEqual(mock_log.logger.debug.call_count, 3)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_node_location_teardown_exception(self, mock_log, mock_execute_command):
        mock_execute_command.side_effect = Exception()

        self.location._teardown()
        self.assertTrue(mock_log.logger.debug.called)
        self.assertEqual(mock_log.logger.debug.call_count, 2)
        self.assertTrue(mock_log.logger.error.called)
        self.assertEqual(mock_log.logger.error.call_count, 1)

    @patch("enmutils_int.lib.netview.log")
    def test_update_node_location_by_rest_success(self, mock_log):
        update_node_location_by_rest(self.user, "LTE997", 1.5453, 1.6564)

        self.assertTrue(self.user.put.called)
        self.assertTrue(mock_log.logger.info.called)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netview.json")
    @patch("enmutils_int.lib.netview.log")
    def test_update_node_location_by_rest_retries_on_http_error(self, mock_log, *_):
        self.user.put.side_effect = [HTTPError(), Mock()]
        update_node_location_by_rest(self.user, "LTE997", 1.5453, 1.6564)

        self.assertTrue(self.user.put.called)
        self.assertEqual(self.user.put.call_count, 2)
        self.assertTrue(mock_log.logger.info.called)
        self.assertEqual(mock_log.logger.info.call_count, 3)

    @patch("enmutils_int.lib.netview.json")
    @patch("enmutils_int.lib.netview.log")
    def test_get_node_location_by_rest_success(self, mock_log, *_):
        response = Mock()
        response.json.return_value = {"treeNodes": [{"geoCoordinates": {"latLng": [1.453453, 2.234453335]}}]}
        self.user.post.return_value = response

        get_node_location_by_rest(self.user, self.mock_node.node_id, self.mock_node.node_poid)

        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.logger.info.called)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netview.json")
    @patch("enmutils_int.lib.netview.log")
    def test_get_node_location_by_rest_retries_on_http_error(self, mock_log, *_):
        response = Mock()
        response.json.return_value = {"treeNodes": [{"geoCoordinates": {"latLng": [1.453453, 2.234453335]}}]}
        self.user.post.side_effect = [HTTPError(), response]

        get_node_location_by_rest(self.user, self.mock_node.node_id, self.mock_node.node_poid)

        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.logger.info.called)
        self.assertEqual(mock_log.logger.info.call_count, 3)

    @patch("enmutils_int.lib.netview.json")
    @patch("enmutils_int.lib.netview.log.logger.info")
    def test_get_node_location_by_rest__raises_exception_when_no_valid_json(self, *_):
        response = Mock()
        response.json.return_value = ValueError
        self.user.post.return_value = response

        self.assertRaises(EnmApplicationError, get_node_location_by_rest, self.user, self.mock_node.node_id,
                          self.mock_node.node_poid)

        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.netview.json")
    @patch("enmutils_int.lib.netview.log.logger.info")
    def test_get_node_location_by_rest__raises_indexerror(self, *_):
        response = Mock()
        response.json.return_value = {"treeNodes": [{"geoCoordinates": {"latLng": []}}]}
        self.user.post.return_value = response

        self.assertRaises(EnmApplicationError, get_node_location_by_rest, self.user, self.mock_node.node_id,
                          self.mock_node.node_poid)

        self.assertTrue(self.user.post.called)

    def test_get_existing_locations(self):
        get_output_1 = Mock()
        get_output_1.groups.return_value = True
        mock_group = Mock()
        mock_group.find_by_label.return_value = ["LTE997"]
        get_output_2 = Mock()
        get_output_2.groups.return_value = [[]]
        mock_response = Mock()
        mock_response.is_complete.return_value = True
        mock_response.get_output.side_effect = [get_output_1, get_output_2]
        self.user.enm_execute.return_value = mock_response
        get_existing_locations(self.user)

        self.assertEqual(mock_response.get_output.call_count, 2)

    def test_get_existing_locations_response_not_complete(self):
        get_output_1 = Mock()
        get_output_1.groups.return_value = True
        mock_response = Mock()
        mock_response.is_complete.return_value = False
        mock_response.get_output.side_effect = [get_output_1]
        self.user.enm_execute.return_value = mock_response
        get_existing_locations(self.user)

        self.assertTrue(mock_response.is_complete.called)
        self.assertFalse(mock_response.get_output.called)

    @patch("enmutils_int.lib.netview.execute_command_on_enm_cli")
    @patch("enmutils_int.lib.netview.log")
    def test_delete_location_on_node(self, mock_log, mock_execute_command):

        delete_location_on_node(self.user, "LTE997")
        self.assertTrue(mock_execute_command.called)
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.netview.log")
    def test_get_physical_links_on_nodes_by_rest_call_success(self, mock_log):
        mock_response = Mock()
        mock_response.json.return_value = {"relationTypeToTargets": {"X2_eNB-gNB": ["link"], "TRANSPORT_LINK": ["some other link"]}}
        self.user.post.return_value = mock_response
        get_physical_links_on_nodes_by_rest_call(self.user, ["8573875389"])

        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_response.json.called)
        self.assertTrue(mock_log.logger.info.called)
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.netview.log")
    def test_get_physical_links_on_nodes_by_rest_call_raises_EnvironError1(self, mock_log):
        mock_response = Mock()
        mock_response.json.return_value = {"relationTypeToTargets": {}}

        self.user.post.return_value = mock_response
        self.assertRaises(EnvironError, get_physical_links_on_nodes_by_rest_call, self.user, ["8573875389"])
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_response.json.called)
        self.assertFalse(mock_log.logger.info.called)

    @patch("enmutils_int.lib.netview.log")
    def test_get_physical_links_on_nodes_by_rest_call_raises_EnvironError2(self, mock_log):
        mock_response = Mock()
        mock_response.json.return_value = {}

        self.user.post.return_value = mock_response
        self.assertRaises(EnvironError, get_physical_links_on_nodes_by_rest_call, self.user, ["8573875389"])
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_response.json.called)
        self.assertFalse(mock_log.logger.info.called)

    @patch("enmutils_int.lib.netview.log")
    def test_get_physical_links_on_nodes_by_rest_call_raises_EnmApplicationError(self, mock_log):
        mock_response = Mock()
        mock_response.json.side_effect = ValueError

        self.user.post.return_value = mock_response
        self.assertRaises(EnmApplicationError, get_physical_links_on_nodes_by_rest_call, self.user, ["8573875389"])
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_response.json.called)
        self.assertFalse(mock_log.logger.info.called)

    @patch("enmutils_int.lib.netview.persistence")
    def test_get_plm_dynamic_content_is_successful(self, mock_persistence):
        mock_persistence.has_key.return_value = True
        mock_persistence.get.return_value = ['/home/enmutils/dynamic_content/PLMimport1.csv']
        data = '\n'.join(["link1,CORE01SGSN002,100/1,CORE01SGSN001,100/1",
                          "link2,CORE01SGSN004,100/1,CORE01SGSN003,100/1",
                          "link3,CORE01SGSN004,100/2,CORE01SGSN003,100/2"])
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            with open(mock_open_file(), 'rb'):
                actual_result = get_plm_dynamic_content()
                self.assertEqual(actual_result, ['CORE01SGSN004', 'CORE01SGSN002', 'CORE01SGSN003', 'CORE01SGSN001'])

    @patch("enmutils_int.lib.netview.persistence")
    def test_get_plm_dynamic_content_raises_EnvironError_if_no_imported_files(self, mock_persistence):
        mock_persistence.has_key.return_value = False
        self.assertRaises(EnvironError, get_plm_dynamic_content)

    @patch("enmutils_int.lib.netview.persistence")
    def test_get_plm_dynamic_content_raises_EnvironError_while_fetching_from_persistence(self, mock_persistence):
        mock_persistence.has_key.side_effect = Exception
        self.assertRaises(EnvironError, get_plm_dynamic_content)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
