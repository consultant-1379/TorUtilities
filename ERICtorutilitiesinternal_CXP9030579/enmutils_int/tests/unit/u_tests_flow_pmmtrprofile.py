#!/usr/bin/env python

import datetime
import unittest2
from enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile import PmMtrProfile, toggle_state_of_subscription
from enmutils_int.lib.workload.pm_78 import PM_78
from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils


class PmMtrProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmMtrProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'MSC': 1}
        self.profile.TOTAL_REQUIRED_NODES = 5

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.toggle_state_of_subscriptions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.create_mtr_subscriptions")
    def test_execute_flow__is_successful(
            self, mock_create_mtr_subscriptions, mock_toggle_state_of_subscriptions, *_):
        mock_create_mtr_subscriptions.return_value = [Mock()]

        self.profile.execute_flow()
        self.assertTrue(mock_toggle_state_of_subscriptions.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.create_mtr_subscriptions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.toggle_state_of_subscriptions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    def test_execute_flow_adds_error__if_cannot_create_user(
            self, mock_execute_flow, mock_toggle_state_of_subscriptions, mock_add_error_as_exception, *_):
        mock_execute_flow.side_effect = Exception

        self.profile.execute_flow()
        self.assertFalse(mock_toggle_state_of_subscriptions.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.toggle_state_of_subscriptions")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.create_mtr_subscriptions")
    def test_execute_flow_adds_error__if_cannot_create_subscriptions(
            self, mock_create_mtr_subscriptions, mock_toggle_state_of_subscriptions, mock_add_error_as_exception, *_):
        mock_create_mtr_subscriptions.return_value = []

        self.profile.execute_flow()
        self.assertFalse(mock_toggle_state_of_subscriptions.called)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    @patch("enmutils_int.lib.profile.Profile.identifier", new_callable=PropertyMock, return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.MtrSubscription")
    def test_create_mtr_subscription__is_successful(self, mock_subscription, *_):
        subscription = Mock(id="999")
        mock_subscription.return_value = subscription
        self.assertEqual(subscription, self.profile.create_mtr_subscription(1, [Mock(), Mock()]))
        self.assertEqual(mock_subscription.return_value.recording_reference, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.identifier", new_callable=PropertyMock,
           return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.MtrSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.create_mtr_subscription")
    def test_create_mtr_subscriptions__is_successful(self, mock_create_mtr_subscription, mock_nodes_list,
                                                     mock_check_msc_nodes, *_):
        self.profile.SUBSCRIPTION_COUNT = 3
        self.profile.NODES_PER_SUBSCRIPTION = 2

        nodes = [Mock(node_id="M20"), Mock(node_id="M21"), Mock(node_id="M22")]
        mock_check_msc_nodes.return_value = nodes

        mock_nodes_list.return_value = nodes
        subscriptions = [Mock() for _ in xrange(3)]
        mock_create_mtr_subscription.side_effect = subscriptions

        self.assertEqual(subscriptions, self.profile.create_mtr_subscriptions())
        mock_create_mtr_subscription.assert_called_with(2, nodes[:2])
        self.assertEqual(mock_check_msc_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.identifier", new_callable=PropertyMock,
           return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.MtrSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.EnmApplicationError")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.create_mtr_subscription")
    def test_create_mtr_subscriptions__returns_empty_list_if_cannot_create_subscriptions(
            self, mock_create_mtr_subscription, mock_nodes_list, mock_add_error_as_exception,
            mock_enmapplicationerror, mock_check_msc_nodes, *_):
        self.profile.SUBSCRIPTION_COUNT = 3
        self.profile.NODES_PER_SUBSCRIPTION = 2

        mock_nodes_list.return_value = [Mock(node_id="M2{0}".format(_)) for _ in xrange(4)]
        mock_check_msc_nodes.return_value = mock_nodes_list.return_value
        mock_create_mtr_subscription.side_effect = Exception

        self.assertEqual([], self.profile.create_mtr_subscriptions())
        mock_add_error_as_exception.assert_called_with(
            mock_enmapplicationerror("Unable to create 3 MTR subscription(s)"))
        self.assertEqual(mock_check_msc_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.show_errored_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.toggle_state_of_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.ThreadQueue")
    def test_activate_deactivate_mtr_subscriptions_with_threads__is_successful(
            self, mock_threadqueue, mock_toggle_state_of_subscription, *_):
        subscriptions = [Mock(), Mock()]
        self.profile.activate_deactivate_mtr_subscriptions_with_threads("activate", subscriptions)
        mock_threadqueue.assert_called_with(subscriptions, num_workers=2, func_ref=mock_toggle_state_of_subscription,
                                            args=["activate"], task_wait_timeout=20 * 60)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "activate_deactivate_mtr_subscriptions_with_threads")
    def test_toggle_state_of_subscriptions__activated_successfully(
            self, mock_activate_deactivate_mtr_subscriptions_with_threads,
            mock_get_sub_file_action_enable_or_disable_command, mock_get_schedule_times, *_):
        subscriptions = [Mock(), Mock()]
        mock_get_sub_file_action_enable_or_disable_command.return_value = "Enable"
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 1, 52)
        mock_get_schedule_times.retun_value = [datetime.datetime(2019, 8, 22, 1, 52),
                                               datetime.datetime(2019, 8, 22, 3, 52),
                                               datetime.datetime(2019, 8, 22, 7, 52),
                                               datetime.datetime(2019, 8, 22, 9, 52),
                                               datetime.datetime(2019, 8, 22, 13, 52),
                                               datetime.datetime(2019, 8, 22, 15, 52),
                                               datetime.datetime(2019, 8, 22, 19, 52),
                                               datetime.datetime(2019, 8, 22, 21, 52)]
        self.profile.toggle_state_of_subscriptions(subscriptions)
        self.assertTrue(mock_activate_deactivate_mtr_subscriptions_with_threads.called)
        self.assertEqual(mock_get_sub_file_action_enable_or_disable_command.return_value, "Enable")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.keep_running",
           side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "activate_deactivate_mtr_subscriptions_with_threads")
    def test_toggle_state_of_subscriptions__deactivated_successfully(
            self, mock_activate_deactivate_mtr_subscriptions_with_threads,
            mock_get_sub_file_action_enable_or_disable_command, mock_get_schedule_times, *_):
        subscriptions = [Mock(), Mock()]
        mock_get_sub_file_action_enable_or_disable_command.side_effect = ["Enable", "Disable"]
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 3, 52)
        mock_get_schedule_times.retun_value = [datetime.datetime(2019, 8, 22, 1, 52),
                                               datetime.datetime(2019, 8, 22, 3, 52),
                                               datetime.datetime(2019, 8, 22, 7, 52),
                                               datetime.datetime(2019, 8, 22, 9, 52),
                                               datetime.datetime(2019, 8, 22, 13, 52),
                                               datetime.datetime(2019, 8, 22, 15, 52),
                                               datetime.datetime(2019, 8, 22, 19, 52),
                                               datetime.datetime(2019, 8, 22, 21, 52)]
        self.profile.toggle_state_of_subscriptions(subscriptions)
        self.assertTrue(mock_activate_deactivate_mtr_subscriptions_with_threads.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "activate_deactivate_mtr_subscriptions_with_threads")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_toggle_state_of_subscriptions__activation_failed(
            self, mock_exception, mock_activate_deactivate_mtr_subscriptions_with_threads, *_):
        subscriptions = [Mock(), Mock()]
        self.profile.toggle_state_of_subscriptions(subscriptions)
        mock_activate_deactivate_mtr_subscriptions_with_threads.side_Effect = Exception
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile."
           "activate_deactivate_mtr_subscriptions_with_threads")
    def test_toggle_state_of_subscriptions__deactivated_unsuccessfully(
            self, mock_activate_deactivate_mtr_subscriptions_with_threads,
            mock_get_sub_file_action_enable_or_disable_command, mock_get_schedule_times, *_):
        subscriptions = [Mock(), Mock()]
        mock_get_sub_file_action_enable_or_disable_command.return_value = "Disable"
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 3, 52)
        mock_get_schedule_times.retun_value = [datetime.datetime(2019, 8, 22, 1, 52),
                                               datetime.datetime(2019, 8, 22, 3, 52),
                                               datetime.datetime(2019, 8, 22, 7, 52),
                                               datetime.datetime(2019, 8, 22, 9, 52),
                                               datetime.datetime(2019, 8, 22, 13, 52),
                                               datetime.datetime(2019, 8, 22, 15, 52),
                                               datetime.datetime(2019, 8, 22, 19, 52),
                                               datetime.datetime(2019, 8, 22, 21, 52)]
        self.profile.toggle_state_of_subscriptions(subscriptions)
        self.assertFalse(mock_activate_deactivate_mtr_subscriptions_with_threads.called)
        self.assertEqual(mock_get_sub_file_action_enable_or_disable_command.return_value, "Disable")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.sleep")
    def test_toggle_state_of_subscription__is_successful_when_activate_called(self, mock_sleep):
        subscription = Mock()
        subscription.name = "subscription_0"
        toggle_state_of_subscription(subscription, "activate")
        self.assertTrue(subscription.activate.called)
        self.assertFalse(subscription.deactivate.called)
        self.assertFalse(mock_sleep.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.sleep")
    def test_toggle_state_of_subscription__sleep_called_depending_on_subscription_index(self, mock_sleep):
        subscription_0 = Mock()
        subscription_0.name = "subscription_0"
        subscription_4 = Mock()
        subscription_4.name = "subscription_4"
        subscription_8 = Mock()
        subscription_8.name = "subscription_8"

        toggle_state_of_subscription(subscription_0, "activate")
        self.assertFalse(mock_sleep.called)
        toggle_state_of_subscription(subscription_0, "deactivate")
        self.assertFalse(mock_sleep.called)
        toggle_state_of_subscription(subscription_4, "activate")
        mock_sleep.assert_called_with(10)
        toggle_state_of_subscription(subscription_4, "deactivate")
        mock_sleep.assert_called_with(10)
        toggle_state_of_subscription(subscription_8, "activate")
        mock_sleep.assert_called_with(20)
        toggle_state_of_subscription(subscription_8, "deactivate")
        mock_sleep.assert_called_with(20)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.sleep")
    def test_toggle_state_of_subscription__is_successful_when_deactivate_called(self, mock_sleep):
        subscription = Mock()
        subscription.name = "subscription_0"

        toggle_state_of_subscription(subscription, "deactivate")
        self.assertFalse(subscription.activate.called)
        self.assertTrue(subscription.deactivate.called)
        self.assertFalse(mock_sleep.called)

    @patch('enmutils_int.lib.workload.pm_78.PmMtrProfile.execute_flow')
    def test_run_in_pm_78__returns_none(self, *_):
        profile = PM_78()
        self.assertEqual(None, profile.run())

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.log.logger.debug")
    def test_get_msc_node_connected_bsc_nodes__is_success(self, mock_debug_log):
        self.profile.USER.enm_execute.return_value.get_output.return_value = [u'FDN : NetworkElement=M20B39',
                                                                              u'connectedMsc : NetworkElement=M20',
                                                                              u'', u'FDN : NetworkElement=M20B40',
                                                                              u'connectedMsc : NetworkElement=M20',
                                                                              u'', u'', u'2 instance(s)']
        actual_output = self.profile.get_msc_node_connected_bsc_nodes("M20")
        self.assertEqual(["M20B39", "M20B40"], actual_output)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.log.logger.debug")
    def test_get_msc_node_connected_bsc_nodes__if_bsc_nodes_not_found(self, mock_debug_log):
        self.profile.USER.enm_execute.return_value.get_output.return_value = [u'', u'0 instance(s)']
        actual_output = self.profile.get_msc_node_connected_bsc_nodes("M21")
        self.assertEqual([], actual_output)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.log.logger.debug")
    def test_get_msc_node_connected_bsc_nodes__if_getting_error_response(self, mock_debug_log):
        self.profile.USER.enm_execute.return_value.get_output.return_value = [u'', u"Error 4020 : Command syntax error,"
                                                                                   u" invalid character `'` at position"
                                                                                   u" 42",
                                                                              u'Suggested Solution : Enclose the values'
                                                                              u' containing invalid characters within '
                                                                              u'quotes.']

        actual_output = self.profile.get_msc_node_connected_bsc_nodes("M22")
        self.assertEqual([], actual_output)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_msc_node_connected_bsc_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.all_nodes_in_workload_pool")
    def test_check_whether_msc_nodes_cnctd_bsc_nodes_existed_in_workload_pool__is_success(
            self, mock_all_nodes, mock_get_msc_node_connected_bsc_nodes,
            mock_update_profile_persistence_nodes_list, mock_debug_log):
        nodes = [Mock(node_id="M20"), Mock(node_id="M21"), Mock(node_id="M22")]
        bsc_nodes = [Mock(node_id="MB20"), Mock(node_id="MB21"), Mock(node_id="MB22"), Mock(node_id="MB23")]
        mock_get_msc_node_connected_bsc_nodes.side_effect = [["MB20", "MB21"], ["MB22", "MB23"], []]
        mock_all_nodes.return_value = nodes + bsc_nodes
        self.profile.check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool(nodes)
        self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
        self.assertEqual(mock_all_nodes.call_count, 1)
        self.assertEqual(mock_get_msc_node_connected_bsc_nodes.call_count, 3)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.get_msc_node_connected_bsc_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile.PmMtrProfile.all_nodes_in_workload_pool")
    def test_check_whether_msc_nodes_cnctd_bsc_nodes_existed_in_workload_pool__if_bsc_node_existed_in_pool(
            self, mock_all_nodes, mock_get_msc_node_connected_bsc_nodes,
            mock_update_profile_persistence_nodes_list, mock_debug_log):
        nodes = [Mock(node_id="M20"), Mock(node_id="M21"), Mock(node_id="M22")]
        bsc_nodes = [Mock(node_id="MB20"), Mock(node_id="MB21")]
        mock_get_msc_node_connected_bsc_nodes.side_effect = [["MB20", "MB21"], ["MB22", "MB23"], []]
        mock_all_nodes.return_value = nodes + bsc_nodes
        self.profile.check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool(nodes)
        self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
        self.assertEqual(mock_all_nodes.call_count, 1)
        self.assertEqual(mock_get_msc_node_connected_bsc_nodes.call_count, 3)
        self.assertEqual(mock_debug_log.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
