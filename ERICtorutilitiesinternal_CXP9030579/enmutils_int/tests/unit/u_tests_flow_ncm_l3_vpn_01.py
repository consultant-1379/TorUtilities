#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow import NcmL3Vpn01Flow
from enmutils_int.lib.workload import ncm_l3_vpn_01
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class NcmL3VPN01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.ncm_l3_vpn_01 = ncm_l3_vpn_01.NCM_L3_VPN_01()
        self.flow = NcmL3Vpn01Flow()
        self.flow.NAME = "NCM_L3_VPN_01"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Administrator"]
        self.flow.SERVICE_PREFIX = "service_LCM_"
        self.flow.SERVICE_TYPE = "L3_VPN"
        self.flow.MAX_SERVICES = 2
        self.flow.NUMBER_OF_RUNS = 2
        self.flow.SLEEP_TIME_AFTER_ACT = 0
        self.flow.SLEEP_TIME_AFTER_DEACT = 0
        self.flow.RESTORE_FILE_NAME = "/tmp/ncm_backup.tar.gz"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.execute_flow')
    def test_run__in_ncm_l3_vpn_01_is_successful(self, mock_execute_flow):
        self.ncm_l3_vpn_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.lcm_db_restore')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.vpn_lcm_serv_act_deact')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.log.logger.debug")
    def test_execute_flow__restore_success(self, mock_log, mock_op, *_):
        self.flow.RUN_RESTORE = True
        self.flow.execute_flow()
        self.assertEqual(2, mock_log.call_count)
        self.assertEqual(4, mock_op.call_count)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.vpn_lcm_serv_act_deact')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.log.logger.debug")
    def test_execute_flow__success_without_restore(self, mock_log, mock_op, *_):
        self.flow.RUN_RESTORE = False
        self.flow.execute_flow()
        self.assertEqual(1, mock_log.call_count)
        self.assertEqual(4, mock_op.call_count)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.sleep_until_day')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.lcm_db_restore')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.add_error_as_exception")
    def test_execute_flow__add_error_as_exception(self, mock_error, mock_db_res, *_):
        self.flow.RUN_RESTORE = True
        mock_db_res.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.NcmL3Vpn01Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.fetch_ncm_vm", return_value="1.1.1.1")
    def test_execute_flow__raises_environ_error_exception(self, *_):
        self.assertRaises(EnvironError, self.flow.execute_flow())

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.ncm_rest_query")
    def test_vpn_lcm_serv_act_deact__success(self, mock_realign, *_):
        self.flow.LIST_OF_LCM_SERVICES = []
        self.flow.vpn_lcm_serv_act_deact(self.user, "rest_act", 0, 1, "Act")
        self.assertTrue(mock_realign.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.json.dumps")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow.ncm_rest_query")
    def test_vpn_lcm_serv_act_deact__raises_enm_application_error(self, mock_realign, *_):
        self.flow.LIST_OF_LCM_SERVICES = ["NcmVpnLcm"]
        mock_realign.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.flow.vpn_lcm_serv_act_deact, self.user, "rest_deact", 0, 2, "Deact")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
