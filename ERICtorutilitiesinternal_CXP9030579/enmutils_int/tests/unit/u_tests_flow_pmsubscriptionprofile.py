#!/usr/bin/env python
from datetime import datetime

import unittest2
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.exceptions import TimeOutError
from enmutils_int.lib.pm_subscriptions import Subscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class PmSubscriptionProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmSubscriptionProfile()
        self.profile.USER = Mock()
        self.mock_user = Mock()
        self.profile.USER_ROLES = ['TestRole']
        self.profile.NETEX_QUERY = 'select networkelement where neType = {node_type}'
        self.profile.NUM_NODES = {'ERBS': 1}

        self.profile.ACTIVITY_FREQUENCY_HOURS = 6
        self.profile.ACTIVITY_DURATION_HOURS = 2
        self.profile.THREAD_TIMEOUT = 20 * 60
        self.profile.ROP_DURATION_IN_MINS = 15
        self.profile.OFFSET_FROM_START_OF_ROP_TO_ACTIVATION_TIME_IN_MINS = 7

    def tearDown(self):
        unit_test_utils.tear_down()

    # is_cluster_configured tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_ebs_tag_exists")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_cluster_exists")
    def test_is_cluster_configured__on_cloud(self, mock_check_cluster_exists, mock_cache, mock_log,
                                             mock_check_if_ebs_tag_exists):
        mock_cache.is_host_physical_deployment.return_value = False
        mock_cache.is_enm_on_cloud_native.return_value = False

        self.assertFalse(self.profile.is_cluster_configured('cluster_name'))
        self.assertFalse(mock_check_cluster_exists.called)
        self.assertFalse(mock_check_if_ebs_tag_exists.called)
        self.assertTrue(mock_log.logger.debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_ebs_tag_exists")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_cluster_exists")
    def test_is_cluster_configured__on_physical_if_cluster_exists(self, mock_check_cluster_exists, mock_cache,
                                                                  mock_log, mock_check_if_ebs_tag_exists):
        mock_cache.is_host_physical_deployment.return_value = True
        mock_cache.is_enm_on_cloud_native.return_value = False
        mock_check_cluster_exists.return_value = True

        self.assertTrue(self.profile.is_cluster_configured('cluster_name'))
        self.assertTrue(mock_check_cluster_exists.called)
        self.assertFalse(mock_check_if_ebs_tag_exists.called)
        self.assertFalse(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_ebs_tag_exists")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_cluster_exists")
    def test_is_cluster_configured__on_physical_if_cluster_does_not_exist(self, mock_check_cluster_exists, mock_cache,
                                                                          mock_log, mock_check_if_ebs_tag_exists):
        mock_cache.is_host_physical_deployment.return_value = True
        mock_cache.is_enm_on_cloud_native.return_value = False
        mock_check_cluster_exists.return_value = False

        self.assertFalse(self.profile.is_cluster_configured('cluster_name'))
        self.assertTrue(mock_check_cluster_exists.called)
        self.assertFalse(mock_check_if_ebs_tag_exists.called)
        self.assertTrue(mock_log.logger.debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_ebs_tag_exists")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_cluster_exists")
    def test_is_cluster_configured__on_cloud_native(self, mock_check_cluster_exists, mock_cache, mock_log,
                                                    mock_check_if_ebs_tag_exists):
        mock_cache.is_host_physical_deployment.return_value = False
        mock_cache.is_enm_on_cloud_native.return_value = True
        mock_check_if_ebs_tag_exists.return_value = True

        self.assertTrue(self.profile.is_cluster_configured('value_pack_ebs_m'))
        self.assertFalse(mock_check_cluster_exists.called)
        mock_check_if_ebs_tag_exists.assert_called_with('value_pack_ebs_m')
        self.assertFalse(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_ebs_tag_exists")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.check_if_cluster_exists")
    def test_is_cluster_configured__if_ebs_tag_not_found(self, mock_check_cluster_exists, mock_cache, mock_log,
                                                         mock_check_if_ebs_tag_exists):
        mock_cache.is_host_physical_deployment.return_value = False
        mock_cache.is_enm_on_cloud_native.return_value = True
        mock_check_if_ebs_tag_exists.return_value = False

        self.assertFalse(self.profile.is_cluster_configured('value_pack_ebs_m'))
        self.assertFalse(mock_check_cluster_exists.called)
        mock_check_if_ebs_tag_exists.assert_called_with('value_pack_ebs_m')
        self.assertTrue(mock_log.logger.debug.call_count, 1)

    # set_values_from_cbs tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_true_and_netex_query_is_supplied(
            self, mock_search_criteria):
        self.profile.CBS = True
        mock_search_criteria.return_value = [{'name': 'PmSubscriptionProfile_cbs_subscription',
                                              'criteriaIdString': self.profile.NETEX_QUERY}]
        cbs, criteria = self.profile.set_values_from_cbs()
        self.assertTrue(mock_search_criteria.called)
        self.assertTrue(cbs)
        self.assertEqual(criteria, [{'name': 'PmSubscriptionProfile_cbs_subscription',
                                     'criteriaIdString': self.profile.NETEX_QUERY}])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_but_netex_query_not_supplied(self, mock_search_criteria):
        self.profile.CBS = True
        mock_search_criteria.return_value = [{'name': 'PmSubscriptionProfile_cbs_subscription',
                                              'criteriaIdString': 'select networkelement where neType = ERBS'}]
        self.profile.NETEX_QUERY = None
        cbs, criteria = self.profile.set_values_from_cbs()

        self.assertTrue(mock_search_criteria.called)
        self.assertTrue(cbs)
        self.assertEqual(criteria, [{'name': 'PmSubscriptionProfile_cbs_subscription',
                                     'criteriaIdString': 'select networkelement where neType = ERBS'}])

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_false(self, mock_search_criteria, mock_debug):
        self.profile.CBS = False
        self.profile.NETEX_QUERY = None
        cbs, criteria = self.profile.set_values_from_cbs()

        self.assertFalse(mock_debug.called)
        self.assertFalse(mock_search_criteria.called)
        self.assertFalse(cbs)
        self.assertEqual(criteria, [])

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_false_and_netex_query_is_set(self, mock_search_criteria, mock_debug):
        self.profile.CBS = False
        cbs, criteria = self.profile.set_values_from_cbs()

        self.assertTrue(mock_debug.called)
        self.assertFalse(mock_search_criteria.called)
        self.assertFalse(cbs)
        self.assertEqual(criteria, [])

    # set_search_criteria tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile"
           ".set_nodes_from_netex_via_query")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.search_and_save")
    def test_set_search_criteria__successful(
            self, mock_search_and_save, mock_all_nodes_in_workload_pool, mock_set_nodes_from_netex_via_query):
        self.profile.USER = "PM_USER1"
        self.profile.NUM_NODES = {"ERBS": 2, "RadioNode": 3}
        self.profile.NETEX_QUERY = "select managedelement where neType={node_type}"
        self.profile.NAME = "PM_123"

        nodes = [Mock()]
        mock_all_nodes_in_workload_pool.return_value = nodes

        saved_search = Mock(rc=0, stdout="")
        saved_search.name = "some_search_name"
        saved_search.query = "some_search_query"
        mock_search_and_save.return_value = (saved_search, Mock())

        expected_result = [{"name": "some_search_name", "criteriaIdString": "some_search_query"}]

        self.assertEqual(expected_result, self.profile.set_search_criteria())
        mock_search_and_save.assert_called_with(self.profile, "PM_USER1",
                                                "select managedelement where neType=ERBS or neType=RadioNode",
                                                "PM_123_cbs_subscription", nodes, delete_existing=True,
                                                version="v1", num_nodes=len(nodes))
        mock_set_nodes_from_netex_via_query.assert_called_with(saved_search, nodes)
        mock_all_nodes_in_workload_pool.assert_called_with(node_attributes=["node_id", "poid", "primary_type", "node_version"])

    def test_set_nodes_from_netex_via_query__success(self):
        node = Mock(node_id="id")
        search = Mock()
        search.execute.return_value = {'id': ''}
        self.profile.set_nodes_from_netex_via_query(search, [node])
        self.assertEqual(1, search.execute.call_count)
        self.assertEqual(1, len(getattr(self.profile, 'nodes_from_netex', [])))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    def test_set_nodes_from_netex_via_query__adds_error(self, mock_add):
        node = Mock(node_id="id")
        search = Mock()
        search.execute.side_effect = Exception('Error')
        self.profile.set_nodes_from_netex_via_query(search, [node])
        self.assertEqual(1, mock_add.call_count)

    # set_subscription_description tests
    def test_subcription_description_w_cbs(self):
        self.profile.CBS = "TRUE"
        sub_description = self.profile.set_subscription_description()
        self.assertEqual(sub_description, 'PmSubscriptionProfile_cbs_load_profile')

    def test_subcription_description_no_cbs(self):
        sub_description = self.profile.set_subscription_description()
        self.assertEqual(sub_description, 'PmSubscriptionProfile_load_profile')

    # check_system_subscription_activation tests
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_by_name")
    def test_system_subscription_active(self, mock_get_sub_by_name, mock_activate_subscription, mock_get_subscription,
                                        mock_keep_running, mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = 'System_subscription'
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        mock_get_subscription.return_value = {'administrationState': 'ACTIVE'}
        mock_get_sub_by_name.return_value = subscription
        mock_keep_running.side_effect = [True, True, False]

        self.profile.check_system_subscription_activation(subscription)
        self.assertTrue(mock_get_subscription.called)
        self.assertFalse(mock_activate_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_by_name")
    def test_system_subscription_in_pending_state(
            self, mock_get_sub_by_name, mock_activate_subscription, mock_get_subscription, mock_keep_running,
            mock_sleep, mock_add_exception):
        self.profile.SYS_DEF_SUB_PATTERN = 'System_subscription'
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        mock_get_subscription.side_effect = [{'administrationState': 'ACTIVATING'},
                                             {'administrationState': 'DEACTIVATING'},
                                             {'administrationState': 'UPDATING'}]
        mock_get_sub_by_name.return_value = subscription
        mock_keep_running.side_effect = [True, False, True, False, True, False]

        self.profile.check_system_subscription_activation(subscription)
        self.assertTrue(mock_get_subscription.called)
        self.assertFalse(mock_activate_subscription.called)
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_sleep.called)

        self.profile.check_system_subscription_activation(subscription)
        self.assertTrue(mock_get_subscription.called)
        self.assertFalse(mock_activate_subscription.called)
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_sleep.called)

        self.profile.check_system_subscription_activation(subscription)
        self.assertTrue(mock_get_subscription.called)
        self.assertFalse(mock_activate_subscription.called)
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.get_by_name")
    def test_system_subscription__if_disabled(self, mock_get_sub_by_name, mock_activate_subscription,
                                              mock_get_subscription, mock_keep_running, mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = 'System_subscription'
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        mock_get_subscription.return_value = {'administrationState': 'INACTIVE'}
        mock_get_sub_by_name.return_value = subscription
        mock_activate_subscription.side_effect = TimeOutError
        mock_keep_running.side_effect = [True, True, True, True, True, False]

        self.assertRaises(TimeOutError, self.profile.check_subscription_state, subscription)
        self.assertTrue(mock_get_subscription.called)
        self.assertEqual(3, mock_activate_subscription.call_count)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_subscription_state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    def test_check_system_subscription_activation__is_successful(
            self, mock_add_error_as_exception, mock_check_subscription_state, *_):
        system_subscription = Mock()
        self.profile.check_system_subscription_activation(system_subscription)
        self.assertFalse(mock_add_error_as_exception.called)
        mock_check_subscription_state.assert_called_with(system_subscription, None)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_subscription_state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    def test_check_system_subscription_activation__adds_error_if_subscription_doesnt_exist(
            self, mock_add_error_as_exception, mock_check_subscription_state,
            *_):
        self.profile.SYS_DEF_SUB_PATTERN = 'Some_System_subscription'
        subscription = Mock(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        subscription.get_by_name.side_effect = EnmApplicationError('Subscription search failed')

        self.profile.check_system_subscription_activation(subscription)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertFalse(mock_check_subscription_state.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    def test_check_subscription_state__cctr_inactive_by_default(
            self, mock_keep_running, mock_debug, *_):
        self.profile.teardown_list = []
        self.profile.SYS_DEF_SUB_PATTERN = 'CCTR'
        mock_keep_running.side_effect = [True, True, True, True, False]
        subscription = Mock(user=self.profile.USER)
        subscription.name = "CCTR_sys_defined_subscription"
        subscription.get_subscription.return_value = {'administrationState': 'INACTIVE'}
        self.profile.teardown_list = []

        self.profile.check_subscription_state(subscription, self.profile.SYS_DEF_SUB_PATTERN)
        mock_debug.assert_called_with(
            "Adding instruction to teardown_list to deactivate subscription 'CCTR_sys_defined_subscription' so that "
            "subscription is reverted to default admin state when profile is stopped.")
        self.assertEqual(len(self.profile.teardown_list), 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    def test_check_subscription_state__ctum_inactive_by_default(
            self, mock_keep_running, mock_debug, mock_add_error_as_exception, *_):
        self.profile.teardown_list = []
        self.profile.SYS_DEF_SUB_PATTERN = 'CTUM'
        mock_keep_running.side_effect = [True, True, True, True, False]
        subscription = Mock(user=self.profile.USER)
        subscription.name = "CTUM_sys_defined_subscription"
        subscription.get_subscription.return_value = {'administrationState': 'INACTIVE'}

        self.profile.check_subscription_state(subscription, self.profile.SYS_DEF_SUB_PATTERN)
        mock_debug.assert_called_with(
            "Adding instruction to teardown_list to deactivate subscription 'CTUM_sys_defined_subscription' so that "
            "subscription is reverted to default admin state when profile is stopped.")
        self.assertEqual(mock_add_error_as_exception.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    def test_check_subscription_state__sys_def_sub_unexpectedly_inactive(
            self, mock_keep_running, mock_debug, mock_add_error_as_exception, *_):
        self.profile.teardown_list = []
        self.profile.SYS_DEF_SUB_PATTERN = 'SBG'
        mock_keep_running.side_effect = [True, True, True, True, False]
        subscription = Mock(user=self.profile.USER)
        subscription.name = "SBG_sys_defined_subscription"
        subscription.get_subscription.return_value = {'administrationState': 'INACTIVE'}

        self.profile.check_subscription_state(subscription, self.profile.SYS_DEF_SUB_PATTERN)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    def test_check_subscription_state__raises_enmapplicationerror_if_subscription_is_in_unrecognised_state(
            self, mock_keep_running, *_):
        self.profile.teardown_list = []
        self.profile.SYS_DEF_SUB_PATTERN = 'CTUM'
        mock_keep_running.side_effect = [True, True, True, False]
        system_subscription = Mock(user=self.profile.USER)
        system_subscription.name = "CTUM_sys_defined_subscription"
        system_subscription.get_subscription.return_value = {'administrationState': 'UNKNOWN'}

        with self.assertRaises(EnmApplicationError) as enm_application_error:
            self.profile.check_subscription_state(system_subscription, self.profile.SYS_DEF_SUB_PATTERN)
        self.assertEqual("Subscription 'CTUM_sys_defined_subscription' is in unexpected admin state: UNKNOWN",
                         enm_application_error.exception.message)
        self.assertEqual(system_subscription.get_subscription.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.keep_running')
    def test_check_subscription_state_CCTR_NRAN_inactive_by_default(self, mock_keep_running, mock_debug, *_):
        self.profile.teardown_list = []
        self.profile.SYS_DEF_SUB_PATTERN = "Continuous Cell Trace NRAN"
        mock_keep_running.side_effect = [True, True, True, True, False]
        subscription = Mock(user=self.profile.USER)
        subscription.name = "CCTR_NRAN_sys_defined_subscription"
        subscription.get_subscription.return_value = {'administrationState': 'INACTIVE'}
        self.profile.teardown_list = []
        self.profile.check_subscription_state(subscription, self.profile.SYS_DEF_SUB_PATTERN)
        mock_debug.assert_called_with(
            "Adding instruction to teardown_list to deactivate subscription 'CCTR_NRAN_sys_defined_subscription'"
            " so that subscription is reverted to default admin state when profile is stopped.")
        self.assertEqual(len(self.profile.teardown_list), 1)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.create_users')
    def test_execute_flow__with_netex(self, mock_create_users, mock_clean_subscriptions, mock_debug_log):
        self.profile.execute_flow(netex_query='netex_query')
        self.assertEqual(self.profile.NETEX_QUERY, 'netex_query')
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.create_users')
    def test_execute_flow__no_netex(self, mock_create_users, mock_clean_subscriptions, mock_debug_log):
        self.profile.execute_flow()
        self.assertFalse(self.profile.NETEX_QUERY)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.create_users')
    def test_execute_flow__removing_old_subscriptions(self, mock_create_users, mock_clean_subscriptions,
                                                      mock_debug_log):
        self.profile.execute_flow()
        self.assertFalse(self.profile.NETEX_QUERY)
        mock_create_users.return_value = self.profile.USER
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_debug_log.call_count, 3)
        mock_clean_subscriptions.assert_called_with(name=self.profile.NAME, user=mock_create_users.return_value)

    def test_delete_nodes_from_netex_attribute(self):
        self.profile.delete_nodes_from_netex_attribute()
        self.assertFalse(hasattr(self.profile, "nodes_from_netex"))
        self.profile.nodes_from_netex = [Mock()]
        self.assertTrue(hasattr(self.profile, "nodes_from_netex"))
        self.profile.delete_nodes_from_netex_attribute()
        self.assertFalse(hasattr(self.profile, "nodes_from_netex"))
        self.profile.delete_nodes_from_netex_attribute()

    def test_set_teardown__is_successful(self):
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        self.profile.teardown_list = []
        self.profile.set_teardown(subscription.__class__, subscription.name, subscription.id)
        self.assertEqual(len(self.profile.teardown_list), 1)

    def test_set_teardown__if_poll_scanners_true(self):
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription")
        self.profile.teardown_list = []
        self.profile.set_teardown(subscription.__class__, subscription.name, subscription.id, True)
        self.assertEqual(len(self.profile.teardown_list), 1)

    def test_set_teardown__if_poll_scanners_true_and_nodes_existed(self):
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription", nodes=[Mock()])
        self.profile.teardown_list = []
        self.profile.set_teardown(subscription.__class__, subscription.name, subscription.id, True,
                                  node_types=["ERBS"])
        self.assertEqual(len(self.profile.teardown_list), 1)

    def test_set_teardown_if_nodes_existed(self):
        self.profile.teardown_list = []
        subscription = Subscription(user=self.profile.USER, name="PmSubscriptionProfile_subscription", nodes=[Mock()])
        self.profile.set_teardown(subscription.__class__, subscription.name, subscription.id, node_types=[])
        self.assertEqual(len(self.profile.teardown_list), 1)

    def test_get_system_subscription_name_by_pattern__raises_EnmApplicationError_if_more_than_one_match_found(self):
        self.mock_user.get.return_value = Mock()

        erbs1_sub_name = "ERBS type-1 System Defined Statistical Subscription"
        erbs2_sub_name = "ERBS type-2 System Defined Statistical Subscription"

        subscription_data = [
            {"id": "111", "name": erbs1_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"},
            {"id": "222", "name": erbs2_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"}]

        self.mock_user.get.return_value.ok = 1
        self.mock_user.get.return_value.json.return_value = subscription_data

        self.assertRaises(EnmApplicationError, Subscription.get_system_subscription_name_by_pattern, "ERBS",
                          self.mock_user)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.time")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.datetime")
    def test_set_scheduled_times__is_successful(self, mock_datetime, mock_debug, _):
        current_timestamp = datetime(2019, 2, 15, 1, 53)
        mock_datetime.fromtimestamp.return_value = current_timestamp

        activation_time = current_timestamp.replace(hour=2, minute=7)
        scheduled_times = [activation_time, activation_time.replace(hour=4),
                           activation_time.replace(hour=8), activation_time.replace(hour=10),
                           activation_time.replace(hour=14), activation_time.replace(hour=16),
                           activation_time.replace(hour=20), activation_time.replace(hour=22)]

        self.profile.set_scheduled_times()
        self.assertEqual(self.profile.SCHEDULED_TIMES, scheduled_times)
        mock_debug.assert_called_with("Setting scheduled times complete: {0}"
                                      .format(["02:07", "04:07", "08:07", "10:07", "14:07", "16:07", "20:07", "22:07"]))

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    def test_check_all_nodes_added_to_subscription__does_nothing_if_node_counts_are_equal(
            self, mock_add_error_as_exception):
        nodes = [Mock()]
        subscription = Mock(nodes=nodes, parsed_nodes=nodes)
        self.profile.check_all_nodes_added_to_subscription(subscription)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    def test_check_all_nodes_added_to_subscription__adds_error_if_node_counts_dont_add_up(
            self, mock_add_error_as_exception):
        subscription = Mock(nodes=[Mock()], parsed_nodes=[])
        self.profile.check_all_nodes_added_to_subscription(subscription)
        self.assertTrue(mock_add_error_as_exception.called)

    def test_get_sub_file_generation_action_enable_command_based_on_next_run_time(
            self, *_):
        next_run_time = datetime.now().replace(hour=00, minute=52, second=00)
        self.profile.SCHEDULED_TIMES_STRINGS = ["00:52:00", "02:52:00", "06:52:00", "08:52:00", "12:52:00",
                                                "14:52:00", "18:52:00", "20:52:00"]
        scheduled_times = self.profile.get_schedule_times()
        sub_state = self.profile.get_subscription_file_generation_action_enable_or_disable_command(
            next_run_time, scheduled_times)
        self.assertEqual(sub_state, "Enable")

    def test_get_sub_file_generation_action_disable_command_based_on_next_run_time(
            self, *_):
        next_run_time = datetime.now().replace(hour=02, minute=52, second=00)
        self.profile.SCHEDULED_TIMES_STRINGS = ["00:52:00", "02:52:00", "06:52:00", "08:52:00", "12:52:00",
                                                "14:52:00", "18:52:00", "20:52:00"]
        scheduled_times = self.profile.get_schedule_times()
        sub_state = self.profile.get_subscription_file_generation_action_enable_or_disable_command(
            next_run_time, scheduled_times)
        self.assertEqual(sub_state, "Disable")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "deallocate_and_update_nodes_count_for_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_all_nodes_in_workload_pool_based_on_node_filter")
    def test_get_profile_nodes__successful_if_node_filter_used(
            self, mock_get_all_nodes_in_workload_pool_based_on_node_filter, mock_deallocate_update_nodes, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NODE_FILTER = Mock()

        self.assertEqual(mock_get_all_nodes_in_workload_pool_based_on_node_filter.return_value,
                         profile.get_profile_nodes())
        mock_deallocate_update_nodes.assert_called_with(
            mock_get_all_nodes_in_workload_pool_based_on_node_filter.return_value, None)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "deallocate_and_update_nodes_count_for_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "all_nodes_in_workload_pool")
    def test_get_profile_nodes__successful_if_all_nodes_required(
            self, mock_all_nodes_in_workload_pool, mock_get_nodes_list_by_attribute, mock_deallocate_update_nodes, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": -1}
        profile.get_profile_nodes()
        self.assertEqual(mock_all_nodes_in_workload_pool.return_value, profile.get_profile_nodes())
        self.assertFalse(mock_get_nodes_list_by_attribute.called)
        mock_all_nodes_in_workload_pool.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])
        mock_deallocate_update_nodes.assert_called_with(mock_all_nodes_in_workload_pool.return_value, None)

    def test_check_and_pick_cran_nodes__successful_with_same_nodes(self):
        """
        Deprecated in 24.09 and to be deleted in 25.04  ENMRTD-25460
        """

    def test_check_and_pick_cran_nodes__successful_with_diff_nodes(self):
        """
        Deprecated in 24.09 and to be deleted in 25.04  ENMRTD-25460
        """

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "deallocate_and_update_nodes_count_for_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "all_nodes_in_workload_pool")
    def test_get_profile_nodes__successful_if_all_nodes_not_required(
            self, mock_all_nodes_in_workload_pool, mock_get_nodes_list_by_attribute, mock_deallocate_update_nodes, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_102"
        profile.NUM_NODES = {"ERBS": 1}

        profile.get_profile_nodes()
        self.assertEqual(mock_get_nodes_list_by_attribute.return_value,
                         profile.get_profile_nodes(node_attributes=["node_id", "poid", "primary_type", "netsim"]))
        self.assertFalse(mock_all_nodes_in_workload_pool.called)
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=["node_id", "poid", "primary_type", "netsim"])
        mock_deallocate_update_nodes.assert_called_with(mock_get_nodes_list_by_attribute.return_value, None)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "deallocate_and_update_nodes_count_for_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "all_nodes_in_workload_pool")
    def test_get_profile_nodes__successful_for_pm95_pm96(self, mock_all_nodes_in_workload_pool,
                                                         mock_deallocate_update_nodes, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_95"
        profile.NUM_NODES = {"ROUTER6672": 1}

        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        mock_all_nodes_in_workload_pool.return_value = [node2, node3, node1]

        self.assertEqual([node1], profile.get_profile_nodes())
        mock_all_nodes_in_workload_pool.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])
        mock_deallocate_update_nodes.assert_called_with([node1], None)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "deallocate_and_update_nodes_count_for_profile")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_nodes_list_by_attribute", return_value=[])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "all_nodes_in_workload_pool")
    def test_get_profile_nodes__raises_enmapplicationerror_if_no_nodes_found(
            self, mock_all_nodes_in_workload_pool, mock_get_nodes_list_by_attribute, mock_deallocate_update_nodes, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": 1}

        with self.assertRaises(EnmApplicationError) as e:
            profile.get_profile_nodes()
        self.assertEqual(e.exception.message, "No nodes available for PM_XX profile")
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])
        self.assertFalse(mock_all_nodes_in_workload_pool.called)
        self.assertFalse(mock_deallocate_update_nodes.called)

    # deallocate_and_update_nodes_count_for_profile test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.node_pool_mgr.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__if_service_is_not_used(self, mock_deallocate_nodes,
                                                                                   mock_persist, mock_add_error,
                                                                                   mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": -1}
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], False)
        mock_deallocate_nodes.assert_called_with(profile)
        self.assertTrue(mock_persist.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.nodemanager_adaptor.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__if_service_is_used(self, mock_deallocate_nodes,
                                                                               mock_persist, mock_add_error,
                                                                               mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": -1}
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], False)
        mock_deallocate_nodes.assert_called_with(profile)
        self.assertTrue(mock_persist.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.node_pool_mgr.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__if_cbs_true(self, mock_deallocate_nodes,
                                                                        mock_persist, mock_add_error,
                                                                        mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": -1}
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], True)
        self.assertFalse(mock_deallocate_nodes.called)
        self.assertFalse(mock_persist.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.node_pool_mgr.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__if_nodes_count_existed(self, mock_deallocate_nodes,
                                                                                   mock_persist, mock_add_error,
                                                                                   mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": 1}
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], False)
        self.assertFalse(mock_deallocate_nodes.called)
        self.assertFalse(mock_persist.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.node_pool_mgr.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__if_nodes_count_existed_and_cbs_true(
            self, mock_deallocate_nodes, mock_persist, mock_add_error, mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": 1}
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], True)
        self.assertFalse(mock_deallocate_nodes.called)
        self.assertFalse(mock_persist.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.nodemanager_adaptor.deallocate_nodes")
    def test_deallocate_and_update_nodes_count_for_profile__add_error_exception(
            self, mock_deallocate_nodes, mock_persist, mock_add_error, mock_debug_log, _):
        profile = PmSubscriptionProfile()
        profile.NAME = "PM_XX"
        profile.NUM_NODES = {"ERBS": -1}
        mock_deallocate_nodes.side_effect = Exception("Something is wrong")
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        profile.deallocate_and_update_nodes_count_for_profile([node1, node2, node3], False)
        mock_deallocate_nodes.assert_called_with(profile)
        self.assertFalse(mock_persist.called)
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_debug_log.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
