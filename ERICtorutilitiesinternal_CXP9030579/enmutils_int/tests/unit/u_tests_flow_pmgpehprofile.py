#!/usr/bin/env python
import unittest2

from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils
from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile import PmGpehProfile
from enmutils_int.lib.workload import pm_46, pm_51, pm_53


class PmGpehProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmGpehProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'RNC': 1}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.delete_nodes_from_netex_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.GpehSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.create_gpeh_subscription_object")
    def test_create_gpeh_subscription__successful(
            self, mock_create_gpeh_subscription_object, mock_set_teardown, mock_check_all_nodes_added_to_subscription,
            mock_gpehsubscription, *_):
        profile = PmGpehProfile()
        profile.create_gpeh_subscription()

        subscription = mock_create_gpeh_subscription_object.return_value
        self.assertTrue(subscription.create.called)
        self.assertTrue(subscription.activate.called)
        mock_set_teardown.assert_called_with(mock_gpehsubscription, subscription.name, subscription.id,
                                             subscription.poll_scanners)
        mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.identifier", new_callable=PropertyMock,
           return_value="PM_XY_12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.GpehSubscription",)
    def test_create_gpeh_subscription_object__successful(
            self, mock_gpehsubscription, mock_get_profile_nodes, mock_set_values_from_cbs, *_):

        profile = PmGpehProfile()
        profile.USER = "USER1"
        profile.POLL_SCANNERS = True

        criteria, nodes = Mock(), [Mock()]
        mock_get_profile_nodes.return_value = nodes
        mock_set_values_from_cbs.return_value = True, criteria

        self.assertEqual(mock_gpehsubscription.return_value, profile.create_gpeh_subscription_object())

        mock_gpehsubscription.assert_called_with(
            name="PM_XY_12345", cbs=True, description="some_desc", user="USER1", poll_scanners=True, nodes=nodes,
            rop_enum='FIFTEEN_MIN', num_events=3, criteria_specification=criteria)
        mock_get_profile_nodes.assert_called_with(cbs=True)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.identifier", new_callable=PropertyMock,
           return_value="PM_XY_12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.GpehSubscription", )
    def test_create_gpeh_subscription_object__if_cbs_false(
            self, mock_gpehsubscription, mock_get_profile_nodes, mock_set_values_from_cbs, *_):
        profile = PmGpehProfile()
        profile.USER = "USER1"
        profile.POLL_SCANNERS = True

        criteria, nodes = Mock(), [Mock()]
        mock_get_profile_nodes.return_value = nodes
        mock_set_values_from_cbs.return_value = False, criteria

        self.assertEqual(mock_gpehsubscription.return_value, profile.create_gpeh_subscription_object())

        mock_gpehsubscription.assert_called_with(
            name="PM_XY_12345", cbs=False, description="some_desc", user="USER1", poll_scanners=True, nodes=nodes,
            rop_enum='FIFTEEN_MIN', num_events=3, criteria_specification=criteria)
        mock_get_profile_nodes.assert_called_with(cbs=False)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.create_gpeh_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__is_successful(self, mock_superclass_flow, mock_create_gpeh_subscription, mock_add_exception):
        self.profile.USER_ROLES = ['TestRole']

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_create_gpeh_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "delete_nodes_from_netex_attribute")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.all_nodes_in_workload_pool', new_callable=PropertyMock,
           return_value=["node"])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.create_gpeh_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_is_subscription_fails_to_create(
            self, mock_superclass_flow, mock_create_gpeh_subscription, mock_add_exception, *_):
        self.profile.USER_ROLES = ['TestRole']
        mock_create_gpeh_subscription.side_effect = Exception("Failed Subscription")

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_create_gpeh_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile.PmGpehProfile.execute_flow')
    def test_run__in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_46.PM_46()
        profile.run()
        profile = pm_51.PM_51()
        profile.run()
        profile = pm_53.PM_53()
        profile.run()
        self.assertEqual(mock_flow.call_count, 3)

    def test_pm_profiles__if_cbs_profile_has_network_explorer_administrator_user_role_existed_or_not(self):
        profiles = ["PM_46", "PM_51", "PM_53"]
        for profile in profiles:
            profile_network_config = forty_k_network["forty_k_network"]["pm"][profile]
            self.assertTrue("Network_Explorer_Administrator" in profile_network_config["USER_ROLES"])
            self.assertEqual(True, profile_network_config["CBS"])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
