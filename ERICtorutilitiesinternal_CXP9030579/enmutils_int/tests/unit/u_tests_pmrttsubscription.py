import unittest2
from testslib import unit_test_utils
from mock import patch, PropertyMock, Mock
from enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription import PmRTTSubscription
from enmutils_int.lib.workload import pm_81


class PMRTTSubscriptionTest(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.pm_81 = pm_81.PM_81()
        self.profile = PmRTTSubscription()
        self.profile.USER_ROLES = ["PM_Operator"]
        self.nodes_list = [Mock(node_id="BSC01", primary_type="BSC", poid=1234),
                           Mock(node_id="BSC02", primary_type="BSC", poid=1235)]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.execute_flow")
    def test_run__in_pm_81__is_successful(self, mock_flow):
        self.pm_81.run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.enm_deployment.get_values_from_global_properties")
    def test_execute_flow__str_cluster_error(self, mock_check_if_cluster_exists, mock_add_error):
        mock_check_if_cluster_exists.side_effect = Exception
        self.profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.main_rtt_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.enm_deployment.get_values_from_global_properties")
    def test_execute_flow__str_cluster_not_exits(self, mock_check_if_cluster_exists, mock_add_error, _):
        mock_check_if_cluster_exists.return_value = False
        self.profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.main_rtt_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.enm_deployment.get_values_from_global_properties")
    def test_execute_flow__is_successfully(self, mock_check_if_cluster_exists, mock_main_rtt_flow, _):
        mock_check_if_cluster_exists.return_value = True
        self.profile.execute_flow()
        self.assertTrue(mock_main_rtt_flow.called)

    # create_rtt_subscription test cases
    @patch("enmutils_int.lib.profile.Profile.identifier", new_callable=PropertyMock, return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile."
           "set_subscription_description")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile."
           "check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.RTTSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.log.logger.debug")
    def test_create_rtt_subscription__is_successful(self, mock_log, mock_subscription, mock_nodes_list, *_):
        mock_nodes_list.return_value = self.nodes_list
        subscription = mock_subscription.return_value = Mock()
        self.profile.create_rtt_subscription()
        self.assertTrue(subscription.create.called)
        self.assertEqual(mock_log.call_count, 3)
        mock_nodes_list.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.keep_running",
           side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.create_rtt_subscription")
    def test_main_rtt_flow__successful(self, mock_create_rtt_subscription, *_):
        subscription = mock_create_rtt_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{"administrationState": "INACTIVE"},
                                                     {"administrationState": "ACTIVE"}]

        self.profile.main_rtt_flow()
        self.assertEqual(subscription.activate.call_count, 3)
        self.assertEqual(subscription.deactivate.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.create_rtt_subscription")
    def test_main_rtt_flow__profile_invalid_state(self, mock_create_rtt_subscription, *_):
        subscription = mock_create_rtt_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{"administrationState": "inactive"},
                                                     {"administrationState": "activate"}]

        self.profile.main_rtt_flow()
        self.assertEqual(subscription.activate.call_count, 1)
        self.assertFalse(subscription.deactivate.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.create_rtt_subscription")
    def test_main_rtt_flow__profile_deactivate_error(self, mock_create_rtt_subscription, mock_add_error, *_):
        subscription = mock_create_rtt_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{"administrationState": "ACTIVE"},
                                                     {"administrationState": "INACTIVE"}]
        subscription.deactivate.side_effect = Exception
        self.profile.main_rtt_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription.PmRTTSubscription.create_rtt_subscription")
    def test_main_rtt_flow__profile_activate_error(self, mock_create_rtt_subscription, mock_add_error, *_):
        subscription = mock_create_rtt_subscription.return_value = Mock()
        subscription.get_subscription.side_effect = [{"administrationState": "INACTIVE"},
                                                     {"administrationState": "ACTIVE"}]
        subscription.activate.side_effect = Exception
        self.profile.main_rtt_flow()
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
