#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.esm_flows.esm_flow import ESM01Flow

ABC_TEST = 'abc_test'
ESMON_VM_KEY = 'esmon'


class ESM01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.user.username = "User_u0"
        self.flow = ESM01Flow()
        self.flow.PHYSICAL_DEPLOYMENT = True
        self.flow.THREAD_QUEUE_TIMEOUT = 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_list_of_db_vms_host_names')
    def test_get_esmon_vm_ip__successful_on_physical(self, mock_get_list_of_db, mock_log):
        self.flow.PHYSICAL_DEPLOYMENT = True
        mock_get_list_of_db.return_value = ["some_ip"]
        self.flow.get_esmon_vm_ip()
        mock_get_list_of_db.assert_called_with(ESMON_VM_KEY)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_ip_of_cloud')
    def test_get_esmon_vm_ip__successful_on_cloud(self, mock_ip):
        self.flow.PHYSICAL_DEPLOYMENT = False
        mock_ip.return_value = ABC_TEST
        self.flow.get_esmon_vm_ip()

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_parameter_value_from_sed_document', return_value='ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id', return_value=["ip"])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.pexpect.spawn')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_get_esmon_vm_ip_cloud__successful_on_cloud(self, mock_log, *_):
        self.flow.get_esmon_vm_ip_cloud()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_parameter_value_from_sed_document', return_value='some_ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id', side_effect=[None, None, None, None,
                                                                                        None, None, None, None, None])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.pexpect.spawn')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_list_of_db_vms_host_names')
    def test_get_esmon_vm_ip_cloud__successful_on_cloud_sed_none(self, mock_get_list_of_db, mock_log, mock_spawn,
                                                                 mock_get_emp, mock_get_sed_id, mock_get_cloud_members,
                                                                 *_):
        self.assertFalse(mock_get_list_of_db.called)
        self.flow.get_esmon_vm_ip_cloud()
        self.assertTrue(mock_log.called)
        self.assertEqual(mock_get_list_of_db.call_count, 0)
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_get_emp.call_count, 1)
        self.assertEqual(mock_get_sed_id.call_count, 3)
        self.assertEqual(mock_get_cloud_members.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_parameter_value_from_sed_document', return_value='some_ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id', side_effect=[None, None, 'ip', None,
                                                                                        None, None, 'ip', None, 'ip'])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.pexpect.spawn')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_list_of_db_vms_host_names')
    def test_get_esmon_vm_ip_cloud__successful_on_cloud_sed_none_cloud(self, mock_get_list_of_db, mock_log, mock_spawn,
                                                                       mock_get_emp, mock_get_sed_id,
                                                                       mock_get_cloud_members, *_):
        self.assertFalse(mock_get_list_of_db.called)
        self.flow.get_esmon_vm_ip_cloud()
        self.assertTrue(mock_log.called)
        self.assertEqual(mock_get_list_of_db.call_count, 0)
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_get_emp.call_count, 1)
        self.assertEqual(mock_get_sed_id.call_count, 3)
        self.assertEqual(mock_get_cloud_members.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_parameter_value_from_sed_document', return_value='some_ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_cloud_members_ip_address')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id', side_effect=[None, 'ip', None, 'ip',
                                                                                        None, 'ip'])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_emp')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.pexpect.spawn')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_list_of_db_vms_host_names')
    def test_get_esmon_vm_ip_cloud__successful_on_cloud_sed_vio(self, mock_get_list_of_db, mock_log, mock_spawn,
                                                                mock_get_emp, mock_get_sed_id, mock_get_cloud_members,
                                                                *_):
        self.assertFalse(mock_get_list_of_db.called)
        self.flow.get_esmon_vm_ip_cloud()
        self.assertTrue(mock_log.called)
        self.assertEqual(mock_get_list_of_db.call_count, 0)
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_get_emp.call_count, 1)
        self.assertEqual(mock_get_sed_id.call_count, 2)
        self.assertEqual(mock_get_cloud_members.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_list_of_db_vms_host_names')
    def test_get_esmon_vm_ip__raises_environ_error(self, mock_get_list_of_db, mock_log):
        self.flow.PHYSICAL_DEPLOYMENT = True
        mock_get_list_of_db.return_value = None
        self.assertRaises(EnvironError, self.flow.get_esmon_vm_ip)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.info")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.random_get_request_cn')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_login')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_logout')
    def test_perform_esm_tasks__is_successful(self, mock_logout, mock_login, mock_random_get, mock_log, *_):
        user = Mock()
        self.flow.perform_esm_tasks(self.user, self.flow, user, esmon_vm_ip='ip')
        self.assertTrue(mock_login.called)
        self.assertTrue(mock_random_get.called)
        self.assertTrue(mock_logout.called)
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip', return_value="ip")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.is_enm_on_cloud_native')
    def test_set_esm_urls__is_successful(self, mock_is_enm_on_cn, *_):
        self.flow.NUM_USERS = 1
        self.flow.PHYSICAL_DEPLOYMENT = True
        mock_is_enm_on_cn.return_value = False
        self.flow.set_esm_urls()
        self.assertEqual(self.flow.NEW_PASSWORD, "Sec_Admin12345")

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip', return_value=EnvironError)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.is_enm_on_cloud_native')
    def test_set_esm_urls__exception(self, mock_is_enm_on_cn, *_):
        self.flow.NUM_USERS = 1
        self.flow.PHYSICAL_DEPLOYMENT = True
        mock_is_enm_on_cn.return_value = False
        self.assertRaises(EnvironError, self.flow.set_esm_urls())

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip', return_value="ip")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.is_enm_on_cloud_native')
    def test_set_esm_urls__is_successful_for_cn(self, mock_is_enm_on_cn, *_):
        self.flow.NUM_USERS = 1
        mock_is_enm_on_cn.return_value = True
        self.flow.set_esm_urls()
        self.assertEqual(self.flow.NEW_PASSWORD, "Test@Passw0rd")

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip', side_effect=EnvironError)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.is_enm_on_cloud_native')
    def test_set_esm_urls__exception_cn(self, mock_is_enm_on_cn, *_):
        self.flow.NUM_USERS = 1
        mock_is_enm_on_cn.return_value = True
        self.assertRaises(EnvironError, self.flow.set_esm_urls())

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_logout')
    @patch("enmutils.lib.enm_user_2.get_admin_user")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_login')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.create_esm_users')
    def test_execute_flow__is_successful(self, mock_create_esm_user, mock_create_and_execute_threads, mock_sleep,
                                         mock_get_workload_admin_user, mock_esm_login, *_):
        self.flow.NUM_USERS = 1
        response = Mock(ok=True)
        response.json.return_value = [{u"username": u"sec_admin"}, {u"username": u"sec"}]
        mock_get_workload_admin_user.return_value = Mock()
        mock_get_workload_admin_user.return_value.get.return_value = response
        self.flow.execute_flow()
        self.assertTrue(mock_create_esm_user.called)
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_esm_login.called)
        self.assertTrue(mock_get_workload_admin_user.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_logout')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_login')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.create_esm_users')
    def test_execute_flow__raises_exception(self, mock_create_esm_user, mock_create_and_execute_threads,
                                            mock_esm_login, mock_add_error, *_):
        self.flow.NUM_USERS = 1
        mock_create_esm_user.side_effect = Exception
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_esm_login.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__change_password_successful(self, mock_change_password, mock_add_error):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"changePassword": True}
        self.flow.esm_login(self.user, "test")
        self.assertTrue(mock_change_password.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__authentication_successful(self, mock_change_password, mock_add_error):
        response = Mock()
        self.user.post.return_value = response
        response.ok.side_effect = [False, False]
        response.json.side_effect = [None, {"changePassword": True}]
        self.flow.esm_login(self.user, "test")
        self.assertFalse(mock_change_password.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__change_password_successful_for_sec_admin(self, mock_change_password, mock_add_error):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"changePassword": True}
        self.flow.esm_login(self.user, "sec_admin")
        self.assertTrue(mock_change_password.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__authentication_successful_sec_admin(self, mock_change_password, mock_add_error):
        response = Mock()
        self.user.post.return_value = response
        response.ok.side_effect = [False, False]
        response.json.side_effect = [None, {"changePassword": True}]
        self.flow.esm_login(self.user, "sec_admin")
        self.assertFalse(mock_change_password.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__raises_exception(self, mock_change_password, mock_add_error):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"changePassword": True}
        mock_change_password.side_effect = Exception
        self.flow.esm_login(self.user, "test")
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.change_esm_login_password')
    def test_esm_login__raises_exception_sec_admin(self, mock_change_password, mock_add_error):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"changePassword": True}
        mock_change_password.side_effect = Exception
        self.flow.esm_login(self.user, "sec_admin")
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_change_esm_login_password__successful(self, mock_debug_log):
        response = Mock(ok=True)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": True}
        self.flow.change_esm_login_password(self.user, "test", "Old_pwd", "new_pwd")
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_change_esm_login_password__raises_error(self, mock_debug_log):
        response = Mock(ok=False)
        self.user.post.return_value = response
        response.json.return_value = {"brand2": True}
        self.assertRaises(EnmApplicationError, self.flow.change_esm_login_password, self.user, "test",
                          "Old_pwd", "new_pwd")
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.raise_for_status")
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_esm_logout__successful(self, mock_debug_log, mock_raise_for_status):
        response = Mock(ok=True)
        self.user.post.return_value = response
        self.flow.esm_logout(self.user, "test")
        self.assertTrue(mock_debug_log.call_count, 2)
        self.assertFalse(mock_raise_for_status.called)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.raise_for_status")
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_esm_logout__raises_status_error(self, mock_debug_log, mock_raise_for_status):
        response = Mock(ok=False)
        self.user.post.return_value = response
        self.flow.esm_logout(self.user, "test")
        self.assertTrue(mock_debug_log.call_count, 1)
        self.assertTrue(mock_raise_for_status.called)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_create_esm_users__successful(self, mock_debug_log):
        response = Mock(ok=True)
        self.user.post.return_value = response
        self.flow.create_esm_users(self.user, [{"username": "test"}], [Mock()])
        self.assertTrue(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_create_esm_users__raises_httperror(self, mock_debug_log):
        response = Mock(ok=False)
        self.user.post.return_value = response
        self.assertRaises(EnvironError, self.flow.create_esm_users, self.user, [{"username": "test"}], [Mock()])
        self.assertTrue(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_login')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_logout')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_workload_admin_user')
    def test_delete_esm_users_cn(self, mock_get_workload_admin_user, mock_debug_log, *_):
        response = Mock(ok=True)
        mock_get_workload_admin_user.return_value = Mock()
        self.user.delete_request.return_value = response
        self.flow.delete_esm_users_cn(["test"])
        self.assertTrue(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_login')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.esm_logout')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_workload_admin_user')
    @patch("enmutils_int.lib.profile_flows.esm_flows.esm_flow.log.logger.debug")
    def test_delete_esm_users_cn__raises_error(self, mock_debug_log, mock_get_workload_admin_user, mock_add_error, *_):
        response = Mock(ok=False)
        mock_get_workload_admin_user.return_value = Mock()
        self.user.delete_request.return_value = response
        self.flow.delete_esm_users_cn(["test"], self.user)
        self.assertTrue(mock_debug_log.call_count, 2)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_hostname_cloud_deployment')
    def test_get_get_esmon_ip_of_cloud_having_sed_id(self, mock_cloud_deployment, mock_sed_id):
        mock_cloud_deployment.return_value = 'dp_hostname', 'deployment_hostname'
        mock_sed_id.return_value = 'sed_id'
        self.flow.get_esmon_ip_of_cloud()

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip_cloud')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_sed_id')
    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.get_hostname_cloud_deployment')
    def test_get_get_esmon_ip_of_cloud_no_sed_id(self, mock_cloud_deployment, mock_sed_id, mock_cloud_name):
        mock_cloud_deployment.return_value = 'dp_hostname', 'deployment_hostname'
        mock_sed_id.return_value = ''
        mock_cloud_name.return_value = 'cloud_name'
        self.flow.get_esmon_ip_of_cloud()

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.add_error_as_exception')
    def test_get_get_esmon_ip_of_cloud_error(self, mock_add_error):
        self.flow.get_esmon_ip_of_cloud()
        self.assertEqual(mock_add_error.call_count, 1)
if __name__ == "__main__":
    unittest2.main(verbosity=2)
