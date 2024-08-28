#!/usr/bin/env python
import pexpect
import unittest2
from mock import patch, Mock

from enmutils.lib.exceptions import EnvironError, ShellCommandReturnedNonZero, EnmApplicationError
from enmutils_int.lib.fm_nbi import FmNbi, IPv4, IPv6
from testslib import unit_test_utils


class FmNbiUnitTests(unittest2.TestCase):
    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

        self.fm_nbi = FmNbi(user=self.user, timeout=2, ip=IPv4, ports=10, snmp_subs_count=5)
        self.fm_nbi.NBI_filters = ["LTE0", "LTE1", "LTE2", "LTE3", "LTE4", "LTE5", "LTE6"]
        self.fm_nbi.WORKLOAD_VM_IP = unit_test_utils.generate_configurable_ip()
        self.fm_nbi.NBALARMIRP = ['svc-1-nbalarmirp', 'svc-2-nbalarmirp']
        self.fm_nbi.VISINAMINGPUB_IP = [unit_test_utils.generate_configurable_ip()]
        self.fm_nbi.IP = IPv4
        self.fm_nbi.PHYSICAL = self.fm_nbi.CLOUD = self.fm_nbi.CLOUD_NATIVE = False
        self.error_response = [Exception("Some Exception")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.fm_nbi.is_host_physical_deployment")
    def test_check_deployment_type__physical(self, mock_physical):
        mock_physical.return_value = True
        self.fm_nbi.check_deployment_type()
        self.assertEqual(self.fm_nbi.PHYSICAL, True)

    @patch("enmutils_int.lib.fm_nbi.is_emp")
    @patch("enmutils_int.lib.fm_nbi.is_host_physical_deployment")
    def test_check_deployment_type__cloud(self, mock_physical, mock_cloud):
        mock_physical.return_value = False
        mock_cloud.return_value = True
        self.fm_nbi.check_deployment_type()
        self.assertEqual(self.fm_nbi.CLOUD, True)

    @patch("enmutils_int.lib.fm_nbi.is_emp")
    @patch("enmutils_int.lib.fm_nbi.is_host_physical_deployment")
    def test_check_deployment_type__cloud_native(self, mock_physical, mock_cloud):
        mock_physical.return_value = False
        mock_cloud.return_value = False
        self.fm_nbi.check_deployment_type()
        self.assertEqual(self.fm_nbi.CLOUD_NATIVE, True)

    def test_is_ipv4(self):
        self.assertEqual(self.fm_nbi._is_ipv4, True)

    def test_is_ipv6(self):
        self.assertEqual(self.fm_nbi._is_ipv6, False)

    def test_reset_ports_is_successful(self):
        self.fm_nbi.reset_ports()
        self.assertEqual(self.fm_nbi.number_ports_used, 0)

    def test_reset_num_filters_is_successful(self):
        self.fm_nbi.reset_num_filters()
        self.assertEqual(self.fm_nbi.NUMBER_FILTERS_USED, 0)

    def test_is_nbi_framework_ok(self):
        self.fm_nbi.WORKLOAD_VM_IP = '11.11.11.11'
        self.fm_nbi.NBALARMIRP = ['10.10.10.10', '11.11.11.11']
        self.fm_nbi.VISINAMINGPUB_IP = ['12.12.12.12']
        self.assertTrue(self.fm_nbi.is_nbi_framework_ok)

    def test_is_nbi_framework_not_ok(self):
        self.fm_nbi.WORKLOAD_VM_IP = ''
        self.fm_nbi.NBALARMIRP = ['10.10.10.10', '11.11.11.11']
        self.fm_nbi.VISINAMINGPUB_IP = ['12.12.12.12']
        self.assertFalse(self.fm_nbi.is_nbi_framework_ok)

        self.fm_nbi.WORKLOAD_VM_IP = '11.11.11.11'
        self.fm_nbi.NBALARMIRP = []
        self.fm_nbi.VISINAMINGPUB_IP = ['12.12.12.12']
        self.assertFalse(self.fm_nbi.is_nbi_framework_ok)

        self.fm_nbi.WORKLOAD_VM_IP = '11.11.11.11'
        self.fm_nbi.NBALARMIRP = ['10.10.10.10', '11.11.11.11']
        self.fm_nbi.VISINAMINGPUB_IP = ''
        self.assertFalse(self.fm_nbi.is_nbi_framework_ok)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_create_nbi_framework_not_ipv4(self, mock_debug, *_):
        self.fm_nbi.IP = IPv6
        self.fm_nbi.create_nbi_framework()
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_create_nbi_framework_raise_exception_1(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.side_effect = Exception
        self.assertRaises(EnvironError, self.fm_nbi.create_nbi_framework)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.FmNbi._get_ip_of_service")
    def test_create_nbi_framework_raise_EnmApplicationError(self, mock_get_ip_of_service, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 0
        response.stdout = unit_test_utils.generate_configurable_ip()
        mock_run_local_cmd.return_value = response
        mock_get_ip_of_service.return_value = unit_test_utils.generate_configurable_ip()
        mock_get_ip_of_service.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.fm_nbi.create_nbi_framework)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.FmNbi._get_ip_of_service")
    def test_create_nbi_framework_raise_EnvironError(self, mock_get_ip_of_service, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 0
        response.stdout = unit_test_utils.generate_configurable_ip()
        mock_run_local_cmd.return_value = response
        mock_get_ip_of_service.side_effect = [[], []]
        self.assertRaises(EnvironError, self.fm_nbi.create_nbi_framework)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.FmNbi._get_ip_of_service")
    def test_create_nbi_framework_raise_EnmApplicationError_on_cloud(self, mock_get_ip_of_service, *_):
        self.fm_nbi.CLOUD = True
        mock_get_ip_of_service.return_value = unit_test_utils.generate_configurable_ip()
        mock_get_ip_of_service.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.fm_nbi.create_nbi_framework)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.FmNbi._get_ip_of_service")
    def test_create_nbi_framework_raise_second_EnmApplicationError(self, mock_get_ip_of_service, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 0
        response.stdout = unit_test_utils.generate_configurable_ip()
        mock_run_local_cmd.return_value = response
        new_arg_list = [['svc-1-nbalarmirp', 'svc-2-nbalarmirp'], [unit_test_utils.generate_configurable_ip()],
                        [Exception]]
        mock_get_ip_of_service.side_effect = new_arg_list[0], new_arg_list[1], new_arg_list[2]
        self.fm_nbi.create_nbi_framework()
        self.assertEqual(self.fm_nbi.NBALARMIRP, ['svc-1-nbalarmirp', 'svc-2-nbalarmirp'])
        self.assertRaises(EnmApplicationError, self.fm_nbi.create_nbi_framework)

    @patch('enmutils_int.lib.fm_nbi.get_pod_hostnames_in_cloud_native')
    def test_visinaming_pub_ipv4__for_cloud_native(self, mock_get_pod_hostnames_in_cloud_native):
        self.fm_nbi.CLOUD_NATIVE = True
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_get_pod_hostnames_in_cloud_native.return_value = [ip_addr]
        self.assertTrue(ip_addr in self.fm_nbi._get_ip_of_service('visinamingnb'))

    @patch('enmutils_int.lib.fm_nbi.get_cloud_members_ip_address')
    def test_visinaming_pub_ipv4_for_cloud(self, mock_get_cloud_members_ip_address):
        self.fm_nbi.CLOUD = True
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_get_cloud_members_ip_address.return_value = [ip_addr]
        self.assertTrue(ip_addr in self.fm_nbi._get_ip_of_service('visinamingnb'))

    @patch('enmutils_int.lib.fm_nbi.get_service_ip')
    def test_visinaming_pub_ipv4(self, mock_get_service_ip, *_):
        mock_get_service_ip.return_value = 'svc-1-visinamingnb, svc-2-visinamingnb'
        self.assertTrue('svc-1-visinamingnb' in self.fm_nbi._get_ip_of_service('visinamingnb'))

    @patch('enmutils_int.lib.fm_nbi.shutil')
    @patch('enmutils_int.lib.fm_nbi.os.path.exists')
    @patch('enmutils_int.lib.fm_nbi.os.listdir')
    def test_check_test_client_exist_yes(self, mock_list_dir, mock_os_path_exists, mock_shutil):
        mock_list_dir.return_value = ['testclient.sh', 'corbaserver-testClient-1.36.1.jar', 'log4j-1.2.16.jar']
        mock_os_path_exists.side_effect = [True, False, False, False]
        self.fm_nbi.check_test_client_exist()
        self.assertTrue(mock_shutil.copy.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.os.path.exists')
    @patch('enmutils_int.lib.fm_nbi.os.listdir')
    def test_check_test_client_exist_yes_yes(self, mock_list_dir, mock_os_path_exists, mock_logger_debug):
        mock_list_dir.return_value = ['testclient.sh', 'corbaserver-testClient-1.36.1.jar', 'log4j-1.2.16.jar']
        mock_os_path_exists.side_effect = [True, True, True, True]
        self.fm_nbi.check_test_client_exist()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.shutil')
    @patch('enmutils_int.lib.fm_nbi.os.path.exists')
    @patch('enmutils_int.lib.fm_nbi.os.listdir')
    def test_check_test_client_exist_no(self, mock_list_dir, mock_os_path_exists, mock_shutil):
        mock_list_dir.return_value = ['testclient.sh', 'corbaserver-testClient-1.36.1.jar', 'log4j-1.2.16.jar']
        mock_os_path_exists.side_effect = [False, True]
        self.fm_nbi.check_test_client_exist()
        self.assertTrue(mock_shutil.copy.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.os.path.exists')
    def test_create_dir_creates_new_directory(self, mock_os_path_exists, mock_logger_debug):
        mock_os_path_exists.return_value = True
        self.fm_nbi.create_dir()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.os.makedirs')
    @patch('enmutils_int.lib.fm_nbi.os.path.dirname')
    @patch('enmutils_int.lib.fm_nbi.os.path.exists')
    def test_create_dir_does_not_create_a_directory(self, mock_os_path_exists, mock_os_path_dirname, mock_os_makedirs):
        mock_os_path_exists.return_value = False
        self.fm_nbi.create_dir()
        self.assertTrue(mock_os_path_dirname.called)
        self.assertTrue(mock_os_makedirs.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    def test_create_test_client_dir_on_ms(self, mock_run_cmd_on_ms, mock_logger_debug):
        response = Mock()
        response._rc = 0
        response._stdout = 'OK'
        self.fm_nbi.PHYSICAL = True
        mock_run_cmd_on_ms.return_value = response
        self.fm_nbi.create_test_client_dir_on_ms_or_emp()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    def test_create_test_client_dir_on_emp(self, mock_run_cmd_on_vm, mock_logger_debug):
        response = Mock()
        response._rc = 0
        response._stdout = 'OK'
        self.fm_nbi.CLOUD = True
        mock_run_cmd_on_vm.return_value = response
        self.fm_nbi.create_test_client_dir_on_ms_or_emp()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    def test_remove_test_client_dir_on_ms(self, mock_run_cmd_on_ms, mock_logger_debug, *_):
        response = Mock()
        response._rc = 0
        response._stdout = 'OK'
        self.fm_nbi.PHYSICAL = True
        mock_run_cmd_on_ms.return_value = response
        self.fm_nbi.remove_test_client_dir_on_ms_or_emp()
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    def test_remove_test_client_dir_on_ms_fails(self, mock_run_cmd_on_ms, mock_logger_debug, *_):
        self.fm_nbi.PHYSICAL = True
        mock_run_cmd_on_ms.return_value = False
        self.fm_nbi.remove_test_client_dir_on_ms_or_emp()
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    def test_remove_test_client_dir_on_vm_fails(self, mock_run_cmd_on_vm, mock_logger_debug, *_):
        self.fm_nbi.CLOUD = True
        mock_run_cmd_on_vm.return_value = False
        self.fm_nbi.remove_test_client_dir_on_ms_or_emp()
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertFalse(mock_logger_debug.called)

    def test_nbalarmirp_ip_returns_ip(self):
        self.assertTrue(self.fm_nbi._nbalarmirp_ip() == 'svc-1-nbalarmirp')

    def test_nbalarmirp_ip_does_not_return_ip(self):
        self.fm_nbi.NBALARMIRP = []
        self.fm_nbi._nbalarmirp_ip()
        self.assertFalse(self.fm_nbi._nbalarmirp_ip() == 'svc-1-nbalarmirp')

    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.pexpect.spawn.expect')
    @patch('enmutils_int.lib.fm_nbi.pexpect.spawn.sendline')
    def test_return_client_files_from_nbalarmirp_vm(self, mock_pexpect_sendline, mock_spawn_expect,
                                                    mock_logger_info):
        self.fm_nbi.PHYSICAL = True
        mock_spawn_expect.return_value = 0
        self.fm_nbi.return_test_client_files_from_nbalarmirp_vm(pexpect.spawn('/usr/bin/ssh root@localhost'))
        self.assertTrue(mock_spawn_expect.called)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_pexpect_sendline.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    def test_return_test_client_files_from_nbalarmirp_vm_for_cloud(self, mock_run_cmd_on_vm, mock_logger_info):
        self.fm_nbi.CLOUD = True
        response = Mock()
        response.rc = 0
        response._stdout = 'OK'
        mock_run_cmd_on_vm.return_value = response
        self.fm_nbi.return_test_client_files_from_nbalarmirp_vm(mock_run_cmd_on_vm('/usr/bin/ssh root@localhost'))
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertTrue(mock_logger_info.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    def test_return_test_client_files_from_nbalarmirp_vm_for_cloud_retry(self, mock_run_cmd_on_vm, mock_logger_info):
        self.fm_nbi.CLOUD = True
        mock_run_cmd_on_vm.side_effect = [Mock(rc=1), Mock(rc=0)]
        self.fm_nbi.return_test_client_files_from_nbalarmirp_vm(Mock())
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertTrue(mock_logger_info.called)

    @patch('enmutils_int.lib.fm_nbi.pexpect.spawn.expect')
    def test_return_test_client_files_from_nbalarmirp_vm_error(self, mock_spawn_expect, *_):
        self.fm_nbi.PHYSICAL = True
        mock_spawn_expect.side_effect = self.error_response
        child = Mock()
        child.expect.side_effect = EnvironError
        self.assertRaises(EnvironError, self.fm_nbi.return_test_client_files_from_nbalarmirp_vm, child)

    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    def test_return_test_client_files_from_nbalarmirp_vm_error_for_cloud(self, mock_run_cmd_on_vm):
        response = Mock()
        response.side_effect = [1, 1]
        response._stdout = 'OK'
        mock_run_cmd_on_vm.return_value = response
        self.fm_nbi.CLOUD = True
        self.assertRaises(ShellCommandReturnedNonZero, self.fm_nbi.return_test_client_files_from_nbalarmirp_vm,
                          response)

    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms')
    def test_get_subscription_ids_gets_subscription_ids(self, mock_run_cmd_on_emp_or_ms, *_):
        response = Mock()
        response.rc = 0
        response.stdout = ('Subscription data :\n'
                           'SubscriptionData [ subscriptionId=257976565508271,\n'
                           ' clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1z1], \n'
                           'filter=\'LTE\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n'
                           ' SubscriptionData [ \n'
                           'subscriptionId=255531258342165, \n'
                           'clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1f1], \n'
                           'filter=\'LTE1\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n'
                           ' SubscriptionData [ \n'
                           'subscriptionId=255531258342168, \n'
                           'clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1f1], \n'
                           'filter=\'LTE03ERBS00001\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n')
        mock_run_cmd_on_emp_or_ms.return_value = response
        self.fm_nbi.CLOUD = True
        self.assertEqual(self.fm_nbi.get_subscription_ids(),
                         [('LTE', '257976565508271'),
                          ('LTE1', '255531258342165'),
                          ('LTE03ERBS00001', '255531258342168')])

    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_cloud_native_pod')
    def test_get_subscription_ids_gets_subscription_ids_pod(self, mock_run_cmd_on_pod):
        response = Mock()
        response.rc = 0
        response.stdout = ('Subscription data :\n'
                           'SubscriptionData [ subscriptionId=257976565508271,\n'
                           ' clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1z1], \n'
                           'filter=\'LTE\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n'
                           ' SubscriptionData [ \n'
                           'subscriptionId=255531258342165, \n'
                           'clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1f1], \n'
                           'filter=\'LTE1\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n'
                           ' SubscriptionData [ \n'
                           'subscriptionId=255531258342168, \n'
                           'clientIOR=IOR:00000,\n'
                           'timeTick=20, \n'
                           'notificationCategorySet=[1f1], \n'
                           'filter=\'LTE03ERBS00001\', \n'
                           'subscriptionState=true, \n'
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]\n')
        mock_run_cmd_on_pod.return_value = response
        self.fm_nbi.CLOUD_NATIVE = True
        self.assertEqual(self.fm_nbi.get_subscription_ids(),
                         [('LTE', '257976565508271'),
                          ('LTE1', '255531258342165'),
                          ('LTE03ERBS00001', '255531258342168')])

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms')
    def test_get_subscription_ids_logs_no_subscription_ids_present(self, mock_run_cmd_on_emp_or_ms, mock_logger_debug):
        response = Mock()
        response.rc = 0
        response.stdout = ('Subscription data : SubscriptionData [ clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1z1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]'
                           ' SubscriptionData [ clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1f1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]')
        mock_run_cmd_on_emp_or_ms.return_value = response
        self.fm_nbi.get_subscription_ids()
        self.assertTrue(mock_logger_debug.call_count, 5)

    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms')
    def test_get_subscription_ids_raise_ShellCommandReturnedNonZero_exception(self, mock_run_cmd_on_emp_or_ms, *_):
        self.fm_nbi.CLOUD = True
        mock_run_cmd_on_emp_or_ms.side_effect = EnvironError
        self.assertRaises(EnvironError, self.fm_nbi.get_subscription_ids)

    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms')
    def test_get_subscription_ids_raise_exception2(self, mock_run_cmd_on_emp_or_ms, *_):
        self.fm_nbi.CLOUD = True
        response = Mock()
        response.rc = 1
        response.stdout = ('Subscription data :'
                           'SubscriptionData [ subscriptionId=257976565508271, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1z1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]'
                           ' SubscriptionData [ subscriptionId=255531258342165, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1f1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]')

        mock_run_cmd_on_emp_or_ms.return_value = response
        self.assertRaises(ShellCommandReturnedNonZero, self.fm_nbi.get_subscription_ids)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_check_and_remove_old_files_is_successful(self, mock_run_local_cmd, mock_logger_info, *_):
        response = Mock()
        response._rc = 0
        response._stdout = 'OK'
        mock_run_local_cmd.return_value = response
        self.fm_nbi.check_and_remove_old_files(self.fm_nbi.SRCDIR)
        self.assertTrue(mock_logger_info.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_check_and_remove_old_files_failed(self, mock_run_local_cmd, mock_logger_debug, *_):
        mock_run_local_cmd.return_value = 0
        self.fm_nbi.check_and_remove_old_files(self.fm_nbi.SRCDIR)
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_transfer_test_client_files_to_workload_vm_is_successful(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                                     mock_logger_info, *_):
        response = Mock()
        response.rc = 0
        response.stdout = "10.10.10.10"
        mock_run_local_cmd.side_effect = [response, response]
        self.fm_nbi.PHYSICAL = True
        mock_run_cmd_on_ms.return_value = response
        self.fm_nbi.transfer_test_client_files_to_workload_vm()
        self.assertEqual(2, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_logger_info.call_count)
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_vm')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_transfer_test_client_files_to_workload_vm_is_successful_for_cloud(self, mock_run_local_cmd,
                                                                               mock_run_cmd_on_vm, mock_logger_info,
                                                                               *_):
        response = Mock()
        response.rc = 0
        response.stdout = "10.10.10.10"
        mock_run_local_cmd.side_effect = [response, response]
        self.fm_nbi.CLOUD = True
        self.fm_nbi.transfer_test_client_files_to_workload_vm()
        self.assertEqual(2, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_logger_info.call_count)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)

    @patch("enmutils_int.lib.fm_nbi.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_transfer_test_client_files_to_workload_vm_is_successful_for_cloud_native(self, mock_run_local_cmd,
                                                                                      mock_logger_info, *_):
        response = Mock()
        response.rc = 0
        response.stdout = "10.10.10.10"
        mock_run_local_cmd.side_effect = [response, response]
        self.fm_nbi.CLOUD_NATIVE = True
        self.fm_nbi.transfer_test_client_files_to_workload_vm()
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_logger_info.call_count)

    @patch('enmutils_int.lib.fm_nbi.log.logger.info')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_transfer_test_client_files_to_workload_vm_failed(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                              mock_logger_info):
        response = Mock()
        response.rc = 1
        response.stdout = 'OK'
        mock_run_local_cmd.side_effect = [response, response]
        self.fm_nbi.PHYSICAL = True
        mock_run_cmd_on_ms.return_value = response
        self.fm_nbi.transfer_test_client_files_to_workload_vm()
        self.assertEqual(2, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_logger_info.call_count)
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch("enmutils_int.lib.fm_nbi.GenericFlow.switch_to_ms_or_emp")
    @patch('enmutils_int.lib.fm_nbi.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.fm_nbi.get_emp')
    @patch('enmutils_int.lib.fm_nbi.pexpect.spawn.expect')
    @patch('enmutils_int.lib.fm_nbi.shell.run_cmd_on_ms')
    @patch('enmutils_int.lib.fm_nbi.shell.run_local_cmd')
    def test_transfer_files_to_ms_or_emp(self, mock_run_local_cmd, mock_run_cmd_on_ms, mock_get_emp, *_):
        self.fm_nbi.PHYSICAL = True
        mock_get_emp.return_value = 'localhost'
        response = Mock()
        response.rc = 0
        response.stdout = 'OK'
        mock_run_local_cmd.side_effect = [response, response, response]
        mock_run_cmd_on_ms.side_effect = [response, response]
        self.fm_nbi.transfer_files_to_ms_or_emp()
        self.assertEqual(3, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_run_cmd_on_ms.call_count)

    @patch('enmutils_int.lib.fm_nbi.FmNbi.transfer_test_client_files_to_workload_vm')
    @patch('enmutils_int.lib.fm_nbi.FmNbi.clear_test_client_folder_on_workload_vm')
    def test_transfer_files_to_ms_or_emp_CN(self, *_):
        self.fm_nbi.CLOUD_NATIVE = True
        self.fm_nbi.transfer_files_to_ms_or_emp()

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_clear_test_client_folder_on_workload_vm(self, mock_run_local_cmd, mock_logger_debug, *_):
        response = Mock()
        response.rc = 0
        response.stdout = 'Command OK'
        mock_run_local_cmd.return_value = response
        self.fm_nbi.clear_test_client_folder_on_workload_vm()
        self.assertTrue(mock_run_local_cmd.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch('enmutils_int.lib.fm_nbi.shutil.copy')
    def test_copy_test_client_file(self, mock_copy, mock_logger_debug):
        mock_copy.return_value = None
        self.fm_nbi.copy_test_client_file('testclient.sh')
        self.assertTrue(mock_copy.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.shutil')
    @patch('enmutils_int.lib.fm_nbi.os.listdir')
    def test_copy_test_client_files(self, mock_os_listdir, mock_shutil):
        mock_os_listdir.return_value = ['testclient.sh', 'corbaserver-testClient-1.36.1.jar', 'log4j-1.2.16.jar']
        self.fm_nbi.copy_test_client_files()
        self.assertEqual(3, mock_shutil.copy.call_count)

    @patch("enmutils_int.lib.fm_nbi.mutex")
    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_subscribe_nbi_is_successful(self, mock_run_local_cmd, mock_logger_debug, *_):
        response = Mock
        response._rc = 0
        response._stdout = 'connection success'
        mock_run_local_cmd.return_value = response
        self.fm_nbi.subscribe_nbi(60 * 6, self.fm_nbi.NBI_filters)
        self.assertEqual(2, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.mutex")
    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_subscribe_nbi_raises_environ_error(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.side_effect = EnvironError
        self.assertRaises(EnvironError, self.fm_nbi.subscribe_nbi, 60 * 6, self.fm_nbi.NBI_filters)

    @patch("enmutils_int.lib.fm_nbi.mutex")
    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_subscribe_nbi_resets_num_filters_used(self, mock_run_local_cmd, mock_logger_debug, *_):
        self.fm_nbi.NUMBER_FILTERS_USED = 7
        self.fm_nbi.subscribe_nbi(60 * 6, self.fm_nbi.NBI_filters)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertEqual(3, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.mutex")
    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_subscribe_nbi_updates_channel_flag_for_1f1_channel(self, mock_run_local_cmd, mock_logger_debug, *_):
        self.fm_nbi.subscribe_nbi(60 * 6, self.fm_nbi.NBI_filters)
        self.assertEqual(2, mock_logger_debug.call_count)
        self.assertTrue(self.fm_nbi.CHANNEL_FLAG)
        self.assertTrue(mock_run_local_cmd.called)

    @patch("enmutils_int.lib.fm_nbi.shell.Command")
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_subscribe_nbi_updates_channel_flag_for_1z1_channel(self, mock_run_local_cmd, mock_logger_debug, *_):
        self.fm_nbi.CHANNEL_FLAG = True
        self.fm_nbi.subscribe_nbi(60 * 6, self.fm_nbi.NBI_filters)
        self.assertEqual(2, mock_logger_debug.call_count)
        self.assertFalse(self.fm_nbi.CHANNEL_FLAG)
        self.assertTrue(mock_run_local_cmd.called)

    @patch('enmutils_int.lib.fm_nbi.shell.Command')
    @patch('enmutils_int.lib.fm_nbi.deployment_info_helper_methods.get_cloud_native_service_vip')
    def test_corba_sub_test(self, *_):
        self.fm_nbi.CLOUD_NATIVE = True
        self.fm_nbi.corba_sub_test(511, self.fm_nbi.NBI_filters, 60)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_unsubscribe_nbi(self, mock_run_local_cmd, mock_logger_debug):
        response = Mock()
        response.rc = 0
        response.stdout = 'Command OK'
        mock_run_local_cmd.return_value = response
        self.fm_nbi.unsubscribe_nbi('01')
        self.assertEqual(3, mock_logger_debug.call_count)

    @patch('enmutils_int.lib.fm_nbi.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_unsbscribe_nbi_cloudnative(self, mock_run_local_cmd, mock_logger_debug, _):
        self.fm_nbi.CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        response.stdout = 'Command OK'
        mock_run_local_cmd.return_value = response
        self.fm_nbi.unsubscribe_nbi('01')
        self.assertEqual(3, mock_logger_debug.call_count)

    @patch('enmutils_int.lib.fm_nbi.FmNbi.unsubscribe_nbi')
    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_unsubscribe_all_nbi(self, mock_run_local_cmd, mock_debug_logger, *_):
        response = Mock()
        response.rc = 0
        response.stdout = 'Command OK'
        mock_run_local_cmd.side_effect = [response, response, response]
        self.fm_nbi.unsubscribe_all_nbi(['subscription_01', 'subscription_02', 'subscription_03'])
        self.assertEqual(1, mock_debug_logger.call_count)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_unsubscribe_all_nbi_none(self, mock_run_local_cmd, mock_debug_logger):
        self.fm_nbi.unsubscribe_all_nbi([])
        self.assertEqual(0, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_logger.call_count)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    def test_print_info_ipv4(self, mock_logger_debug):
        self.fm_nbi.IP = IPv4
        self.fm_nbi.print_info(['subscription_01', 'subscription_02', 'subscription_03'])
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    def test_print_info_logs_no_nbalarmirp_group_found_for_IPV4(self, mock_logger_debug):
        self.fm_nbi.IP = IPv4
        self.fm_nbi.NBALARMIRP = []
        self.fm_nbi.print_info()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    def test_print_info_ipv6(self, mock_logger_debug):
        self.fm_nbi.IP = IPv6
        self.fm_nbi.print_info(['subscription_01', 'subscription_02', 'subscription_03'])
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    def test_print_info_logs_no_nbalarmirp_group_found_for_IPV6(self, mock_logger_debug):
        self.fm_nbi.IP = IPv6
        self.fm_nbi.NBALARMIRP = []
        self.fm_nbi.print_info()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm_nbi.log.logger.debug')
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    def test_close_is_successful(self, mock_run_local_cmd, mock_logger_debug):
        response = Mock()
        response._rc = 0
        response._stdout = 'Command run OK'
        mock_run_local_cmd.side_effect = [response, response]
        self.fm_nbi.close()
        self.assertEqual(2, mock_logger_debug.call_count)
        self.assertEqual(2, mock_run_local_cmd.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.FmNbi.get_workload_vm_ip")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_create_fm_snmp_nbi_subscriptions_is_successful(self, mock_logger_debug, *_):
        responses_list = []
        output = ["fmsnmp create command executed", "fmsnmp create command executed", "fmsnmp create command executed",
                  "fmsnmp create command executed", "fmsnmp create command executed"]
        for resp in output:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)
        self.user.enm_execute.side_effect = responses_list
        self.fm_nbi.create_fm_snmp_nbi_subscriptions()
        self.assertEqual(5, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.FmNbi.get_workload_vm_ip")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_create_fm_snmp_nbi_subscriptions_continues_when_Exception_is_caught(self, mock_logger_debug, *_):
        self.user.enm_execute.side_effect = Exception
        self.fm_nbi.create_fm_snmp_nbi_subscriptions()
        self.assertEqual(5, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.FmNbi.get_workload_vm_ip")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_create_fm_snmp_nbi_subscriptions_raises_EnmApplication_Error(self, mock_logger_debug, *_):
        responses_list = []
        output = ["fmsnmp create command executed", "fmsnmp create command executed", "fmsnmp create command executed",
                  "fmsnmp create command executed", "failed with ERROR 593: Service unavailable"]
        for resp in output:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)
        self.user.enm_execute.side_effect = responses_list
        self.assertRaises(EnmApplicationError, self.fm_nbi.create_fm_snmp_nbi_subscriptions)
        self.assertEqual(5, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.FmNbi.get_workload_vm_ip")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_create_fm_snmp_nbi_subscriptions_logs_when_zero_subs_to_be_created(self, mock_logger_debug, *_):
        self.fm_nbi.snmp_subs_list = range(0)
        self.fm_nbi.create_fm_snmp_nbi_subscriptions()
        self.assertEqual(1, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.re.compile")
    @patch("enmutils_int.lib.fm_nbi.json.dumps")
    @patch("enmutils_int.lib.fm_nbi.re.findall")
    @patch("enmutils_int.lib.fm_nbi.re.split")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_get_fm_snmp_nbi_subscriptions_is_successful(self, mock_logger_debug, mock_re_split, mock_re_findall, *_):
        response = Mock()
        response.get_output.return_value = [u'fmsnmp get nmslist', u'', u'   snmpSub1', u'   snmpSub2', u'', u'2 instance(s)  ', u'']
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = [" ", "2"]
        mock_re_findall.return_value = ["snmpSub1", "snmpSub2"]
        self.fm_nbi.get_fm_snmp_nbi_subscriptions()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.re.compile")
    @patch("enmutils_int.lib.fm_nbi.json.dumps")
    @patch("enmutils_int.lib.fm_nbi.re.split")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_get_fm_snmp_nbi_subscriptions_failed(self, mock_logger_debug, mock_re_split, *_):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)  ', u'']
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = [" ", "0"]
        self.fm_nbi.get_fm_snmp_nbi_subscriptions()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_delete_fm_snmp_nbi_subscriptions_is_successful(self, mock_logger_debug, _):
        response = Mock()
        response.get_output.return_value = ["subscription snmpSub1 deleted", "subscription snmpSub2 deleted"]
        self.user.enm_execute.return_value = response
        self.fm_nbi.delete_fm_snmp_nbi_subscriptions(["snmpSub1", "snmpSub2"])
        self.assertEqual(4, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    def test_delete_fm_snmp_nbi_subscriptions_failed(self, mock_logger_debug, _):
        response = Mock()
        response.get_output.return_value = ["failed", "failed"]
        self.user.enm_execute.return_value = response
        self.fm_nbi.delete_fm_snmp_nbi_subscriptions(["snmpSub1", "snmpSub2"])
        self.assertEqual(4, mock_logger_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.re.compile")
    @patch("enmutils_int.lib.fm_nbi.json.dumps")
    @patch("enmutils_int.lib.fm_nbi.re.findall")
    @patch("enmutils_int.lib.fm_nbi.re.split")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms")
    def test_teardown_is_successful(self, mock_run_cmd_on_emp_or_ms, mock_run_local_cmd, mock_re_split, mock_re_findall, *_):
        self.fm_nbi.CLOUD = True
        responses_list = []
        output = [[u'fmsnmp get nmslist', u'', u'   snmpSub1', u'   snmpSub2', u'', u'2 instance(s)  ', u''],
                  "subscription snmpSub1 deleted", "subscription snmpSub2 deleted"]
        self.fm_nbi.NBFMSNMP = True
        for resp in output:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)
        self.user.enm_execute.side_effect = responses_list
        mock_re_split.return_value = [" ", "2"]
        mock_re_findall.side_effect = [["snmpSub1", "snmpSub2"], ['257976565508271', '257976565508272'], ['LTE', 'LTE1']]
        response = Mock()
        response.rc = 0
        response.stdout = ('Subscription data :'
                           'SubscriptionData [ subscriptionId=257976565508271, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1z1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]'
                           ' SubscriptionData [ subscriptionId=255531258342165, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1f1], filter=LTE1, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]')
        mock_run_cmd_on_emp_or_ms.return_value = response
        mock_run_local_cmd.side_effect = [response, response, response, response]
        self.fm_nbi.teardown(filters=self.fm_nbi.NBI_filters)
        self.assertTrue(mock_run_cmd_on_emp_or_ms.called)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.json.dumps")
    @patch("enmutils_int.lib.fm_nbi.re.compile")
    @patch("enmutils_int.lib.fm_nbi.shell.run_local_cmd")
    @patch("enmutils_int.lib.fm_nbi.shell.run_cmd_on_emp_or_ms")
    def test_teardown_fails_for_SNMP_NBI(self, mock_run_cmd_on_emp_or_ms, mock_run_local_cmd, mock_re_compile, *_):
        response = Mock()
        response.get_output.return_value = [u'fmsnmp get nmslist', u'', u'   snmpSub1', u'   snmpSub2', u'', u'2 instance(s)  ', u'']
        self.fm_nbi.CLOUD = True
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.return_value = None
        response = Mock()
        response.rc = 0
        response.stdout = ('Subscription data :'
                           'SubscriptionData [ subscriptionId=257976565508271, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1z1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]'
                           ' SubscriptionData [ subscriptionId=255531258342165, clientIOR=IOR:00000,'
                           'timeTick=20, notificationCategorySet=[1f1], filter=LTE, subscriptionState=true, '
                           'Last Subscription Ping Time=Sat Sep 23 13:20:57 IST 2017]')
        mock_run_cmd_on_emp_or_ms.return_value = response
        mock_run_local_cmd.side_effect = [response, response, response, response]
        self.fm_nbi.teardown(filters=self.fm_nbi.NBI_filters)
        self.assertTrue(mock_run_cmd_on_emp_or_ms.called)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.info")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    @patch('enmutils_int.lib.fm_nbi.get_cloud_members_ip_address')
    def test_fetch_snmp_nbi_service_ip__cloud_is_successful(self, mock_get_cloud_members_ip_address, mock_log_debug,
                                                            mock_log_info, *_):
        self.fm_nbi.CLOUD = True
        mock_get_cloud_members_ip_address.return_value = [Mock()]
        self.fm_nbi.fetch_snmp_nbi_service_ip()
        self.assertEqual(2, mock_log_info.call_count)
        self.assertEqual(1, mock_log_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.info")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    @patch('enmutils_int.lib.fm_nbi.get_pod_hostnames_in_cloud_native')
    def test_fetch_snmp_nbi_service_ip__cloud_native_is_successful(self, mock_get_cloud_members_ip_address, mock_log_debug, *_):
        self.fm_nbi.CLOUD_NATIVE = True
        mock_get_cloud_members_ip_address.return_value = [Mock()]
        self.fm_nbi.fetch_snmp_nbi_service_ip()
        self.assertEqual(1, mock_log_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.info")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    @patch('enmutils_int.lib.fm_nbi.get_service_ip')
    def test_fetch_snmp_nbi_service_ip__physical_is_successful(self, mock_get_cloud_members_ip_address, mock_log_debug, *_):
        self.fm_nbi.PHYSICAL = True
        mock_get_cloud_members_ip_address.return_value = [Mock()]
        self.fm_nbi.fetch_snmp_nbi_service_ip()
        self.assertEqual(2, mock_log_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.log.logger.debug")
    @patch('enmutils_int.lib.fm_nbi.get_cloud_members_ip_address')
    def test_fetch_snmp_nbi_service_ip_catches_exception(self, mock_get_cloud_members_ip_address, mock_log_debug,
                                                         *_):
        self.fm_nbi.CLOUD = True
        mock_get_cloud_members_ip_address.side_effect = Exception
        self.fm_nbi.fetch_snmp_nbi_service_ip()
        self.assertEqual(2, mock_log_debug.call_count)

    @patch("enmutils_int.lib.fm_nbi.log.logger.info")
    def test_corba_nbi_teardown_will_not_work_for_cloud_native(self, mock_logger_info):
        self.fm_nbi.NBALARMIRP = []
        self.fm_nbi.corba_nbi_teardown()
        self.assertEqual(1, mock_logger_info.call_count)

    @patch("enmutils_int.lib.fm_nbi.sleep")
    @patch("enmutils_int.lib.fm_nbi.json.dumps")
    @patch("enmutils_int.lib.fm_nbi.re.compile")
    def test_snmp_nbi_teardown_will_not_unsubscribe_if_no_subscriptions_found(self, mock_re_compile, *_):
        self.fm_nbi.NBFMSNMP = [unit_test_utils.generate_configurable_ip()]
        response = Mock()
        response.get_output.return_value = [u'fmsnmp get nmslist', u'']
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.return_value = None
        response = Mock()
        response.rc = 0
        response.stdout = 'No Subscriptions Found!'
        self.fm_nbi.snmp_nbi_teardown()
        self.assertTrue(mock_re_compile.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
