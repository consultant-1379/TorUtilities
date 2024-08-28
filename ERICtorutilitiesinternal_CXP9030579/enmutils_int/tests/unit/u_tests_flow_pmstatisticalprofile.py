#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError

from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile
from enmutils_int.lib.workload import (pm_02, pm_11, pm_25, pm_27, pm_30, pm_31, pm_32, pm_38, pm_48, pm_50, pm_54,
                                       pm_55, pm_56, pm_58, pm_59, pm_60, pm_62, pm_63, pm_64, pm_65, pm_66, pm_70,
                                       pm_82, pm_83, pm_84, pm_85, pm_88, pm_89, pm_90, pm_91, pm_92, pm_93, pm_94,
                                       pm_95, pm_96, pm_97, pm_98, pm_99, pm_100, pm_102, pm_103, pm_104)
from mock import patch, Mock, PropertyMock, call
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
        self.profile.OFFSET = self.profile_offset

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delete_nodes_from_netex_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription_object")
    def test_create_statistical_subscription__successful(
            self, mock_create_statistical_subscription_object, mock_set_teardown,
            mock_check_all_nodes_added_to_subscription, mock_statisticalsubscription, *_):
        mock_subscription = Mock(id="999", poll_scanners=True, nodes=[Mock()])
        mock_subscription.name = "sub_name"
        mock_subscription.node_types = ["RadioNode"]
        mock_create_statistical_subscription_object.return_value = mock_subscription

        profile = PmStatisticalProfile()
        self.assertEqual(mock_subscription, profile.create_statistical_subscription())
        self.assertTrue(mock_subscription.create.called)
        mock_set_teardown.assert_called_with(mock_statisticalsubscription, "sub_name", "999", True,
                                             node_types=mock_subscription.node_types)
        mock_check_all_nodes_added_to_subscription.assert_called_with(mock_subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__successful(
            self, mock_statisticalsubscription, mock_get_profile_nodes, mock_set_values_from_cbs, *_):

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

        criteria, nodes = Mock(), [Mock]
        mock_get_profile_nodes.return_value = nodes
        mock_set_values_from_cbs.return_value = False, criteria

        self.assertEqual(mock_statisticalsubscription.return_value, profile.create_statistical_subscription_object())

        mock_statisticalsubscription.assert_called_with(
            name="PM_01-1234567", cbs=False, description="some_desc", user="user_123", poll_scanners=True,
            nodes=nodes, rop_enum='FIFTEEN_MIN', num_counters=5, mo_class_counters_excluded="ABC",
            criteria_specification=criteria, technology_domain_counter_limits="XYZ",
            mo_class_counters_included="DEF", mo_class_sub_counters_included={"DEF": ["xyz"]},
            reserved_counters=99, node_types=profile.NUM_NODES.keys(), definer=None)
        mock_get_profile_nodes.assert_called_with(cbs=False)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__if_cbs_true(
            self, mock_statisticalsubscription, mock_get_profile_nodes, mock_set_values_from_cbs, *_):

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

        criteria, nodes = Mock(), [Mock]
        mock_get_profile_nodes.return_value = nodes
        mock_set_values_from_cbs.return_value = True, criteria

        self.assertEqual(mock_statisticalsubscription.return_value, profile.create_statistical_subscription_object())

        mock_statisticalsubscription.assert_called_with(
            name="PM_01-1234567", cbs=True, description="some_desc", user="user_123", poll_scanners=True,
            nodes=nodes, rop_enum='FIFTEEN_MIN', num_counters=5, mo_class_counters_excluded="ABC",
            criteria_specification=criteria, technology_domain_counter_limits="XYZ",
            mo_class_counters_included="DEF", mo_class_sub_counters_included={"DEF": ["xyz"]},
            reserved_counters=99, node_types=profile.NUM_NODES.keys(), definer=None)
        mock_get_profile_nodes.assert_called_with(cbs=True)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.identifier",
           new_callable=PropertyMock, return_value="PM_01-1234567")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription")
    def test_create_statistical_subscription_object__successful_if_definer_is_not_none(
            self, mock_statisticalsubscription, mock_get_profile_nodes, mock_set_values_from_cbs, *_):

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

        criteria, nodes = Mock(), [Mock]
        mock_get_profile_nodes.return_value = nodes
        mock_set_values_from_cbs.return_value = False, criteria

        self.assertEqual(mock_statisticalsubscription.return_value, profile.create_statistical_subscription_object())

        mock_statisticalsubscription.assert_called_with(
            name="PM_01-1234567", cbs=False, description="some_desc", user="user_123", poll_scanners=True,
            nodes=nodes, rop_enum='FIFTEEN_MIN', num_counters=5, mo_class_counters_excluded="ABC",
            criteria_specification=criteria, technology_domain_counter_limits="XYZ",
            mo_class_counters_included="DEF", mo_class_sub_counters_included={"DEF": ["xyz"]},
            reserved_counters=99, node_types=profile.NUM_NODES.keys(), definer="STATISTICAL_SubscriptionAttributes")
        mock_get_profile_nodes.assert_called_with(cbs=False)

    # check_statistical_system_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    def test_check_statistical_system_subscription__is_successful(self, mock_check_system_sub_activation, *_):
        self.profile.SYS_DEF_SUB_PATTERN = 'some subscription pattern'
        self.profile.check_statistical_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.USER)
        self.assertTrue(mock_check_system_sub_activation.called)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_flow__no_error_thrown_when_user_stats_subscription_created_and_activated(
            self, mock_subscription, mock_add_exception, mock_teardown_append, *_):

        subscription = mock_subscription.return_value = Mock()
        self.profile.NAME = "PM_38"
        self.profile.execute_flow()
        self.assertTrue(subscription.activate.called)
        self.assertFalse(mock_add_exception.called)
        self.assertEqual(mock_teardown_append.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_flow__if_profile_name_is_pm_32(
            self, mock_subscription, mock_add_exception, *_):
        subscription = mock_subscription.return_value = Mock()
        self.profile.NAME = "PM_32"
        self.profile.execute_flow()
        self.assertTrue(subscription.activate.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmSubscriptionProfile."
           "delete_nodes_from_netex_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_flow__exception_thrown_during_subscription_creation(
            self, mock_create_statistical_subscription, mock_add_exception, mock_debug, *_):
        mock_create_statistical_subscription.side_effect = Exception("Subscription not created")

        self.profile.execute_flow()
        self.assertFalse(mock_debug.called)
        self.assertTrue(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".execute_additional_pm_profile_tasks")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.persist')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.'
           'set_subscription_description')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmSubscriptionProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.Subscription.get_system_subscription_name_by_pattern')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.Subscription.activate')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmSubscriptionProfile.'
           'check_system_subscription_activation')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.StatisticalSubscription')
    def test_execute_flow__no_exception_thrown_when_system_subscription_exists_and_is_active(
            self, mock_subscription, mock_check, mock_add_exception, mock_activate, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "CCTR"
        subscription = mock_subscription.return_value = Mock()

        subscription_data = [
            {"id": "666", "name": "ContinuousCellTraceSubscription", "nextVersionName": "null",
             "prevVersionName": "null", "owner": "PMIC",
             "description": "Continuous Cell Trace (CCTR) System Defined Subscription",
             "userType": "SYSTEM_DEF", "type": "CONTINUOUSCELLTRACE"}]

        self.profile.USER.get.return_value.ok = 1
        self.profile.USER.get.return_value.json.return_value = subscription_data

        self.profile.execute_flow()
        self.assertTrue(mock_check.called_with(subscription))
        self.assertFalse(mock_activate.called)
        self.assertFalse(mock_add_exception.called)

    # Test profiles that call run() method which in turn call execute_offset_flow with some parameters

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_offset_flow")
    def test_run__in_pm_profiles_that_call_execute_offset_flow_is_successful(self, _):

        profile = pm_11.PM_11()
        profile.run()
        profile = pm_48.PM_48()
        profile.run()

    # tests that cover execute_offset_flow

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delay_execution_until_other_profile_started")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_offset_flow__is_successful(
            self, mock_create_statistical_subscription, mock_keep_running, mock_add_error_as_exception,
            mock_sleep, mock_teardown_append, *_):
        subscription = mock_create_statistical_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{'administrationState': 'INACTIVE'},
                                                     {'administrationState': 'ACTIVE'}]
        self.profile.NAME = "PM_48"
        mock_keep_running.side_effect = [True, True, False]

        self.profile.execute_offset_flow(profile_to_wait_for="blah")
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertEqual(mock_teardown_append.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delay_execution_until_other_profile_started")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_offset_flow__if_profile_name_is_pm_42(
            self, mock_create_statistical_subscription, mock_keep_running, mock_add_error_as_exception,
            mock_sleep, *_):
        subscription = mock_create_statistical_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{'administrationState': 'INACTIVE'},
                                                     {'administrationState': 'ACTIVE'}]
        self.profile.NAME = "PM_42"
        mock_keep_running.side_effect = [True, True, False]

        self.profile.execute_offset_flow(profile_to_wait_for="blah")
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "delete_nodes_from_netex_attribute")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delay_execution_until_other_profile_started")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_offset_flow__generates_errors_if_sub_not_created(
            self, mock_create_statistical_subscription, mock_keep_running, mock_add_error_as_exception,
            mock_sleep, *_):
        mock_create_statistical_subscription.side_effect = Exception

        mock_keep_running.side_effect = [True, False]

        self.profile.execute_offset_flow(profile_to_wait_for="blah")
        self.assertFalse(mock_keep_running.called)
        self.assertEqual(1, mock_add_error_as_exception.call_count)
        self.assertFalse(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delay_execution_until_other_profile_started")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_offset_flow__generates_errors_if_sub_created_but_activate_raises_exception(
            self, mock_create_statistical_subscription, mock_keep_running, mock_add_error_as_exception,
            mock_sleep, mock_teardown_append, *_):
        subscription = mock_create_statistical_subscription.return_value = Mock()
        self.profile.NAME = "PM_48"
        subscription.get_subscription.return_value = {'administrationState': 'INACTIVE'}
        subscription.activate.side_effect = Exception()

        mock_keep_running.side_effect = [True, False]

        self.profile.execute_offset_flow(profile_to_wait_for="blah")

        self.assertEqual(1, mock_add_error_as_exception.call_count)
        self.assertEqual(1, mock_sleep.call_count)
        self.assertTrue(subscription.activate.called)
        self.assertFalse(subscription.deactivate.called)
        self.assertEqual(mock_teardown_append.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "delay_execution_until_other_profile_started")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_statistical_subscription")
    def test_execute_offset_flow__generates_errors_if_sub_created_but_state_is_activating_or_deactivating(
            self, mock_create_statistical_subscription, mock_keep_running, mock_add_error_as_exception,
            mock_sleep, mock_teardown_append, *_):
        subscription = mock_create_statistical_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{'administrationState': 'DEACTIVATING'},
                                                     {'administrationState': 'ACTIVATING'}]
        self.profile.NAME = "PM_48"
        mock_keep_running.side_effect = [True, True, False]

        self.profile.execute_offset_flow(profile_to_wait_for="blah")

        self.assertEqual(2, mock_add_error_as_exception.call_count)
        self.assertEqual(2, mock_sleep.call_count)
        self.assertFalse(subscription.activate.called)
        self.assertFalse(subscription.deactivate.called)
        self.assertEqual(mock_teardown_append.call_count, 1)

    # support functions that are used by execute_offset_flow

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.get_start_time_of_profile')
    def test_delay_execution_until_other_profile_started__sleep_if_other_profile_not_running_longer_than_wait_time(
            self, mock_start_time, mock_time_sleep, *_):
        profile_to_wait_for = "PM_02"

        number_of_hours_ago = 2
        mock_start_time.return_value = (datetime.now() -
                                        timedelta(seconds=(number_of_hours_ago * 60 * 60)))

        self.profile.delay_execution_until_other_profile_started(profile_to_wait_for, self.profile_offset)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.get_start_time_of_profile')
    def test_delay_execution_until_other_profile_started__no_sleep_if_other_profile_running_longer_than_wait_time(
            self, mock_start_time, mock_time_sleep, *_):
        profile_to_wait_for = "PM_02"

        number_of_hours_ago = 10
        mock_start_time.return_value = (datetime.now() -
                                        timedelta(seconds=(number_of_hours_ago * 60 * 60)))

        self.profile.delay_execution_until_other_profile_started(profile_to_wait_for, self.profile_offset)
        self.assertFalse(mock_time_sleep.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.load_mgr.get_start_time_of_profile')
    def test_delay_execution_until_other_profile_started__no_sleep_if_other_profile_not_running(
            self, mock_start_time, mock_time_sleep, *_):
        profile_to_wait_for = "PM_02"

        mock_start_time.return_value = None
        self.profile.delay_execution_until_other_profile_started(profile_to_wait_for, self.profile_offset)
        self.assertFalse(mock_time_sleep.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".configure_smrs_upload_on_sbg_is_nodes")
    def test_execute_additional_pm_profile_tasks__wont_do_anything_if_profile_doesnt_use_sbg_is_nodes(
            self, mock_configure_smrs_upload_on_sbg_is_nodes):
        self.profile.NUM_NODES = {'ERBS': 1}
        self.profile.execute_additional_pm_profile_tasks()
        self.assertFalse(mock_configure_smrs_upload_on_sbg_is_nodes.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".configure_smrs_upload_on_sbg_is_nodes")
    def test_execute_additional_pm_profile_tasks__wont_do_anything_if_profile_doesnt_have_num_nodes(
            self, mock_configure_smrs_upload_on_sbg_is_nodes):
        self.profile.execute_additional_pm_profile_tasks()
        self.assertFalse(mock_configure_smrs_upload_on_sbg_is_nodes.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".disable_pm_on_sbg_is_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".configure_smrs_upload_on_sbg_is_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile"
           ".all_nodes_in_workload_pool")
    def test_execute_additional_pm_profile_tasks__calls_configure_smrs_upload_if_profile_uses_sbg_is_nodes(
            self, mock_all_nodes_in_workload_pool, mock_configure_smrs_upload_on_sbg_is_nodes,
            mock_disable_pm_on_sbg_is_nodes, mock_picklable_boundmethod, mock_partial):
        self.profile.NUM_NODES = {'SBG-IS': -1}
        nodes = [Mock()]
        mock_all_nodes_in_workload_pool.return_value = nodes
        self.profile.execute_additional_pm_profile_tasks()

        mock_configure_smrs_upload_on_sbg_is_nodes.assert_called_with(nodes)
        mock_disable_pm_on_sbg_is_nodes.assert_called_with(nodes)
        mock_picklable_boundmethod.assert_called_with(mock_disable_pm_on_sbg_is_nodes)
        mock_partial.assert_called_with(mock_picklable_boundmethod.return_value)
        self.assertEqual([mock_partial.return_value], self.profile.teardown_list)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "disable_pm_on_sbg_is_node")
    def test_disable_pm_on_sbg_is_nodes__successful_if_nodes_specified(
            self, mock_disable_pm_on_sbg_is_node, mock_all_nodes_in_workload_pool, mock_create_and_execute_threads):
        nodes = [Mock(), Mock()]

        self.profile.disable_pm_on_sbg_is_nodes(nodes)

        mock_create_and_execute_threads.assert_called_with(nodes, 2, func_ref=mock_disable_pm_on_sbg_is_node,
                                                           args=[self.profile])
        self.assertFalse(mock_all_nodes_in_workload_pool.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "disable_pm_on_sbg_is_node")
    def test_disable_pm_on_sbg_is_nodes__successful_if_nodes_not_specified(
            self, mock_disable_pm_on_sbg_is_node, mock_all_nodes_in_workload_pool, mock_create_and_execute_threads):
        nodes = [Mock(), Mock()]
        mock_all_nodes_in_workload_pool.return_value = nodes
        self.profile.disable_pm_on_sbg_is_nodes()

        mock_create_and_execute_threads.assert_called_with(nodes, 2, func_ref=mock_disable_pm_on_sbg_is_node,
                                                           args=[self.profile])
        self.assertTrue(mock_all_nodes_in_workload_pool.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "enable_pm_on_sbg_is_node")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.get_smrs_sftp_password")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.get_cm_vip_ipaddress")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "create_and_execute_threads")
    def test_configure_smrs_upload_on_sbg_is_nodes__is_successful(
            self, mock_create_and_execute_threads, mock_get_cm_vip_ipaddress, mock_get_smrs_sftp_password,
            mock_enable_pm_on_sbg_is_node):
        nodes_list = [Mock(), Mock()]
        mock_get_smrs_sftp_password.return_value = "some_password"
        mock_get_cm_vip_ipaddress.return_value = "some_ip_address"
        self.profile.configure_smrs_upload_on_sbg_is_nodes(nodes_list)
        mock_create_and_execute_threads.assert_called_with(nodes_list, 2, func_ref=mock_enable_pm_on_sbg_is_node,
                                                           args=[self.profile, "some_ip_address", "some_password"])

    def test_get_smrs_sftp_password__is_successful(self):
        password = u'some_password'
        enm_reponse_output = [u'Password', password, u'', u'Command Executed Successfully']
        self.profile.USER.enm_execute.return_value.get_output.return_value = enm_reponse_output
        self.assertEqual(password, self.profile.get_smrs_sftp_password("SBG-IS"))

    def test_get_smrs_sftp_password__raises_enmapplicationerror_if_enm_execute_throws_exception(self):
        self.profile.USER.enm_execute.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.profile.get_smrs_sftp_password, "SBG-IS")

    def test_get_smrs_sftp_password__raises_enmapplicationerror_if_password_not_set(self):
        password = u''
        enm_reponse_output = [u'Password', password, u'', u'Command Executed Successfully']
        self.profile.USER.enm_execute.return_value.get_output.return_value = enm_reponse_output
        self.assertRaises(EnmApplicationError, self.profile.get_smrs_sftp_password, "SBG-IS")

    def test_get_smrs_sftp_password__raises_enmapplicationerror_if_output_not_in_correct_format(self):
        enm_reponse_output = [u'', u'Command Executed Unsuccessfully']
        self.profile.USER.enm_execute.return_value.get_output.return_value = enm_reponse_output
        self.assertRaises(EnmApplicationError, self.profile.get_smrs_sftp_password, "SBG-IS")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_values_from_global_properties")
    def test_get_cm_vip_ipaddress__is_successful_if_enm_cloud_native(self, mock_get_values_from_global_properties,
                                                                     mock_get_cloud_native_service_vip, *_):
        ip_address = "some_ip_address"

        mock_get_cloud_native_service_vip.return_value = ip_address
        self.assertEqual(ip_address, self.profile.get_cm_vip_ipaddress())
        self.assertFalse(mock_get_values_from_global_properties.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_values_from_global_properties")
    def test_get_cm_vip_ipaddress__is_successful_if_enm_cloud_or_physical(self, mock_get_values_from_global_properties,
                                                                          mock_get_cloud_native_service_vip,
                                                                          mock_debug_log, *_):
        ip_address = "some_ip_address"

        mock_get_values_from_global_properties.return_value = [ip_address]
        self.assertEqual(ip_address, self.profile.get_cm_vip_ipaddress())
        self.assertFalse(mock_get_cloud_native_service_vip.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_values_from_global_properties")
    def test_get_cm_vip_ipaddress__raises_enmapplicationerror_if_cloud_native_enm_not_giving_correct_response(
            self, mock_get_values_from_global_properties, mock_get_cloud_native_service_vip, *_):
        mock_get_cloud_native_service_vip.return_value = []
        self.assertRaises(EnmApplicationError, self.profile.get_cm_vip_ipaddress)
        self.assertFalse(mock_get_values_from_global_properties.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_cloud_native_service_vip")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.get_values_from_global_properties")
    def test_get_cm_vip_ipaddress__raises_enmapplicationerror_if_cloud_or_physical_enm_not_giving_correct_response(
            self, mock_get_values_from_global_properties, mock_get_cloud_native_service_vip, mock_debug_log, *_):
        mock_get_values_from_global_properties.return_value = []
        self.assertRaises(EnmApplicationError, self.profile.get_cm_vip_ipaddress)
        self.assertFalse(mock_get_cloud_native_service_vip.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "get_node_pmdata_status")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "execute_netsim_command_on_netsim_node", return_value=True)
    def test_enable_pm_on_sbg_is_node__returns_true_if_operation_successful(
            self, mock_execute_netsim_command_on_netsim_node, mock_get_node_pmdata_status):
        node = Mock(node_id="some_node")
        cm_vip_ip_address = "some_ip_address"
        smrs_sftp_password = "some_password"
        resume_cmd = ("resumePMMeasurements "
                      "Sftp://m2m-sbg-is-pm:some_password@some_ip_address/smrsroot/pm/sbg-is/some_node/ 900 900")

        self.assertTrue(self.profile.enable_pm_on_sbg_is_node(node, self.profile, cm_vip_ip_address,
                                                              smrs_sftp_password))

        self.assertTrue(call([node], "pmdata:enable;") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertTrue(call([node], resume_cmd) in mock_execute_netsim_command_on_netsim_node.mock_calls)
        mock_get_node_pmdata_status.assert_called_with(node, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "get_node_pmdata_status")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "execute_netsim_command_on_netsim_node", side_effect=[True, False])
    def test_enable_pm_on_sbg_is_node__raises_environerror_if_operation_unsuccessful(
            self, mock_execute_netsim_command_on_netsim_node, mock_get_node_pmdata_status):
        node = Mock(node_id="some_node")
        cm_vip_ip_address = "some_ip_address"
        smrs_sftp_password = "some_password"
        resume_cmd = ("resumePMMeasurements "
                      "Sftp://m2m-sbg-is-pm:some_password@some_ip_address/smrsroot/pm/sbg-is/some_node/ 900 900")

        self.assertRaises(EnvironError, self.profile.enable_pm_on_sbg_is_node, node, self.profile,
                          cm_vip_ip_address, smrs_sftp_password)

        self.assertTrue(call([node], "pmdata:enable;") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertTrue(call([node], resume_cmd) in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertFalse(mock_get_node_pmdata_status.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "get_node_pmdata_status")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "execute_netsim_command_on_netsim_node", return_value=True)
    def test_disable_pm_on_sbg_is_node__successful(self, mock_execute_netsim_command_on_netsim_node,
                                                   mock_get_node_pmdata_status):
        node = Mock()
        self.profile.disable_pm_on_sbg_is_node(node, self.profile)
        self.assertTrue(call([node], "suspendPMMeasurements") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertTrue(call([node], "pmdata:disable;") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        mock_get_node_pmdata_status.assert_called_with(node, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "execute_netsim_command_on_netsim_node", return_value=True)
    def test_get_node_pmdata_status__is_successful(self, mock_execute_netsim_command_on_netsim_node, mock_debug_log):
        node = Mock()
        self.assertEqual(True, self.profile.get_node_pmdata_status(node, self.profile))
        self.assertTrue(call([node], "pmdata:status;") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile."
           "execute_netsim_command_on_netsim_node", return_value=False)
    def test_get_node_pmdata_status__is_failed(self, mock_execute_netsim_command_on_netsim_node, mock_debug_log):
        node = Mock()
        self.assertEqual(False, self.profile.get_node_pmdata_status(node, self.profile))
        self.assertTrue(call([node], "pmdata:status;") in mock_execute_netsim_command_on_netsim_node.mock_calls)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_02.PM_02()
        profile.run()
        profile = pm_25.PM_25()
        profile.run()
        profile = pm_27.PM_27()
        profile.run()
        profile = pm_30.PM_30()
        profile.run()
        profile = pm_31.PM_31()
        profile.run()
        profile = pm_32.PM_32()
        profile.run()
        profile = pm_38.PM_38()
        profile.run()
        profile = pm_50.PM_50()
        profile.run()
        profile = pm_54.PM_54()
        profile.run()
        self.assertEqual(mock_flow.call_count, 9)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__2_in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_55.PM_55()
        profile.run()
        profile = pm_56.PM_56()
        profile.run()
        profile = pm_58.PM_58()
        profile.run()
        profile = pm_59.PM_59()
        profile.run()
        profile = pm_60.PM_60()
        profile.run()
        profile = pm_62.PM_62()
        profile.run()
        profile = pm_63.PM_63()
        profile.run()
        profile = pm_64.PM_64()
        profile.run()
        profile = pm_65.PM_65()
        profile.run()
        self.assertEqual(mock_flow.call_count, 9)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__3_in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_66.PM_66()
        profile.run()
        profile = pm_70.PM_70()
        profile.run()
        profile = pm_82.PM_82()
        profile.run()
        profile = pm_83.PM_83()
        profile.run()
        profile = pm_84.PM_84()
        profile.run()
        profile = pm_85.PM_85()
        profile.run()
        profile = pm_88.PM_88()
        profile.run()
        profile = pm_89.PM_89()
        profile.run()
        profile = pm_90.PM_90()
        profile.run()
        self.assertEqual(mock_flow.call_count, 9)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__4_in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_91.PM_91()
        profile.run()
        profile = pm_92.PM_92()
        profile.run()
        profile = pm_93.PM_93()
        profile.run()
        profile = pm_94.PM_94()
        profile.run()
        profile = pm_95.PM_95()
        profile.run()
        profile = pm_96.PM_96()
        profile.run()
        profile = pm_97.PM_97()
        profile.run()
        profile = pm_98.PM_98()
        profile.run()
        profile = pm_99.PM_99()
        profile.run()
        profile = pm_100.PM_100()
        profile.run()
        self.assertEqual(mock_flow.call_count, 10)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile.PmStatisticalProfile.execute_flow')
    def test_run__5_in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_102.PM_102()
        profile.run()
        profile = pm_103.PM_103()
        profile.run()
        profile = pm_104.PM_104()
        profile.run()
        self.assertEqual(mock_flow.call_count, 3)

    def test_pm_profiles__if_cbs_profile_has_network_explorer_administrator_user_role_existed_or_not(self):
        profiles = ["PM_02", "PM_25", "PM_32", "PM_38", "PM_40", "PM_50", "PM_54", "PM_55", "PM_61", "PM_62",
                    "PM_63", "PM_64", "PM_65", "PM_66", "PM_67", "PM_69", "PM_71", "PM_72", "PM_74", "PM_75",
                    "PM_76", "PM_82", "PM_83", "PM_90", "PM_91", "PM_92", "PM_93", "PM_97", "PM_98"]
        for profile in profiles:
            profile_network_config = forty_k_network["forty_k_network"]["pm"][profile]
            self.assertTrue("Network_Explorer_Administrator" in profile_network_config["USER_ROLES"])
            self.assertEqual(True, profile_network_config["CBS"])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
