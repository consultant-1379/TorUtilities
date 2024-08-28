#!/usr/bin/env python

import unittest2
from mock import patch, mock_open

from enmutils_int.lib.node_parse import (set_nodes_ranges, verify_nodes_on_enm, EnmApplicationError,
                                         parse_command_result_for_ne_values, update_row_with_enm_values,
                                         get_node_data_from_xml, get_node_data, update_row_values,
                                         get_node_names_from_xml)
from testslib import unit_test_utils

CMD_RESPONSE = ['FDN : NetworkElement=netsim_LTE08ERBS00011',
                'neProductVersion : null',
                'neType : ERBS',
                'ossModelIdentity : null',
                'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,'
                'MeContext=netsim_LTE08ERBS00011',
                'release : 17.Q4',
                'FDN : NetworkElement=netsim_LTE08ERBS00006',
                'neProductVersion : [{identity=CXP9018505/27, revision=R74A}]',
                'neType : ERBS',
                'ossModelIdentity : 19.Q3-J.4.50',
                'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,'
                'MeContext=netsim_LTE08ERBS00006',
                'release : 17.Q4',
                'FDN : NetworkElement=netsim_LTE08ERBS00004',
                'neProductVersion : [{identity=CXP9018505/27, revision=R74A}]',
                'neType : ERBS',
                'ossModelIdentity : 19.Q3-J.4.50',
                'ossPrefix : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,'
                'MeContext=netsim_LTE08ERBS00004',
                'release : 17.Q4']


class NodeParseUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.node_parse.parse_command_result_for_ne_values')
    @patch('enmutils_int.lib.node_parse.get_workload_admin_user')
    def test_update_row_with_enm_values__supplies_matched_indexes(self, mock_user, mock_parse):
        mock_user.return_value.enm_execute.return_value.get_output.return_value = CMD_RESPONSE
        update_row_with_enm_values(["Node"])
        mock_parse.assert_any_call(CMD_RESPONSE[0:6], {})

    @patch('enmutils_int.lib.node_parse.parse_command_result_for_ne_values')
    @patch('enmutils_int.lib.node_parse.log.logger.debug')
    @patch('enmutils_int.lib.node_parse.get_workload_admin_user')
    def test_update_row_with_enm_values__logs_defaulting_to_arne_data(self, mock_user, mock_debug, _):
        mock_user.return_value.enm_execute.return_value.get_output.side_effect = Exception("error")
        update_row_with_enm_values(["Node"])
        mock_debug.assert_called_with("Could not retrieve ENM node information, error encountered: error. "
                                      "Information available in the supplied .csv file will be used.")

    @patch('enmutils_int.lib.node_parse.set_nodes_ranges', return_value=[0, 162])
    @patch('enmutils_int.lib.node_parse.verify_nodes_on_enm', return_value=["Node{0}".format(_) for _ in range(161)])
    @patch('enmutils_int.lib.node_parse.update_row_with_enm_values', return_value={"Node1": {}})
    @patch('enmutils_int.lib.node_parse.update_row_values')
    @patch('enmutils_int.lib.node_parse.get_node_data_from_xml')
    def test_get_node_data__updates_node_if_created_on_enm(self, mock_data, mock_update, mock_enm_values, *_):
        mock_data.return_value = [{'primary_type': 'MLTN', 'node_ip': 'ip', 'mim_version': '17A',
                                   'node_id': 'Node{0}'.format(_), 'managed_element_type': '',
                                   'oss_model_identity': '-', 'netsim_fqdn': 'netsim', 'identity': '',
                                   'node_version': '', 'simulation': '', 'subnetwork': 'NetW', 'revision': ''}
                                  for _ in range(162)]
        _, not_created = get_node_data("some_file")
        self.assertEqual(1, mock_update.call_count)
        self.assertListEqual(["Node161"], not_created)
        self.assertEqual(2, mock_enm_values.call_count)

    def test_update_row_values__only_updates_matching_keys(self):
        sub = "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1"
        expected = {'model_identity': '-', 'primary_type': 'ERBS', 'node_ip': 'ip', 'mim_version': '17A',
                    'oss_prefix': '{0},MeContext=netsim_LTE08ERBS00011'.format(sub), 'node_id': 'Node3',
                    'managed_element_type': '', 'netsim_fqdn': 'netsim', 'identity': '', 'node_version': '',
                    'simulation': '', 'subnetwork': '{0}'.format(sub), 'revision': ''}
        row = {'node_id': "Node3", 'node_ip': "ip", 'mim_version': "17A", 'model_identity': "-",
               'subnetwork': "NetW", 'revision': "", 'identity': "", 'primary_type': "MLTN", 'node_version': "",
               'netsim_fqdn': "netsim", 'simulation': "", 'managed_element_type': ""}
        enm_data = {'primary_type': 'ERBS', 'model_identity': 'null', 'mim_version': 'null',
                    'oss_prefix': '{0},MeContext=netsim_LTE08ERBS00011'.format(sub), 'identity': 'null',
                    'release': 'null', 'subnetwork': '{0}'.format(sub), 'revision': 'null'}
        self.assertEqual(expected, update_row_values(row, enm_data))

    def test_parse_command_result_for_ne_values__parses_values_correctly(self):
        results_dict = {}
        expected = {'netsim_LTE08ERBS00011': {
            'primary_type': 'ERBS', 'model_identity': 'null', 'mim_version': 'null',
            'oss_prefix': 'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,MeContext='
                          'netsim_LTE08ERBS00011',
            'identity': 'null',
            'node_version': '17.Q4',
            'subnetwork': 'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1',
            'revision': 'null'}}
        self.assertEqual(parse_command_result_for_ne_values(CMD_RESPONSE[0:6], results_dict), expected)

    def test_set_nodes_ranges__sets_range_correctly_if_no_ranges_supplied(self):
        start, end = set_nodes_ranges(40)
        self.assertEqual(start, 0)
        self.assertEqual(end, 40)

    def test_set_nodes_ranges__sets_range_correctly_if_only_start_provided(self):
        start, end = set_nodes_ranges(40, 2)
        self.assertEqual(start, 1)
        self.assertEqual(end, 2)

    def test_set_nodes_ranges__sets_range_correctly_if_start_and_end_provided(self):
        start, end = set_nodes_ranges(40, 2, 4)
        self.assertEqual(start, 1)
        self.assertEqual(end, 4)

    @patch('enmutils_int.lib.node_parse.get_workload_admin_user')
    def test_verify_nodes_on_enm__returns_only_created_nodes(self, mock_user):
        mock_user.return_value.enm_execute.return_value.get_output.return_value = [
            u'', u'FDN : NetworkElement=Node1', u'', u'FDN : NetworkElement=Node2', u'', u'2 instance(s)']
        found_nodes = verify_nodes_on_enm(["Node1"])
        self.assertEqual(found_nodes[0], "Node1")
        self.assertEqual(1, len(found_nodes))

    @patch('enmutils_int.lib.node_parse.get_workload_admin_user')
    def test_verify_nodes_on_enm__raises_enm_applicaton_error(self, mock_user):
        mock_user.return_value.enm_execute.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, verify_nodes_on_enm, ["Node1"])

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.node_parse.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.node_parse.csv.DictReader')
    def test_get_node_data_from_xml__correctly_parses_csv(self, mock_reader, *_):
        mock_reader.return_value = [{'node_name': "Node1", 'node_ip': "ip", 'mim_version': "17A",
                                     'oss_model_identity': "11.22.33", 'security_state': 'ON', 'normal_user': "user",
                                     'normal_password': "pass", 'secure_user': "user", 'secure_password': "pass",
                                     'subnetwork': "NetW", 'invalid_fields': "", 'netconf': "111", 'snmp': "",
                                     'snmp_versions': "V1", 'snmp_community': "user", 'snmp_security_name': None,
                                     'snmp_authentication_method': "", 'snmp_encryption_method': "", 'revision': "",
                                     'identity': "", 'primary_type': "MLTN", 'node_version': "",
                                     'netsim_fqdn': "netsim", 'simulation': "", 'managed_element_type': "",
                                     'source_type': "", 'time_zone': "GMT", "group_data": "Group=RNC01"}]
        parsed_csv_data = get_node_data_from_xml("some_file")
        self.assertEqual("Node1", parsed_csv_data[0].get("node_id"))
        self.assertEqual("MLTN", parsed_csv_data[0].get("primary_type"))

    @patch('enmutils_int.lib.node_parse.filesystem.does_file_exist', return_value=False)
    def test_get_node_data_from_xml__raises_runtime_error_if_file_does_not_exist(self, _):
        self.assertRaises(RuntimeError, get_node_data_from_xml, "some_file")

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.node_parse.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.node_parse.csv.DictReader')
    def test_get_node_name_from_xml__correctly_parses_csv(self, mock_reader, *_):
        mock_reader.return_value = [{'node_name': "Node1"}, {'node_name': "Node2"}]
        parsed_csv_data = get_node_names_from_xml("some_file")
        self.assertListEqual(["Node1", "Node2"], parsed_csv_data)

    @patch('enmutils_int.lib.node_parse.filesystem.does_file_exist', return_value=False)
    def test_get_node_name_from_xml__raises_runtime_error_if_file_does_not_exist(self, _):
        self.assertRaises(RuntimeError, get_node_names_from_xml, "some_file")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
