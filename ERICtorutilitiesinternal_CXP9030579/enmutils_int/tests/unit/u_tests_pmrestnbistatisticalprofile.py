#!/usr/bin/env python
import unittest2

from enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile import (PmStatisticalProfile,
                                                                                 toggle_subscription_action_on_node,
                                                                                 toggle_subscription_action_on_nodes)
from enmutils_int.lib.workload import (pm_rest_nbi_01, pm_rest_nbi_02)
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils

DEFAULT_CRITERIA = [
    {"name": "PmStatisticalProfile_cbs_subscription", "criteriaIdString": "select networkelement where neType = ERBS"}]


class PmStatisticalProfileUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

        self.profile_offset = 6 * 60 * 60  # 6 Hour offset

        self.profile = PmStatisticalProfile()
        self.profile.USER_ROLES = ['TestRole']
        self.profile.USER = Mock()
        self.profile.SCHEDULE_SLEEP = 10
        self.profile.WAIT_TIME = 5
        self.profile.OFFSET = self.profile_offset

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "delete_nodes_from_netex_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.StatisticalSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription_object")
    def test_create_statistical_subscription__successful(
            self, mock_create_statistical_subscription_object, *_):
        nodes = [Mock()]
        mock_subscription = Mock(id="999", poll_scanners=True, nodes=nodes)
        mock_subscription.name = "sub_name"
        mock_subscription.node_types = ["RadioNode"]
        mock_create_statistical_subscription_object.return_value = mock_subscription
        profile = PmStatisticalProfile()
        self.assertEqual(mock_subscription, profile.create_statistical_subscription(999, nodes))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__successful(
            self, mock_statisticalsubscription, mock_set_values_from_cbs, *_):

        profile = PmStatisticalProfile()
        profile.POLL_SCANNERS = True
        profile.USER = "user_123"
        profile.NUM_COUNTERS = 5
        profile.MO_CLASS_COUNTERS_EXCLUDED = "ABC"
        profile.TECHNOLOGY_DOMAIN_COUNTER_LIMITS = "XYZ"
        profile.MO_CLASS_COUNTERS_INCLUDED = "DEF"
        profile.MO_CLASS_SUB_COUNTERS_INCLUDED = {"DEF": ["xyz"]}
        profile.RESERVED_COUNTERS = 99
        profile.NUM_NODES = {"ERBS": -1}

        criteria, _ = Mock(), [Mock]
        mock_set_values_from_cbs.return_value = False, criteria

        self.assertEqual(mock_statisticalsubscription.return_value,
                         profile.create_statistical_subscription_object("11", [Mock()]))
        self.assertEqual(mock_set_values_from_cbs.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__if_cbs_true(
            self, mock_statisticalsubscription, mock_set_values_from_cbs, *_):

        profile = PmStatisticalProfile()
        profile.POLL_SCANNERS = True
        profile.USER = "user_123"
        profile.NUM_COUNTERS = 5
        profile.MO_CLASS_COUNTERS_EXCLUDED = "ABC"
        profile.TECHNOLOGY_DOMAIN_COUNTER_LIMITS = "XYZ"
        profile.MO_CLASS_COUNTERS_INCLUDED = "DEF"
        profile.MO_CLASS_SUB_COUNTERS_INCLUDED = {"DEF": ["xyz"]}
        profile.RESERVED_COUNTERS = 99
        profile.NUM_NODES = {"ERBS": -1}

        criteria, _ = Mock(), [Mock]
        mock_set_values_from_cbs.return_value = True, criteria
        self.assertEqual(mock_statisticalsubscription.return_value,
                         profile.create_statistical_subscription_object("11", [Mock()]))
        self.assertEqual(mock_set_values_from_cbs.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__successful_if_definer_is_not_none(
            self, mock_statisticalsubscription, mock_set_values_from_cbs, *_):

        profile = PmStatisticalProfile()
        profile.POLL_SCANNERS = True
        profile.USER = "user_123"
        profile.NUM_COUNTERS = 5
        profile.MO_CLASS_COUNTERS_EXCLUDED = "ABC"
        profile.TECHNOLOGY_DOMAIN_COUNTER_LIMITS = "XYZ"
        profile.MO_CLASS_COUNTERS_INCLUDED = "DEF"
        profile.MO_CLASS_SUB_COUNTERS_INCLUDED = {"DEF": ["xyz"]}
        profile.DEFINER = "STATISTICAL_SubscriptionAttributes"
        profile.RESERVED_COUNTERS = 99
        profile.NUM_NODES = {"ERBS": -1}

        criteria, _ = Mock(), [Mock]
        mock_set_values_from_cbs.return_value = False, criteria
        self.assertEqual(mock_statisticalsubscription.return_value,
                         profile.create_statistical_subscription_object("11", [Mock()]))
        self.assertEqual(mock_set_values_from_cbs.call_count, 1)

    # execute_flow tests
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.'
           'toggle_subscription_action_on_nodes')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_rest_nbi_subscriptions")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_execute_flow__no_error_thrown_when_user_stats_subscription_created_and_activated_fornbi_01(
            self, mock_add_exception, *_):
        self.profile.NAME = "PM_REST_NBI_01"
        self.profile.execute_flow(operations=["create", "activate", "deactivate", "delete"])
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.'
           'toggle_subscription_action_on_nodes')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_rest_nbi_subscriptions")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_execute_flow__no_error_thrown_when_user_stats_subscription_created_and_activated_fornbi_02(
            self, mock_add_exception, *_):
        self.profile.NAME = "PM_REST_NBI_02"
        self.profile.execute_flow(operations=[])
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.'
           'toggle_subscription_action_on_nodes')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_rest_nbi_subscriptions")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_execute_flow__no_error_thrown_when_user_stats_subscription_created_and_activated_fornbi_03(
            self, mock_add_exception, *_):
        self.profile.NAME = "PM_REST_NBI_03"
        self.profile.execute_flow(operations=[])
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.state",
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_rest_nbi_subscriptions")
    def test_execute_flow__exception_thrown_during_subscription_creation(
            self, mock_create_rest_nbi_subscriptions, mock_add_exception, *_):
        mock_create_rest_nbi_subscriptions.side_effect = [Exception("Subscription not created")]
        self.profile.execute_flow()
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmSubscriptionProfile.execute_flow',
           side_effect=[Exception("Subscription not activated")])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_rest_nbi_subscriptions")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_execute_flow__exception_thrown_during_subscription_activation(
            self, mock_add_exception, *_):
        self.profile.execute_flow()
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'check_all_nodes_added_to_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'set_teardown')
    def test_toggle_subscription_action_on_node__if_action_is_create(self, mock_set_teardown,
                                                                     mock_check_all_nodes_added_to_subscription):
        toggle_subscription_action_on_node(Mock(), "create", self.profile)
        self.assertTrue(mock_set_teardown.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'check_all_nodes_added_to_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'set_teardown')
    def test_toggle_subscription_action_on_node__if_action_is_activate(self, mock_set_teardown,
                                                                       mock_check_all_nodes_added_to_subscription):
        toggle_subscription_action_on_node(Mock(), "activate", self.profile)
        self.assertFalse(mock_set_teardown.called)
        self.assertFalse(mock_check_all_nodes_added_to_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'check_all_nodes_added_to_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'set_teardown')
    def test_toggle_subscription_action_on_node__if_action_is_deactivate(self, mock_set_teardown,
                                                                         mock_check_all_nodes_added_to_subscription):
        toggle_subscription_action_on_node(Mock(), "deactivate", self.profile)
        self.assertFalse(mock_set_teardown.called)
        self.assertFalse(mock_check_all_nodes_added_to_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'check_all_nodes_added_to_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'set_teardown')
    def test_toggle_subscription_action_on_node__if_action_is_wrong(self, mock_set_teardown,
                                                                    mock_check_all_nodes_added_to_subscription):
        toggle_subscription_action_on_node(Mock(), "test", self.profile)
        self.assertFalse(mock_set_teardown.called)
        self.assertFalse(mock_check_all_nodes_added_to_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'check_all_nodes_added_to_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'set_teardown')
    def test_toggle_subscription_action_on_node__if_action_is_delete(self, mock_set_teardown,
                                                                     mock_check_all_nodes_added_to_subscription):
        toggle_subscription_action_on_node(Mock(), "delete", self.profile)
        self.assertFalse(mock_set_teardown.called)
        self.assertFalse(mock_check_all_nodes_added_to_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.'
           'toggle_subscription_action_on_nodes')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_pm_rest_nbi_create_sub_operations(self, mock_add_exception, mock_create_single_process_and_execute_task, _):
        mock_create_single_process_and_execute_task.side_effect = [Exception("Subscription not created")]
        self.profile.pm_rest_nbi_create_sub_operations([Mock()], ["create", "activate"])
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.'
           'toggle_subscription_action_on_nodes')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.'
           'add_error_as_exception')
    def test_pm_rest_nbi_delete_sub_operations(self, mock_add_exception, mock_create_single_process_and_execute_task, _):
        mock_create_single_process_and_execute_task.side_effect = [Exception("Subscription not created")]
        self.profile.pm_rest_nbi_delete_sub_operations([Mock()], ["delete", "deactivate"])
        self.assertTrue(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.multitasking."
           "create_single_process_and_execute_task")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.ThreadQueue")
    def test_toggle_subscription_action_on_nodes__is_successful(self, *_):
        toggle_subscription_action_on_nodes(self.profile, 'create', [Mock()])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription", side_effect=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "get_nodes_list_by_attribute", return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    def test_create_rest_nbi_subscriptions__is_successful(self, mock_debug_log, *_):
        self.profile.SUBSCRIPTION_COUNT = 2
        self.profile.create_rest_nbi_subscriptions()
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription", side_effect=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "get_nodes_list_by_attribute", return_value=10 * [Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    def test_create_rest_nbi_subscriptions__if_subs_count_is_less_than_nodes_count(self, mock_debug_log, *_):
        self.profile.SUBSCRIPTION_COUNT = 2
        self.profile.create_rest_nbi_subscriptions()
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription", side_effect=6 * [Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "get_nodes_list_by_attribute", return_value=5 * [Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    def test_create_rest_nbi_subscriptions__if_subs_count_is_greater_than_nodes_count(self, mock_debug_log, *_):
        self.profile.SUBSCRIPTION_COUNT = 6
        self.profile.create_rest_nbi_subscriptions()
        self.assertEqual(mock_debug_log.call_count, 10)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription", side_effect=[Exception("Error")])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "get_nodes_list_by_attribute", return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.log.logger.debug")
    def test_create_rest_nbi_subscriptions__if_create_subscription_is_failed(self, mock_debug_log, mock_add_error, *_):
        self.profile.SUBSCRIPTION_COUNT = 2
        self.profile.create_rest_nbi_subscriptions()
        self.assertEqual(mock_debug_log.call_count, 8)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__is_successful_for_pm_rest_nbi_01(self, mock_flow):
        pm_rest_nbi_01.PM_REST_NBI_01().run()
        self.assertEqual(mock_flow.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__is_successful_for_pm_rest_nbi_02(self, mock_flow):
        pm_rest_nbi_02.PM_REST_NBI_02().run()
        self.assertEqual(mock_flow.call_count, 1)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
