#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow import CmExport02
from testslib import unit_test_utils


class Cmexport02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.users = [Mock(), Mock(), Mock()]
        self.flow = CmExport02()
        self.flow.TOTAL_NODES = 5
        self.flow.NUM_USERS = 1
        self.flow.ADMIN_ROLE = ['Cmedit_Administrator']
        self.flow.OPERATOR_ROLE = ['Cmedit_Operator']
        self.flow.NUMBER_OF_EXPORTS = 3
        self.flow.NUMBER_OF_NETWORK_EXPORTS = 2
        self.flow.FILETYPE = ['dynamic', 'dynamic']
        self.flow.VALIDATION_TIMEOUT = 0.1
        self.flow.NUM_NODES_FOR_EXPORT = 2
        self.flow.THREAD_QUEUE_TIMEOUT = 0.1
        self.flow.FILE_COMPRESSION = "gzip"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.identifier', return_value='123')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport')
    def test_create_export_objects__is_successful(self, mock_cmexport, mock_identifier, _):
        self.flow.create_export_objects(users=self.users)
        self.assertEqual(mock_cmexport.call_count, 3)
        mock_cmexport.assert_called_with(
            name='{0}_EXPORT'.format(mock_identifier), user=self.users[2], nodes=[],
            verify_timeout=self.flow.VALIDATION_TIMEOUT, filetype=self.flow.FILETYPE[0],
            file_compression=self.flow.FILE_COMPRESSION)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.identifier',
           return_value='123')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport')
    def test_create_export_objects__selects_radio_nodes_for_100_node_export(self, mock_cmexport, mock_identifier,
                                                                            mock_nodes):
        self.flow.NUMBER_OF_NETWORK_EXPORTS = 0
        self.flow.SMALL_EXPORT_PRIMARY_TYPE = "RadioNode"
        node, node1, node2 = Mock(), Mock(), Mock()
        node.primary_type, node1.primary_type, node2.primary_type = "ERBS", "RadioNode", "SBG-IS"
        mock_nodes.return_value = [node, node1, node2]
        self.flow.create_export_objects(users=self.users)
        self.assertEqual(mock_cmexport.call_count, 1)

        mock_cmexport.assert_called_with(
            name='{0}_EXPORT'.format(mock_identifier), user=self.users[2], nodes=[node1],
            verify_timeout=self.flow.VALIDATION_TIMEOUT, filetype=self.flow.FILETYPE[0],
            file_compression=self.flow.FILE_COMPRESSION)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport02.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow.CmExport')
    def test_execute_flow_is_successful(self, mock_cmexport, mock_create_and_execute_threads, mock_create_users, *_):
        mock_create_users.return_value = self.users
        self.flow.execute_flow()
        self.assertEqual(mock_cmexport.call_count, 3)
        self.assertTrue(mock_create_and_execute_threads.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
