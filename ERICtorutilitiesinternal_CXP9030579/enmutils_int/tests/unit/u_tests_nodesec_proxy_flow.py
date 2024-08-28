#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.workload import nodesec_17, nodesec_16
from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow import (NodeSec17Flow, get_user_role_capabilities,
                                                                             create_custom_user_role, NodeSec16Flow)


class NodeSec17FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_17 = nodesec_17.NODESEC_17()
        self.flow = NodeSec17Flow()
        self.flow.NUM_USERS = 1
        self.flow.USERS = [Mock()]
        self.flow.USER_ROLES = ["proxycleanupper"]
        self.flow.CAPABILITIES = {"nodesec_proxy": ["read", "update", "delete"]}
        self.flow.INACTIVE_HOURS = 48
        self.proxy_xml_data = ['cn=ProxyAccount_1800d749-7029-410c-97ba-6f2ca26099aa,ou=proxyagentlockable,'
                               'ou=com,dc=ieatlms5742,dc=com',
                               'cn=ProxyAccount_7bc2ef76-08c0-424d-8c2d-aac0f0577ed8,ou=proxyagentlockable,'
                               'ou=com,dc=ieatlms5742,dc=com']

    def tearDown(self):
        unit_test_utils.tear_down()

    # get_user_role_capabilities test case
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.RoleCapability."
           "get_role_capabilities_for_resource_based_on_operation", return_value=["read"])
    def test_get_user_role_capabilities__success(self, mock_get_role, mock_debug_log):
        get_user_role_capabilities(self.flow, self.flow.USER_ROLES[0])
        self.assertEqual(3, mock_get_role.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    # create_custom_user_role test cases
    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.get_user_role_capabilities",
           return_value=["update"])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmComRole")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmRole.check_if_role_exists")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.CustomRole")
    def test_create_custom_user_role__is_successful(self, mock_custom_role, mock_role_exists, mock_debug_log, *_):
        mock_role_exists.return_value = {"test": "test"}
        create_custom_user_role(self.flow, "role1", "nodesec profile custom role")
        self.assertTrue(mock_role_exists.called)
        self.assertTrue(mock_custom_role.return_value.create.called)
        self.assertEqual(mock_debug_log.call_count, 2)
        mock_custom_role.return_value.create.assert_called_once_with(role_details={"test": "test"})

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.get_user_role_capabilities",
           return_value=["create"])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmComRole")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmRole.check_if_role_exists")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.CustomRole")
    def test_create_custom_user_role__raises_error(self, mock_custom_role, mock_role_exists,
                                                   mock_debug_log, *_):

        mock_custom_role.return_value.create.side_effect = [Exception("Some Exception"), None]
        mock_role_exists.return_value = {"test": "test"}
        create_custom_user_role(self.flow, "role1", "nodesec profile custom role")
        self.assertTrue(mock_role_exists.called)
        self.assertTrue(mock_custom_role.return_value.create.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.get_user_role_capabilities",
           return_value=["update"])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmComRole")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.EnmRole.check_if_role_exists")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.CustomRole")
    def test_create_custom_user_role__if_role_already_existed(self, mock_custom_role, mock_role_exists,
                                                              mock_debug_log, *_):
        mock_role_exists.return_value = None
        create_custom_user_role(self.flow, "role1", "nodesec profile custom role")
        self.assertTrue(mock_role_exists.called)
        self.assertFalse(mock_custom_role.return_value.create.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    # NodeSec17Flow execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.sleep_until_time",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "perform_disable_delete_ldap_proxy_accounts_operations")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem")
    def test_execute_flow__is_successful(self, mock_filesystem, mock_debug_log, mock_proxy, *_):
        mock_filesystem.does_dir_exist.return_value = False
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 9)
        self.assertEqual(mock_filesystem.does_dir_exist.call_count, 1)
        self.assertEqual(mock_filesystem.create_dir.call_count, 1)
        self.assertEqual(mock_proxy.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.sleep_until_time",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "perform_disable_delete_ldap_proxy_accounts_operations")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem")
    def test_execute_flow__raises_exception(self, mock_filesystem, mock_debug_log, mock_proxy, mock_add_error, *_):
        mock_filesystem.does_dir_exist.return_value = True
        mock_proxy.side_effect = EnvironError("error")
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 8)
        self.assertEqual(mock_filesystem.does_dir_exist.call_count, 1)
        self.assertEqual(mock_filesystem.create_dir.call_count, 0)
        self.assertEqual(mock_proxy.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    # perform_disable_delete_ldap_proxy_accounts_operations test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "log_proxy_accounts_dn_from_file")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "get_and_verify_inactive_proxy_accounts")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "toggle_ldap_proxy_accounts_admin_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.delete_ldap_proxy_accounts")
    def test_perform_disable_delete_ldap_proxy_accounts_operations__is_successful(
            self, mock_delete_ldap_proxy, mock_toggle_ldap_proxy, mock_get_and_verify_inactive_proxy, *_):
        mock_get_and_verify_inactive_proxy.return_value = True
        mock_toggle_ldap_proxy.return_value = True
        mock_delete_ldap_proxy.return_value = True
        self.flow.perform_disable_delete_ldap_proxy_accounts_operations()
        self.assertEqual(mock_get_and_verify_inactive_proxy.call_count, 1)
        self.assertEqual(mock_toggle_ldap_proxy.call_count, 1)
        self.assertEqual(mock_delete_ldap_proxy.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "log_proxy_accounts_dn_from_file")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "get_and_verify_inactive_proxy_accounts")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "toggle_ldap_proxy_accounts_admin_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.delete_ldap_proxy_accounts")
    def test_perform_disable_delete_ldap_proxy_accounts_operations__raises_exception(
            self, mock_delete_ldap_proxy, mock_toggle_ldap_proxy, mock_get_and_verify_inactive_proxy, mock_add_error, _):
        mock_get_and_verify_inactive_proxy.side_effect = EnvironError("error")
        self.flow.perform_disable_delete_ldap_proxy_accounts_operations()
        self.assertEqual(mock_get_and_verify_inactive_proxy.call_count, 1)
        self.assertEqual(mock_toggle_ldap_proxy.call_count, 0)
        self.assertEqual(mock_delete_ldap_proxy.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "log_proxy_accounts_dn_from_file")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "get_and_verify_inactive_proxy_accounts")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "toggle_ldap_proxy_accounts_admin_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.delete_ldap_proxy_accounts")
    def test_perform_disable_delete_ldap_proxy_accounts_operations__if_inactive_proxy_accounts_not_found(
            self, mock_delete_ldap_proxy, mock_toggle_ldap_proxy, mock_get_and_verify_inactive_proxy, *_):
        mock_get_and_verify_inactive_proxy.return_value = False
        self.flow.perform_disable_delete_ldap_proxy_accounts_operations()
        self.assertEqual(mock_get_and_verify_inactive_proxy.call_count, 1)
        self.assertEqual(mock_toggle_ldap_proxy.call_count, 0)
        self.assertEqual(mock_delete_ldap_proxy.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "log_proxy_accounts_dn_from_file")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "get_and_verify_inactive_proxy_accounts")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow."
           "toggle_ldap_proxy_accounts_admin_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.delete_ldap_proxy_accounts")
    def test_perform_disable_delete_ldap_proxy_accounts_operations__if_toggle_proxy_acnts_admin_status_returns_false(
            self, mock_delete_ldap_proxy, mock_toggle_ldap_proxy, mock_get_and_verify_inactive_proxy, *_):
        mock_get_and_verify_inactive_proxy.return_value = True
        mock_toggle_ldap_proxy.return_value = False
        self.flow.perform_disable_delete_ldap_proxy_accounts_operations()
        self.assertEqual(mock_get_and_verify_inactive_proxy.call_count, 1)
        self.assertEqual(mock_toggle_ldap_proxy.call_count, 1)
        self.assertEqual(mock_delete_ldap_proxy.call_count, 0)

    # get_and_verify_inactive_proxy_accounts test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_get_and_verify_inactive_proxy_accounts__is_successful(self, mock_debug_log, mock_run_local_cmd, _):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Successfully generated file '
                                            'ldap_proxy_get_inactive_for_1_hours_20230417_150511.xml '
                                            '(size = 6552 bytes)']
        mock_run_local_cmd.return_value = Mock(ok=True, stdout="18\n")
        self.flow.get_and_verify_inactive_proxy_accounts()
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_get_and_verify_inactive_proxy_accounts__when_inactive_accounts_not_found(self, mock_debug_log,
                                                                                      mock_run_local_cmd, _):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Successfully generated file '
                                            'ldap_proxy_get_inactive_for_1_hours_20230417_150511.xml '
                                            '(size = 6552 bytes)']
        mock_run_local_cmd.return_value = Mock(ok=True, stdout="0\n")
        self.flow.get_and_verify_inactive_proxy_accounts()
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_get_and_verify_inactive_proxy_accounts__error_response(self, mock_debug_log,
                                                                    mock_run_local_cmd, _):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Error']
        mock_run_local_cmd.return_value = Mock(ok=True, stdout="0\n")
        self.assertRaises(EnvironError, self.flow.get_and_verify_inactive_proxy_accounts)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_run_local_cmd.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_get_and_verify_inactive_proxy_accounts__unable_get_proxy_accounts_count(self, mock_debug_log,
                                                                                     mock_run_local_cmd, _):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Successfully generated file '
                                            'ldap_proxy_get_inactive_for_1_hours_20230417_150511.xml '
                                            '(size = 6552 bytes)']
        mock_run_local_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.flow.get_and_verify_inactive_proxy_accounts)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    # toggle_ldap_proxy_accounts_admin_status test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_toggle_ldap_proxy_accounts_admin_status__is_successful(self, mock_debug_log):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Successfully updated all 18 proxy accounts.']
        self.flow.toggle_ldap_proxy_accounts_admin_status()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_toggle_ldap_proxy_accounts_admin_status__raises_error(self, mock_debug_log):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['error']
        self.assertRaises(EnvironError, self.flow.toggle_ldap_proxy_accounts_admin_status)
        self.assertEqual(mock_debug_log.call_count, 2)

    # delete_ldap_proxy_accounts test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_delete_ldap_proxy_accounts__is_successful(self, mock_debug_log):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['Successfully deleted all 18 proxy accounts.']
        self.flow.delete_ldap_proxy_accounts()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_delete_ldap_proxy_accounts__raises_error(self, mock_debug_log):
        response = self.flow.USERS[0].enm_execute.return_value
        response.get_output.return_value = ['error']
        self.assertRaises(EnvironError, self.flow.delete_ldap_proxy_accounts)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.et")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_log_proxy_accounts_dn_from_file__is_success(self, mock_debug_log, mock_et):
        data = mock_et.parse.return_value = Mock()
        data.xpath.return_value = self.proxy_xml_data
        self.flow.log_proxy_accounts_dn_from_file()
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.et")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_log_proxy_accounts_dn_from_file__if_data_not_found(self, mock_debug_log, mock_et):
        data = mock_et.parse.return_value = Mock()
        data.xpath.return_value = []
        self.flow.log_proxy_accounts_dn_from_file()
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.et")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    def test_log_proxy_accounts_dn_from_file__raises_error(self, mock_debug_log, mock_et):
        data = mock_et.parse.return_value = Mock()
        data.xpath.side_effect = [Exception("error")]
        self.flow.log_proxy_accounts_dn_from_file()
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec17Flow.execute_flow")
    def test_run__in_nodesec_17_is_successful(self, _):
        self.nodesec_17.run()


