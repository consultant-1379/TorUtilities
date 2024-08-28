#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow import NcmMef03Flow
from enmutils_int.lib.workload import ncm_mef_03
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class NcmMef03UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.ncm_mef_03 = ncm_mef_03.NCM_MEF_03()
        self.flow = NcmMef03Flow()
        self.flow.NAME = "NCM_MEF_03"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.execute_flow')
    def test_run__in_ncm_mef_03_is_successful(self, mock_execute_flow):
        self.ncm_mef_03.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.perform_ncm_db_activites")
    def test_execute_flow__success(self, mock_db_ops, mock_create_profile_users, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_db_ops.called)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.perform_ncm_db_activites")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.NcmMef03Flow.add_error_as_exception")
    def test_execute_flow__add_error_as_exception(self, mock_error, mock_db_ops, mock_create_profile_users, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_db_ops.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.fetch_ncm_vm',
           return_value=unit_test_utils.generate_configurable_ip())
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.ncm_run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.log.logger.debug")
    def test_perform_ncm_db_activites__success(self, mock_debug, *_):
        self.flow.perform_ncm_db_activites()
        self.assertEqual(6, mock_debug.call_count)

    @patch("enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow.fetch_ncm_vm',
           return_value=[])
    def test_perform_ncm_db_activites__raises_environ_error(self, *_):
        self.assertRaises(EnvironError, self.flow.perform_ncm_db_activites)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
