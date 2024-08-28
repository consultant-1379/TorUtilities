#!/usr/bin/env python
import unittest2
from mock import patch, call, Mock, PropertyMock
from enmutils_int.lib.workload import ebsn_01, ebsn_03, ebsn_04, ebsn_05
from enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile import (EBSNProfile, EBSN01Profile, EBSN03Profile,
                                                                   EBSN04Profile, EBSN05Profile,
                                                                   verify_import_flex_counters_status,
                                                                   perform_flex_counters_prerequisites)
from enmutils.lib.exceptions import EnvironWarning, EnmApplicationError

from testslib import unit_test_utils

from requests.exceptions import HTTPError


class EBSNProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.ebsn_profile = EBSNProfile()
        self.ebsn_profile.NUM_NODES = {"RADIONODE": -1}
        self.ebsn_profile.DEFINER = None
        self.ebsn01_profile = EBSN01Profile()
        self.ebsn01_profile.USER_ROLES = ["PM_Operator"]
        self.ebsn03_profile = EBSN03Profile()
        self.ebsn03_profile.USER_ROLES = ["PM_Operator", "Cmedit_Administrator"]

    def tearDown(self):
        unit_test_utils.tear_down()

    # EBSNProfile create_celltrace_ebsn_subscription tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_all_nodes_added_to_subscription")
    @patch('enmutils_int.lib.profile.Profile.get_all_nodes_in_workload_pool_based_on_node_filter')
    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.CelltraceSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile."
           "PmSubscriptionProfile.set_subscription_description")
    def test_create_and_activate_celltrace_ebsn_subscription__with_counters_and_events(
            self, mock_sub_description, mock_set_teardown, mock_celltracesubscription, mock_nodes, *_):
        subscription_name = 'EBSN_Profile'
        self.ebsn_profile.NUM_COUNTERS = 1.0
        self.ebsn_profile.NUM_EVENTS = 1.0
        self.ebsn_profile.POLL_SCANNERS = True
        self.ebsn_profile.NODE_FILTER = {'RADIONODE': {'managed_element_type': ["ENodeB", "ENodeB|NodeB", "NodeB"]}}
        mock_sub_description.return_value = "EBSNProfile_load_profile_Project"
        mock_nodes.return_value = [Mock(managed_element_type="ENodeB"), Mock(managed_element_type="NodeB")]
        mock_celltracesubscription.return_value = Mock(id="999", node_types=self.ebsn_profile.NUM_NODES.keys())
        self.ebsn_profile.create_and_activate_celltrace_ebsn_subscription(subscription_name)
        self.assertEqual(mock_sub_description.return_value, "EBSNProfile_load_profile_Project")
        mock_celltracesubscription.assert_called_with(event_filter=None, output_mode='FILE', name=subscription_name,
                                                      ebs_events=None, ebs_enabled='true', num_events=1.0,
                                                      rop_enum='FIFTEEN_MIN', cell_trace_category=None,
                                                      poll_scanners=True, user=None, technology_domain=None,
                                                      num_counters=1.0, nodes=mock_nodes.return_value,
                                                      description=mock_sub_description.return_value,
                                                      node_types=self.ebsn_profile.NUM_NODES.keys(),
                                                      definer=self.ebsn_profile.DEFINER)
        self.assertTrue(mock_celltracesubscription.called)
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_celltracesubscription.return_value.create.called)
        mock_set_teardown.assert_called_with(mock_celltracesubscription, subscription_name,
                                             mock_celltracesubscription.return_value.id, True,
                                             node_types=mock_celltracesubscription.return_value.node_types)
        self.assertTrue(mock_celltracesubscription.return_value.activate.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_all_nodes_added_to_subscription")
    @patch('enmutils_int.lib.profile.Profile.get_all_nodes_in_workload_pool_based_on_node_filter')
    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.CelltraceSubscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile."
           "PmSubscriptionProfile.set_subscription_description")
    def test_create_and_activate_celltrace_ebsn_subscription__with_counters_and_events_if_definer_is_not_none(
            self, mock_sub_description, mock_set_teardown, mock_celltracesubscription, mock_nodes, *_):
        subscription_name = 'EBSN_Profile'
        self.ebsn_profile.NUM_COUNTERS = 1.0
        self.ebsn_profile.NUM_EVENTS = 1.0
        self.ebsn_profile.POLL_SCANNERS = True
        self.ebsn_profile.DEFINER = "CELLTRACENRAN_SubscriptionAttributes"
        self.ebsn_profile.NODE_FILTER = {'RADIONODE': {'managed_element_type': ["ENodeB", "ENodeB|NodeB", "NodeB"]}}
        mock_sub_description.return_value = "EBSNProfile_load_profile_Project"
        mock_nodes.return_value = [Mock(managed_element_type="ENodeB"), Mock(managed_element_type="NodeB")]
        mock_celltracesubscription.return_value = Mock(id="999", node_types=self.ebsn_profile.NUM_NODES.keys())
        self.ebsn_profile.create_and_activate_celltrace_ebsn_subscription(subscription_name)
        self.assertEqual(mock_sub_description.return_value, "EBSNProfile_load_profile_Project")
        mock_celltracesubscription.assert_called_with(event_filter=None, output_mode='FILE', name=subscription_name,
                                                      ebs_events=None, ebs_enabled='true', num_events=1.0,
                                                      rop_enum='FIFTEEN_MIN', cell_trace_category=None,
                                                      poll_scanners=True, user=None, technology_domain=None,
                                                      num_counters=1.0, nodes=mock_nodes.return_value,
                                                      description=mock_sub_description.return_value,
                                                      node_types=self.ebsn_profile.NUM_NODES.keys(),
                                                      definer=self.ebsn_profile.DEFINER)
        self.assertTrue(mock_celltracesubscription.called)
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_celltracesubscription.return_value.create.called)
        mock_set_teardown.assert_called_with(mock_celltracesubscription, subscription_name,
                                             mock_celltracesubscription.return_value.id, True,
                                             node_types=mock_celltracesubscription.return_value.node_types)
        self.assertTrue(mock_celltracesubscription.return_value.activate.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_all_nodes_added_to_subscription")
    @patch('enmutils_int.lib.profile.Profile.get_all_nodes_in_workload_pool_based_on_node_filter')
    @patch("enmutils_int.lib.pm_subscriptions.CelltraceSubscription.create")
    @patch("enmutils_int.lib.pm_subscriptions.CelltraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    def test_create_ebsn_celltrace_sub__without_counters_and_events(
            self, mock_sub_description, mock_set_teardown, mock_sub_activate, mock_sub_create, *_):
        mock_sub_description.return_value = "EBSNProfile_load_profile_Project"

        self.ebsn_profile.create_and_activate_celltrace_ebsn_subscription('subscription_name')
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_sub_create.called)
        self.assertTrue(mock_set_teardown.called)
        self.assertTrue(mock_sub_activate.called)

    # EBSN01Profile execute_flow tests
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.get_timestamp_str',
           return_value="some_time_stamp")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_ebsn01_execute_flow__is_successful_with_evt_cluster_configured_on_enm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, mock_wait_for_setup_profile,
            mock_debug_log, *_):
        mock_is_evt_cluster_configured.return_value = True
        self.ebsn01_profile.execute_flow()
        self.assertTrue(mock_is_evt_cluster_configured.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        mock_create_sub.assert_called_with("EBSN_FILE_01_CellTrace_subscription_some_time_stamp")
        self.assertFalse(mock_add_exception.called)
        mock_wait_for_setup_profile.assert_called_with("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60,
                                                       timeout_mins=30)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.get_timestamp_str',
           return_value="some_time_stamp")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_ebsn01_execute_flow__if_value_pack_ebs_ln_tag_is_enabled_on_cenm(
            self, mock_create_sub, mock_value_pack_ebs_ln_tag_configured, mock_add_exception,
            mock_wait_for_setup_profile, mock_debug_log, *_):
        mock_value_pack_ebs_ln_tag_configured.return_value = True
        self.ebsn01_profile.execute_flow()
        mock_value_pack_ebs_ln_tag_configured.assert_has_calls([call('value_pack_ebs_ln')])
        mock_create_sub.assert_called_with("EBSN_FILE_01_CellTrace_subscription_some_time_stamp")
        self.assertFalse(mock_add_exception.called)
        mock_wait_for_setup_profile.assert_called_with("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60,
                                                       timeout_mins=30)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.get_timestamp_str',
           return_value="some_time_stamp")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_ebsn01_execute_flow__is_raises_environ_warning_if_value_pack_ebs_ln_tag_not_enabled_on_cenm(
            self, mock_create_sub, mock_value_pack_ebs_ln_tag_configured, mock_add_exception,
            mock_wait_for_setup_profile, mock_debug_log, *_):
        mock_value_pack_ebs_ln_tag_configured.return_value = False
        self.ebsn01_profile.execute_flow()
        mock_value_pack_ebs_ln_tag_configured.assert_has_calls([call('value_pack_ebs_ln')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)
        mock_wait_for_setup_profile.assert_called_with("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60,
                                                       timeout_mins=30)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.get_timestamp_str',
           return_value="some_time_stamp")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_ebsn01_execute_flow__is_raises_environ_warning_if_no_evt_cluster_configured_on_enm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, mock_wait_for_setup_profile,
            mock_debug_log, *_):
        mock_is_evt_cluster_configured.return_value = False
        self.ebsn01_profile.execute_flow()
        self.assertTrue(mock_is_evt_cluster_configured.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)
        mock_wait_for_setup_profile.assert_called_with("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60,
                                                       timeout_mins=30)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.get_timestamp_str',
           return_value="some_time_stamp")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_ebsn01_execute_flow__create_sub_failure(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, mock_wait_for_setup_profile,
            mock_debug_log, *_):
        mock_is_evt_cluster_configured.return_value = True
        mock_create_sub.side_effect = Exception('Subscription creation failed')
        self.ebsn01_profile.execute_flow()
        self.assertTrue(mock_is_evt_cluster_configured.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        mock_create_sub.assert_called_with("EBSN_FILE_01_CellTrace_subscription_some_time_stamp")
        self.assertTrue(mock_add_exception.called)
        mock_wait_for_setup_profile.assert_called_with("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60,
                                                       timeout_mins=30)
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN01Profile.execute_flow')
    def test_run__in_ebsn_01_is_successful(self, mock_flow):
        profile = ebsn_01.EBSN_01()
        profile.run()
        self.assertTrue(mock_flow.called)

    # EBSN03Profile execute_flow tests

    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__str_cluster_error(self, mock_check_if_cluster_exists, mock_add_error, *_):
        mock_check_if_cluster_exists.side_effect = Exception
        self.ebsn03_profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__str_cluster_not_exits(self, mock_get_pib_value_on_enm, mock_add_error, *_):
        mock_get_pib_value_on_enm.return_value = "false"
        self.ebsn03_profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__is_successful(self, mock_get_pib_value_on_enm,
                                         mock_create_and_activate_celltrace_ebsn_subscription, *_):
        mock_get_pib_value_on_enm.return_value = "true"
        self.ebsn03_profile.execute_flow()
        self.assertTrue(mock_create_and_activate_celltrace_ebsn_subscription.called)

    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.'
           'create_and_activate_celltrace_ebsn_subscription', side_effect=HTTPError('error'))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__throws_exception(self, mock_get_pib_value_on_enm,
                                            mock_create_and_activate_celltrace_ebsn_subscription,
                                            mock_add_error, *_):
        mock_get_pib_value_on_enm.return_value = "true"
        self.ebsn03_profile.execute_flow()
        self.assertTrue(mock_create_and_activate_celltrace_ebsn_subscription.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN03Profile.execute_flow')
    def test_run__in_ebsn_03_is_successful(self, mock_flow):
        profile = ebsn_03.EBSN_03()
        profile.run()
        self.assertTrue(mock_flow.called)


class EBSN04ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.ebsn_04 = ebsn_04.EBSN_04()
        self.ebsn04_profile = EBSN04Profile()
        self.ebsn_profile = EBSNProfile()
        self.ebsn04_profile.USER_ROLES = ["ADMINISTRATOR", "Cmedit_Administrator", "PM_Operator"]
        self.ebsn04_profile.TOTAL_IMPORTED_FLEX_COUNTERS = 2
        self.ebsn04_profile.SLEEP_TIME = 10
        self.ebsn04_profile.teardown_list = []
        self.ebsn04_profile.NUM_NODES = {"RadioNode": -1}
        self.ebsn04_profile.USER = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.execute_flow")
    def test_run__is_successful(self, _):
        self.ebsn_04.run()

    # execute_flow test cases
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="1000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("evt", "For pENM deployment, evt is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__is_successful_with_evt_cluster_configured_on_enm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True
        self.ebsn04_profile.execute_flow()
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="1000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("value_pack_ebs_ln", "For cENM deployment, value_pack_ebs_ln tag is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__is_successful_with_value_pack_ebs_ln_tag_enabled_on_cenm(
            self, mock_create_sub, mock_is_value_pack_ebs_ln_tag_configured, mock_add_exception, *_):
        mock_is_value_pack_ebs_ln_tag_configured.return_value = True
        self.ebsn04_profile.execute_flow()
        mock_is_value_pack_ebs_ln_tag_configured.assert_has_calls([call('value_pack_ebs_ln')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="1000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("evt", "For pENM deployment, evt is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__is_raises_environ_warning_if_no_evt_cluster_configured_on_enm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = False
        self.ebsn04_profile.execute_flow()
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)
        msg = ("For pENM deployment, This profile requires an Events (EVT) Cluster configured in this ENM deployment "
               "But Events (EVT) Cluster is NOT currently configured")
        self.assertTrue(call(EnvironWarning(msg) in mock_add_exception.mock_calls))

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="1000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("value_pack_ebs_ln", "For cENM deployment, value_pack_ebs_ln tag is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__is_raises_environ_warning_if_value_pack_ebs_ln_tag_not_enabled_on_cenm(
            self, mock_create_sub, mock_is_value_pack_ebs_ln_tag_configured, mock_add_exception, *_):
        mock_is_value_pack_ebs_ln_tag_configured.return_value = False
        self.ebsn04_profile.execute_flow()
        mock_is_value_pack_ebs_ln_tag_configured.assert_has_calls([call('value_pack_ebs_ln')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)
        msg = ("For cENM deployment, This profile requires an value_pack_ebs_ln Tag configured in this ENM deployment "
               "But value_pack_ebs_ln Tag is NOT currently configured")
        self.assertTrue(call(EnvironWarning(msg) in mock_add_exception.mock_calls))

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("evt", "For pENM deployment, evt is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="1000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__if_sub_creation_failed_in_enm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True
        mock_create_sub.side_effect = Exception()
        self.ebsn04_profile.execute_flow()
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertTrue(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm', return_value="3000")
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.get_cluster_and_error_message',
           return_value=("evt", "For rENM deployment, evt is not currently configured"))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    def test_execute_flow__is_successful_with_evt_cluster_configured_on_renm(
            self, mock_create_sub, mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True
        self.ebsn04_profile.execute_flow()
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    # perform_flex_counters_prerequisites test cases
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.verify_import_flex_counters_status')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.verify_creation_or_deletion_flex_counters_status')
    def test_perform_flex_counters_prerequisites__is_successful(
            self, mock_verify_create_or_delete_flex_counters_status, mock_verify_import_flex_counters_status,
            mock_remove_any_existing_flexible_counters):
        perform_flex_counters_prerequisites(self.ebsn04_profile)
        self.assertTrue(mock_verify_import_flex_counters_status.called)
        mock_verify_create_or_delete_flex_counters_status.assert_called_with(
            self.ebsn04_profile.USER, self.ebsn04_profile.SLEEP_TIME, "create",
            self.ebsn04_profile.TOTAL_IMPORTED_FLEX_COUNTERS)
        mock_remove_any_existing_flexible_counters.assert_called_with(self.ebsn04_profile.USER,
                                                                      self.ebsn04_profile.SLEEP_TIME)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.remove_any_existing_flexible_counters')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.verify_import_flex_counters_status')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.verify_creation_or_deletion_flex_counters_status')
    def test_perform_flex_counters_prerequisites__raises_enm_application_error(
            self, mock_verify_create_or_delete_flex_counters_status, mock_verify_import_flex_counters_status,
            mock_remove_any_existing_flexible_counters):
        mock_verify_import_flex_counters_status.side_effect = EnmApplicationError("1 EBS Flex counters failed to "
                                                                                  "import in enm")
        self.assertRaises(EnmApplicationError, perform_flex_counters_prerequisites, self.ebsn04_profile)
        self.assertTrue(mock_verify_import_flex_counters_status.called)
        self.assertFalse(mock_verify_create_or_delete_flex_counters_status.called)
        mock_remove_any_existing_flexible_counters.assert_called_with(self.ebsn04_profile.USER,
                                                                      self.ebsn04_profile.SLEEP_TIME)

    # verify_import_flex_counters_status test cases
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.partial')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.import_flex_counters_in_enm')
    def test_verify_import_flex_counters_status__is_successful(self, mock_import_flex_counters, mock_add_error, _):
        mock_import_flex_counters.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd",
                                                  "Total Flex Counters": "2", "Total Failed Flex Counters": '0'}
        verify_import_flex_counters_status(self.ebsn04_profile)
        mock_import_flex_counters.assert_called_with(self.ebsn04_profile.USER,
                                                     self.ebsn04_profile.FLEX_COUNTERS_FILE_PATH)
        self.assertEqual(1, len(self.ebsn04_profile.teardown_list))
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.partial')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.import_flex_counters_in_enm')
    def test_verify_import_flex_counters_status__if_import_flex_counters_returns_empty_response(
            self, mock_import_flex_counters, mock_add_error, _):
        mock_import_flex_counters.return_value = {}
        verify_import_flex_counters_status(self.ebsn04_profile)
        mock_import_flex_counters.assert_called_with(self.ebsn04_profile.USER,
                                                     self.ebsn04_profile.FLEX_COUNTERS_FILE_PATH)
        self.assertEqual(0, len(self.ebsn04_profile.teardown_list))
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.partial')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.import_flex_counters_in_enm')
    def test_verify_import_flex_counters_status__add_error_as_exception(self, mock_import_flex_counters,
                                                                        mock_add_error, _):
        mock_import_flex_counters.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd",
                                                  "Total Flex Counters": "1", "Total Failed Flex Counters": '1'}
        message = EnmApplicationError("1 EBS Flex counters failed to import in enm out of 2 flex counters in ENM")
        verify_import_flex_counters_status(self.ebsn04_profile)
        self.assertTrue(call(message in mock_add_error.mock_calls))
        mock_import_flex_counters.assert_called_with(self.ebsn04_profile.USER,
                                                     self.ebsn04_profile.FLEX_COUNTERS_FILE_PATH)
        self.assertEqual(1, len(self.ebsn04_profile.teardown_list))

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.partial')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN04Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.import_flex_counters_in_enm')
    def test_verify_import_flex_counters_status__raises_enm_application_error_when_import_flex_counters_failed(
            self, mock_import_flex_counters, mock_add_error, _):
        mock_import_flex_counters.return_value = {"JobId": "cd767a8e-f348-11ea-8b99-a153311852cd",
                                                  "Total Flex Counters": "0", "Total Failed Flex Counters": '2'}
        self.assertRaises(EnmApplicationError, verify_import_flex_counters_status, self.ebsn04_profile)
        mock_import_flex_counters.assert_called_with(self.ebsn04_profile.USER,
                                                     self.ebsn04_profile.FLEX_COUNTERS_FILE_PATH)
        self.assertEqual(1, len(self.ebsn04_profile.teardown_list))
        self.assertFalse(mock_add_error.called)

    # get_cluster_and_error_message test cases
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.is_enm_on_rack', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native',
           return_value=True)
    def test_get_cluster_and_error_message__is_successful_on_cenm(self, *_):
        self.assertEqual(('value_pack_ebs_ln', 'For cENM deployment, This profile requires an value_pack_ebs_ln '
                                               'Tag configured in this ENM deployment But value_pack_ebs_ln Tag '
                                               'is NOT currently configured'),
                         self.ebsn04_profile.get_cluster_and_error_message())

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.is_enm_on_rack', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native',
           return_value=False)
    def test_get_cluster_and_error_message__is_successful_on_renm(self, *_):
        self.assertEqual(('evt', 'For rENM deployment, This profile requires an Events (EVT) Cluster '
                                 'configured in this ENM deployment But Events (EVT) Cluster is NOT currently '
                                 'configured'), self.ebsn04_profile.get_cluster_and_error_message())

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.is_enm_on_rack', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_host_physical_deployment',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.cache.is_enm_on_cloud_native',
           return_value=False)
    def test_get_cluster_and_error_message__is_successful_on_penm(self, *_):
        self.assertEqual(('evt', 'For pENM deployment, This profile requires an Events (EVT) '
                                 'Cluster configured in this ENM deployment But Events (EVT) Cluster '
                                 'is NOT currently configured'), self.ebsn04_profile.get_cluster_and_error_message())


