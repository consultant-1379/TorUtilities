#!/usr/bin/env python
import unittest2
from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.profile_flows.pm_flows.pmebmprofile import PmEBMProfile
from enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow import EBSM04Profile, EnvironWarning
from enmutils_int.lib.workload import ebsm_04, pm_20
from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils


class PmEBMProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmEBMProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'SGSN': 1}
        self.profile.NUM_EVENTS = 1.0
        self.profile.POLL_SCANNERS = Mock()
        self.profile.ROP_STR = "FIFTEEN_MIN"
        self.profile.USER_ROLES = ['TestRole']
        self.pm_20 = pm_20.PM_20()

        self.ebsm_04 = ebsm_04.EBSM_04()
        self.ebsm_04_profile = EBSM04Profile()
        self.ebsm_04_profile.USER_ROLES = ["Blah"]
        self.ebsm_04_profile.NUM_EVENTS = 1.0
        self.ebsm_04_profile.NUM_COUNTERS = 1.0
        self.ebsm_04_profile.COUNTER_FILE_FORMAT = 'TGPP_ENIQ_GZ'
        self.ebsm_04_profile.EBM_ROP_INTERVAL = 'ONE_MIN'
        self.ebsm_04_profile.EVT_CLUSTER_NOT_EXISTS_MESSAGE = (
            "This profile requires an Events (EVT) Cluster configured in this ENM deployment"
            "in order to create an 'EBM and EBS-M Subscription' in PMIC."
            "Given that an EVT Cluster is NOT currently configured, this profile is not "
            "applicable to this deployment. Profile PM_20 handles the 'EBM Subscription' "
            "instead. ")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.execute_flow')
    def test_run__in_pm_20_is_successful(self, mock_flow):
        self.pm_20.run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.execute_flow')
    def test_run__in_ebsm_04_is_successful(self, mock_flow):
        self.ebsm_04.run()
        self.assertTrue(mock_flow.called)

    # create_ebm_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.EBMSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription_object")
    def test_create_ebm_subscription__is_successful(
            self, mock_create_ebm_subscription_object, mock_set_teardown, mock_ebmsubscription,
            mock_check_all_nodes_added_to_subscription, *_):
        subscription = mock_create_ebm_subscription_object.return_value
        subscription.name = "XYZ"
        subscription.id = 999
        subscription.poll_scanners = True
        profile = PmEBMProfile()
        self.assertEqual(subscription, profile.create_ebm_subscription())
        self.assertTrue(subscription.create.called)
        mock_set_teardown.assert_called_with(mock_ebmsubscription, "XYZ", 999, True)
        mock_check_all_nodes_added_to_subscription.assert_called_with(subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.identifier", new_callable=PropertyMock,
           return_value="PM_XX_12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.EBMSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.set_values_from_cbs")
    def test_create_ebm_subscription_object__successful(
            self, mock_set_values_from_cbs, mock_ebmsubscription, mock_get_profile_nodes, *_):
        profile = PmEBMProfile()
        profile.NUM_EVENTS, profile.USER, profile.POLL_SCANNERS, profile.ROP_STR = 5, "user1", True, "15min"

        cbs, criteria, nodes = True, Mock(), [Mock()]
        profile.nodes_from_netex = nodes
        profile.DEFINER = "EBM_SubscriptionAttributes"
        mock_get_profile_nodes.return_value = nodes

        mock_set_values_from_cbs.return_value = cbs, criteria

        self.assertEqual(mock_ebmsubscription.return_value, profile.create_ebm_subscription_object())
        mock_ebmsubscription.assert_called_with(
            name="PM_XX_12345-EBM", num_events=5, cbs=True, description="some_desc", user="user1",
            criteria_specification=criteria, poll_scanners=True, nodes=nodes, rop_enum="15min", definer=profile.DEFINER)
        mock_get_profile_nodes.assert_called_with(cbs=cbs)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.identifier", new_callable=PropertyMock,
           return_value="PM_XX_12345")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.set_subscription_description",
           return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.EBMSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.set_values_from_cbs")
    def test_create_ebm_subscription_object__if_cbs_false(
            self, mock_set_values_from_cbs, mock_ebmsubscription, mock_get_profile_nodes, *_):
        profile = PmEBMProfile()
        profile.NUM_EVENTS, profile.USER, profile.POLL_SCANNERS, profile.ROP_STR = 5, "user1", True, "15min"

        cbs, criteria, nodes = False, Mock(), [Mock()]
        profile.nodes_from_netex = nodes

        mock_set_values_from_cbs.return_value = cbs, criteria
        mock_get_profile_nodes.return_value = nodes

        self.assertEqual(mock_ebmsubscription.return_value, profile.create_ebm_subscription_object())
        mock_ebmsubscription.assert_called_with(
            name="PM_XX_12345-EBM", num_events=5, cbs=False, description="some_desc", user="user1",
            criteria_specification=criteria, poll_scanners=True, nodes=nodes, rop_enum="15min", definer=None)
        mock_get_profile_nodes.assert_called_with(cbs=cbs)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_good_ebm_flow__no_evt_cluster(
            self, mock_superclass_flow, mock_is_evt_cluster_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = False

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertTrue(mock_create_ebm_subscription.called)
        self.assertTrue(mock_create_ebm_subscription.return_value.activate.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__with_evt_raises_error(
            self, mock_superclass_flow, mock_is_evt_cluster_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(mock_create_ebm_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_if_evt_search_us_unsuccessful(
            self, mock_superclass_flow, mock_is_evt_cluster_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_is_evt_cluster_configured.side_effect = Exception('Cannot search EVT cluster')

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_ebm_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__adds_error_if_cannot_create_subscription(
            self, mock_superclass_flow, mock_is_evt_cluster_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = False
        mock_create_ebm_subscription.side_effect = Exception('Failed subscription')
        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertTrue(mock_create_ebm_subscription.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__on_cloud_native_and_value_pack_ebs_m_tag_is_enabled(
            self, mock_superclass_flow, mock_value_pack_ebs_m_tag_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_value_pack_ebs_m_tag_configured.return_value = True

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_value_pack_ebs_m_tag_configured.called)
        self.assertFalse(mock_create_ebm_subscription.called)
        self.assertTrue(call(EnvironWarning("Profile will only create EBM Subscription if the ENM deployment does NOT contain an "
                                            "Events Cluster/value_pack_ebs_m Tag") in mock_add_exception.mock_calls))

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmEBMProfile.create_ebm_subscription')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmebmprofile.PmSubscriptionProfile.execute_flow')
    def test_execute_flow__on_cloud_native_and_value_pack_ebs_m_tag_is_disabled(
            self, mock_superclass_flow, mock_value_pack_ebs_m_tag_configured, mock_create_ebm_subscription,
            mock_add_exception, *_):
        mock_value_pack_ebs_m_tag_configured.return_value = False

        self.profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_value_pack_ebs_m_tag_configured.called)
        self.assertTrue(mock_create_ebm_subscription.called)
        self.assertFalse(mock_add_exception.called)

    # EBSM_04 execute_flow test cases
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__executes_successfully_if_evt_cluster_exists(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.return_value = True
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('evt')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        mock_create_activate_sub.assert_called_with(mock_create_user.return_value[0])
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__if_value_pack_ebs_m_tag_exists_on_cloud_native(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.return_value = True
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('value_pack_ebs_m')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        mock_create_activate_sub.assert_called_with(mock_create_user.return_value[0])
        self.assertTrue(call(EnvironWarning(self.ebsm_04_profile.EVT_CLUSTER_NOT_EXISTS_MESSAGE) in
                             mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__if_value_pack_ebs_m_tag_not_exists_on_cloud_native(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.return_value = False
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('value_pack_ebs_m')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        self.assertFalse(mock_create_activate_sub.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__if_problem_occurs_checking_value_pack_ebs_m_tag_not_on_cloud_native(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.side_effect = Exception("Some thing is wrong")
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('value_pack_ebs_m')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        self.assertEqual(0, mock_create_activate_sub.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__add_error_as_environ_warning_if_no_evt_cluster_exists(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.return_value = False
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('evt')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        self.assertEqual(0, mock_create_activate_sub.call_count)
        self.assertTrue(call(EnvironWarning(self.ebsm_04_profile.EVT_CLUSTER_NOT_EXISTS_MESSAGE) in
                             mock_add_error.mock_calls))

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_and_activate_ebsm_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.PmSubscriptionProfile')
    def test_execute_flow__if_problem_occurs_checking_evt_cluster_exists(
            self, mock_pm_subscription_profile, mock_add_error, mock_create_user, mock_create_activate_sub, *_):
        mock_create_user.return_value = [Mock()]
        mock_pm_subscription_profile.return_value = Mock()
        mock_pm_subscription_profile.return_value.is_cluster_configured.side_effect = Exception("Some thing is wrong")
        self.ebsm_04_profile.execute_flow()
        mock_pm_subscription_profile.return_value.is_cluster_configured.assert_called_with('evt')
        mock_create_user.assert_called_with(1, self.ebsm_04_profile.USER_ROLES, retry=True)
        self.assertEqual(0, mock_create_activate_sub.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    # EBSM_04 create_and_activate_ebsm_subscription test cases
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBMSubscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.get_nodes_list_by_attribute')
    def test_create_and_activate_ebsm_subscription__is_successful(self, mock_get_nodes_list, mock_subscription,
                                                                  mock_add_error):
        mock_get_nodes_list.return_value = [Mock(node_id="sgsn1", poid=1234, primary_type="SGSN-MME")]
        self.ebsm_04_profile.create_and_activate_ebsm_subscription([Mock()])
        self.assertEqual(1, len(self.ebsm_04_profile.teardown_list))
        self.assertTrue(mock_subscription.return_value.create.called)
        self.assertTrue(mock_subscription.return_value.activate.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBMSubscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.get_nodes_list_by_attribute')
    def test_create_and_activate_ebsm_subscription__is_successful_if_definer_is_existed(self, mock_get_nodes_list,
                                                                                        mock_subscription,
                                                                                        mock_add_error):
        mock_get_nodes_list.return_value = [Mock(node_id="sgsn1", poid=1234, primary_type="SGSN-MME")]
        self.ebsm_04_profile.DEFINER = "EBM_SubscriptionAttributes"
        self.ebsm_04_profile.create_and_activate_ebsm_subscription([Mock()])
        self.assertEqual(1, len(self.ebsm_04_profile.teardown_list))
        self.assertTrue(mock_subscription.return_value.create.called)
        self.assertTrue(mock_subscription.return_value.activate.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBMSubscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.get_nodes_list_by_attribute')
    def test_create_and_activate_ebsm_subscription__if_problem_occurs_creating_subscription(self, mock_get_nodes_list,
                                                                                            mock_subscription,
                                                                                            mock_add_error):
        mock_get_nodes_list.return_value = [Mock(node_id="sgsn1", poid=1234, primary_type="SGSN-MME")]
        mock_subscription.return_value.create.side_effect = Exception("Something is wrong")
        self.ebsm_04_profile.create_and_activate_ebsm_subscription([Mock()])
        self.assertTrue(mock_subscription.return_value.create.called)
        self.assertEqual(0, len(self.ebsm_04_profile.teardown_list))
        self.assertFalse(mock_subscription.return_value.activate.called)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBMSubscription')
    @patch('enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow.EBSM04Profile.get_nodes_list_by_attribute')
    def test_create_and_activate_ebsm_subscription__if_problem_occurs_activating_subscription(self,
                                                                                              mock_get_nodes_list,
                                                                                              mock_subscription,
                                                                                              mock_add_error):
        mock_get_nodes_list.return_value = [Mock(node_id="sgsn1", poid=1234, primary_type="SGSN-MME")]
        mock_subscription.return_value.activate.side_effect = Exception("Something is wrong")
        self.ebsm_04_profile.create_and_activate_ebsm_subscription([Mock()])
        self.assertTrue(mock_subscription.return_value.create.called)
        self.assertEqual(1, len(self.ebsm_04_profile.teardown_list))
        self.assertTrue(mock_subscription.return_value.activate.called)
        self.assertEqual(1, mock_add_error.call_count)

    def test_pm_20__if_cbs_profile_has_network_explorer_administrator_user_role_existed_or_not(self):
        profile_network_config = forty_k_network["forty_k_network"]["pm"]["PM_20"]
        self.assertTrue("Network_Explorer_Administrator" in profile_network_config["USER_ROLES"])
        self.assertEqual(True, profile_network_config["CBS"])


if __name__ == "__main__":
    unittest2.main(verbosity=2)
