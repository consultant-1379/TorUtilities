#!/usr/bin/env python

import unittest2
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.pm_subscriptions import Subscription
from enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile import PmSubscriptionProfile
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

    # set_values_from_cbs tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
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

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_false(self, mock_search_criteria, mock_debug):
        self.profile.CBS = False
        self.profile.NETEX_QUERY = None
        cbs, criteria = self.profile.set_values_from_cbs()

        self.assertFalse(mock_debug.called)
        self.assertFalse(mock_search_criteria.called)
        self.assertFalse(cbs)
        self.assertEqual(criteria, [])

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.set_search_criteria")
    def test_set_values_from_cbs__is_successful_where_cbs_is_false_and_netex_query_is_set(self, mock_search_criteria, mock_debug):
        self.profile.CBS = False
        cbs, criteria = self.profile.set_values_from_cbs()

        self.assertTrue(mock_debug.called)
        self.assertFalse(mock_search_criteria.called)
        self.assertFalse(cbs)
        self.assertEqual(criteria, [])

    # set_search_criteria tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile"
           ".set_nodes_from_netex_via_query")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.all_nodes_in_workload_pool")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.search_and_save")
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
        mock_all_nodes_in_workload_pool.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])

    def test_set_nodes_from_netex_via_query__success(self):
        node = Mock(node_id="id")
        search = Mock()
        search.execute.return_value = {'id': ''}
        self.profile.set_nodes_from_netex_via_query(search, [node])
        self.assertEqual(1, search.execute.call_count)
        self.assertEqual(1, len(getattr(self.profile, 'nodes_from_netex', [])))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
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

    # execute_flow tests
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.create_users')
    def test_execute_flow__with_netex(self, mock_create_users, mock_clean_subscriptions, mock_debug_log):
        self.profile.execute_flow(netex_query='netex_query')
        self.assertEqual(self.profile.NETEX_QUERY, 'netex_query')
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.create_users')
    def test_execute_flow__no_netex(self, mock_create_users, mock_clean_subscriptions, mock_debug_log):
        self.profile.execute_flow()
        self.assertFalse(self.profile.NETEX_QUERY)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.create_users')
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

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    def test_check_all_nodes_added_to_subscription__does_nothing_if_node_counts_are_equal(
            self, mock_add_error_as_exception):
        nodes = [Mock()]
        subscription = Mock(nodes=nodes, parsed_nodes=nodes)
        self.profile.check_all_nodes_added_to_subscription(subscription)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.'
           'add_error_as_exception')
    def test_check_all_nodes_added_to_subscription__adds_error_if_node_counts_dont_add_up(
            self, mock_add_error_as_exception):
        subscription = Mock(nodes=[Mock()], parsed_nodes=[])
        self.profile.check_all_nodes_added_to_subscription(subscription)
        self.assertTrue(mock_add_error_as_exception.called)

    # deallocate_and_update_nodes_count_for_profile test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.node_pool_mgr.deallocate_nodes")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.nodemanager_adaptor.deallocate_nodes")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.node_pool_mgr.deallocate_nodes")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.node_pool_mgr.deallocate_nodes")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.node_pool_mgr.deallocate_nodes")
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

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile."
           "nodemanager_service_can_be_used", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.PmSubscriptionProfile.persist")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile.nodemanager_adaptor.deallocate_nodes")
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