class EBSN05ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.ebsn05_profile = EBSN05Profile()
        self.ebsn05_profile.USER_ROLES = ["ADMINISTRATOR", "Cmedit_Administrator", "PM_Operator"]
        self.ebsn05_profile.TOTAL_IMPORTED_FLEX_COUNTERS = 2
        self.ebsn05_profile.SLEEP_TIME = 10
        self.ebsn05_profile.teardown_list = []
        self.ebsn05_profile.NUM_NODES = {"RadioNode": -1}
        self.ebsn05_profile.USER = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.get_cluster_and_pib_value')
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__str_cluster_error(self, mock_get_pib_value_on_enm, mock_add_error, *_):
        mock_get_pib_value_on_enm.side_effect = Exception
        self.ebsn05_profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.get_cluster_and_pib_value')
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__str_cluster_not_exits(self, mock_get_pib_value_on_enm, mock_add_error, *_):
        mock_get_pib_value_on_enm.return_value = "false"
        self.ebsn05_profile.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.get_cluster_and_pib_value')
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.'
           'create_and_activate_celltrace_ebsn_subscription')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__is_successful(self, mock_get_pib_value_on_enm,
                                         mock_create_and_activate_celltrace_ebsn_subscription, *_):
        mock_get_pib_value_on_enm.return_value = "true"
        self.ebsn05_profile.execute_flow()
        self.assertTrue(mock_create_and_activate_celltrace_ebsn_subscription.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.get_cluster_and_pib_value', return_value="500")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.perform_flex_counters_prerequisites')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.create_users')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.'
           'create_and_activate_celltrace_ebsn_subscription', side_effect=HTTPError('error'))
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    def test_execute_flow__throws_exception(self, mock_get_pib_value_on_enm,
                                            mock_create_and_activate_celltrace_ebsn_subscription,
                                            mock_add_error, *_):
        mock_get_pib_value_on_enm.return_value = "true"
        self.ebsn05_profile.execute_flow()
        self.assertTrue(mock_create_and_activate_celltrace_ebsn_subscription.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.EBSN05Profile.execute_flow')
    def test_run__in_ebsn_05_is_successful(self, mock_flow):
        profile = ebsn_05.EBSN_05()
        profile.run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.is_enm_on_rack')
    def test_get_cluster_and_pib_value_500(self, mock_is_enm_on_rack, mock_get_pib_value_on_enm):
        mock_is_enm_on_rack.return_value = True
        mock_get_pib_value_on_enm.return_value = "500"
        self.ebsn05_profile.get_cluster_and_pib_value()
        self.assertTrue(mock_is_enm_on_rack.called)

    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile.is_enm_on_rack')
    def test_get_cluster_and_pib_value_50(self, mock_is_enm_on_rack, mock_get_pib_value_on_enm):
        mock_is_enm_on_rack.return_value = False
        mock_get_pib_value_on_enm.return_value = "50"
        self.ebsn05_profile.get_cluster_and_pib_value()
        self.assertTrue(mock_is_enm_on_rack.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
