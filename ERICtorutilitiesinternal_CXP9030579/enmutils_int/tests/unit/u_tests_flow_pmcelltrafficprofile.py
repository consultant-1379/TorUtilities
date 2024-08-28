#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock, call

from enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile import PmCelltrafficProfile, EnmApplicationError
from enmutils_int.lib.workload import pm_29
from testslib import unit_test_utils


class PmCelltrafficProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.pm_29 = pm_29.PM_29()
        self.profile = PmCelltrafficProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'RNC': 1}
        self.profile.NUM_OF_SUBSCRIPTIONS = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    # create_celltraffic_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.identifier",
           new_callable=PropertyMock, return_value="PM_XX-12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "create_celltraffic_subscription_object")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.CelltrafficSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "check_all_nodes_added_to_subscription")
    def test_create_celltraffic_subscription__successful(
            self, mock_check_all_nodes_added_to_subscription, mock_celltrafficsubscription, mock_set_teardown,
            mock_create_celltraffic_subscription_object, mock_get_profile_nodes, *_):
        mock_get_profile_nodes.return_value = [Mock(primary_type="RNC", node_id="Rnc1")]
        mock_create_celltraffic_subscription_object.return_value = Mock(name="PM_XX-12345", id=999, poll_scanners=True)
        subscription = mock_create_celltraffic_subscription_object.return_value
        subscription.name, subscription.id, subscription.poll_scanners = "PM_XX-12345", 999, True

        self.profile.create_celltraffic_subscription()
        self.assertEqual(subscription.create.call_count, 2)
        self.assertEqual(subscription.activate.call_count, 2)
        mock_set_teardown.assert_called_with(mock_celltrafficsubscription, "PM_XX-12345", 999, True)
        mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.identifier",
           new_callable=PropertyMock, return_value="PM_XX-12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "create_celltraffic_subscription_object")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.CelltrafficSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "check_all_nodes_added_to_subscription")
    def test_create_celltraffic_subscription__when_one_sub_creation_failed(
            self, mock_check_all_nodes_added_to_subscription, mock_celltrafficsubscription, mock_set_teardown,
            mock_create_celltraffic_subscription_object, mock_get_profile_nodes, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
                   "add_error_as_exception") as mock_add_error:
            mock_get_profile_nodes.return_value = [Mock(primary_type="RNC", node_id="Rnc1")]
            mock_create_celltraffic_subscription_object.return_value = Mock(name="PM_XX-12345", id=999,
                                                                            poll_scanners=True)
            subscription = mock_create_celltraffic_subscription_object.return_value
            subscription.create.side_effect = [Exception("something is wrong"), Mock()]
            subscription.name, subscription.id, subscription.poll_scanners = "PM_XX-12345", 999, True

            self.profile.create_celltraffic_subscription()
            self.assertTrue(call(EnmApplicationError("Unable to create/activate 1 CTR subscription(s)") in
                                 mock_add_error.mock_calls))
            self.assertEqual(subscription.create.call_count, 2)
            self.assertEqual(subscription.activate.call_count, 1)
            mock_set_teardown.assert_called_with(mock_celltrafficsubscription, "PM_XX-12345", 999, True)
            mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.CelltrafficSubscription")
    def test_create_celltraffic_subscription_object__successful(self, mock_celltrafficsubscription, *_):
        self.profile.USER, self.profile.POLL_SCANNERS = "user1", True

        nodes = [Mock()]
        self.assertEqual(mock_celltrafficsubscription.return_value,
                         self.profile.create_celltraffic_subscription_object(nodes, "PM_XX-12345"))
        mock_celltrafficsubscription.assert_called_with(
            name="PM_XX-12345", description="some_desc", num_events=3, user="user1", poll_scanners=True,
            nodes=nodes)

    # check_celltraffic_system_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.CelltrafficSubscription")
    @patch("enmutils_int.lib.pm_subscriptions.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    def test_check_active_system_subscription(self, mock_check_system_sub_activation, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "Cell Traffic System_subscription"
        self.profile.check_celltraffic_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.USER)
        self.assertTrue(mock_check_system_sub_activation.called)

    # execute_flow tests ###############################################################################################

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.check_celltraffic_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.create_celltraffic_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow_is_successful(
            self, mock_superclass_flow, mock_create_celltraffic_subscription, mock_check_system_subscription,
            mock_add_exception, *_):

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_check_system_subscription.called)
        self.assertTrue(mock_create_celltraffic_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.check_celltraffic_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.create_celltraffic_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_while_exception_encountered_while_creating_subscription(
            self, mock_superclass_flow, mock_create_celltraffic_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.USER_ROLES = ['TestRole']
        mock_create_celltraffic_subscription.side_effect = Exception("Failed Subscription")

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_check_system_subscription.called)
        self.assertTrue(mock_create_celltraffic_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.check_celltraffic_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.create_celltraffic_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__is_successful_checking_system_subscription(
            self, mock_superclass_flow, mock_create_celltraffic_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "System_subscription"
        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_check_system_subscription.called)
        self.assertFalse(mock_create_celltraffic_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.state")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.check_celltraffic_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.create_celltraffic_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_when_exception_raised_if_system_subscription_missing(
            self, mock_superclass_flow, mock_create_celltraffic_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "System_subscription"
        mock_check_system_subscription.side_effect = Exception("Failed Subscription")
        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_check_system_subscription.called)
        self.assertFalse(mock_create_celltraffic_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile.PmCelltrafficProfile.execute_flow')
    def test_run__in_pm_29_is_successful(self, mock_flow):
        self.pm_29.run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
