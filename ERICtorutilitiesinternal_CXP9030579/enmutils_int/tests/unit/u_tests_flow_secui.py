#!/usr/bin/env python
import unittest2
from mock import Mock, PropertyMock, patch, call
from requests.exceptions import HTTPError

from enmutils.lib.enm_user_2 import Target
from enmutils_int.lib.load_node import ERBSLoadNode
from enmutils_int.lib.profile_flows.secui_flows.secui_flow import (Secui01Flow, Secui02Flow, Secui03Flow, Secui05Flow,
                                                                   Secui06Flow, Secui07Flow, Secui08Flow, Secui09Flow,
                                                                   Secui10Flow, Secui11Flow, Secui12Flow, SecuiFlow,
                                                                   toggle_password_aging_policy, ValidationError,
                                                                   EnmApplicationError, EnvironError)
from enmutils_int.lib.workload import (secui_01, secui_02, secui_03, secui_05, secui_06, secui_07, secui_08,
                                       secui_09, secui_10, secui_11, secui_12)
from testslib import unit_test_utils

URL = 'http://test.com'


class SecuiFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes_list = [Mock(id='LTE01', simulation='LTE-120', model_identity='1-2-34'),
                           Mock(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34')]
        self.secuiflow = SecuiFlow()
        self.secuiflow.teardown_list = []
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils.lib.enm_user_2.User.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomUser.create')
    def test_create_custom_user__raises_error(self, mock_create, mock_add_error, *_):
        mock_create.side_effect = [self.exception, None]
        self.secuiflow.create_custom_user(0, ["Administrator"], Mock())
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.capabilities', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole.check_if_role_exists')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole')
    def test_create_custom_role__raises_error(self, mock_custom_role, mock_add_error, mock_role_exists,
                                              mock_debug_log, *_):
        mock_custom_role.return_value.create.side_effect = [self.exception, None]
        self.secuiflow.CAPABILITIES = ['fm', 'netex']
        mock_role_exists.return_value = {"test": "test"}
        self.secuiflow.create_custom_role('role', 'some role', user=self.user)
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_role_exists.called)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.capabilities', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole.check_if_role_exists')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole')
    def test_create_custom_role__is_successful(self, mock_custom_role, mock_add_error, mock_role_exists,
                                               mock_debug_log, *_):
        self.secuiflow.CAPABILITIES = ['fm', 'netex']
        mock_role_exists.return_value = {"test": "test"}
        self.secuiflow.create_custom_role('role', 'some role', user=self.user)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_role_exists.called)
        self.assertTrue(mock_custom_role.return_value.create.called)
        mock_debug_log.assert_any_call('[role] custom role created successfully')
        mock_custom_role.return_value.create.assert_called_once_with(role_details={'test': 'test'})

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.capabilities', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole.check_if_role_exists')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole')
    def test_create_custom_role__if_role_already_existed(self, mock_custom_role, mock_add_error,
                                                         mock_role_exists, *_):
        mock_role = Mock()
        mock_role.name = "CustomTest"
        mock_role_exists.return_value = None
        self.secuiflow.CAPABILITIES = ['fm', 'netex']
        mock_custom_role.return_value = mock_role
        self.secuiflow.create_custom_role('CustomTest', 'Test role', user=self.user)
        self.assertFalse(mock_add_error.called)
        self.assertFalse(mock_custom_role.create.called)
        self.assertTrue(mock_role_exists.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_check_ldap_is_configured__on_radio_nodes(self, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
            u'MeContext=LTE01dg2ERBS00031,ManagedElement=1,SystemFunctions=1,'
            u'SecM=1,UserManagement=1,LdapAuthenticationMethod=1',
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
            u'MeContext=LTE01dg2ERBS00032,ManagedElement=1,SystemFunctions=1,'
            u'SecM=1,UserManagement=1,LdapAuthenticationMethod=1', u'']
        self.user.enm_execute.return_value = response
        nodes = [Mock(node_id="LTE01dg2ERBS00031", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                      profiles=['SECUI_10']),
                 Mock(node_id="LTE01dg2ERBS00032", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                      profiles=['SECUI_10'])]
        self.secuiflow.check_ldap_is_configured_on_nodes(self.user, nodes)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_check_ldap_is_configured__on_5g_radio_nodes(self, mock_debug, *_):
        response = Mock()
        response.get_output.return_value = [
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
            u'MeContext=NR45gNodeBRadio00018,ManagedElement=1,SystemFunctions=1,'
            u'SecM=1,UserManagement=1,LdapAuthenticationMethod=1',
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
            u'MeContext=NR45gNodeBRadio00019,ManagedElement=1,SystemFunctions=1,'
            u'SecM=1,UserManagement=1,LdapAuthenticationMethod=1', u'']
        self.user.enm_execute.return_value = response
        nodes = [Mock(node_id="NR45gNodeBRadio00018",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00018",
                      profiles=['SECUI_10']),
                 Mock(node_id="NR45gNodeBRadio00019",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00019",
                      profiles=['SECUI_10'])]
        self.secuiflow.check_ldap_is_configured_on_nodes(self.user, nodes)
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.re.compile")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    def test_check_ldap_is_not_configured_on_radio_nodes__adds_exception(self, mock_add_error_as_exception, *_):
        nodes = [Mock(node_id="LTE01dg2ERBS00031",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland", profiles=['SECUI_10']),
                 Mock(node_id="NR45gNodeBRadio00019",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00019",
                      profiles=['SECUI_10'])]
        self.user.enm_execute.return_value.get_output.return_value = [
            u'FDN : SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,'
            u'MeContext=LTE01dg2ERBS00031,ManagedElement=1,SystemFunctions=1,'
            u'SecM=1,UserManagement=1,LdapAuthenticationMethod=1', u'']
        self.secuiflow.check_ldap_is_configured_on_nodes(self.user, nodes)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.re.compile")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    def test_check_ldap_is_not_configured_on_radio_nodes__empty_response(self, mock_add_error_as_exception, *_):
        nodes = [Mock(node_id="LTE01dg2ERBS00031",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland", profiles=['SECUI_10']),
                 Mock(node_id="NR45gNodeBRadio00019",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00019",
                      profiles=['SECUI_10'])]
        self.user.enm_execute.return_value.get_output.return_value = []
        self.secuiflow.check_ldap_is_configured_on_nodes(self.user, nodes)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    def test_check_ldap_is_configured_on_nodes__raise_exception(self, mock_add_error_as_exception):
        nodes = [Mock(node_id="LTE01dg2ERBS00031",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland", profiles=['SECUI_10']),
                 Mock(node_id="NR45gNodeBRadio00019",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00019",
                      profiles=['SECUI_10'])]
        self.user.enm_execute.side_effect = Exception
        self.secuiflow.check_ldap_is_configured_on_nodes(self.user, nodes)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.RoleCapability.get_role_capabilities_for_resource',
           return_value=["cap"])
    def test_capabilities__calls_get_roles(self, mock_get_role):
        self.secuiflow.CAPABILITIES = ["1", "2"]
        self.assertEqual(2, len(self.secuiflow.capabilities))
        self.assertEqual(2, mock_get_role.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    def test_create_custom_target_groups__is_successful(self, mock_target, mock_add_error):
        mock_target.return_value.exists = True
        self.secuiflow.create_custom_target_groups(["ACMENORTH", "ACMESOUTH"], self.user)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_target.return_value.delete.called)
        self.assertTrue(mock_target.return_value.create.called)
        self.assertEqual(len(self.secuiflow.teardown_list), 2)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    def test_create_custom_target_groups__if_target_groups_not_exist(self, mock_target, mock_add_error):
        mock_target.return_value.exists = False
        self.secuiflow.create_custom_target_groups(["ACMENORTH", "ACMESOUTH"], self.user)
        self.assertFalse(mock_add_error.called)
        self.assertFalse(mock_target.return_value.delete.called)
        self.assertTrue(mock_target.return_value.create.called)
        self.assertEqual(len(self.secuiflow.teardown_list), 2)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    def test_create_custom_target_groups__if_create_target_throws_exception(self, mock_target):
        mock_target.return_value.exists = False
        mock_target.return_value.create.side_effect = HTTPError("Could not create target group")
        self.assertRaises(HTTPError, self.secuiflow.create_custom_target_groups, ["ACMENORTH", "ACMESOUTH"], self.user)
        self.assertFalse(mock_target.return_value.delete.called)
        self.assertTrue(mock_target.return_value.create.called)
        self.assertEqual(len(self.secuiflow.teardown_list), 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_custom_role')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_custom_target_groups')
    def test_create_custom_roles_and_target_groups__is_successful(self, mock_create_custom_target_group,
                                                                  mock_create_custom_role, mock_debug_log, mock_admin):
        mock_create_custom_target_group.return_value = [Mock(name="ACMENORTH", description="ACMENORTH Target Group")]
        mock_create_custom_role.return_value = (Mock(name="ACME_PKI_Operator", description="ACME_PKI_Operator role"),
                                                Mock(name="ACME_PKI_Operator", description="ACME_PKI_Operator role"))
        self.secuiflow.create_custom_roles_and_target_groups(["ACME_PKI_Operator", "Admin"], ["ACMENORTH"])
        self.assertEqual(len(self.secuiflow.teardown_list), 2)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(mock_create_custom_target_group.called)
        self.assertTrue(mock_create_custom_role.called)
        self.assertEqual(1, mock_admin.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_custom_role')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_custom_target_groups')
    def test_create_custom_roles_and_target_groups__if_user_role_creation_fail(self, mock_create_custom_target_group,
                                                                               mock_create_custom_role, mock_debug_log,
                                                                               mock_admin, _):
        mock_create_custom_target_group.return_value = [Mock(name="ACMENORTH", description="ACMENORTH Target Group")]
        mock_create_custom_role.side_effect = EnmApplicationError("Failed to create custom role")
        self.assertRaises(EnmApplicationError, self.secuiflow.create_custom_roles_and_target_groups,
                          ["ACME_PKI_Operator", "Admin"], ["ACMENORTH"])
        self.assertEqual(len(self.secuiflow.teardown_list), 0)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertTrue(mock_create_custom_target_group.called)
        self.assertTrue(mock_create_custom_role.called)
        self.assertEqual(1, mock_admin.call_count)


class Secui01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_01 = secui_01.SECUI_01()
        self.secuiflow01 = Secui01Flow()
        self.secuiflow01.NUMBER_OF_SECURITY_ADMINS = 2
        self.secuiflow01.NUMBER_OF_USERS_TO_CREATE = 10
        self.secuiflow01.NUMBER_OF_ROLES_TO_ASSIGN = 2
        self.secuiflow01.THREAD_QUEUE_TIMEOUT = 1
        self.secuiflow01.USER_ROLES = [u'Target_Group_Administrator', u'Topology_Browser_Administrator']
        self.secuiflow01.teardown_list = []
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.execute_flow')
    def test_run__in_secui_01_is_successful(self, _):
        self.secui_01.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User')
    def test_tasket__user_create_failure_adds_exception(self, mock_user, mock_add_error, *_):
        mock_user.return_value.create.side_effect = self.exception
        self.secuiflow01.task_set([self.user, self.user], self.secuiflow01, [5])
        self.assertTrue(mock_user.return_value.create.called)
        self.assertFalse(mock_user.return_value.remove_session.called)
        self.assertTrue(mock_add_error.called)
        self.assertEqual(0, len(self.secuiflow01.teardown_list))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User')
    def test_tasket__remove_session_failure_adds_exception(self, mock_user, mock_add_error, *_):
        mock_user.return_value.create.return_value = self.user
        mock_user.return_value.remove_session.side_effect = self.exception
        self.secuiflow01.task_set([self.user, self.user], self.secuiflow01, [5])
        self.assertTrue(mock_user.return_value.create.called)
        self.assertTrue(mock_user.return_value.remove_session.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User')
    def test_tasket__is_successful(self, mock_user, mock_add_error, *_):
        mock_user.return_value.create.return_value = self.user
        self.secuiflow01.NUMBER_OF_USERS_TO_CREATE = 11
        self.secuiflow01.SECURITY_ADMIN_USERS = [self.user, self.user]
        self.secuiflow01.task_set(self.secuiflow01.SECURITY_ADMIN_USERS[0], self.secuiflow01, [6, 5])
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_user.return_value.create.called)
        self.assertTrue(mock_user.return_value.remove_session.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.'
           'get_number_of_users_count_based_admin_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_profile_users')
    def test_execute_flow__is_sucessful(self, mock_create_profile_users, mock_create_and_execute_threads,
                                        mock_get_number_of_users_count, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_number_of_users_count.return_value = [3, 2]
        self.secuiflow01.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_get_number_of_users_count.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.'
           'get_number_of_users_count_based_admin_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_profile_users')
    def test_execute_flow__raises_env_error(self, mock_create_profile_users, mock_create_and_execute_threads,
                                            mock_get_number_of_users_count, mock_add_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_number_of_users_count.return_value = []
        self.secuiflow01.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_get_number_of_users_count.called)
        self.assertTrue(call(EnvironError("Unable to divide the number of users to create "
                                          "for each admin user") in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.'
           'get_number_of_users_count_based_admin_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.create_profile_users')
    def test_execute_flow__add_env_error_if_create_and_execute_threads_throws_error(
            self, mock_create_profile_users, mock_create_and_execute_threads,
            mock_get_number_of_users_count, mock_add_error, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_number_of_users_count.return_value = [3, 2]
        mock_create_and_execute_threads.side_effect = Exception("something is wrong")
        self.secuiflow01.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_get_number_of_users_count.called)
        self.assertTrue(call(EnmApplicationError(mock_create_and_execute_threads.side_effect)
                             in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_get_number_of_users_count_based_admin_users__is_successful(self, mock_debug_log, mock_add_error):
        self.assertEqual(self.secuiflow01.get_number_of_users_count_based_admin_users(), [5])
        self.assertTrue(mock_debug_log.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_get_number_of_users_count_based_admin_users__if_getting_different_users_count(self, mock_debug_log,
                                                                                           mock_add_error):
        self.secuiflow01.NUMBER_OF_USERS_TO_CREATE = 25
        self.assertEqual(self.secuiflow01.get_number_of_users_count_based_admin_users(), [13, 12])
        self.assertTrue(mock_debug_log.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_get_number_of_users_count_based_admin_users__if_getting_zero_secuirty_admin_users(self, mock_debug_log,
                                                                                               mock_add_error):
        self.secuiflow01.NUMBER_OF_SECURITY_ADMINS = 0
        self.assertEqual(self.secuiflow01.get_number_of_users_count_based_admin_users(), [])
        self.assertFalse(mock_debug_log.called)
        self.assertTrue(mock_add_error.called)


class Secui02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_02 = secui_02.SECUI_02()
        self.secui02flow = Secui02Flow()
        self.secui02flow.NUMBER_OF_ROLES = 2
        self.secui02flow.NUMBER_OF_USERS = 2
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.execute_flow')
    def test_run__in_secui_02_is_successful(self, _):
        self.secui_02.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmComRole.delete')
    def test_delete_role_failure_adds_exception(self, mock_delete, mock_add_error):
        mock_delete.side_effect = self.exception
        self.secui02flow.delete_roles([Mock()])
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmComRole.delete')
    def test_delete_role_removes_from_teardown(self, mock_delete):
        mock_delete.side_effect = None
        role = Mock()
        self.secui02flow.teardown_list.append(role)
        self.assertEqual(len(self.secui02flow.teardown_list), 1)
        self.secui02flow.delete_roles([role])
        self.assertEqual(len(self.secui02flow.teardown_list), 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User.delete')
    def test_delete_users_failure_adds_exception(self, mock_delete, mock_add_error):
        mock_delete.side_effect = self.exception
        self.secui02flow.delete_users([Mock()], self.user)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User.delete')
    def test_delete_user_removes_from_teardown(self, mock_delete):
        mock_delete.side_effect = None
        user = Mock()
        self.secui02flow.teardown_list.append(user)
        self.assertEqual(len(self.secui02flow.teardown_list), 1)
        self.secui02flow.delete_users([user], self.user)
        self.assertEqual(len(self.secui02flow.teardown_list), 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmComRole.create')
    def test_create_roles(self, mock_create, mock_add_error):
        mock_create.side_effect = [self.exception, None]
        roles = self.secui02flow.create_roles_as(self.user, 2)
        self.assertTrue(mock_add_error.called)
        self.assertIsNotNone(roles)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmApplicationError')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.User')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.add_error_as_exception')
    def test_create_users(self, mock_add_error, mock_user, mock_identifier, mock_enm_error):
        mock_exception = mock_enm_error.return_value = Exception('some error')
        mock_identifier.return_value = "Test"
        mock_user.return_value.create.side_effect = [self.exception, None]
        mock_roles = [Mock(), Mock()]

        users = self.secui02flow.create_users_as(mock_roles, self.user, 2)

        mock_add_error.assert_called_with(mock_exception)
        mock_user.assert_any_call('Test-SECUI_02_USERS-0', 'TestPassw0rd', keep_password=True, roles=mock_roles)
        mock_user.assert_called_with('Test-SECUI_02_USERS-1', 'TestPassw0rd', keep_password=True, roles=mock_roles)
        self.assertEqual(1, len(users))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.delete_roles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.delete_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.create_users_as')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.create_roles_as')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui02Flow.keep_running')
    def test_execute_flow(self, mock_keep_running, mock_debug, mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        self.secui02flow.execute_flow()
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_sleep.called)


class Secui03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_03 = secui_03.SECUI_03()
        self.flow = Secui03Flow()
        self.flow.SCHEDULED_TIMES = ["00:00:00"]
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.execute_flow')
    def test_run__in_secui_03_is_successful(self, _):
        self.secui_03.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.toggle_password_aging_policy')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.add_error_as_exception')
    def test_execute_flow__adds_exception(self, mock_add_exception, mock_toggle_password, mock_create_profile_users,
                                          *_):
        mock_toggle_password.side_effect = self.exception
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        mock_create_profile_users.assert_called_with(1, ["SECURITY_ADMIN"])
        mock_toggle_password.assert_called_with(mock_create_profile_users.return_value[0], enabled=False)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.toggle_password_aging_policy')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui03Flow.add_error_as_exception')
    def test_execute_flow__is_successful(self, mock_add_exception, mock_toggle_password, mock_create_profile_users,
                                         *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        mock_create_profile_users.assert_called_with(1, ["SECURITY_ADMIN"])
        mock_toggle_password.assert_called_with(mock_create_profile_users.return_value[0], enabled=False)
        self.assertEqual(mock_add_exception.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    def test_toggle_password_aging_policy__raises_http_error(self, mock_raise_for_status, *_):
        mock_raise_for_status.side_effect = [HTTPError("Error"), None]
        toggle_password_aging_policy(Mock())


class Secui05FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_05 = secui_05.SECUI_05()
        self.secuiflow05 = Secui05Flow()
        self.secuiflow05.NUM_USERS = 1
        self.secuiflow05.USER_ROLES = ["SECURITY_ADMIN"]
        self.secuiflow05.SECUI_01_KEY = "SECUI_01"
        self.secuiflow05.CREATED_ROLE_COUNT = 2
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.execute_flow')
    def test_run__in_secui_05_is_successful(self, _):
        self.secui_05.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.capabilities', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.delete_existing_secui_roles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.create_custom_roles_for_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.wait_until_secui_01_active')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_wait_until_secui_01_active,
                          mock_create_custom_roles_for_users, mock_delete, *_):
        mock_create_profile_users.return_value = [self.user]
        self.secuiflow05.execute_flow()
        self.assertTrue(mock_wait_until_secui_01_active.called)
        self.assertTrue(mock_create_custom_roles_for_users.called)
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole.create')
    def test_create_custom_roles_for_users(self, mock_create, mock_add_error, *_):
        mock_create.side_effect = [self.exception, None]
        self.secuiflow05.create_custom_roles_for_users([self.user, self.user], self.secuiflow05.CAPABILITIES)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_active_profile_names')
    def test_wait_until_secui_01_active__is_successful_if_secui_01_is_starting(
            self, mock_get_active_profile_names, mock_get, mock_add_error_as_exception, *_):
        mock_get.side_effect = [None, Mock(state="STARTING")]
        mock_get_active_profile_names.side_effect = [["SECUI_05"], ["SECUI_05", "SECUI_01"], ["SECUI_05", "SECUI_01"]]
        self.secuiflow05.wait_until_secui_01_active()
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_active_profile_names')
    def test_wait_until_secui_01_active__is_successful_if_secui_01_is_running(
            self, mock_get_active_profile_names, mock_get, mock_add_error_as_exception, *_):
        mock_get.return_value = Mock(state="RUNNING")
        mock_get_active_profile_names.side_effect = [["SECUI_05"], ["SECUI_05", "SECUI_01"]]
        self.secuiflow05.wait_until_secui_01_active()
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_active_profile_names')
    def test_wait_until_secui_01_active__is_successful_if_secui_01_is_completed(
            self, mock_get_active_profile_names, mock_get, mock_add_error_as_exception, *_):
        mock_get.return_value = Mock(state="COMPLETED")
        mock_get_active_profile_names.side_effect = [["SECUI_05"], ["SECUI_05", "SECUI_01"]]
        self.secuiflow05.wait_until_secui_01_active()
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_active_profile_names')
    def test_wait_until_secui_01_active__adds_errors_as_exception(
            self, mock_get_active_profile_names, mock_get, mock_add_error_as_exception, *_):
        mock_get.return_value = Mock(state="COMPLETED")
        mock_get_active_profile_names.side_effect = [["SECUI_05"] for _ in xrange(60)] + [["SECUI_05", "SECUI_01"]]
        self.secuiflow05.wait_until_secui_01_active()
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmComRole.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmComRole.get_all_roles')
    def test_delete_existing_secui_roles(self, mock_get_all_roles, mock_add_error_as_exception, _):
        self.secuiflow05.NAME = "SECUI_05"
        role, role1, role2 = Mock(), Mock(), Mock()
        role.name, role1.name, role2.name = "SECUI_05_01", "SECUI_05_02", "ADMIN"
        role.delete.side_effect = Exception()
        mock_get_all_roles.return_value = [role, role1, role2]
        self.secuiflow05.delete_existing_secui_roles("user")
        self.assertEqual(0, role2.delete.call_count)
        self.assertEqual(1, mock_add_error_as_exception.call_count)


class Secui06FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="SECUI_06_0604-06281846_u0")
        self.secui_06 = secui_06.SECUI_06()
        self.secuiflow06 = Secui06Flow()
        self.secuiflow06.NUM_USERS = 1
        self.secuiflow06.USER_ROLES = ["PKI_Administrator"]
        self.secuiflow06.REQUIRED = 1
        self.secuiflow06.PKI_NAME = "Secui_Six_{0}"
        self.exception = Exception("Some Exception")
        self.all_profiles = [{"name": "test", "id": 111, "type": "ENTITY_PROFILE"},
                             {"name": "Random", "id": 111, "type": "ENTITY_PROFILE"}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.execute_flow')
    def test_run__in_secui_06_is_successful(self, _):
        self.secui_06.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.clean_up_old_pki_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_and_issue_entity_certificate')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_entity_profile')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_certificate_profile')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.recreate_deleted_user')
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.partial')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_profile_users')
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_partial, mock_debug_log,
                                         mock_teardown_append, mock_recreate_deleted_user, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.'
                   'get_workload_admin_user') as mock_get_workload_admin_user:
            with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.'
                       'get_all_entity_profiles') as mock_get_all_entity_profiles:
                mock_get_all_entity_profiles.return_value = self.all_profiles
                mock_create_profile_users.return_value = [self.user]
                mock_get_workload_admin_user.return_value = Mock()
                self.secuiflow06.PKI_NAME = "TEST_{0}"
                self.secuiflow06.execute_flow()
                mock_partial.assert_called_with(mock_recreate_deleted_user, self.user.username,
                                                self.secuiflow06.USER_ROLES, mock_get_workload_admin_user.return_value)
                self.assertTrue(mock_debug_log.called)
                self.assertTrue(call(mock_partial.return_value) in mock_teardown_append.mock_calls)
                self.assertEqual(mock_get_all_entity_profiles.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.clean_up_old_pki_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_and_issue_entity_certificate')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_entity_profile')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_all_entity_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.recreate_deleted_user')
    @patch('enmutils_int.lib.profile.TeardownList.append')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.partial')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.create_profile_users')
    def test_execute_flow__raises_exception_while_calling_create_certificate_profile(self, mock_create_profile_users,
                                                                                     mock_partial,
                                                                                     mock_debug_log,
                                                                                     mock_teardown_append,
                                                                                     mock_recreate_deleted_user, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.'
                   'add_error_as_exception') as mock_add_error:
            with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.'
                       'create_certificate_profile') as mock_create_certificate_profile:
                with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.'
                           'get_workload_admin_user') as mock_get_workload_admin_user:
                    mock_get_workload_admin_user.return_value = Mock()
                    mock_create_profile_users.return_value = [self.user]
                    mock_create_certificate_profile.side_effect = Exception("Error")
                    self.secuiflow06.PKI_NAME = "TEST_{0}"
                    self.secuiflow06.execute_flow()
                    mock_partial.assert_called_with(mock_recreate_deleted_user, self.user.username,
                                                    self.secuiflow06.USER_ROLES,
                                                    mock_get_workload_admin_user.return_value)
                    self.assertEqual(2, mock_debug_log.call_count)
                    self.assertTrue(call(mock_partial.return_value) in mock_teardown_append.mock_calls)
                    self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CertificateProfile.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.add_error_as_exception')
    def test_create_certificate_profile__add_exception(self, mock_add_exception, mock_create):
        mock_create.side_effect = self.exception
        self.secuiflow06.create_certificate_profile(self.user, 'Test')
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CertificateProfile.create')
    def test_create_certificate_profile__adds_to_teardown(self, mock_create):
        mock_create.return_value = Mock()
        self.assertEqual(len(self.secuiflow06.teardown_list), 0)
        self.secuiflow06.create_certificate_profile(self.user, 'Test')
        self.assertEqual(len(self.secuiflow06.teardown_list), 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EntityProfile.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.add_error_as_exception')
    def test_create_entity_profile__add_exception(self, mock_add_exception, mock_create):
        mock_create.side_effect = self.exception
        self.secuiflow06.create_entity_profile(self.user, 'Test')
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EntityProfile.create')
    def test_create_entity_profile__adds_to_teardown(self, mock_create):
        mock_create.return_value = Mock()
        self.assertEqual(len(self.secuiflow06.teardown_list), 0)
        self.secuiflow06.create_entity_profile(self.user, 'Test')
        self.assertEqual(len(self.secuiflow06.teardown_list), 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.set_entity_profile_name_and_id')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.set_all_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.add_error_as_exception')
    def test_create_and_issue_entity_certificate__add_exception_on_create(self, mock_add_exception, mock_create,
                                                                          set_all_profiles,
                                                                          set_entity_profile_name_and_id):
        mock_create.side_effect = self.exception
        self.secuiflow06.create_and_issue_entity_certificate(self.user, 'Test', self.all_profiles)
        self.assertEqual(1, set_all_profiles.call_count)
        self.assertEqual(1, set_entity_profile_name_and_id.call_count)
        self.assertEqual(1, mock_add_exception.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.set_entity_profile_name_and_id')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.set_all_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.issue')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui06Flow.add_error_as_exception')
    def test_create_and_issue_entity_certificate__add_exception_on_issue(self, mock_add_exception, mock_create,
                                                                         mock_issue, set_all_profiles,
                                                                         set_entity_profile_name_and_id):
        mock_create.return_value = Mock()
        mock_issue.side_effect = self.exception
        self.secuiflow06.create_and_issue_entity_certificate(self.user, 'Test', self.all_profiles)
        self.assertTrue(mock_add_exception.called)
        self.assertEqual(1, set_all_profiles.call_count)
        self.assertEqual(1, set_entity_profile_name_and_id.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Entity.remove_old_entities')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EntityProfile.remove_old_entity_profiles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CertificateProfile.remove_old_certificate_profiles')
    def test_clean_up_old_pki_profiles__is_successful(self, mock_remove_old_entities, mock_remove_old_entity_profiles,
                                                      mock_remove_old_certificate_profiles):
        self.secuiflow06.clean_up_old_pki_profiles(self.user)
        self.assertEqual(mock_remove_old_entities.call_count, 1)
        self.assertEqual(mock_remove_old_entity_profiles.call_count, 1)
        self.assertEqual(mock_remove_old_certificate_profiles.call_count, 1)


class Secui07FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.test_nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34'),
                                ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34')]
        self.secui_07 = secui_07.SECUI_07()
        self.secuiflow07 = Secui07Flow()
        self.secuiflow07.NUM_TARGET_GROUPS = 2
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.execute_flow')
    def test_run__in_secui_07_is_successful(self, _):
        self.secui_07.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.exists', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.update_assignment')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete')
    def test_create_target_groups_and_assign_nodes_continues_with_errors(self, mock_delete, mock_create,
                                                                         mock_update_assignment, mock_nodes_list,
                                                                         mock_add_error, *_):
        mock_nodes_list.return_value = self.test_nodes_list

        mock_delete.side_effect = [self.exception, None, None, None, None]
        mock_create.side_effect = [self.exception, None, None, None]
        mock_update_assignment.side_effect = [self.exception, None, None]
        self.secuiflow07.create_target_groups_and_assign_nodes()
        self.assertTrue(call(EnmApplicationError(self.exception) in mock_add_error.mock_calls))
        self.assertEqual(mock_update_assignment.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.exists', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.create')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete')
    def test_create_target_groups_and_assign_nodes__target_does_not_exist(self, mock_delete, *_):
        self.secuiflow07.create_target_groups_and_assign_nodes()
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.state', new_callable=PropertyMock)
    @patch('enmutils.lib.enm_user_2.User.delete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.flow_cleanup')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.create_custom_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.create_custom_role')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.create_target_groups_and_assign_nodes')
    def test_flow_continues_with_errors(self, mock_create_targets, mock_create_custom_role,
                                        mock_create_custom_user, mock_flow_cleanup, *_):
        mock_create_targets.return_value = [Mock(), Mock()]
        mock_create_custom_role.return_value = (Mock(), Mock())
        mock_create_custom_user.return_value = [Mock()]
        self.secuiflow07.execute_flow()
        self.assertTrue(mock_flow_cleanup.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow.create_target_groups_and_assign_nodes')
    def test_flow_adds_exception(self, mock_create_targets, mock_add_error, *_):
        mock_create_targets.return_value = None
        self.secuiflow07.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_flow_cleanup(self, mock_debug, *_):
        self.secuiflow07.flow_cleanup(Mock(), [self.user])
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_flow_cleanup__removes_deleted_users(self, *_):
        self.secuiflow07.teardown_list.append(self.user)
        self.secuiflow07.flow_cleanup(Mock(), [self.user])
        self.assertNotIn(self.user, self.secuiflow07.teardown_list)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_flow_cleanup__removes_from_teardown(self, *_):
        self.secuiflow07.teardown_list.append(self.user)
        self.secuiflow07.flow_cleanup(Mock(), [self.user])
        self.assertNotIn(self.user, self.secuiflow07.teardown_list)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow._set_teardown_objects')
    def test_flow_cleanup_sets_teardown_objects(self, mock_set_teardown, *_):
        self.secuiflow07.TARGET_GROUPS = [Mock()]
        self.secuiflow07.flow_cleanup(Mock(), [self.user])
        self.assertTrue(mock_set_teardown.call_count is 2)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui07Flow._set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_flow_cleanup__logs_failed_delete(self, mock_debug, *_):
        self.secuiflow07.teardown_list.append(self.user)
        self.user.delete.side_effect = Exception("Error")
        self.secuiflow07.flow_cleanup(Mock(), [self.user])
        mock_debug.assert_called_with("Failed to delete user, response: Error, teardown may be impacted.")


class Secui08FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_08 = secui_08.SECUI_08()
        self.secuiflow08 = Secui08Flow()
        self.secuiflow08.NUM_TARGET_GROUPS = 2
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.execute_flow')
    def test_run__in_secui_08_is_successful(self, _):
        self.secui_08.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.update')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.create_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.get_timestamp_str')
    def test_execute_flow__is_success(self, mock_timestamp, mock_create_target_groups, mock_keep_running,
                                      mock_update, mock_add_error, *_):
        mock_timestamp.return_value = "1234"
        mock_keep_running.side_effect = [True, True, False]
        mock_create_target_groups.return_value = [Target(name="Test", description="Test"),
                                                  Target(name="Test", description="Test")]
        mock_update.side_effect = [self.exception, self.exception, None, None]
        self.secuiflow08.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.add_error_as_exception')
    def test_create_target_groups__add_error_on_target_delete(self, mock_add_error, mock_target):
        mock_target.return_value.delete.side_effect = self.exception
        mock_target.return_value.exists = True
        self.secuiflow08.create_target_groups(self.user, 1)
        self.assertTrue(call(EnmApplicationError(self.exception) in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.add_error_as_exception')
    def test_create_target_groups__add_error_on_target_create(self, mock_add_error, mock_target):
        mock_target.return_value.create.side_effect = self.exception
        mock_target.return_value.exists = False
        self.secuiflow08.create_target_groups(self.user, 1)
        self.assertTrue(call(EnmApplicationError(self.exception) in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui08Flow.add_error_as_exception')
    def test_create_target_groups__is_success(self, mock_add_error, mock_target):
        mock_target.return_value.create.side_effect = Mock()
        mock_target.return_value.exists = False
        self.secuiflow08.create_target_groups(self.user, 1)
        self.assertFalse(mock_add_error.called)


class Secui09FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_09 = secui_09.SECUI_09()
        self.secuiflow09 = Secui09Flow()
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.execute_flow')
    def test_run__in_secui_09_is_successful(self, _):
        self.secui_09.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.delete_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.create_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.get_timestamp_str')
    def test_execute_flow__is_success(self, mock_timestamp, mock_create_target_groups, mock_keep_running, mock_sleep, *_):
        mock_timestamp.return_value = "1234"
        mock_keep_running.side_effect = [True, False]
        mock_create_target_groups.return_value = [Target(name="Test", description="Test"),
                                                  Target(name="Test", description="Test")]
        self.secuiflow09.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete')
    def test_delete_target_groups__is_success(self, *_):
        group = Target(name="Test", description="Test")
        self.secuiflow09.teardown_list.append(group)
        self.secuiflow09.delete_target_groups([group])
        self.assertNotIn(group, self.secuiflow09.teardown_list)
        self.assertTrue(len(self.secuiflow09.teardown_list) is 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui09Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete')
    def test_delete_target_groups__adds_exception(self, mock_delete, mock_add_error, _):
        mock_delete.side_effect = self.exception
        self.secuiflow09.delete_target_groups([Target(name="Test", description="Test")])
        self.assertTrue(call(EnmApplicationError(self.exception) in mock_add_error.mock_calls))


class Secui10FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_10 = secui_10.SECUI_10()
        self.secuiflow10 = Secui10Flow()
        self.secuiflow10.NUM_USERS = 1
        self.secuiflow10.USER_ROLES = ["ADMINISTRATOR"]
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.execute_flow')
    def test_run__in_secui_10_is_successful(self, _):
        self.secui_10.run()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.check_ldap_is_configured_on_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.determine_nodes')
    def test_execute_flow__is_successful(
            self, mock_nodes, mock_keep_running, mock_sleep, mock_check_ldap_is_configured_on_nodes, mock_debug, *_):
        mock_keep_running.side_effect = [True, False]
        nodes = [Mock(node_id="LTE01dg2ERBS00031",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland", profiles=['SECUI_10']),
                 Mock(node_id="NR45gNodeBRadio00018",
                      oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00018",
                      rofiles=['SECUI_10'])]
        mock_nodes.return_value = nodes
        mock_check_ldap_is_configured_on_nodes.return_value = mock_nodes.return_value
        self.secuiflow10.execute_flow()
        self.assertTrue(mock_sleep.called)
        mock_debug.assert_called_with("2 synced radio nodes: ['LTE01dg2ERBS00031', 'NR45gNodeBRadio00018']")

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.check_ldap_is_configured_on_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.determine_nodes')
    def test_execute_flow__if_nodes_no_ldap_configured(
            self, mock_nodes, mock_keep_running, mock_sleep, mock_check_ldap_is_configured_on_nodes,
            mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = [Mock()]
        mock_check_ldap_is_configured_on_nodes.return_value = []
        self.secuiflow10.execute_flow()
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SecuiFlow.check_ldap_is_configured_on_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.determine_nodes')
    def test_execute_flow__if_nodes_are_not_synced(
            self, mock_nodes, mock_keep_running, mock_sleep, mock_check_ldap_is_configured_on_nodes,
            mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_nodes.return_value = []
        self.secuiflow10.execute_flow()
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertFalse(mock_check_ldap_is_configured_on_nodes.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.get_synchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SHMUtils.deallocate_unused_nodes')
    def test_determine_nodes(self, mock_deallocate_unused_nodes, mock_get_synced_nodes, mock_nodes_list):
        node1 = Mock(node_id="LTE01dg2ERBS00030", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                     profiles=['SECUI_10'])
        node2 = Mock(node_id="LTE01dg2ERBS00031", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                     profiles=['SECUI_10'])
        node3 = Mock(node_id="NR45gNodeBRadio00018",
                     oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00018",
                     profiles=['SECUI_10'])
        mock_nodes_list.return_value = [node1, node2, node3]
        mock_get_synced_nodes.return_value = [node2, node3]
        self.secuiflow10.determine_nodes(self.user)
        mock_get_synced_nodes.assert_called_with([node1, node2, node3], self.user)
        mock_deallocate_unused_nodes.assert_called_with([node1], self.secuiflow10)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.get_synchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.SHMUtils.deallocate_unused_nodes')
    def test_determine_nodes__if_no_nodes(self, mock_deallocate_unused_nodes, mock_get_synced_nodes, mock_nodes_list):
        mock_nodes_list.return_value = []
        mock_get_synced_nodes.return_value = []
        self.secuiflow10.determine_nodes(self.user)
        mock_get_synced_nodes.assert_called_with([], self.user)
        mock_deallocate_unused_nodes.assert_called_with([], self.secuiflow10)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_random_string')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_task_set__if_node_type_is_4g(self, mock_debug, *_):
        node = Mock(node_id="LTE01dg2ERBS00030", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                    profiles=['SECUI_10'])
        self.user.enm_execute.return_value.get_output.return_value = "1 instance(s) found"
        self.secuiflow10.task_set([self.user, node], self.secuiflow10)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_random_string')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_task_set__if_node_type_is_5g(self, mock_debug, *_):
        node = Mock(node_id="NR45gNodeBRadio00018",
                    oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00018",
                    profiles=['SECUI_10'])
        self.user.enm_execute.return_value.get_output.return_value = "1 instance(s) found"
        self.secuiflow10.task_set([self.user, node], self.secuiflow10)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_random_string')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.add_error_as_exception')
    def test_task_set__adds_exception_if_node_type_is_4g(self, mock_add_error, *_):
        node = Mock(node_id="LTE01dg2ERBS00030", subnetwork="NETSimW",
                    oss_prefix="SubNetwork=Europe,SubNetwork=Ireland", profiles=['SECUI_10'])
        self.user.enm_execute.return_value.side_effect = self.exception
        self.secuiflow10.task_set([self.user, node], self.secuiflow10)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_random_string')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui10Flow.add_error_as_exception')
    def test_task_set__adds_exception_if_node_type_is_5g(self, mock_add_error, *_):
        node = Mock(node_id="NR45gNodeBRadio00018",
                    oss_prefix="SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR45gNodeBRadio00018",
                    profiles=['SECUI_10'])
        self.user.enm_execute.return_value.side_effect = self.exception
        self.secuiflow10.task_set([self.user, node], self.secuiflow10)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_random_string')
    def test_task_set__raises_EnmApplication_error_if_no_output(self, *_):
        self.user.enm_execute.return_value.get_output.return_value = None
        node = Mock(node_id="LTE01dg2ERBS00030", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                    profiles=['SECUI_10'])
        self.assertRaises(EnmApplicationError, self.secuiflow10.task_set([self.user, node], self.secuiflow10))

    def test_task_set__raises_environ_error(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'Error']
        node = Mock(node_id="LTE01dg2ERBS00030", oss_prefix="SubNetwork=Europe,SubNetwork=Ireland",
                    profiles=['SECUI_10'])
        self.assertRaises(EnvironError, self.secuiflow10.task_set([self.user, node], self.secuiflow10))


class Secui11FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.secui_11 = secui_11.SECUI_11()
        self.secui11flow = Secui11Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui11Flow.state', new_callable=PropertyMock)
    def test_execute_flow__in_secui11_is_successful(self, _):
        self.secui11flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui11Flow.execute_flow')
    def test_run__in_secui_11_is_successful(self, _):
        self.secui_11.run()


class Secui12FlowUnitTests(unittest2.TestCase):

    ldap_proper_settings_response = {u'isBindPasswordEmpty': False,
                                     u'extIdpSettings': {u'bindDN': u'cn=extldapadmin,ou=people,dc=acme,dc=com',
                                                         u'authType': u'REMOTEAUTHN', u'searchScope': u'SUBTREE',
                                                         u'bindPassword': u'', u'searchFilter': u'',
                                                         u'secondaryServerAddress':
                                                             unit_test_utils.generate_configurable_ip(),
                                                         u'primaryServerAddress':
                                                             unit_test_utils.generate_configurable_ip(),
                                                         u'baseDN': u'dc=acme,dc=com',
                                                         u'remoteAuthProfile': u'STANDARD',
                                                         u'ldapConnectionMode': u'LDAP', u'searchControls': u'',
                                                         u'userBindDNFormat': u'uid=$user', u'searchAttribute': u''}}

    ldap_faulty_settings_response = {u'isBindPasswordEmpty': False,
                                     u'extIdpSettings': {u'bindDN': u'cn=extldapadmin,ou=people,dc=acme,dc=com',
                                                         u'authType': u'REMOTEAUTHN', u'searchScope': u'SUBTREE',
                                                         u'bindPassword': u'', u'searchFilter': u'',
                                                         u'secondaryServerAddress':
                                                             unit_test_utils.generate_configurable_ip(),
                                                         u'primaryServerAddress':
                                                             unit_test_utils.generate_configurable_ip(),
                                                         u'baseDN': u'dc=acme,dc=com',
                                                         u'remoteAuthProfile': u'STANDARD',
                                                         u'ldapConnectionMode': u'LDAP', u'searchControls': u'',
                                                         u'userBindDNFormat': u'uid=$user', u'searchAttribute': u''}}

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.secui_12 = secui_12.SECUI_12()
        self.secui12flow = Secui12Flow()
        self.secui12flow.USER_NAME = "RemoteUser_01"
        self.secui12flow.USER_PASSWORD = "RemotePassword_01"
        self.secui12flow.authType = "REMOTEAUTHN"
        self.secui12flow.remoteAuthProfile = "STANDARD"
        self.secui12flow.baseDN = "dc=acme,dc=com"
        self.secui12flow.ldapConnectionMode = "LDAP"
        self.secui12flow.userBindDNFormat = "uid=$user"
        self.secui12flow.bindDN = "cn=extldapadmin,ou=people,dc=acme,dc=com"
        self.secui12flow.bindPwd = "Externalldapadmin01"
        self.secui12flow.USER_ROLES = ["SECURITY_ADMIN"]
        self.secui12flow.NUM_USERS = 1
        self.secui12flow.SCHEDULE_SLEEP = 1
        self.secui12flow.CUSTOM_USER_ROLES = ["ACME_PKI_Operator"]
        self.secui12flow.CUSTOM_TARGET_GROUPS = ["ACMENORTH", "ACMESOUTH"]
        self.secui12flow.teardown_list = []
        self.secui12flow.FEDERATED_USER_NAME = "fedacmeenduser2"
        self.secui12flow.COMROLE = "SystemAdministrator"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'check_remove_old_federated_users_with_roles_tgs')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_federated_user_instance')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.federated_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.external_ldap_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.set_fidm_sync_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.perform_fidm_sync_preconditions')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_roles_and_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'ldap_configuration_prerequisites')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_user_in_enm')
    def test_execute_flow_is__successful(self, mock_get_user, mock_add_error, mock_ldap_config,
                                         mock_create_custom_roles_target_groups, mock_fidm_sync_pre_conditions, *_):
        mock_get_user.return_value = self.user
        self.secui12flow.execute_flow()
        self.assertTrue(mock_ldap_config.called)
        mock_create_custom_roles_target_groups.assert_called_with(self.secui12flow.CUSTOM_USER_ROLES,
                                                                  self.secui12flow.CUSTOM_TARGET_GROUPS)
        self.assertTrue(mock_fidm_sync_pre_conditions.called)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'check_remove_old_federated_users_with_roles_tgs')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_federated_user_instance')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.federated_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.external_ldap_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.set_fidm_sync_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_user_in_enm',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'perform_fidm_sync_preconditions')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_roles_and_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.ldap_configuration_prerequisites')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_execute_flow__adds_error_as_exception_when_user_creation_fails(self, mock_add_error, mock_sleep,
                                                                            mock_ldap_config,
                                                                            mock_create_custom_roles_target_groups,
                                                                            mock_fidm_sync_pre_conditions, *_):
        self.secui12flow.execute_flow()
        self.assertTrue(mock_ldap_config.called)
        mock_create_custom_roles_target_groups.assert_called_with(self.secui12flow.CUSTOM_USER_ROLES,
                                                                  self.secui12flow.CUSTOM_TARGET_GROUPS)
        self.assertFalse(mock_fidm_sync_pre_conditions.called)
        self.assertEqual(1, mock_add_error.call_count)
        self.assertEqual(0, mock_sleep.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'set_federated_identity_synchronization_admin_state')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'check_remove_old_federated_users_with_roles_tgs')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_federated_user_instance')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.federated_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.external_ldap_user_login')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.set_fidm_sync_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'perform_fidm_sync_preconditions', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_user_in_enm')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.create_custom_roles_and_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.ldap_configuration_prerequisites')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_execute_flow__adds_error_as_exception_when_fidm_sync_fails(self, mock_add_error, mock_sleep,
                                                                        mock_ldap_config,
                                                                        mock_create_custom_roles_target_groups,
                                                                        mock_get_user, *_):
        mock_get_user.return_value = self.user
        self.secui12flow.execute_flow()
        self.assertTrue(mock_ldap_config.called)
        mock_create_custom_roles_target_groups.assert_called_with(self.secui12flow.CUSTOM_USER_ROLES,
                                                                  self.secui12flow.CUSTOM_TARGET_GROUPS)
        self.assertEqual(1, mock_add_error.call_count)
        self.assertEqual(0, mock_sleep.call_count)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    def test_verify_external_ldap_connectivity__raises_validation_error(self, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {u'successfulTest': False, u'failureReason': u''}
        self.user.post.return_value = response
        self.assertRaises(ValidationError, self.secui12flow.verify_external_ldap_connectivity, self.user)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    def test_verify_external_ldap_authentication__raises_validation_error(self, *_):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {u'successfulTest': False, u'failureReason': u''}
        self.user.post.return_value = response
        self.assertRaises(ValidationError, self.secui12flow.verify_external_ldap_authentication, self.user)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.check_external_ldap_settings')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.config')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_ldap_configuration_prerequisites__does_not_configure_if_ldap_already_configured(
            self, mock_get_user, mock_config, mock_check_external_ldap_settings, *_):
        get_response = Mock()
        get_response.status_code = 200
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_config.get_prop.side_effect = [ip_addr, ip_addr, ip_addr, ip_addr]
        get_response.json.return_value = self.ldap_proper_settings_response
        mock_get_user.return_value.get.return_value = get_response
        post_response = Mock()
        post_response.status_code = 200
        post_response.json.return_value = {u'successfulTest': u'true', u'failureReason': u''}
        mock_get_user.return_value.post.side_effect = [post_response, post_response]
        self.secui12flow.ldap_configuration_prerequisites()
        self.assertEqual(mock_get_user.return_value.get.call_count, 1)
        self.assertEqual(mock_get_user.return_value.post.call_count, 2)
        self.assertTrue(mock_check_external_ldap_settings.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.check_external_ldap_settings')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.config')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_ldap_configuration_prerequisites__if_check_external_ldap_settings_return_false(
            self, mock_get_user, mock_config, mock_check_external_ldap_settings, *_):
        get_response = Mock()
        get_response.status_code = 200
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_config.get_prop.side_effect = [ip_addr, ip_addr, ip_addr, ip_addr]
        get_response.json.return_value = self.ldap_proper_settings_response
        mock_get_user.return_value.get.return_value = get_response
        mock_check_external_ldap_settings.return_value = False
        post_response = Mock()
        post_response.status_code = 200
        post_response.json.return_value = {u'successfulTest': u'true', u'failureReason': u''}
        mock_get_user.return_value.post.side_effect = [post_response, post_response]
        self.secui12flow.ldap_configuration_prerequisites()
        self.assertEqual(mock_get_user.return_value.get.call_count, 1)
        self.assertEqual(mock_get_user.return_value.post.call_count, 2)
        self.assertTrue(mock_check_external_ldap_settings.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.raise_for_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.check_external_ldap_settings')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_ldap_configuration_prerequisites__raises_enm_application_error(self, mock_get_user,
                                                                            mock_check_external_ldap_settings, *_):
        get_response = Mock()
        get_response.status_code = 404
        get_response.json.return_value = None
        mock_get_user.return_value.get.return_value = get_response
        self.assertRaises(EnmApplicationError, self.secui12flow.ldap_configuration_prerequisites)
        self.assertFalse(mock_check_external_ldap_settings.called)

    def test_create_ldap_user_in_enm__is_successful(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def test_create_ldap_user_in_enm__raises_exception_while_creating_user(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def test_create_ldap_user_in_enm__raises_enm_application_error(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_check_external_ldap_settings__is_successful(self, mock_debug_log):
        external_ldap_settings = {u'isBindPasswordEmpty': False,
                                  u'extIdpSettings': {u'bindDN': u'cn=extldapadmin,ou=people,dc=acme,dc=com',
                                                      u'authType': u'REMOTEAUTHN', u'searchScope': u'SUBTREE',
                                                      u'bindPassword': u'', u'searchFilter': u'',
                                                      u'secondaryServerAddress': u'10.42.173.44:7389',
                                                      u'primaryServerAddress': u'10.45.205.253:1389',
                                                      u'baseDN': u'dc=acme,dc=com', u'remoteAuthProfile': u'STANDARD',
                                                      u'ldapConnectionMode': u'LDAP', u'searchControls': u'',
                                                      u'userBindDNFormat': u'uid=$user', u'searchAttribute': u''}}
        self.secui12flow.check_external_ldap_settings(external_ldap_settings)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    def test_check_external_ldap_settings__if_bind_dn_different(self, mock_debug_log):
        self.secui12flow.bindDN = "cn=extldapadmin,ou=people,dc=acme"
        external_ldap_settings = {u'isBindPasswordEmpty': False,
                                  u'extIdpSettings': {u'bindDN': u'cn=extldapadmin,ou=people,dc=acme,dc=com',
                                                      u'authType': u'REMOTEAUTHN', u'searchScope': u'SUBTREE',
                                                      u'bindPassword': u'', u'searchFilter': u'',
                                                      u'secondaryServerAddress': u'10.42.173.44:7389',
                                                      u'primaryServerAddress': u'10.45.205.253:1389',
                                                      u'baseDN': u'dc=acme,dc=com', u'remoteAuthProfile': u'STANDARD',
                                                      u'ldapConnectionMode': u'LDAP', u'searchControls': u'',
                                                      u'userBindDNFormat': u'uid=$user', u'searchAttribute': u''}}
        self.assertEqual(False, self.secui12flow.check_external_ldap_settings(external_ldap_settings))
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.perform_fidm_sync_postconditions')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'import_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'set_federated_identity_synchronization_period')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'set_federated_identity_synchronization_admin_state')
    def test_perform_fidm_sync_preconditions__is_sucessful(
            self, mock_set_fid_sync_state, mock_set_fid_sync_period, mock_import_fid_sync,
            mock_fidm_sync_post_conditions):
        self.secui12flow.perform_fidm_sync_preconditions(self.user)
        self.assertTrue(mock_set_fid_sync_state.called)
        self.assertTrue(mock_set_fid_sync_period.called)
        self.assertTrue(mock_import_fid_sync.called)
        self.assertTrue(mock_fidm_sync_post_conditions.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.perform_fidm_sync_postconditions')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'import_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'set_federated_identity_synchronization_period')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'set_federated_identity_synchronization_admin_state')
    def test_perform_fidm_sync_preconditions__if_import_fid_sync_raises_http_error(
            self, mock_set_fid_sync_state, mock_set_fid_sync_period, mock_import_fid_sync,
            mock_fidm_sync_post_conditions, mock_debug_log):
        mock_import_fid_sync.side_effect = HTTPError("Failed to import the federated identity synchronization")
        self.assertRaises(HTTPError, self.secui12flow.perform_fidm_sync_preconditions, self.user)
        self.assertFalse(mock_set_fid_sync_state.called)
        self.assertFalse(mock_set_fid_sync_period.called)
        self.assertTrue(mock_import_fid_sync.called)
        self.assertFalse(mock_fidm_sync_post_conditions.called)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'wait_force_sync_federated_identity_synchronization_to_complete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'force_sync_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'get_federated_identity_last_synchronization_report')
    def test_perform_fidm_sync_postconditions__is_successful(
            self, mock_get_fid_last_sync_report, mock_force_fid_sync_state, mock_wait_force_sync, mock_debug_log, *_):
        self.secui12flow.perform_fidm_sync_postconditions(self.user)
        self.assertTrue(mock_force_fid_sync_state.called)
        self.assertTrue(mock_get_fid_last_sync_report.called)
        self.assertTrue(mock_wait_force_sync.called)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'wait_force_sync_federated_identity_synchronization_to_complete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'force_sync_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'get_federated_identity_last_synchronization_report')
    def test_perform_fidm_sync_postconditions__if_force_sync_fid_raises_http_error(
            self, mock_get_fid_last_sync_report, mock_force_sync_fdi, mock_wait_force_sync, mock_debug_log, *_):
        mock_force_sync_fdi.side_effect = HTTPError("Failed to force sync federated identity synchronization")
        self.assertRaises(HTTPError, self.secui12flow.perform_fidm_sync_postconditions,
                          self.user)
        self.assertTrue(mock_force_sync_fdi.called)
        self.assertFalse(mock_get_fid_last_sync_report.called)
        self.assertFalse(mock_wait_force_sync.called)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'restore_to_defaults_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'wait_force_delete_federated_identity_synchronization_to_complete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.FIDM_interface.'
           'force_delete_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.'
           'FIDM_interface.set_federated_identity_synchronization_admin_state')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.partial')
    def test_set_fidm_sync_teardown_objects__is_successful(self, mock_partial, mock_picklable_boundmethod, *_):
        self.secui12flow.set_fidm_sync_teardown_objects(self.user)
        self.assertEqual(mock_picklable_boundmethod.call_count, 5)
        self.assertEqual(mock_partial.call_count, 5)
        self.assertEqual(len(self.secui12flow.teardown_list), 5)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_federated_user_login__is_successful(self, mock_add_error, mock_debug_log, mock_sleep, *_):
        self.secui12flow.federated_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(self.user.open_session.called)
        self.assertTrue(self.user.remove_session.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_federated_user_login__adds_error_as_exception_while_opening_session(self, mock_add_error, mock_debug_log,
                                                                                 mock_sleep, *_):
        self.user.open_session.side_effect = Exception("Unable to open session with the federated user")
        self.secui12flow.federated_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertTrue(self.user.open_session.called)
        self.assertFalse(self.user.remove_session.called)
        self.assertFalse(mock_sleep.called)
        self.assertTrue(call(self.user.open_session.side_effect in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_federated_user_login__adds_error_as_exception_while_remove_session(self, mock_add_error, mock_debug_log,
                                                                                mock_sleep, *_):
        self.user.remove_session.side_effect = Exception("Unable to remove session of federated user")
        self.secui12flow.federated_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(self.user.open_session.called)
        self.assertTrue(self.user.remove_session.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(call(self.user.remove_session.side_effect in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_external_ldap_user_login__is_successful(self, mock_add_error, mock_debug_log, mock_sleep, *_):
        self.secui12flow.external_ldap_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(self.user.open_session.called)
        self.assertTrue(self.user.remove_session.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_external_ldap_user_login__adds_error_as_exception_while_opening_session(self, mock_add_error,
                                                                                     mock_debug_log, mock_sleep, *_):
        self.user.open_session.side_effect = Exception("Unable to open session with the ldap user")
        self.secui12flow.external_ldap_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertTrue(self.user.open_session.called)
        self.assertFalse(self.user.remove_session.called)
        self.assertFalse(mock_sleep.called)
        self.assertTrue(call(self.user.return_value.open_session.side_effect in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    def test_external_ldap_user_login__adds_error_as_exception_while_remove_session(self, mock_add_error,
                                                                                    mock_debug_log, mock_sleep, *_):
        self.user.remove_session.side_effect = Exception("Unable to remove session of ldap user")
        self.secui12flow.external_ldap_user_login(self.user)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(self.user.open_session.called)
        self.assertTrue(self.user.remove_session.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(call(self.user.return_value.remove_session.side_effect in mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomUser')
    def test_create_federated_user_instance__is_successful(self, mock_custom_user, mock_target, mock_enm_role):
        mock_custom_user.return_value = self.user
        self.secui12flow.create_federated_user_instance()
        self.assertTrue(mock_custom_user.called)
        self.assertEqual(mock_target.call_count, 2)
        self.assertEqual(mock_enm_role.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.User.get_usernames")
    def test_verify_federated_users_deletion_status__if_federated_users_not_exist_in_enm(self, mock_get_usernames,
                                                                                         mock_debug_log):
        mock_get_usernames.return_value = ["user1", "user2", "user3"]
        self.secui12flow.verify_federated_users_deletion_status()
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.User.get_usernames")
    def test_verify_federated_users_deletion_status__if_federated_users_existed_in_enm(self, mock_get_usernames,
                                                                                       mock_debug_log):
        mock_get_usernames.return_value = ["user1", "user2", "user3", "fedacmeenduser1", "fedacmeenduser2"]
        self.assertRaises(EnvironError, self.secui12flow.verify_federated_users_deletion_status)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.User.get_usernames")
    def test_verify_federated_users_deletion_status__if_return_value_required(self, mock_get_usernames,
                                                                              mock_debug_log):
        mock_get_usernames.return_value = ["user1", "user2", "user3"]
        self.secui12flow.verify_federated_users_deletion_status(required_return_value=True)
        self.assertEqual(1, mock_debug_log.call_count)

    # check_remove_old_federated_users_with_roles_tgs test cases
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_roles')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_federated_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_ldap_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_remove_old_federated_users_with_roles_tgs__is_successful(self, mock_admin, mock_verify_fd_users,
                                                                            mock_delete_ldap_user, mock_delete_fd_users,
                                                                            mock_delete_fd_users_roles, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
                   'check_old_ldap_user_exist') as mock_check_old_ldap_user_exist:
            mock_admin.return_value = Mock()
            mock_verify_fd_users.return_value = True
            self.secui12flow.check_remove_old_federated_users_with_roles_tgs()
            self.assertEqual(mock_admin.call_count, 1)
            mock_verify_fd_users.assert_called_with(required_return_value=True)
            mock_delete_fd_users_roles.assert_called_with(mock_admin.return_value)
            mock_delete_fd_users.assert_called_with(mock_admin.return_value)
            self.assertEqual(mock_delete_ldap_user.call_count, 1)
            self.assertEqual(mock_check_old_ldap_user_exist.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_roles')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_federated_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_ldap_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_remove_old_federated_users_with_roles_tgs__if_fed_users_not_existed(self, mock_admin,
                                                                                       mock_verify_fd_users,
                                                                                       mock_delete_ldap_user,
                                                                                       mock_delete_fd_users,
                                                                                       mock_debug_log, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
                   'check_old_ldap_user_exist') as mock_check_old_ldap_user_exist:
            mock_admin.return_value = Mock()
            mock_verify_fd_users.return_value = False
            mock_check_old_ldap_user_exist.return_value = True
            self.secui12flow.check_remove_old_federated_users_with_roles_tgs()
            self.assertEqual(mock_admin.call_count, 1)
            mock_verify_fd_users.assert_called_with(required_return_value=True)
            self.assertEqual(mock_delete_fd_users.call_count, 0)
            self.assertEqual(mock_delete_ldap_user.call_count, 1)
            self.assertEqual(mock_debug_log.call_count, 2)
            self.assertEqual(mock_check_old_ldap_user_exist.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_roles')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_federated_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_ldap_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_remove_old_federated_users_with_roles_tgs__raises_exception(self, mock_admin,
                                                                               mock_verify_fd_users,
                                                                               mock_delete_ldap_user,
                                                                               mock_delete_fd_users,
                                                                               mock_add_error, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
                   'check_old_ldap_user_exist') as mock_check_old_ldap_user_exist:

            mock_admin.return_value = Mock()
            mock_verify_fd_users.return_value = True
            mock_delete_ldap_user.side_effect = Exception("something is wrong")
            self.secui12flow.check_remove_old_federated_users_with_roles_tgs()
            self.assertEqual(mock_admin.call_count, 1)
            mock_verify_fd_users.assert_called_with(required_return_value=True)
            self.assertEqual(mock_delete_fd_users.call_count, 0)
            self.assertEqual(mock_delete_ldap_user.call_count, 1)
            self.assertEqual(mock_add_error.call_count, 1)
            self.assertEqual(mock_check_old_ldap_user_exist.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_target_groups')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'delete_existing_federated_users_required_roles')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_federated_users')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.delete_old_ldap_user')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_remove_old_federated_users_with_roles_tgs__if_fed_users_and_ldap_users_not_existed(
            self, mock_admin, mock_verify_fd_users, mock_delete_ldap_user, mock_delete_fd_users, mock_debug_log, *_):
        with patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
                   'check_old_ldap_user_exist') as mock_check_old_ldap_user_exist:
            mock_admin.return_value = Mock()
            mock_verify_fd_users.return_value = False
            mock_check_old_ldap_user_exist.return_value = False
            self.secui12flow.check_remove_old_federated_users_with_roles_tgs()
            self.assertEqual(mock_admin.call_count, 1)
            mock_verify_fd_users.assert_called_with(required_return_value=True)
            self.assertEqual(mock_delete_fd_users.call_count, 0)
            self.assertEqual(mock_delete_ldap_user.call_count, 0)
            self.assertEqual(mock_debug_log.call_count, 2)
            self.assertEqual(mock_check_old_ldap_user_exist.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'set_federated_identity_synchronization_admin_state')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'force_delete_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'wait_force_delete_federated_identity_synchronization_to_complete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'restore_to_defaults_federated_identity_synchronization')
    def test_delete_old_federated_users__is_successful(self, mock_restore_fid_sync,
                                                       mock_verify_users_del_status,
                                                       mock_wait_force_del_fid_sync, mock_force_delete_fid_sync,
                                                       mock_set_fid_sync_admin_state,
                                                       mock_add_error):
        self.secui12flow.delete_old_federated_users(self.user)
        mock_set_fid_sync_admin_state.assert_called_with(self.user, "disabled")
        mock_force_delete_fid_sync.assert_called_with(self.user)
        mock_wait_force_del_fid_sync.assert_called_with(self.user)
        self.assertEqual(mock_verify_users_del_status.call_count, 1)
        mock_restore_fid_sync.assert_called_with(self.user)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'set_federated_identity_synchronization_admin_state')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'force_delete_federated_identity_synchronization')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'wait_force_delete_federated_identity_synchronization_to_complete')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.verify_federated_users_deletion_status')
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.'
           'restore_to_defaults_federated_identity_synchronization')
    def test_delete_old_federated_users__raises_exception(self, mock_restore_fid_sync, mock_verify_users_del_status,
                                                          mock_wait_force_del_fid_sync, mock_force_delete_fid_sync,
                                                          mock_set_fid_sync_admin_state, mock_add_error):
        mock_set_fid_sync_admin_state.side_effect = Exception("something is wrong")
        self.secui12flow.delete_old_federated_users(self.user)
        mock_set_fid_sync_admin_state.assert_called_with(self.user, "disabled")
        self.assertEqual(mock_wait_force_del_fid_sync.call_count, 0)
        self.assertEqual(mock_force_delete_fid_sync.call_count, 0)
        self.assertEqual(mock_verify_users_del_status.call_count, 0)
        self.assertEqual(mock_restore_fid_sync.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomUser.delete")
    def test_delete_old_ldap_user__is_successful(self, mock_cust_user_delete, mock_debug_log):
        self.secui12flow.delete_old_ldap_user()
        self.assertEqual(mock_cust_user_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomUser.delete")
    def test_delete_old_ldap_user__raises_exception(self, mock_cust_user_delete, mock_debug_log):
        mock_cust_user_delete.side_effect = Exception("error")
        self.secui12flow.delete_old_ldap_user()
        self.assertEqual(mock_cust_user_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.capabilities")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole.delete")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    def test_delete_existing_federated_users_required_roles__is_successful(self, mock_debug_log,
                                                                           mock_custom_role_delete, mock_enm_role, *_):
        mock_enm_role.return_value = Mock()
        self.secui12flow.delete_existing_federated_users_required_roles(self.user)
        self.assertEqual(mock_custom_role_delete.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.capabilities")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.EnmRole")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.CustomRole.delete")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    def test_delete_existing_federated_users_required_roles__raises_exception(self, mock_debug_log,
                                                                              mock_custom_role_delete, mock_enm_role,
                                                                              *_):
        mock_enm_role.return_value = Mock()
        mock_custom_role_delete.side_effect = [Exception("error"), None]
        self.secui12flow.delete_existing_federated_users_required_roles(self.user)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_custom_role_delete.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    def test_delete_existing_federated_users_required_target_groups__is_successful(self, mock_debug_log,
                                                                                   mock_tg_delete):
        self.secui12flow.delete_existing_federated_users_required_target_groups(self.user)
        mock_tg_delete.assert_called_with(user=self.user)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.Target.delete")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    def test_delete_existing_federated_users_required_target_groups__raises_exception(self, mock_debug_log,
                                                                                      mock_tg_delete):
        mock_tg_delete.side_effect = [Exception("error")]
        self.secui12flow.delete_existing_federated_users_required_target_groups(self.user)
        mock_tg_delete.assert_called_with(user=self.user)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.user_exists")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_old_ldap_user_exist__if_user_found(self, mock_admin, mock_user_exists, mock_debug_log):
        mock_admin.return_value = Mock()
        mock_user_exists.return_value = True
        self.assertEqual(True, self.secui12flow.check_old_ldap_user_exist())
        self.assertEqual(mock_admin.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.user_exists")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_old_ldap_user_exist__if_user_not_found(self, mock_admin, mock_user_exists, mock_debug_log):
        mock_admin.return_value = Mock()
        mock_user_exists.return_value = False
        self.assertEqual(False, self.secui12flow.check_old_ldap_user_exist())
        self.assertEqual(mock_admin.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.secui_flows.secui_flow.user_exists")
    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.get_workload_admin_user')
    def test_check_old_ldap_user_exist__raises_exception(self, mock_admin, mock_user_exists, mock_debug_log):
        mock_admin.return_value = Mock()
        mock_user_exists.side_effect = Exception()
        self.secui12flow.check_old_ldap_user_exist()
        self.assertEqual(mock_admin.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.secui_flows.secui_flow.Secui12Flow.execute_flow')
    def test_run__in_secui_12_is_successful(self, _):
        self.secui_12.run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
