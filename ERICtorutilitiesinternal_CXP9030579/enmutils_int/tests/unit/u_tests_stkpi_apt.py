#!/usr/bin/env python

import unittest2
from mock import patch, Mock, PropertyMock

from enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow import STKPIFlow
from enmutils_int.lib.workload import apt_01
from enmutils.lib.exceptions import EnvironError
from testslib import unit_test_utils

NODE_NAME = "node"


class STKPIApt01Tests(unittest2.TestCase):

    APT_01_all_ran_core_NODES = {"ERBS": ["ieatnetsimv9002-10_LTE03ERBS00001"],
                                 "SGSN": ["CORE01SGSN002", "CORE01SGSN003", "CORE01SGSN004"],
                                 "RadioNode": ["LTE45dg2ERBS00001"]}

    APT_01_transport_NODES = {"MINILINK_Indoor": ['CORE01MLTN6-0-1-01',
                                                  'CORE01MLTN6-0-1-02',
                                                  'CORE01MLTN6-0-1-03'],
                              "ROUTER_6000": ['CORE01SPFRER00001']}

    APT_01_radio_sgsn_NODES = {"SGSN": ["CORE01SGSN002", "CORE01SGSN003", "CORE01SGSN004"],
                               "RadioNode": ["LTE45dg2ERBS00001"]}

    APT_01_erbs_sgsn_NODES = {"SGSN": ["CORE01SGSN002", "CORE01SGSN003", "CORE01SGSN004"],
                              "ERBS": ["ieatnetsimv9002-10_LTE03ERBS00001"]}

    APT_01_only_sgsn_NODES = {"SGSN": ["CORE01SGSN002", "CORE01SGSN003", "CORE01SGSN004"]}

    def setUp(self):
        unit_test_utils.setup()
        self.flow = STKPIFlow()
        self.flow.ALL_NODES = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get_all_keys')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.check_nodes_present_in_persistence_db')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.assertions_utils.AssertionValues.update')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.get_ran_core_nodes')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.get_transport_nodes')
    def test_execute_flow__success(self, mock_transport, mock_ran, mock_update, *_):
        self.flow.DEFAULT_NODES = self.APT_01_erbs_sgsn_NODES
        self.flow.teardown_list = []
        self.flow.execute_flow()
        self.assertEqual(1, mock_update.call_count)
        self.assertEqual(1, mock_ran.call_count)
        self.assertEqual(1, mock_transport.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get_all_keys',
           side_effect=AttributeError("Error"))
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.EnvironError')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_error_as_exception')
    def test_execute_flow__attribute_error(self, mock_add_error, mock_environ, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)
        self.assertEqual(1, mock_environ.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get_all_keys',
           side_effect=ValueError("Error"))
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_error_as_exception')
    def test_execute_flow__generic_error(self, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get')
    def test_check_nodes_present_in_persistence_db__success(self, mock_get, _):
        node = Mock()
        node.profiles = []
        mock_get.return_value = node
        self.flow.DEFAULT_NODES = {"ERBS": [node]}
        self.flow.check_nodes_present_in_persistence_db([node])
        self.assertEqual(1, node.add_profile.call_count)
        self.assertEqual(self.flow.ALL_NODES, [node])

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.allocate_nodes')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get')
    def test_check_nodes_present_in_persistence_db__uses_service(self, mock_get, mock_allocate, _):
        node = Mock()
        node.profiles = []
        mock_get.return_value = node
        self.flow.DEFAULT_NODES = {"ERBS": [node]}
        self.flow.check_nodes_present_in_persistence_db([node])
        self.assertEqual(1, mock_allocate.call_count)
        self.assertEqual(self.flow.ALL_NODES, [node])

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.allocate_nodes')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get')
    def test_check_nodes_present_in_persistence_db__node_already_added(self, mock_get, *_):
        node = Mock()
        node.profiles = [self.flow.NAME]
        mock_get.return_value = node
        self.flow.DEFAULT_NODES = {"ERBS": [NODE_NAME]}
        self.flow.check_nodes_present_in_persistence_db([NODE_NAME])
        self.assertEqual(0, node.add_profile.call_count)
        self.assertEqual(self.flow.ALL_NODES, [node])

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.allocate_nodes')
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.persistence.get')
    def test_check_nodes_present_in_persistence_db__not_in_keys(self, mock_get, *_):
        self.flow.DEFAULT_NODES = {"ERBS": ["node1"]}
        self.assertRaises(ValueError, self.flow.check_nodes_present_in_persistence_db, NODE_NAME)
        self.assertEqual(0, mock_get.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_ran_core_nodes__success_erbs_and_sgsn(self, mock_print):
        self.flow.DEFAULT_NODES = self.APT_01_erbs_sgsn_NODES
        self.flow.get_ran_core_nodes()
        self.assertEqual(2, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_ran_core_nodes__success_radio_and_sgsn(self, mock_print):
        self.flow.DEFAULT_NODES = self.APT_01_radio_sgsn_NODES
        self.flow.get_ran_core_nodes()
        self.assertEqual(2, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_ran_core_nodes__both_erbs_and_radio_nodes_given(self, mock_print):
        self.flow.DEFAULT_NODES = self.APT_01_all_ran_core_NODES
        with self.assertRaises(EnvironError):
            self.flow.get_ran_core_nodes()
        self.assertEqual(0, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_ran_core_nodes__only_sgsn_nodes_given(self, mock_print):
        self.flow.DEFAULT_NODES = self.APT_01_only_sgsn_NODES
        self.flow.get_ran_core_nodes()
        self.assertEqual(0, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_ran_core_nodes__no_nodes(self, mock_print):
        self.flow.DEFAULT_NODES = {}
        self.flow.get_ran_core_nodes()
        self.assertEqual(0, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_transport_nodes__success(self, mock_print):
        self.flow.DEFAULT_NODES = self.APT_01_transport_NODES
        self.flow.get_transport_nodes()
        self.assertEqual(2, mock_print.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.STKPIFlow.add_nodes_to_list_to_print')
    def test_get_transport_nodes__no_match(self, mock_print):
        self.flow.DEFAULT_NODES = {}
        self.flow.get_transport_nodes()
        self.assertEqual(0, mock_print.call_count)

    def test_add_nodes_to_list_to_print__success(self):
        nodes = []
        self.flow.add_nodes_to_list_to_print([NODE_NAME] * 3, nodes)
        self.assertEqual(3, len(nodes))

    @patch('enmutils_int.lib.workload.apt_01.STKPIFlow.execute_flow')
    def test_apt_01__profile_coverage(self, mock_execute):
        apt_01.APT_01().run()
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.allocate_nodes')
    def test_add_nodes_to_profile__calls_add_profile_when_no_service(self, *_):
        node = Mock()
        self.flow.ALL_NODES = [node]
        self.flow.add_nodes_to_profile()
        self.assertTrue(node.add_profile.called)
        self.assertEqual(node._is_exclusive, True)

    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow.nodemanager_adaptor.allocate_nodes')
    def test_add_nodes_to_profile__calls_allocate_nodes_with_service(self, mock_allocate, *_):
        node = Mock()
        self.flow.ALL_NODES = [node]
        self.flow.add_nodes_to_profile()
        self.assertTrue(mock_allocate.called)
        self.assertEqual(node._is_exclusive, True)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
