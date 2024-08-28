#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import patch, PropertyMock, Mock
from enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile import PmRPMOSubscriptionProfile
from enmutils_int.lib.workload import pm_80


class PmRPMOSubscriptionProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.pm_80 = pm_80.PM_80()
        self.profile = PmRPMOSubscriptionProfile()
        self.profile.NUM_NODES = {'BSC': 1}
        self.profile.USER_ROLES = ["PM_Operator"]
        self.profile.subscriptions = {"usecase1": [Mock(id='007')], "usecase2": [Mock(id='007')]}
        self.profile.use_case_index = 0
        self.profile.SCHEDULE_SLEEP = 3 * 24 * 60 * 60
        self.profile.USE_CASES = [{'Subscriptions': 1, 'Nodes': 95}, {'Subscriptions': 8, 'Nodes': 12}]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile."
           "identifier", new_callable=PropertyMock, return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.RPMOSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    def test_create_and_activate_rpmo_subscription_successful(self, mock_log,
                                                              mock_subscription,
                                                              mock_check_all_nodes_added_to_subscription, *_):
        mock_subscription.return_value = self.profile.subscriptions['usecase1'][0]
        node_list = Mock([])
        self.profile.create_rpmo_subscription(self.profile.sub_id, node_list)
        self.assertTrue(mock_subscription.return_value.create.called)
        self.assertTrue(mock_check_all_nodes_added_to_subscription.called)
        self.assertEqual(mock_log.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.create_rpmo_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.get_profile_nodes")
    def test_create_rpmo_subscriptions_based_on_use_cases__use_case1_success(
            self, mock_selected_nodes, mock_create_rpmo_subscription, mock_debug_log):
        self.profile.use_case_index = 0
        mock_selected_nodes.return_value = [Mock(), Mock()]
        self.profile.create_rpmo_subscriptions_based_on_use_cases()
        self.assertEqual(mock_create_rpmo_subscription.call_count, 1)
        self.assertEqual(self.profile.use_case_index, 1)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(self.profile.sub_id, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.create_rpmo_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.get_profile_nodes")
    def test_create_rpmo_subscriptions_based_on_use_cases__use_case2_success(
            self, mock_selected_nodes, mock_create_rpmo_subscription, mock_debug_log):
        self.profile.use_case_index = 1
        mock_selected_nodes.return_value = [Mock() for _ in range(13)]
        self.profile.create_rpmo_subscriptions_based_on_use_cases()
        self.assertEqual(mock_create_rpmo_subscription.call_count, 2)
        self.assertEqual(self.profile.use_case_index, 0)
        self.assertEqual(mock_debug_log.call_count, 7)
        self.assertEqual(self.profile.sub_id, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.create_rpmo_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile."
           "PmRPMOSubscriptionProfile.get_profile_nodes")
    def test_create_rpmo_subscriptions_based_on_use_cases__if_req_nodes_not_found_for_use_case2_subs(
            self, mock_selected_nodes, mock_create_rpmo_subscription, mock_debug_log):
        self.profile.use_case_index = 1
        mock_selected_nodes.return_value = [Mock() for _ in range(3)]
        self.profile.create_rpmo_subscriptions_based_on_use_cases()
        self.assertEqual(mock_create_rpmo_subscription.call_count, 1)
        self.assertEqual(self.profile.use_case_index, 0)
        self.assertEqual(mock_debug_log.call_count, 5)
        self.assertEqual(self.profile.sub_id, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.'
           'PmRPMOSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.'
           'enm_deployment.get_values_from_global_properties')
    def test_execute_flow_is_cluster_error(self, mock_check_if_cluster_exists, mock_add_error):
        mock_check_if_cluster_exists.side_effect = Exception
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.'
           'PmRPMOSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.'
           'enm_deployment.get_values_from_global_properties')
    def test_execute_flow_is_cluster_environment_error(self, mock_check_if_cluster_exists, mock_add_error):
        mock_check_if_cluster_exists.return_value = False
        self.profile.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'main_rpmo_flow')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.'
           'enm_deployment.get_values_from_global_properties')
    def test_execute_flow_is_successful(self, mock_check_if_cluster_exists, mock_add_error, mock_main_rpmo_flow):
        mock_check_if_cluster_exists.return_value = True
        self.profile.execute_flow()
        self.assertTrue(mock_main_rpmo_flow.called)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.time.sleep')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.RPMOSubscription")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'activate_rpmo_subscription')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    def test_deactivate_and_activate_rpmo_subscription(self, mock_log, mock_activate_rpmo_subscription,
                                                       mock_subscription, *_):
        self.profile.use_case_index = 1
        self.profile.deactivate_and_activate_rpmo_subscription()
        mock_subscription.return_value = self.profile.subscriptions['usecase1'][0]
        self.assertTrue(mock_subscription.return_value.deactivate.called)
        self.assertTrue(mock_activate_rpmo_subscription.called)
        self.assertEqual(mock_log.call_count, 3)
        self.assertEqual(self.profile.use_case_index, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.RPMOSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.log.logger.debug")
    def test_activate_rpmo_subscription(self, mock_log, mock_subscription):
        self.profile.use_case_index = 2
        self.profile.activate_rpmo_subscription()
        mock_subscription.return_value = self.profile.subscriptions['usecase2'][0]
        self.assertTrue(mock_subscription.return_value.activate.called)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.state')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'deactivate_and_activate_rpmo_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile'
           '.create_rpmo_subscriptions_based_on_use_cases')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile'
           '.add_error_as_exception')
    def test_main_rpmo_flow_error(self, mock_add_error, mock_create_rpmo_subscriptions_based_on_use_cases, *_):
        mock_create_rpmo_subscriptions_based_on_use_cases.side_effect = Exception("Error")
        self.profile.main_rpmo_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'deactivate_and_activate_rpmo_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'create_rpmo_subscriptions_based_on_use_cases')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.add_error_as_exception')
    def test_main_rpmo_flow_success(self, mock_add_error, mock_sleep, mock_create_rpmo_subscriptions_based_on_use_cases,
                                    mock_deactivate_and_activate_rpmo_subscription, *_):
        self.profile.main_rpmo_flow()
        self.assertTrue(mock_create_rpmo_subscriptions_based_on_use_cases.called)
        self.assertTrue(mock_deactivate_and_activate_rpmo_subscription.called)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'deactivate_and_activate_rpmo_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.'
           'create_rpmo_subscriptions_based_on_use_cases')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.add_error_as_exception')
    def test_main_rpmo_flow_deactivate_and_activate_error(self, mock_add_error,
                                                          mock_create_rpmo_subscriptions_based_on_use_cases, *_):
        self.profile.deactivate_and_activate_rpmo_subscription.side_effect = Exception
        self.profile.main_rpmo_flow()
        self.assertTrue(mock_create_rpmo_subscriptions_based_on_use_cases.called)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile.PmRPMOSubscriptionProfile.execute_flow')
    def test_run__in_pm_80_is_successful(self, mock_flow):
        self.pm_80.run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
