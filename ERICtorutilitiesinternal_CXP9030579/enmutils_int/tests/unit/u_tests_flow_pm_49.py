#!/usr/bin/env python
from datetime import datetime, timedelta
from mock import patch, Mock, call, PropertyMock, mock_open
import unittest2
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.pm_flows.pm_49_flow import Pm49Flow
from enmutils_int.lib.workload.pm_49 import PM_49


class Pm49FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.pm_49_flow = Pm49Flow()
        self.pm_49_flow.USER_ROLES = ["Cmedit_Administrator", "Scripting_Operator"]
        self.pm_49_flow.SCHEDULE_SLEEP = 1
        self.pm_49_flow.DESTINATION_DIRS = ["/tmp/test/", "/tmp/test1/"]
        self.pm_49_flow.CM_BULK_GEN_START_TIME = "03:00:00"
        self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP = unit_test_utils.generate_configurable_ip()
        self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_PASSWORD = "pwd"
        self.pm_49_flow.NUM_USERS = 1
        self.pm_49_flow.user = self.user
        self.pm_49_flow.teardown_list = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_flow')
    def test_run__execute_flow_pm_49_successful(self, mock_flow):
        PM_49().run()
        self.assertTrue(mock_flow.called)

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.set_fntpushebsfiles_pib_active")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time,
                                         mock_disable_end_point, mock_enable_transfer_only, mock_execute_tasks,
                                         mock_get_push_service_ip, *_):
        mock_create_users.return_value = [self.user]
        mock_get_push_service_ip.return_value = "ip"
        self.pm_49_flow.execute_flow()
        mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
        mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                  self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertTrue(mock_disable_random_time.called)
        self.assertTrue(mock_disable_end_point.called)
        self.assertTrue(mock_enable_transfer_only.called)
        self.assertTrue(mock_execute_tasks.called)
        self.assertTrue(mock_get_push_service_ip.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__raises_env_error_if_profile_is_not_running_on_workload_vm(self, mock_create_users,
                                                                                     mock_ftpes_setup_on_vm,
                                                                                     mock_disable_random_time,
                                                                                     mock_disable_end_point,
                                                                                     mock_enable_transfer_only,
                                                                                     mock_execute_tasks,
                                                                                     mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            self.assertFalse(mock_ftpes_setup_on_vm.called)
            self.assertFalse(mock_disable_random_time.called)
            self.assertFalse(mock_disable_end_point.called)
            self.assertFalse(mock_enable_transfer_only.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertFalse(mock_get_push_service_ip.called)
            self.assertTrue(call(EnvironError("Profile is not running on workload vm") in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__raises_env_error_if_push_service_ip_not_found(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.side_effect = EnvironError("Push service is not available in ENM")
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            self.assertFalse(mock_ftpes_setup_on_vm.called)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertFalse(mock_disable_random_time.called)
            self.assertFalse(mock_disable_end_point.called)
            self.assertFalse(mock_enable_transfer_only.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertTrue(call(EnvironError("Push service is not available in ENM") in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__raises_env_error_when_calling_the_disable_random_time(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.side_effect = EnvironError("error")
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertTrue(mock_disable_random_time.called)
            self.assertFalse(mock_disable_end_point.called)
            self.assertFalse(mock_enable_transfer_only.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertTrue(call(EnvironError("error") in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__raises_env_error_when_calling_the_disable_end_time(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.return_value = True
            mock_disable_end_point.side_effect = EnvironError("error")
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertTrue(mock_disable_random_time.called)
            self.assertTrue(mock_disable_end_point.called)
            self.assertFalse(mock_enable_transfer_only.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertTrue(call(EnvironError("error") in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__raises_env_error_when_calling_the_enable_transfer_only(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.return_value = True
            mock_disable_end_point.return_value = True
            mock_enable_transfer_only.side_effect = EnvironError("error")
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertTrue(mock_disable_random_time.called)
            self.assertTrue(mock_disable_end_point.called)
            self.assertTrue(mock_enable_transfer_only.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertTrue(call(EnvironError("error") in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.set_fntpushebsfiles_pib_active")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__if_disable_random_time_returns_false(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.return_value = False
            mock_disable_end_point.return_value = True
            mock_enable_transfer_only.return_value = True
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_disable_random_time.called)
            self.assertTrue(mock_disable_end_point.called)
            self.assertTrue(mock_enable_transfer_only.called)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.set_fntpushebsfiles_pib_active")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__if_disable_end_point_returns_false(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.return_value = True
            mock_disable_end_point.return_value = False
            mock_enable_transfer_only.return_value = True
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_disable_random_time.called)
            self.assertTrue(mock_disable_end_point.called)
            self.assertTrue(mock_enable_transfer_only.called)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.set_fntpushebsfiles_pib_active")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.get_enm_cloud_native_namespace",
           return_value="enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.cache.check_if_on_workload_vm", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_push_service_ip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "enable_transfer_only_not_store_files_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_end_point_checking_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.disable_random_time_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_profile_users")
    def test_execute_flow__if_enable_transfer_only_returns_false(
            self, mock_create_users, mock_ftpes_setup_on_vm, mock_disable_random_time, mock_disable_end_point,
            mock_enable_transfer_only, mock_execute_tasks, mock_get_push_service_ip, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
                   "add_error_as_exception") as mock_add_error:
            mock_create_users.return_value = [self.user]
            mock_get_push_service_ip.return_value = "ip"
            mock_disable_random_time.return_value = True
            mock_disable_end_point.return_value = True
            mock_enable_transfer_only.return_value = False
            self.pm_49_flow.execute_flow()
            mock_create_users.assert_called_with(self.pm_49_flow.NUM_USERS, roles=self.pm_49_flow.USER_ROLES)
            mock_ftpes_setup_on_vm.assert_called_with(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
            self.assertTrue(mock_disable_random_time.called)
            self.assertTrue(mock_disable_end_point.called)
            self.assertTrue(mock_enable_transfer_only.called)
            self.assertTrue(mock_get_push_service_ip.called)
            self.assertFalse(mock_execute_tasks.called)
            self.assertFalse(mock_add_error.called)

    # enable_and_disable_push_file_transfer_service test cases
    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_and_disable_push_service__successful_if_action_is_enable(self, mock_debug_log, *_):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["PushService is Enabled."]
        self.pm_49_flow.enable_and_disable_push_file_transfer_service("enable")
        self.assertEqual(mock_debug_log.call_count, 8)

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_and_disable_push_service__successful_if_action_is_disable(self, mock_debug_log, *_):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["PushService is Disabled."]
        self.pm_49_flow.enable_and_disable_push_file_transfer_service("disable")
        self.assertEqual(mock_debug_log.call_count, 8)

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_and_disable_push_service__raises_enm_application_error(self, mock_debug_log, *_):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["error"]
        self.assertRaises(EnmApplicationError, self.pm_49_flow.enable_and_disable_push_file_transfer_service,
                          "disable")
        self.assertEqual(mock_debug_log.call_count, 4)

    # get_status_of_push_file_transfer_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_get_status_of_push_file_transfer_service__success_if_action_is_enable(self, mock_debug_log):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["PushService is Active"]
        self.pm_49_flow.get_status_of_push_file_transfer_service("enable")
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_get_status_of_push_file_transfer_service__success_if_action_is_disable(self, mock_debug_log):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["PushService is Inactive"]
        self.pm_49_flow.get_status_of_push_file_transfer_service("disable")
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_get_status_of_push_file_transfer_service__raises_enm_application_error(self, mock_debug_log):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["Error"]
        self.assertRaises(EnmApplicationError, self.pm_49_flow.get_status_of_push_file_transfer_service, "enable")
        self.assertEqual(mock_debug_log.call_count, 2)

    # get_push_service_ip test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pod_info_in_cenm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_values_from_global_properties")
    def test_get_push_service_ip__is_successful_if_physical(self, mock_get_values_from_global_properties, _):
        mock_get_values_from_global_properties.return_value = ["ip"]
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("ip", self.pm_49_flow.get_push_service_ip())
        self.assertEqual(1, mock_get_values_from_global_properties.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pod_info_in_cenm")
    def test_get_push_service_ip__is_successful_if_cenm(self, get_pod_info_in_cenm, _):
        get_pod_info_in_cenm.return_value = "pushservice_pod"
        self.pm_49_flow.is_cloud_native = True
        self.assertEqual("pushservice_pod", self.pm_49_flow.get_push_service_ip())
        self.assertEqual(1, get_pod_info_in_cenm.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pod_info_in_cenm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_values_from_global_properties")
    def test_get_push_service_ip__raises_env_error_if_push_service_ip_not_found(self,
                                                                                mock_get_values_from_global_properties,
                                                                                _):
        mock_get_values_from_global_properties.return_value = []
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.get_push_service_ip)
        self.assertEqual(1, mock_get_values_from_global_properties.call_count)

    # get_disable_pushservice_randomtime_configured_value test cases

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_disable_pushservice_randomtime_configured_value__is_successful_if_physical(self,
                                                                                            mock_run_cmd_on_vm,
                                                                                            mock_debug_log,
                                                                                            mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("TRUE", self.pm_49_flow.get_disable_pushservice_randomtime_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_get_disable_pushservice_randomtime_configured_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                                        mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.pm_49_flow.push_service_ip = "pushservice_1"
        self.assertEqual("TRUE", self.pm_49_flow.get_disable_pushservice_randomtime_configured_value())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_disable_pushservice_randomtime_configured_value__if_property_not_found(self, mock_run_cmd_on_vm,
                                                                                        mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0216: Management resource '[(\"system-property\" => "
                                                         "\"DISABLE_PUSHSERVICE_RANDOMTIME\")]' not found",
                                  "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("FALSE", self.pm_49_flow.get_disable_pushservice_randomtime_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_disable_pushservice_randomtime_configured_value__raises_env_error(self, mock_run_cmd_on_vm,
                                                                                   mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.get_disable_pushservice_randomtime_configured_value)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # get_enable_end_point_checking_configured_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_enable_end_point_checking_configured_value__is_successful_if_physical(self, mock_run_cmd_on_vm,
                                                                                       mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("TRUE", self.pm_49_flow.get_enable_end_point_checking_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_get_enable_end_point_checking_configured_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                                   mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual("TRUE", self.pm_49_flow.get_enable_end_point_checking_configured_value())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_enable_end_point_checking_configured_value__if_property_not_found(self, mock_run_cmd_on_vm,
                                                                                   mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0216: Management resource '[(\"system-property\" => "
                                                         "\"ENABLE_END_POINT_CHECKING\")]' not found",
                                  "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("FALSE", self.pm_49_flow.get_enable_end_point_checking_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_enable_end_point_checking_configured_value__raises_env_error(self, mock_run_cmd_on_vm,
                                                                              mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.get_enable_end_point_checking_configured_value)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # get_transfer_only_not_store_files_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_transfer_only_not_store_files_value__is_successful_if_physical(self, mock_run_cmd_on_vm,
                                                                                mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("TRUE", self.pm_49_flow.get_transfer_only_not_store_files_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_get_transfer_only_not_store_files_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                            mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual("TRUE", self.pm_49_flow.get_transfer_only_not_store_files_value())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_transfer_only_not_store_files_value__if_property_not_found(self, mock_run_cmd_on_vm,
                                                                            mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0216: Management resource '[(\"system-property\" => "
                                                         "\"TRANSFER_ONLY_NOT_STORE_FILES\")]' not found",
                                  "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("FALSE", self.pm_49_flow.get_transfer_only_not_store_files_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_transfer_only_not_store_files_value__raises_env_error(self, mock_run_cmd_on_vm,
                                                                       mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.get_transfer_only_not_store_files_value)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # add_disable_pushservice_randomtime_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_disable_pushservice_randomtime_value__is_successful_if_value_is_true(self, mock_run_cmd_on_vm,
                                                                                      mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_disable_pushservice_randomtime_value("TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_add_disable_pushservice_randomtime_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                             mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.pm_49_flow.add_disable_pushservice_randomtime_value("TRUE")
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_disable_pushservice_randomtime_value__is_successful_if_value_is_false(self, mock_run_cmd_on_vm,
                                                                                       mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_disable_pushservice_randomtime_value("FALSE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_disable_pushservice_randomtime_value__raises_env_error(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                        mock_json, *_):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0212: Duplicate resource [(\"system-property\" => "
                                                         "\"DISABLE_PUSHSERVICE_RANDOMTIME\")]", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.add_disable_pushservice_randomtime_value, "TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # add_enable_end_point_checking_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_enable_end_point_checking_value__is_successful_if_value_is_true(self, mock_run_cmd_on_vm,
                                                                                 mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_enable_end_point_checking_value("TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_add_enable_end_point_checking_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                        mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.pm_49_flow.add_enable_end_point_checking_value("TRUE")
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_enable_end_point_checking_value__is_successful_if_value_is_false(self, mock_run_cmd_on_vm,
                                                                                  mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_enable_end_point_checking_value("FALSE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_enable_end_point_checking_value__raises_env_error(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                   mock_json, *_):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0212: Duplicate resource [(\"system-property\" => "
                                                         "\"ENABLE_END_POINT_CHECKING\")]", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.add_enable_end_point_checking_value, "TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # add_transfer_only_not_store_files_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_transfer_only_not_store_files_value__is_successful_if_value_is_true(self, mock_run_cmd_on_vm,
                                                                                     mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_transfer_only_not_store_files_value("TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_add_transfer_only_not_store_files_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                            mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.pm_49_flow.add_transfer_only_not_store_files_value("TRUE")
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_transfer_only_not_store_files_value__is_successful_if_value_is_false(self, mock_run_cmd_on_vm,
                                                                                      mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_transfer_only_not_store_files_value("FALSE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_transfer_only_not_store_files_value__raises_env_error(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                       mock_json, *_):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0212: Duplicate resource [(\"system-property\" => "
                                                         "\"TRANSFER_ONLY_NOT_STORE_FILES\")]", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.add_transfer_only_not_store_files_value, "TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # remove_disable_pushservice_randomtime_property_on_push_service_sg test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_disable_pushservice_randomtime_property_on_push_service_sg__is_successful(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_disable_pushservice_randomtime_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_remove_disable_pushservice_randomtime_property_on_push_service_sg__is_successful_if_cenm(
            self, mock_run_local_cmd, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual(True, self.pm_49_flow.remove_disable_pushservice_randomtime_property_on_push_service_sg())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_disable_pushservice_randomtime_property_on_push_service_sg__if_property_not_found(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed", "failure-description": "WFLYCTL0216: Management resource "
                                                                              "'[(\"system-property\" => "
                                                                              "\"DISABLE_PUSHSERVICE_RANDOMTIME\")]' "
                                                                              "not found", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_disable_pushservice_randomtime_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_disable_pushservice_randomtime_property_on_push_service_sg__raises_env_error(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError,
                          self.pm_49_flow.remove_disable_pushservice_randomtime_property_on_push_service_sg)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # remove_enable_end_point_checking_property_on_push_service_sg test case
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_enable_end_point_checking_property_on_push_service_sg__is_successful(self, mock_run_cmd_on_vm,
                                                                                         mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_enable_end_point_checking_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_remove_enable_end_point_checking_property_on_push_service_sg__if_cenm(self, mock_run_local_cmd,
                                                                                   mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual(True, self.pm_49_flow.remove_enable_end_point_checking_property_on_push_service_sg())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_enable_end_point_checking_property_on_push_service_sg__if_property_not_found(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed", "failure-description": "WFLYCTL0216: Management resource "
                                                                              "'[(\"system-property\" => "
                                                                              "\"ENABLE_END_POINT_CHECKING\")]' "
                                                                              "not found", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_enable_end_point_checking_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_enable_end_point_checking_property_on_push_service_sg__raises_env_error(self, mock_run_cmd_on_vm,
                                                                                            mock_debug_log,
                                                                                            mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError,
                          self.pm_49_flow.remove_enable_end_point_checking_property_on_push_service_sg)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # remove_transfer_only_not_store_files_property_on_push_service_sg test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_transfer_only_not_store_files_property_on_push_service_sg__is_successful(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_transfer_only_not_store_files_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_remove_transfer_only_not_store_files_property_on_push_service_sg__if_cenm(
            self, mock_run_local_cmd, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual(True, self.pm_49_flow.remove_transfer_only_not_store_files_property_on_push_service_sg())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_transfer_only_not_store_files_property_on_push_service_sg__if_property_not_found(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed", "failure-description": "WFLYCTL0216: Management resource "
                                                                              "'[(\"system-property\" => "
                                                                              "\"TRANSFER_ONLY_NOT_STORE_FILES\")]' "
                                                                              "not found", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_transfer_only_not_store_files_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_transfer_only_not_store_files_property_on_push_service_sg__raises_env_error(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError,
                          self.pm_49_flow.remove_transfer_only_not_store_files_property_on_push_service_sg)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # set_fntpushebsfiles_pib_active test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.update_pib_parameter_on_enm")
    def test_set_fntpushebsfiles_pib_active_true(self, mock_update_pib_parameter, mock_get_pib_value, mock_logger_debug):
        mock_get_pib_value.return_value = "EBSN_DU,EBSN_CUUP,EBSN_CUCP"

        self.pm_49_flow.set_fntpushebsfiles_pib_active()
        self.assertEqual(mock_logger_debug.call_count, 1)
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_update_pib_parameter.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.update_pib_parameter_on_enm")
    def test_set_fntpushebsfiles_pib_active_false(self, mock_update_pib_parameter, mock_get_pib_value, mock_logger_debug):
        mock_get_pib_value.return_value = "EBSN_CUUP,EBSN_CUCP"
        self.pm_49_flow.set_fntpushebsfiles_pib_active()
        self.assertEqual(mock_logger_debug.call_count, 3)
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_update_pib_parameter.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.update_pib_parameter_on_enm")
    def test_set_fntpushebsfiles_pib_active_raises_error(self, mock_update_pib_parameter, mock_get_pib_value,
                                                         mock_logger_debug):
        mock_get_pib_value.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.set_fntpushebsfiles_pib_active)
        self.assertEqual(mock_logger_debug.call_count, 1)
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_update_pib_parameter.call_count, 0)

    # disable_random_time_on_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__is_successful(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "FALSE"
        mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.return_value = True
        mock_add_disable_pushservice_randomtime_value.return_value = True
        self.assertEqual(True, self.pm_49_flow.disable_random_time_on_push_service())
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(1, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__if_disable_pushservice_randomtime_value_is_true(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "TRUE"
        self.assertEqual(True, self.pm_49_flow.disable_random_time_on_push_service())
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(0, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__raises_env_error_when_remove_the_property(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "FALSE"
        mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.disable_random_time_on_push_service)
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(1, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__if_remove_disable_pushservice_randomtime_property_returns_false(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "FALSE"
        mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.return_value = False
        self.pm_49_flow.disable_random_time_on_push_service()
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(1, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__if_add_disable_pushservice_randomtime_value_returns_false(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "FALSE"
        mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.return_value = True
        mock_add_disable_pushservice_randomtime_value.return_value = False
        self.pm_49_flow.disable_random_time_on_push_service()
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(1, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_disable_pushservice_randomtime_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_disable_pushservice_randomtime_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_random_time_on_push_service__raises_env_error_when_add_disable_pushservice_randomtime_value(
            self, mock_debug_log, mock_get_disable_pushservice_randomtime_configured_value,
            mock_remove_disable_pushservice_randomtime_property_on_push_service_sg,
            mock_add_disable_pushservice_randomtime_value):
        mock_get_disable_pushservice_randomtime_configured_value.return_value = "FALSE"
        mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.return_value = True
        mock_add_disable_pushservice_randomtime_value.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.disable_random_time_on_push_service)
        self.assertEqual(1, mock_get_disable_pushservice_randomtime_configured_value.call_count)
        self.assertEqual(1, mock_remove_disable_pushservice_randomtime_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_disable_pushservice_randomtime_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    # disable_end_point_checking_on_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__is_successful(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "FALSE"
        mock_remove_enable_end_point_checking_property_on_push_service_sg.return_value = True
        mock_add_enable_end_point_checking_value.return_value = True
        self.assertEqual(True, self.pm_49_flow.disable_end_point_checking_on_push_service())
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(1, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__if_disable_pushservice_randomtime_value_is_true(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "TRUE"
        self.assertEqual(True, self.pm_49_flow.disable_end_point_checking_on_push_service())
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(0, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__raises_env_error_when_remove_the_property(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "FALSE"
        mock_remove_enable_end_point_checking_property_on_push_service_sg.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.disable_end_point_checking_on_push_service)
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(1, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__if_remove_disable_pushservice_randomtime_property_returns_false(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "FALSE"
        mock_remove_enable_end_point_checking_property_on_push_service_sg.return_value = False
        self.pm_49_flow.disable_end_point_checking_on_push_service()
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(1, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__if_add_disable_pushservice_randomtime_value_returns_false(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "FALSE"
        mock_remove_enable_end_point_checking_property_on_push_service_sg.return_value = True
        mock_add_enable_end_point_checking_value.return_value = False
        self.pm_49_flow.disable_end_point_checking_on_push_service()
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(1, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_enable_end_point_checking_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "get_enable_end_point_checking_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_disable_end_point_checking_on_push_service__raises_env_error_when_add_disable_pushservice_randomtime_value(
            self, mock_debug_log, mock_get_enable_end_point_checking_configured_value,
            mock_remove_enable_end_point_checking_property_on_push_service_sg,
            mock_add_enable_end_point_checking_value):
        mock_get_enable_end_point_checking_configured_value.return_value = "FALSE"
        mock_remove_enable_end_point_checking_property_on_push_service_sg.return_value = True
        mock_add_enable_end_point_checking_value.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.disable_end_point_checking_on_push_service)
        self.assertEqual(1, mock_get_enable_end_point_checking_configured_value.call_count)
        self.assertEqual(1, mock_remove_enable_end_point_checking_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_enable_end_point_checking_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    # enable_transfer_only_not_store_files_on_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__is_successful(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "FALSE"
        mock_remove_transfer_only_not_store_files_property_on_push_service_sg.return_value = True
        mock_add_transfer_only_not_store_files_value.return_value = True
        self.assertEqual(True, self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service())
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__if_transfer_only_not_store_files_value_is_true(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "TRUE"
        self.assertEqual(True, self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service())
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(0, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__raises_env_error_when_remove_the_property(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "FALSE"
        mock_remove_transfer_only_not_store_files_property_on_push_service_sg.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service)
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__if_remove_transfer_only_not_store_files_property_on_push_service_sg_returns_false(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "FALSE"
        mock_remove_transfer_only_not_store_files_property_on_push_service_sg.return_value = False
        self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service()
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__if_add_transfer_only_not_store_files_value_returns_false(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "FALSE"
        mock_remove_transfer_only_not_store_files_property_on_push_service_sg.return_value = True
        mock_add_transfer_only_not_store_files_value.return_value = False
        self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service()
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_transfer_only_not_store_files_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_transfer_only_not_store_files_on_push_service__raises_env_error_when_add_transfer_only_not_store_files_value(
            self, mock_debug_log, mock_get_transfer_only_not_store_files_value,
            mock_remove_transfer_only_not_store_files_property_on_push_service_sg,
            mock_add_transfer_only_not_store_files_value):
        mock_get_transfer_only_not_store_files_value.return_value = "FALSE"
        mock_remove_transfer_only_not_store_files_property_on_push_service_sg.return_value = True
        mock_add_transfer_only_not_store_files_value.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.enable_transfer_only_not_store_files_on_push_service)
        self.assertEqual(1, mock_get_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_remove_transfer_only_not_store_files_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_transfer_only_not_store_files_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    # ftpes_setup_on_vm test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.post_private_key_to_vault_on_pushservice_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.intial_setup_of_ftpes_on_pushservice_terminate_vm")
    def test_ftpes_setup_on_vm__respective_methods_called_and_certificates_imported_success(self,
                                                                                            mock_intial_setup_of_ftpes,
                                                                                            mock_post_private_key, *_):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = [u'', u'PushService certificate is Imported.']
        self.pm_49_flow.ftpes_setup_on_vm(self.pm_49_flow.user, self.pm_49_flow.push_service_ip,
                                          self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_intial_setup_of_ftpes.assert_called_with(self.pm_49_flow.user,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_post_private_key.assert_called_with(self.pm_49_flow.push_service_ip)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.post_private_key_to_vault_on_pushservice_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "intial_setup_of_ftpes_on_pushservice_terminate_vm")
    def test_ftpes_setup_on_vm__respective_methods_called_and_raise_env_err_if_importing_certificates_failed(
            self, mock_intial_setup_of_ftpes, mock_post_private_key, *_):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = [u'', u'PushService certificate is Failed.']
        self.assertRaises(EnvironError, self.pm_49_flow.ftpes_setup_on_vm, self.pm_49_flow.user,
                          self.pm_49_flow.push_service_ip, self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_intial_setup_of_ftpes.assert_called_with(self.pm_49_flow.user,
                                                      self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_post_private_key.assert_called_with(self.pm_49_flow.push_service_ip)

    # intial_setup_of_ftpes_on_pushservice_terminate_vm test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.copy_certificates_to_pushservice_terminate_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_intial_setup_of_ftpes_on_pushservice_terminate_vm__is_successful(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                              mock_copy_certificates):
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout='vsftpd is installed')
        self.pm_49_flow.intial_setup_of_ftpes_on_pushservice_terminate_vm(self.pm_49_flow.user,
                                                                          self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_copy_certificates.assert_called_with(self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertEqual(6, mock_run_cmd_on_vm.call_count)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.copy_certificates_to_pushservice_terminate_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_intial_setup_of_ftpes_on_pushservice_terminate_vm__if_vsftpd_is_not_installed(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_copy_certificates):
        mock_run_cmd_on_vm.side_effect = [Mock(rc=1, stdout=False)] + 6 * [Mock(rc=0, stdout=False)]
        self.pm_49_flow.intial_setup_of_ftpes_on_pushservice_terminate_vm(self.pm_49_flow.user,
                                                                          self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_copy_certificates.assert_called_with(self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertEqual(7, mock_run_cmd_on_vm.call_count)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.copy_certificates_to_pushservice_terminate_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_intial_setup_of_ftpes_on_pushservice_terminate_vm__raises_env(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                           mock_copy_certificates):
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout='vsftpd is installed')
        self.assertRaises(EnvironError, self.pm_49_flow.intial_setup_of_ftpes_on_pushservice_terminate_vm,
                          self.pm_49_flow.user, self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        mock_copy_certificates.assert_called_with(self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertEqual(6, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    # get_vault_token_from_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_vault_token_from_push_service__if_physical(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=True, stdout='abdj34jsjsjt')
        self.pm_49_flow.get_vault_token_from_push_service()
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_get_vault_token_from_push_service__if_cenm(self, mock_run_local_cmd, *_):
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        mock_run_local_cmd.return_value = Mock(ok=True, stdout='abdj34jsjsjt')
        self.pm_49_flow.get_vault_token_from_push_service()
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_vault_token_from_push_service__raies_env_error(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=False, stdout='Error')
        self.assertRaises(EnvironError, self.pm_49_flow.get_vault_token_from_push_service)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    # create_pushservice_privateKey_file_on_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_internal_file_path_for_import")
    @patch('__builtin__.open', new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_create_pushservice_privateKey_file_on_push_service__if_physical(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=True, stdout='abdj34jsjsjt')
        self.pm_49_flow.create_pushservice_privateKey_file_on_push_service()
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_internal_file_path_for_import")
    @patch('__builtin__.open', new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_create_pushservice_privateKey_file_on_push_service__if_cenm(self, mock_run_local_cmd, *_):
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        mock_run_local_cmd.return_value = Mock(ok=True, stdout='some text')
        self.pm_49_flow.create_pushservice_privateKey_file_on_push_service()
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.get_internal_file_path_for_import")
    @patch('__builtin__.open', new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_create_pushservice_privateKey_file_on_push_service__raises_env_error(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=False, stdout='error')
        self.assertRaises(EnvironError, self.pm_49_flow.create_pushservice_privateKey_file_on_push_service)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    # post_private_key_to_vault_on_pushservice test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_post_private_key_to_vault_on_pushservice__if_physical(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=True, stdout='some text')
        self.pm_49_flow.post_private_key_to_vault_on_pushservice(Mock(stdout="test"))
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_post_private_key_to_vault_on_pushservice__if_cenm(self, mock_run_local_cmd, *_):
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        mock_run_local_cmd.return_value = Mock(ok=True, stdout='some text')
        self.pm_49_flow.post_private_key_to_vault_on_pushservice(Mock(stdout="test"))
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_post_private_key_to_vault_on_pushservice__raies_env_error(self, mock_run_cmd_on_vm, *_):
        self.pm_49_flow.is_cloud_native = False
        mock_run_cmd_on_vm.return_value = Mock(ok=False, stdout='Error')
        self.assertRaises(EnvironError, self.pm_49_flow.post_private_key_to_vault_on_pushservice,
                          Mock(stdout="test"))
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    # post_private_key_to_vault_on_pushservice_sg test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_vault_token_from_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_pushservice_privateKey_file_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.post_private_key_to_vault_on_pushservice")
    def test_post_private_key_to_vault_on_pushservice_sg__is_successful(
            self, mock_post_private_key_to_vault, mock_create_pushservice_privatekey_file,
            mock_get_vault_token_from_push_service, mock_debug_log):
        mock_post_private_key_to_vault.return_value = Mock(rc=0, stdout='test')
        mock_create_pushservice_privatekey_file.return_value = Mock(rc=0, stdout='test')
        mock_get_vault_token_from_push_service.return_value = Mock(rc=0, stdout='s.5lgxzcUl8Y13BvnwK4P2cs7I')
        self.pm_49_flow.post_private_key_to_vault_on_pushservice_sg(self.pm_49_flow.push_service_ip)
        self.assertEqual(1, mock_post_private_key_to_vault.call_count)
        self.assertEqual(1, mock_create_pushservice_privatekey_file.call_count)
        self.assertEqual(1, mock_get_vault_token_from_push_service.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_vault_token_from_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.create_pushservice_privateKey_file_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.post_private_key_to_vault_on_pushservice")
    def test_post_private_key_to_vault_on_pushservice_sg__raises_env_error(
            self, mock_post_private_key_to_vault, mock_create_pushservice_privatekey_file,
            mock_get_vault_token_from_push_service, mock_debug_log):
        mock_post_private_key_to_vault.return_value = Mock(rc=1, stdout='test')
        mock_create_pushservice_privatekey_file.return_value = Mock(rc=1, stdout='test')
        mock_get_vault_token_from_push_service.return_value = Mock(rc=1, stdout='s.5lgxzcUl8Y13BvnwK4P2cs7I')
        self.assertRaises(EnvironError, self.pm_49_flow.post_private_key_to_vault_on_pushservice_sg,
                          self.pm_49_flow.push_service_ip)
        self.assertEqual(1, mock_post_private_key_to_vault.call_count)
        self.assertEqual(1, mock_create_pushservice_privatekey_file.call_count)
        self.assertEqual(1, mock_get_vault_token_from_push_service.call_count)
        self.assertEqual(0, mock_debug_log.call_count)

    # copy_certificates_to_pushservice_terminate_vm test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.pexpect.spawn")
    def test_copy_certificates_to_pushservice_terminate_vm__raises_env_error(self, mock_pexpect_spawn, mock_log, *_):
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.return_value = 1
        self.assertRaises(EnvironError, self.pm_49_flow.copy_certificates_to_pushservice_terminate_vm,
                          self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertEqual(25, mock_log.call_count)
        self.assertEqual(0, mock_pexpect_spawn.sendline.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.pexpect.spawn")
    def test_copy_certificates_to_pushservice_terminate_vm__is_successful(self, mock_pexpect_spawn, mock_log, *_):
        mock_pexpect_spawn.return_value = Mock()
        mock_pexpect_spawn.return_value.expect.return_value = 0
        self.pm_49_flow.copy_certificates_to_pushservice_terminate_vm(self.pm_49_flow.PUSH_SERVICE_TERMINATE_VM_IP)
        self.assertEqual(26, mock_log.call_count)

    # ftpes_setup_on_vm_teardown test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_ftpes_setup_on_vm_teardown__is_successful(self, mock_run_cmd_on_vm, *_):
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout='')
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = [u'', u'PushService certificate is Deleted.']
        self.pm_49_flow.ftpes_setup_on_vm_teardown()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_ftpes_setup_on_vm_teardown__raises_env_error(self, mock_run_cmd_on_vm, *_):
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout='userdel: user PM_49_0202-09320993_u0 is currently '
                                                            'used by process 31048 sed:')
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = [u'', u'PushService certificate is Deleted.']
        self.assertRaises(EnvironError, self.pm_49_flow.ftpes_setup_on_vm_teardown)

    # execute_tasks test cases
    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_status_of_push_file_transfer",
           return_value="PushService is Inactive. Product Data: Disabled")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_and_disable_push_file_transfer_service")
    def test_execute_tasks__is_successful(self, mock_enable_and_disable_push_file_transfer_service, *_):
        self.pm_49_flow.execute_tasks()
        mock_enable_and_disable_push_file_transfer_service.assert_called_with("enable")
        self.assertEqual(7, len(self.pm_49_flow.teardown_list))

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_status_of_push_file_transfer",
           return_value="PushService is Inactive. Product Data: Disabling")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_and_disable_push_file_transfer_service")
    def test_execute_tasks__when_product_data_is_in_disabling_state(self,
                                                                    mock_enable_and_disable_push_file_transfer_service,
                                                                    mock_wait_product_data_to_enable_disable_state, *_):
        self.pm_49_flow.execute_tasks()
        mock_enable_and_disable_push_file_transfer_service.assert_called_with("enable")
        self.assertEqual(7, len(self.pm_49_flow.teardown_list))
        self.assertEqual(1, mock_wait_product_data_to_enable_disable_state.call_count)

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_status_of_push_file_transfer",
           return_value="PushService is Active. Product Data: Enabled")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_and_disable_push_file_transfer_service")
    def test_execute_tasks__when_product_data_is_in_enabled_state(self,
                                                                  mock_enable_and_disable_push_file_transfer_service,
                                                                  mock_wait_product_data_to_enable_disable_state, *_):
        self.pm_49_flow.execute_tasks()
        self.assertEqual(0, mock_enable_and_disable_push_file_transfer_service.call_count)
        self.assertEqual(7, len(self.pm_49_flow.teardown_list))
        self.assertEqual(0, mock_wait_product_data_to_enable_disable_state.call_count)

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_status_of_push_file_transfer",
           side_effect=EnmApplicationError("error"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_and_disable_push_file_transfer_service")
    def test_execute_tasks__raises_enm_application_error(self, mock_enable_and_disable_push_file_transfer_service, *_):
        self.assertRaises(EnmApplicationError, self.pm_49_flow.execute_tasks)
        self.assertEqual(0, mock_enable_and_disable_push_file_transfer_service.call_count)
        self.assertEqual(7, len(self.pm_49_flow.teardown_list))

    @patch(
        "enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_use_dummy_ccpdservice_mo_on_push_service")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "wait_product_data_to_enable_disable_state")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_status_of_push_file_transfer",
           return_value="")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.ftpes_setup_on_vm_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_disable_pushservice_randomtime_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_enable_end_point_checking_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_transfer_only_not_store_files_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.enable_and_disable_push_file_transfer_service")
    def test_execute_tasks__when_pd_status_is_empty(self, mock_enable_and_disable_push_file_transfer_service, *_):
        self.pm_49_flow.execute_tasks()
        self.assertEqual(0, mock_enable_and_disable_push_file_transfer_service.call_count)
        self.assertEqual(7, len(self.pm_49_flow.teardown_list))

    # get_use_dummy_ccpdservice_mo_configured_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_use_dummy_ccpdservice_mo_configured_value__is_successful_if_physical(self, mock_run_cmd_on_vm,
                                                                                      mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("TRUE", self.pm_49_flow.get_use_dummy_ccpdservice_mo_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_get_use_dummy_ccpdservice_mo_configured_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                                  mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success", "result": {"value": "TRUE"}}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual("TRUE", self.pm_49_flow.get_use_dummy_ccpdservice_mo_configured_value())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(4, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_use_dummy_ccpdservice_mo_configured_value__if_property_not_found(self, mock_run_cmd_on_vm,
                                                                                  mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0216: Management resource '[(\"system-property\" => "
                                                         "\"USE_DUMMY_CCPDSERVICE_MO\")]' not found",
                                  "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual("FALSE", self.pm_49_flow.get_use_dummy_ccpdservice_mo_configured_value())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_get_use_dummy_ccpdservice_mo_configured_value__raises_env_error(self, mock_run_cmd_on_vm,
                                                                             mock_debug_log, mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError, self.pm_49_flow.get_use_dummy_ccpdservice_mo_configured_value)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # add_use_dummy_ccpdservice_mo_value test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_use_dummy_ccpdservice_mo_value__is_successful_if_value_is_true(self, mock_run_cmd_on_vm,
                                                                                mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_use_dummy_ccpdservice_mo_value("TRUE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_add_use_dummy_ccpdservice_mo_value__is_successful_if_cenm(self, mock_run_local_cmd,
                                                                       mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.pm_49_flow.add_use_dummy_ccpdservice_mo_value("TRUE")
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_use_dummy_ccpdservice_mo_value__is_successful_if_value_is_false(self, mock_run_cmd_on_vm,
                                                                                 mock_debug_log, mock_json, *_):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.pm_49_flow.add_use_dummy_ccpdservice_mo_value("FALSE")
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_add_use_dummy_ccpdservice_mo_value__raises_env_error(self, mock_run_cmd_on_vm, mock_debug_log,
                                                                  mock_json, *_):
        mock_json.return_value = {"outcome": "failed",
                                  "failure-description": "WFLYCTL0212: Duplicate resource [(\"system-property\" => "
                                                         "\"USE_DUMMY_CCPDSERVICE_MO\")]", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.assertRaises(EnvironError, self.pm_49_flow.add_use_dummy_ccpdservice_mo_value, "TRUE")
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # remove_use_dummy_ccpdservice_mo_property_on_push_service_sg test case
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg__is_successful(self, mock_run_cmd_on_vm,
                                                                                        mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    def test_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg__if_cenm(self, mock_run_local_cmd,
                                                                                  mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "success"}
        mock_run_local_cmd.return_value = Mock(rc=0, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = True
        self.pm_49_flow.cenm_namespace = "enm"
        self.assertEqual(True, self.pm_49_flow.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg())
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg__if_property_not_found(
            self, mock_run_cmd_on_vm, mock_debug_log, mock_json, _):
        mock_json.return_value = {"outcome": "failed", "failure-description": "WFLYCTL0216: Management resource "
                                                                              "'[(\"system-property\" => "
                                                                              "\"USE_DUMMY_CCPDSERVICE_MO\")]' "
                                                                              "not found", "rolled-back": "true"}
        mock_run_cmd_on_vm.return_value = Mock(rc=1, stdout=str(mock_json.return_value))
        self.pm_49_flow.is_cloud_native = False
        self.assertEqual(True, self.pm_49_flow.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_json.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.shell.run_cmd_on_vm")
    def test_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg__raises_env_error(self, mock_run_cmd_on_vm,
                                                                                           mock_debug_log,
                                                                                           mock_json, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=2, stdout="something is wrong")
        self.pm_49_flow.is_cloud_native = False
        self.assertRaises(EnvironError,
                          self.pm_49_flow.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_json.call_count)

    # enable_use_dummy_ccpdservice_mo_on_push_service test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service__is_successful(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "FALSE"
        mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.return_value = True
        mock_add_use_dummy_ccpdservice_mo_value.return_value = True
        self.assertEqual(True, self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service())
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(1, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service__if_use_dummy_ccpdservice_mo_value_is_true(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "TRUE"
        self.assertEqual(True, self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service())
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(0, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service__raises_env_error_when_remove_the_property(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "FALSE"
        mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service)
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(1, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service__if_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg_returns_false(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "FALSE"
        mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.return_value = False
        self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service()
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(1, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(0, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service__if_add_use_dummy_ccpdservice_mo_value_returns_false(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "FALSE"
        mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.return_value = True
        mock_add_use_dummy_ccpdservice_mo_value.return_value = False
        self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service()
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(1, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.add_use_dummy_ccpdservice_mo_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow."
           "remove_use_dummy_ccpdservice_mo_property_on_push_service_sg")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.Pm49Flow.get_use_dummy_ccpdservice_mo_configured_value")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_enable_use_dummy_ccpdservice_mo_on_push_service_on_push_service__raises_env_error_when_add_use_dummy_ccpdservice_mo_value(
            self, mock_debug_log, mock_get_use_dummy_ccpdservice_mo_configured_value,
            mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg,
            mock_add_use_dummy_ccpdservice_mo_value):
        mock_get_use_dummy_ccpdservice_mo_configured_value.return_value = "FALSE"
        mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.return_value = True
        mock_add_use_dummy_ccpdservice_mo_value.side_effect = EnvironError("error")
        self.assertRaises(EnvironError, self.pm_49_flow.enable_use_dummy_ccpdservice_mo_on_push_service)
        self.assertEqual(1, mock_get_use_dummy_ccpdservice_mo_configured_value.call_count)
        self.assertEqual(1, mock_remove_use_dummy_ccpdservice_mo_property_on_push_service_sg.call_count)
        self.assertEqual(1, mock_add_use_dummy_ccpdservice_mo_value.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    # wait_product_data_to_enable_disable_state test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.datetime")
    def test_wait_product_data_to_enable_disable_state__if_action_is_enabled(self, mock_datetime, mock_timedelta,
                                                                             mock_debug_log, *_):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=40)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        response = Mock()
        response.get_output.return_value = ("PushService is Active. ipaddress - 1.1.1.1 username - "
                                            "PM_49_1017-12251461_u0 cmbulkgenstarttime - 09:00:00\n"
                                            "Product Data: Enabled")
        self.user.enm_execute.return_value = response
        self.pm_49_flow.wait_product_data_to_enable_disable_state("Enabled")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.datetime")
    def test_wait_product_data_to_enable_disable_state__raises_env_error(self, mock_datetime, mock_timedelta,
                                                                         mock_debug_log, *_):

        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=40)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = expiry_time - time_now
        response = Mock()
        response.get_output.return_value = ("PushService is Active. ipaddress - 1.1.1.1 username - "
                                            "PM_49_1017-12251461_u0 cmbulkgenstarttime - 09:00:00\n"
                                            "Product Data: Enabling")
        self.user.enm_execute.return_value = response
        self.assertRaises(EnvironError, self.pm_49_flow.wait_product_data_to_enable_disable_state, "Enabled")
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.datetime.datetime")
    def test_wait_product_data_to_enable_disable_state__if_action_is_disabled(self, mock_datetime, mock_timedelta,
                                                                              mock_debug_log, *_):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=40)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        response = Mock()
        response.get_output.return_value = ("PushService is Inactive. ipaddress - 1.1.1.1 username - "
                                            "PM_49_1017-12251461_u0 cmbulkgenstarttime - 09:00:00\n"
                                            "Product Data: Disabled")
        self.user.enm_execute.return_value = response
        self.pm_49_flow.wait_product_data_to_enable_disable_state("Disabled")
        self.assertEqual(mock_debug_log.call_count, 6)

    # get_status_of_push_file_transfer test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_get_status_of_push_file_transfer__is_successful(self, mock_debug_log):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = "PushService is Active. Product Data: Enabled"
        self.assertRaises(self.pm_49_flow.get_status_of_push_file_transfer())
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_49_flow.log.logger.debug")
    def test_get_status_of_push_file_transfer__raises_enm_application_error(self, mock_debug_log):
        response = self.pm_49_flow.user.enm_execute.return_value
        response.get_output.return_value = ["Error"]
        self.assertRaises(EnmApplicationError, self.pm_49_flow.get_status_of_push_file_transfer)
        self.assertEqual(mock_debug_log.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
