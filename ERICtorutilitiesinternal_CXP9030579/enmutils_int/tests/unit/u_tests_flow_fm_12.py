#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase

from enmutils_int.lib.fm_bnsi_nbi import FmBnsiNbi
from enmutils_int.lib.fm_nbi import FmNbi, IPv4
from enmutils_int.lib.profile_flows.fm_flows.fm_12_flow import Fm12
from testslib import unit_test_utils


class Fm12UnitTests(ParameterizedTestCase):
    flow = None

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

        self.flow = Fm12()
        self.flow.FM_NBI = FmNbi(user=self.user, timeout=10, ip=IPv4, ports=10, snmp_subs_count=5)
        self.flow.BNSI_NBI = FmBnsiNbi()
        self.flow.TIMEOUT = 10
        self.flow.TIMEOUT_SUBSCRIPTION = 10
        self.flow.NUM_USERS = 1
        self.flow.NUMBER_NBI_SUBSCRIPTIONS = 15
        self.flow.NBI_filters = ["LTE0", "LTE1"]
        self.flow.USER_ROLES = ["Administrator"]
        self.flow.CORBA_ENABLED = True
        self.flow.BNSI = True
        self.flow.CLOUD_NATIVE = False
        self.flow.SCHEDULED_TIMES = "10:00:00"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.print_info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.check_test_client_exist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.transfer_files_to_ms_or_emp")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.create_nbi_framework")
    def test_setting_fm_nbi_framework__is_successful(self, mock_create_nbi_framework, mock_logger_debug,
                                                     mock_transfer_files_to_ms_or_emp,
                                                     mock_check_test_client_exist, *_):

        self.flow._setting_fm_nbi_framework()

        self.assertEqual(3, mock_logger_debug.call_count)
        self.assertTrue(mock_create_nbi_framework.called)
        self.assertTrue(mock_transfer_files_to_ms_or_emp.called)
        self.assertTrue(mock_check_test_client_exist.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.print_info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.check_test_client_exist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.transfer_files_to_ms_or_emp")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.create_nbi_framework")
    def test_setting_fm_nbi_framework__raise_exception_2(self, mock_create_nbi_framework,
                                                         mock_transfer_files_to_ms_or_emp, mock_add_error_as_exception,
                                                         mock_check_test_client_exist, *_):
        mock_create_nbi_framework.side_effect = Exception

        self.flow._setting_fm_nbi_framework()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_create_nbi_framework.called)
        self.assertFalse(mock_transfer_files_to_ms_or_emp.called)
        self.assertFalse(mock_check_test_client_exist.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.print_info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.check_test_client_exist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.transfer_files_to_ms_or_emp")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.create_nbi_framework")
    def test_setting_fm_nbi_framework__raise_exception_3(self, mock_create_nbi_framework,
                                                         mock_transfer_files_to_ms_or_emp,
                                                         mock_add_error_as_exception,
                                                         mock_check_test_client_exist, *_):
        mock_transfer_files_to_ms_or_emp.side_effect = Exception

        self.flow._setting_fm_nbi_framework()

        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_create_nbi_framework.called)
        self.assertTrue(mock_transfer_files_to_ms_or_emp.called)
        self.assertFalse(mock_check_test_client_exist.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.print_info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.check_test_client_exist")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.transfer_files_to_ms_or_emp")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.create_nbi_framework")
    def test_setting_fm_nbi_framework__raise_exception_4(self, mock_create_nbi_framework,
                                                         mock_transfer_files_to_ms_or_emp,
                                                         mock_add_error_as_exception,
                                                         mock_check_test_client_exist, *_):
        mock_check_test_client_exist.side_effect = Exception

        self.assertRaises(Exception, self.flow._setting_fm_nbi_framework())

        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_create_nbi_framework.called)
        self.assertTrue(mock_transfer_files_to_ms_or_emp.called)
        self.assertTrue(mock_check_test_client_exist.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log.logger.debug")
    def test_get_number_of_subscriptions_to_be_created(self, mock_logger_debug):
        self.flow.NUMBER_NBI_SUBSCRIPTIONS = 14
        expected_result = {"cpp_subscriptions": 7, "snmp_subscriptions": 7}
        self.assertEqual(self.flow._get_number_of_subscriptions_to_be_created(self.user), expected_result)
        self.assertTrue(mock_logger_debug.called)

    def test_get_number_of_subscriptions_to_be_created__corba_enabled_is_false(self):
        self.flow.CORBA_ENABLED = False
        self.flow.NUMBER_NBI_SUBSCRIPTIONS = 5
        expected_result = {"cpp_subscriptions": 0, "snmp_subscriptions": 5}
        self.assertEqual(self.flow._get_number_of_subscriptions_to_be_created(self.user), expected_result)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.subscribe_nbi")
    def test_corba_nbi_taskset__is_successful(self, mock_subscribe_nbi):
        self.flow.corba_nbi_taskset(0, self.flow)
        self.assertTrue(mock_subscribe_nbi.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.get_workload_vm_ip")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.snmp_nbi_teardown")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log.logger.debug")
    def test_setup_snmp__is_successful(self, mock_log_debug, *_):
        self.flow.setup_snmp()
        self.assertTrue(mock_log_debug.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.create_fm_snmp_nbi_subscriptions")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    def test_create_snmp_subs__handles_exceptions(self, mock_add_error_as_exception, *_):
        self.flow.SNMP_NBI_IP = []
        self.flow.create_snmp_subs()
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi")
    def test_create_corba_subs__handles_exceptions(self, mock_fm_nbi, mock_add_error_as_exception):
        mock_fm_nbi.return_value.FM_NBI.is_nbi_framework_ok = False
        self.flow.create_corba_subs(5)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.is_nbi_framework_ok")
    def test_create_corba__not_enabled(self, mock_fm_nbi, mock_add_error_as_exception):
        self.flow.CORBA_ENABLED = False
        self.flow.create_corba_subs(5)
        self.assertFalse(mock_fm_nbi.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi.create_bnsiman_user_and_enable_bnsi_nbi")
    def test_setup_bnsi_nbi__is_successful(self, mock_create_bnsiman, *_):
        self.flow.teardown_list = Mock()
        self.flow.setup_bnsi_nbi()
        self.assertTrue(mock_create_bnsiman.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi.create_bnsiman_user_and_enable_bnsi_nbi")
    def test_setup_bnsi_nbi__adds_error_as_exception(self, mock_create_bnsiman, mock_add_error_as_exception, *_):
        mock_create_bnsiman.side_effect = Exception
        self.flow.teardown_list = Mock()
        self.flow.setup_bnsi_nbi()
        self.assertTrue(mock_create_bnsiman.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log.logger.info")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi.create_bnsiman_user_and_enable_bnsi_nbi")
    def test_setup_bnsi_nbi__if_bnsi_not_supported(self, mock_create_bnsiman, mock_log):

        self.flow.BNSI = False
        self.flow.setup_bnsi_nbi()
        self.assertFalse(mock_create_bnsiman.called)
        self.assertEqual(mock_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.pexpect")
    def test_open_bnsi_nbi_session__is_successful(self, mock_pexpect, mock_log, *_):
        self.flow.open_bnsi_nbi_session()
        self.assertTrue(mock_pexpect.spawn.called)
        self.assertTrue(mock_log.logger.info.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.pexpect")
    def test_open_bnsi_nbi_session__adds_error_as_exception(self, mock_pexpect, mock_log, mock_add_error, *_):
        mock_pexpect.spawn.side_effect = Exception
        self.flow.open_bnsi_nbi_session()
        self.assertTrue(mock_pexpect.spawn.called)
        self.assertTrue(mock_log.logger.debug.call_count, 1)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.fm_nbi.FmNbi.teardown")
    @patch("enmutils_int.lib.fm_nbi.FmNbi.is_nbi_framework_ok")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log")
    def test_setup_corba__is_successful(self, mock_log, *_):
        self.flow.CLOUD_NATIVE = False
        self.flow.setup_corba()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.fm_nbi.FmNbi.teardown")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12._setting_fm_nbi_framework")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm_nbi.FmNbi.is_nbi_framework_ok")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.log")
    def test_setup_corba__for_cloudnative(self, mock_log, *_):
        self.flow.CLOUD_NATIVE = True
        self.flow.setup_corba()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.open_bnsi_nbi_session")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.create_users")
    def test_execute_flow__continues_with_corba_not_enabled(self, mock_create_user, mock_fm_nbi,
                                                            mock_open_bnsi, *_):
        self.flow.CORBA_ENABLED = False
        mock_create_user.return_value = [self.user]
        mock_fm_nbi.return_value.is_nbi_framework_ok = True
        mock_fm_nbi.return_value.snmp_nbi_teardown.side_effect = Exception
        self.flow.teardown_list = Mock()
        responses_list = []
        for resp in ["ComConnectivityInformation 400 instance(s) found ", "NetworkElement 600 instance(s) found "]:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)
        self.user.enm_execute.side_effect = responses_list
        mock_fm_nbi.return_value.get_subscription_ids.side_effect = [['1'], ['1', '2']]
        self.flow.NBFMSNMP = [unit_test_utils.generate_configurable_ip()]
        self.flow.execute_flow()
        self.assertTrue(mock_open_bnsi.called)
        self.assertTrue(mock_fm_nbi.return_value.create_fm_snmp_nbi_subscriptions.called)
        self.assertTrue(mock_create_user.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.open_bnsi_nbi_session")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.create_users")
    def test_execute_flow__successful_for_corba_enabled_bnsi_disabled(self, mock_create_user, mock_fm_nbi,
                                                                      mock_thread_constructor, mock_open_bnsi, *_):
        self.flow.BNSI = False
        mock_create_user.return_value = [self.user]
        mock_thread_constructor.return_value = Mock()
        mock_fm_nbi.return_value.is_nbi_framework_ok = True
        mock_fm_nbi.return_value.fetch_snmp_nbi_service_ip.return_value = unit_test_utils.generate_configurable_ip()
        responses_list = []
        for resp in ["ComConnectivityInformation 400 instance(s) found ", "NetworkElement 600 instance(s) found "]:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)

        self.user.enm_execute.side_effect = responses_list
        mock_fm_nbi.return_value.get_subscription_ids.side_effect = [['1'], ['1', '2']]
        self.flow.SNMP_NBI_IP = [unit_test_utils.generate_configurable_ip()]
        self.flow.execute_flow()
        self.assertTrue(mock_fm_nbi.return_value.create_fm_snmp_nbi_subscriptions.called)
        self.assertEqual(1, mock_fm_nbi.return_value.reset_ports.call_count)
        self.assertEqual(1, mock_fm_nbi.return_value.reset_num_filters.call_count)
        self.assertEqual(1, mock_thread_constructor.call_count)
        _, kwargs = mock_thread_constructor.call_args
        self.assertEqual(kwargs.get('work_items'), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(kwargs.get('num_workers'), 7)
        self.assertTrue(mock_thread_constructor.return_value.execute.called)
        self.assertFalse(mock_open_bnsi.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.open_bnsi_nbi_session")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.create_users")
    def test_execute_flow__handles_exceptions(self, mock_create_user, mock_fm_nbi,
                                              mock_add_error_as_exception, *_):
        mock_create_user.return_value = [self.user]
        mock_fm_nbi.return_value.is_nbi_framework_ok = False
        mock_fm_nbi.return_value.fetch_snmp_nbi_service_ip.return_value = unit_test_utils.generate_configurable_ip()
        mock_fm_nbi.return_value.teardown.side_effect = Exception
        responses_list = []
        for resp in ["ComConnectivityInformation 400 instance(s) found ", "NetworkElement 600 instance(s) found "]:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)

        self.user.enm_execute.side_effect = responses_list
        mock_fm_nbi.return_value.get_subscription_ids.side_effect = [['1'], ['1', '2']]
        self.flow.SNMP_NBI_IP = [unit_test_utils.generate_configurable_ip()]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.create_users", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.open_bnsi_nbi_session")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmBnsiNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.FmNbi")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.keep_running")
    def test_execute_flow__does_not_create_corba_subs_if_no_cpp_nodes(self, mock_keep_running, mock_fm_nbi,
                                                                      mock_thread_constructor,
                                                                      mock_bnsi_nbi, mock_open_bnsi_session, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_fm_nbi.return_value.fetch_snmp_nbi_service_ip.return_value = unit_test_utils.generate_configurable_ip()
        mock_fm_nbi.return_value.is_nbi_framework_ok.side_effect = [False, True]
        mock_fm_nbi.return_value.subscribe_nbi.return_value = None
        responses_list = []
        for resp in ["ComConnectivityInformation 0 instance(s) found ", "NetworkElement 0 instance(s) found "]:
            response = Mock()
            response.get_output.return_value = resp
            responses_list.append(response)
        self.user.enm_execute.side_effect = responses_list
        mock_fm_nbi.return_value.get_subscription_ids.side_effect = [['1'], ['1', '2']]
        self.flow.SNMP_NBI_IP = [unit_test_utils.generate_configurable_ip()]
        self.flow.CORBA_ENABLED = True
        self.flow.execute_flow()
        self.assertTrue(mock_open_bnsi_session.called)
        self.assertTrue(mock_fm_nbi.return_value.create_fm_snmp_nbi_subscriptions.called)
        self.assertTrue(mock_thread_constructor.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