class NodeSec16FlowUnitTests(unittest2.TestCase):
    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_16 = nodesec_16.NODESEC_16()
        self.flow = NodeSec16Flow()
        self.flow.NUM_USERS = 1
        self.flow.NUM_OF_NODES = 1000
        self.flow.USERS = [Mock()]
        self.flow.USER_ROLES = ['ldaprenewer']
        self.flow.CAPABILITIES = {"ldap": ["update", "patch"], "cm_editor": ["read"]}

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.GenericFlow.keep_running")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_proxy_renew_accounts_operations")
    def test_execute_flow__successful(self, mock_perform_ldap, mock_keep_running, *_):
        mock_keep_running.return_value = True
        self.flow.execute_flow()
        self.assertTrue(mock_perform_ldap.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_proxy_renew_accounts_operations")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.GenericFlow.keep_running")
    def test_execute_flow__keep_running_false(self, mock_keep_running, mock_perform_ldap, *_):
        mock_keep_running.return_value = False
        self.flow.execute_flow()
        self.assertFalse(mock_perform_ldap.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_proxy_renew_accounts_operations")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_commands_on_nodes")
    def test_execute_flow__raises_exception(self, mock_perform_ldap, *_):
        mock_perform_ldap.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.flow.execute_flow())

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem.read_lines_from_file")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd')
    def test_get_list_of_sync_ldap_configured_nodes__returns_list_of_synced_nodes(self, mock_run_cmd, mock_file, *_):
        mock_run_cmd.return_value = Mock(rc=0, stdout="Output", elapsed_time=.001)
        self.flow.get_list_of_sync_ldap_configured_nodes(
            '1.Getting synced and ldap configured', 'cli_app secadm job get -j dummmy_job_id |grep ERROR|cut -f 7',
            self.flow.NODES_LIST_FILE)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem.read_lines_from_file",
           return_value=['line1', 'line2'])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd')
    def test_get_list_of_sync_ldap_configured_nodes__returns_list_of_synced_nodes_into_tmp_file(self, mock_run_cmd, *_):
        mock_run_cmd.return_value = Mock(rc=0, stdout="Output", elapsed_time=.001)
        self.flow.get_list_of_sync_ldap_configured_nodes(
            '2.Getting synced and ldap configured', self.flow.GET_NODES_MASS_CMD.format(self.flow.NODES_LIST_FILE_TEMP),
            self.flow.NODES_LIST_FILE_TEMP)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem.read_lines_from_file")
    def test_get_list_of_sync_ldap_configured_nodes__raises_error_when_no_nodes_available(self, mock_read_lines,
                                                                                          mock_run_cmd, *_):
        mock_run_cmd.return_value = Mock(rc=0, stdout="", elapsed_time=.001)
        mock_read_lines.return_value = False
        with self.assertRaises(EnvironError):
            self.flow.get_list_of_sync_ldap_configured_nodes(
                '1.Getting synced and ldap configured',
                self.flow.GET_NODES_MASS_CMD.format(self.flow.NUM_OF_NODES),
                self.flow.NODES_LIST_FILE)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.shell.run_local_cmd')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    def test_get_list_of_sync_ldap_configured_nodes__raises_exception(self, mock_add_error, mock_read_lines,
                                                                      mock_run_cmd, *_):
        mock_run_cmd.return_value = Exception
        mock_read_lines.return_value = True
        self.flow.get_list_of_sync_ldap_configured_nodes(
            '2.Getting synced and ldap configured',
            self.flow.GET_NODES_MASS_CMD.format(self.flow.NUM_OF_NODES),
            self.flow.NODES_LIST_FILE)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.et.ElementTree')
    def test_create_xml_file_for_ldap__successful(self, mock_element_tree, *_):
        self.flow.create_xml_file_for_ldap(['LYES2153'])
        self.assertTrue(mock_element_tree.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.get_current_job_status')
    def test_perform_ldap_commands_on_nodes__successful(self, *_):
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Successfully started * 'secadm job get -j "
                                            "13bdb505-ca8f-48f1-abda-2374f60d0d2f'"]
        user.enm_execute.return_value = response
        self.flow.perform_ldap_commands_on_nodes(user, '2.Running first ldap', 'secadm ldap reconfigure -xmlfile')

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.get_current_job_status')
    def test_perform_ldap_commands_on_nodes__raises_env_error(self, *_):
        user, response = Mock(), Mock()
        response.get_output.side_effect = [[u'', u"Error 9999 : Internal Error : "
                                                 u"(WFLYEJB0447: Transaction 'Local transaction "
                                                 u"(delegate=TransactionImple < ac, "
                                                 u"BasicAction: 0:ffff0af7f6de:73ff284d:65f455e5:18eccf8 "
                                                 u"status: ActionStatus.ABORTED >,"
                                                 u" owner=Local transaction context for provider "
                                                 u"JBoss JTA transaction provider)' was already rolled back)"],
                                           [u'Error Code 99 : Unexpected Internal Error',
                                            u'Suggested Solution: This is an unexpected system error, '
                                            u'please check the error log for more details.'],
                                           [u"Successfully started a job for reconfigure LDAP operation. "
                                            u"Perform 'secadm job get -j cf52a9f6-5651-4c87-97ee-5a75e9458df4' "
                                            u"to get progress info. Some input nodes are invalid, see error "
                                            u"details in following table:",
                                            u'Node\tError Code\tError Details\tCaused By\tSuggested Solution',
                                            u'NetworkElement=NR160gNodeBRadio00024\t10005\tThe node specified is '
                                            u'not synchronized\t\tPlease ensure the node specified is synchronized.',
                                            u'', u'Command Executed Successfully']]
        user.enm_execute.return_value = response
        self.assertRaises(EnvironError, self.flow.perform_ldap_commands_on_nodes, user, '2.Running first ldap',
                          'secadm ldap reconfigure -xmlfile')
        self.assertRaises(EnvironError, self.flow.perform_ldap_commands_on_nodes, user, '3.Running second ldap',
                          'secadm ldap reconfigure -xmlfile')
        self.flow.perform_ldap_commands_on_nodes(user, '4.Running third ldap',
                                                 'secadm ldap reconfigure -xmlfile')

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "get_list_of_sync_ldap_configured_nodes")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.get_current_job_status')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_xml_file_for_ldap")
    def test_perform_ldap_commands_on_nodes__if_second_reconfigure_in_action(self, mock_create_xml_file, *_):
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Successfully started * 'secadm job get -j "
                                            "13bdb505-ca8f-48f1-abda-2374f60d0d2f'"]
        user.enm_execute.return_value = response
        self.flow.perform_ldap_commands_on_nodes(user, '3.Running second ldap', 'secadm ldap reconfigure -xmlfile')
        self.assertTrue(mock_create_xml_file.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.get_current_job_status')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_xml_file_for_ldap")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "get_list_of_sync_ldap_configured_nodes")
    def test_perform_ldap_commands_on_nodes__if_final_reconfigure_in_action(self, mock_get_list, *_):
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Successfully started * 'secadm job get -j "
                                            "13bdb505-ca8f-48f1-abda-2374f60d0d2f'"]
        user.enm_execute.return_value = response
        self.flow.perform_ldap_commands_on_nodes(user, '4.Running final ldap', 'secadm ldap reconfigure -xmlfile')
        self.assertEqual(mock_get_list.call_count, 2)

    def test_get_current_job_status__if_job_status_is_completed(self, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Job Status : COMPLETED"]
        user.enm_execute.return_value = response
        self.flow.get_current_job_status(user, 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f')

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep', return_value=10)
    def test_get_current_job_status__if_job_status_is_not_completed(self, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Job Status : PENDING"]
        user.enm_execute.return_value = response
        self.assertRaises(EnvironError, self.flow.get_current_job_status, user,
                          'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f')

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    def test_get_current_job_status__if_job_status_raises_error(self, mock_add_error, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = Exception
        user.enm_execute.return_value = response
        self.flow.get_current_job_status(user, 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f')
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.execute_flow")
    def test_run__is_successful(self, mock_execute_flow):
        nodesec_16.NODESEC_16().run()
        self.assertTrue(mock_execute_flow.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "get_list_of_sync_ldap_configured_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_xml_file_for_ldap")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_commands_on_nodes")
    def test_perform_ldap_proxy_renew_accounts_operations__successful(self, *_):
        user = Mock()
        self.flow.perform_ldap_proxy_renew_accounts_operations(user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow.create_xml_file_for_ldap")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "perform_ldap_commands_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.NodeSec16Flow."
           "get_list_of_sync_ldap_configured_nodes")
    def test_perform_ldap_proxy_renew_accounts_operations__raise_error(self, mock_get_list, *_):
        user = Mock()
        mock_get_list.side_effect = EnvironError('error')
        self.assertRaises(EnvironError, self.flow.perform_ldap_proxy_renew_accounts_operations(user))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
