#!/usr/bin/env python
from mock import patch, Mock
import unittest2
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.amos_flows.amos_flow import AmosCommonFlow


class AmosFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.amosflow = AmosCommonFlow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.grouper")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.construct_command_list")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.GenericFlow.download_tls_certs")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.get_radio_erbs_nodes", return_value=([Mock()],
                                                                                                     [Mock()]))
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.check_ldap_is_configured_on_radio_nodes")
    def test_perform_amos_prerequisites__is_successful_for_profiles_other_than_amos_05(self, mock_configure_ldap,
                                                                                       mock_log_debug, *_):
        users = ["AMOS_01_111111", "AMOS_01_222222", "AMOS_01_333333"]
        nodes = [Mock()] * 10
        self.amosflow.NAME = "AMOS_01"
        self.amosflow.COMMANDS = ["lt all", "cabx"]
        self.amosflow.COMMANDS_PER_ITERATION = 5
        mock_configure_ldap.return_value = [Mock(), Mock()]
        self.amosflow.perform_amos_prerequisites(users, nodes)
        self.assertEqual(mock_log_debug.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.grouper")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.construct_command_list")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.GenericFlow.download_tls_certs")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.get_radio_erbs_nodes", return_value=([Mock()],
                                                                                                     [Mock()]))
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.check_ldap_is_configured_on_radio_nodes")
    def test_perform_amos_prerequisites__is_successful_for_amos_05(self, mock_configure_ldap, mock_log_debug, *_):
        users = ["AMOS_05_111111", "AMOS_05_222222", "AMOS_05_333333"]
        nodes = [Mock()] * 10
        self.amosflow.NAME = "AMOS_05"
        self.amosflow.COMMANDS = ["lt all", "cabx"]
        self.amosflow.COMMANDS_PER_ITERATION = 5
        mock_configure_ldap.return_value = [Mock(), Mock()]
        self.amosflow.perform_amos_prerequisites(users, nodes)
        self.assertEqual(mock_log_debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.grouper")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.construct_command_list")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.GenericFlow.download_tls_certs")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.get_radio_erbs_nodes", return_value=([Mock()],
                                                                                                     [Mock()]))
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.AmosCommonFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_flow.check_ldap_is_configured_on_radio_nodes")
    def test_perform_amos_prerequisites__adds_error_as_exception(self, mock_configure_ldap, mock_log_debug,
                                                                 mock_add_error_as_exception, *_):
        users = ["AMOS_01_111111", "AMOS_01_222222", "AMOS_01_333333"]
        nodes = [Mock()] * 10
        self.amosflow.NAME = "AMOS_01"
        self.amosflow.COMMANDS = ["lt all", "cabx"]
        self.amosflow.COMMANDS_PER_ITERATION = 5
        mock_configure_ldap.side_effect = Exception
        self.amosflow.perform_amos_prerequisites(users, nodes)
        self.assertEqual(mock_log_debug.call_count, 5)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
