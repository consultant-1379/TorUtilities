#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock

from enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile import PmUETRProfile
from enmutils_int.lib.workload import pm_47
from testslib import unit_test_utils


class PmUETRProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.pm_47 = pm_47.PM_47()
        self.profile = PmUETRProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'RNC': 1}

    def tearDown(self):
        unit_test_utils.tear_down()

    # create_uetr_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.create_uetr_subscription_object")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.UETRSubscription", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile."
           "check_all_nodes_added_to_subscription")
    def test_create_celltrace_subscription__successful(
            self, mock_check_all_nodes_added_to_subscription, mock_uetrsubscription, mock_set_teardown,
            mock_create_uetr_subscription_object, *_):
        profile = PmUETRProfile()
        subscription = mock_create_uetr_subscription_object.return_value
        subscription.name, subscription.id, subscription.poll_scanners = "PM_XY", 999, True
        profile.create_uetr_subscription()
        self.assertTrue(subscription.create.called)
        self.assertTrue(subscription.activate.called)
        mock_set_teardown.assert_called_with(mock_uetrsubscription, "PM_XY", 999, True)
        mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.identifier", new_callable=PropertyMock,
           return_value="PM_XY-12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.UETRSubscription", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.get_profile_nodes")
    def test_create_uetr_subscription_object__successful(self, mock_get_profile_nodes, mock_uetrsubscription, *_):
        profile = PmUETRProfile()
        profile.POLL_SCANNERS, profile.USER = True, "user1"
        nodes = [Mock()]
        mock_get_profile_nodes.return_value = nodes
        self.assertEqual(mock_uetrsubscription.return_value, profile.create_uetr_subscription_object())
        mock_uetrsubscription.assert_called_with(
            name="PM_XY-12345", description="some_desc", user="user1", poll_scanners=True, nodes=nodes,
            imsi=[{"type": "IMSI", "value": "123546"}], num_events=3)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.create_uetr_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmSubscriptionProfile.execute_flow')
    def test_good_uetr_flow(self, mock_superclass_flow, mock_create_uetr_subscription, mock_add_exception):
        self.profile.USER_ROLES = ['TestRole']

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_create_uetr_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.create_uetr_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmSubscriptionProfile.execute_flow')
    def test_bad_uetr_flow(self, mock_superclass_flow, mock_create_uetr_subscription, mock_add_exception):
        self.profile.USER_ROLES = ['TestRole']
        mock_create_uetr_subscription.side_effect = Exception("Failed Subscription")

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_create_uetr_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile.PmUETRProfile.execute_flow')
    def test_run__in_pm_47_is_successful(self, mock_flow):
        self.pm_47.run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
