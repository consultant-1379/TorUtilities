#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow import NcmMef01Flow
from enmutils_int.lib.workload import ncm_mef_01
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class NcmMef01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.ncm_mef_01 = ncm_mef_01.NCM_MEF_01()
        self.flow = NcmMef01Flow()
        self.flow.NAME = "NCM_MEF_01"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Administrator"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.execute_flow')
    def test_run__in_ncm_mef_01_is_successful(self, mock_execute_flow):
        self.ncm_mef_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.create_profile_users")
    def test_execute_flow__success(self, mock_create_profile_users, mock_keep_running, mock_realign, mock_log, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        mock_realign.assert_call(self.user, "/ncm/rest/management/realign")
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.fetch_ncm_vm")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.create_profile_users")
    def test_execute_flow__add_error_as_exception(self, mock_create_profile_users, mock_keep_running, mock_realign,
                                                  mock_log, mock_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_realign.side_effect = Exception
        self.flow.execute_flow()
        self.assertIsInstance(mock_error.call_args[0][0], EnmApplicationError)
        self.assertEqual(2, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.ncm_rest_query")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.keep_running')
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.NcmMef01Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow.fetch_ncm_vm")
    def test_execute_flow__raises_environ_error(self, mock_exception, mock_create_profile_users, mock_keep_running, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_exception.return_value = "1.1.1.1"
        self.assertRaises(EnvironError, self.flow.execute_flow())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
