#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow import NcmVpnSd01Flow
from enmutils_int.lib.workload import ncm_vpn_sd_01
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class NcmVpnSd01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(node_id="ML_01"), Mock(node_id="ML_02")]
        self.ncm_vpn_sd_01 = ncm_vpn_sd_01.NCM_VPN_SD_01()
        self.flow = NcmVpnSd01Flow()
        self.flow.NAME = "NCM_VPN_SD_01"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Administrator"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.execute_flow')
    def test_run__in_ncm_vpn_sd_01_is_successful(self, mock_execute_flow):
        self.ncm_vpn_sd_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.check_sync_and_remove')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.create_profile_users")
    def test_execute_flow__success(self, mock_create_profile_users, mock_keep_running, mock_realign, mock_log,
                                   mock_json, mock_nodes, mock_nodes_list, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_nodes_list.return_value = self.nodes
        mock_nodes.return_value = (self.nodes, [])
        self.flow.execute_flow()
        mock_json.assert_called_with({"serviceType": "L3_VPN", "nodes": ["ML_01", "ML_02"]})
        self.assertEqual(3, len(mock_realign.call_args[0]))
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.json.dumps")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.check_sync_and_remove')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.create_profile_users")
    def test_execute_flow__add_error_as_exception(self, mock_create_profile_users, mock_keep_running, mock_realign,
                                                  mock_log, mock_error, mock_nodes, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = ([], self.nodes)
        mock_realign.side_effect = Exception
        self.flow.execute_flow()
        self.assertIsInstance(mock_error.call_args[0][0], EnmApplicationError)
        self.assertEqual(1, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.json.dumps")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.check_sync_and_remove')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.NcmVpnSd01Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow.fetch_ncm_vm")
    def test_execute_flow__raises_environ_error(self, mock_exception, mock_create_profile_users, mock_keep_running, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_exception.return_value = "1.1.1.1"
        self.assertRaises(EnvironError, self.flow.execute_flow())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
