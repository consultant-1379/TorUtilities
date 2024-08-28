#!/usr/bin/env python
import unittest2
from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile
from enmutils_int.lib.workload import (pm_03, pm_04, pm_42, pm_86, pm_87)
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
DEFAULT_CRITERIA = [{"name": "PmCelltraceProfile_cbs_subscription", "criteriaIdString": "select networkelement where neType = ERBS"}]


class PmCelltraceProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmCelltraceProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'ERBS': 1}

    def tearDown(self):
        unit_test_utils.tear_down()

    # create_celltrace_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile."
           "delete_nodes_from_netex_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile."
           "create_celltrace_subscription_object")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.CelltraceSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile."
           "check_all_nodes_added_to_subscription")
    def test_create_celltrace_subscription(
            self, mock_check_all_nodes_added_to_subscription, mock_celltracesubscription, mock_set_teardown,
            mock_create_celltrace_subscription_object, *_):
        profile = PmCelltraceProfile()
        subscription = mock_create_celltrace_subscription_object.return_value
        subscription.name, subscription.id, subscription.poll_scanners, subscription.node_types = ("PM_XY", 999, True,
                                                                                                   ["ERBS"])

        profile.create_celltrace_subscription()
        self.assertTrue(subscription.create.called)
        self.assertTrue(subscription.activate.called)
        mock_set_teardown.assert_called_with(mock_celltracesubscription, "PM_XY", 999, True,
                                             node_types=subscription.node_types)
        mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    # create_celltrace_subscription_object test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.identifier",
           new_callable=PropertyMock, return_value="PM_XY-12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.CelltraceSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.get_profile_nodes")
    def test_create_celltrace_subscription_object__successful(
            self, mock_get_profile_nodes, mock_set_values_from_cbs, mock_celltracesubscription, *_):
        profile = PmCelltraceProfile()
        profile.NUM_NODES = {"RADIONODE": -1}
        cbs, criteria, nodes, excluded_counters = True, "some_criteria", [Mock()], [Mock()]
        profile.ROP_STR, profile.USER, profile.NUM_COUNTERS, profile.POLL_SCANNERS = "FIFTEEN_MIN", "user1", 5, True
        profile.MO_CLASS_COUNTERS_EXCLUDED = excluded_counters
        profile.CELL_TRACE_CATEGORY = "some_category"
        profile.EVENT_FILTER = "some_filter"
        profile.DEFINER = "CELLTRACE_SubscriptionAttributes"

        mock_set_values_from_cbs.return_value = cbs, criteria
        mock_get_profile_nodes.return_value = nodes

        self.assertEqual(mock_celltracesubscription.return_value, profile.create_celltrace_subscription_object())
        mock_celltracesubscription.assert_called_with(
            name="PM_XY-12345", cbs=True, description="some_desc", user="user1", poll_scanners=True, nodes=nodes,
            rop_enum="FIFTEEN_MIN", num_counters=5, mo_class_counters_excluded=excluded_counters,
            criteria_specification="some_criteria", cell_trace_category="some_category", event_filter="some_filter",
            node_types=profile.NUM_NODES.keys(), definer=profile.DEFINER)
        mock_get_profile_nodes.assert_called_with(cbs=True)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.identifier",
           new_callable=PropertyMock, return_value="PM_XY-12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.CelltraceSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.get_profile_nodes")
    def test_create_celltrace_subscription_object__if_cbs_false(
            self, mock_get_profile_nodes, mock_set_values_from_cbs, mock_celltracesubscription, *_):
        profile = PmCelltraceProfile()
        profile.NUM_NODES = {"ERBS": -1}
        cbs, criteria, nodes, excluded_counters = False, "some_criteria", [Mock()], [Mock()]
        profile.ROP_STR, profile.USER, profile.NUM_COUNTERS, profile.POLL_SCANNERS = "FIFTEEN_MIN", "user1", 5, True
        profile.MO_CLASS_COUNTERS_EXCLUDED = excluded_counters
        profile.CELL_TRACE_CATEGORY = "some_category"
        profile.EVENT_FILTER = "some_filter"

        mock_set_values_from_cbs.return_value = cbs, criteria
        mock_get_profile_nodes.return_value = nodes

        self.assertEqual(mock_celltracesubscription.return_value, profile.create_celltrace_subscription_object())
        mock_celltracesubscription.assert_called_with(
            name="PM_XY-12345", cbs=False, description="some_desc", user="user1", poll_scanners=True, nodes=nodes,
            rop_enum="FIFTEEN_MIN", num_counters=5, mo_class_counters_excluded=excluded_counters,
            criteria_specification="some_criteria", cell_trace_category="some_category", event_filter="some_filter",
            node_types=profile.NUM_NODES.keys(), definer=None)
        mock_get_profile_nodes.assert_called_with(cbs=False)

    # check_celltrace_system_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmSubscriptionProfile.check_system_subscription_activation")
    def test_check_active_system_subscription(self, mock_check_system_sub_activation, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "System_subscription"
        self.profile.check_celltrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.USER)
        self.assertTrue(mock_check_system_sub_activation.called)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.persist')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.Subscription.get_system_subscription_name_by_pattern')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.'
           'create_celltrace_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__is_successful_creating_user_subscriptions(
            self, mock_superclass_flow, mock_create_celltrace_subscription, mock_get_system_subscription_name,
            mock_add_exception, *_):
        self.profile.USER_ROLES = ['TestRole']

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_get_system_subscription_name.called)
        self.assertTrue(mock_create_celltrace_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmSubscriptionProfile."
           "delete_nodes_from_netex_attribute")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.persist')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.'
           'check_celltrace_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.'
           'create_celltrace_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_if_exception_occurs_creating_subscription(
            self, mock_superclass_flow, mock_create_celltrace_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.USER_ROLES = ['TestRole']
        mock_create_celltrace_subscription.side_effect = Exception("Failed Subscription")

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_check_system_subscription.called)
        self.assertTrue(mock_create_celltrace_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.persist')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.'
           'check_celltrace_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.'
           'create_celltrace_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__is_successful_checking_system_subscription(
            self, mock_superclass_flow, mock_create_celltrace_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "System_subscription"
        self.profile.USER_ROLES = ['TestRole']

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_check_system_subscription.called)
        self.assertFalse(mock_create_celltrace_subscription.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "delete_nodes_from_netex_attribute")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.persist')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.check_celltrace_system_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.create_celltrace_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_when_exception_raised_if_system_subscription_missing(
            self, mock_superclass_flow, mock_create_celltrace_subscription, mock_check_system_subscription,
            mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "System_subscription"
        self.profile.USER_ROLES = ['TestRole']
        mock_check_system_subscription.side_effect = Exception("Failed Subscription")

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_check_system_subscription.called)
        self.assertFalse(mock_create_celltrace_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile.PmCelltraceProfile.execute_flow')
    def test_run__in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_03.PM_03()
        profile.run()
        profile = pm_04.PM_04()
        profile.run()
        profile = pm_42.PM_42()
        profile.run()
        profile = pm_86.PM_86()
        profile.run()
        profile = pm_87.PM_87()
        profile.run()
        self.assertEqual(mock_flow.call_count, 5)

    def test_pm_profiles__if_cbs_profile_has_network_explorer_administrator_user_role_existed_or_not(self):
        profiles = ["PM_03", "PM_42"]
        for profile in profiles:
            profile_network_config = forty_k_network["forty_k_network"]["pm"][profile]
            self.assertTrue("Network_Explorer_Administrator" in profile_network_config["USER_ROLES"])
            self.assertEqual(True, profile_network_config["CBS"])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
