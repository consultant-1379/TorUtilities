#!/usr/bin/env python
import unittest2
from mock import patch, call, Mock, PropertyMock
from enmutils_int.lib.workload import ebsl_05, ebsl_06
from enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile import (EBSLProfile, EBSL05Profile, EBSL06Profile)
from testslib import unit_test_utils


class EBSLProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.ebsl_profile = EBSLProfile()
        self.ebsl_profile.USER_ROLES = ["PM_Operator"]
        self.ebsl_05_profile = EBSL05Profile()
        self.ebsl_06_profile = EBSL06Profile()

    def tearDown(self):
        unit_test_utils.tear_down()

    # EBSLProfile create_celltrace_ebsl_subscription tests

    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile."
           "get_all_nodes_in_workload_pool_based_on_node_filter", return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_values_from_cbs",
           return_value=(True, "some_criteria"))
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.create")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_subscription_description")
    def test_create_ebsl_celltrace_sub__with_counters_and_events(
            self, mock_sub_description, mock_set_teardown, mock_sub_activate, mock_sub_create,
            mock_set_values_from_cbs, *_):
        self.ebsl_profile.NUM_COUNTERS = 1.0
        self.ebsl_profile.NUM_EVENTS = 1.0
        self.ebsl_profile.POLL_SCANNERS = True
        self.ebsl_profile.NODE_FILTER = {'RADIONODE': {'managed_element_type': ["ENodeB", "ENodeB|NodeB", "NodeB"]}}
        mock_sub_description.return_value = "EBSLProfile_load_profile_Project"
        self.ebsl_profile.DEFINER = "CELLTRACE_SubscriptionAttributes"
        cbs, criteria = True, "some_criteria",
        mock_set_values_from_cbs.return_value = cbs, criteria
        self.ebsl_profile.create_celltrace_ebsl_subscription('subscription_name')
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_sub_create.called)
        self.assertTrue(mock_set_teardown.called)
        self.assertTrue(mock_sub_activate.called)

    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile."
           "get_all_nodes_in_workload_pool_based_on_node_filter", return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_values_from_cbs",
           return_value=(True, "some_criteria"))
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.create")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_subscription_description")
    def test_create_ebsl_celltrace_sub__with_cbs(
            self, mock_sub_description, mock_set_teardown, mock_sub_activate, mock_sub_create, *_):
        self.ebsl_profile.NUM_COUNTERS = 1.0
        self.ebsl_profile.USER = Mock()
        self.ebsl_profile.NUM_EVENTS = 1.0
        self.ebsl_profile.POLL_SCANNERS = True
        self.ebsl_profile.NODE_FILTER = {'RADIONODE': {'managed_element_type': ["ENodeB", "ENodeB|NodeB", "NodeB"]}}
        mock_sub_description.return_value = "EBSLProfile_load_profile_Project"
        self.ebsl_profile.DEFINER = "CELLTRACE_SubscriptionAttributes"

        self.ebsl_profile.create_celltrace_ebsl_subscription('subscription_name')
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_sub_create.called)
        self.assertTrue(mock_set_teardown.called)
        self.assertTrue(mock_sub_activate.called)

    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile."
           "get_all_nodes_in_workload_pool_based_on_node_filter", return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.check_all_nodes_added_to_subscription")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_values_from_cbs")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.create")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.CelltraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_teardown")
    @patch("enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.set_subscription_description")
    def test_create_ebsl_celltrace_sub__successfully(
            self, mock_sub_description, mock_set_teardown, mock_sub_activate, mock_sub_create,
            mock_set_values_from_cbs, *_):
        mock_sub_description.return_value = "EBSLProfile_load_profile_Project"
        cbs, criteria = True, "some_criteria",
        mock_set_values_from_cbs.return_value = cbs, criteria
        self.ebsl_profile.create_celltrace_ebsl_subscription('subscription_name')
        self.assertTrue(mock_sub_description.called)
        self.assertTrue(mock_sub_create.called)
        self.assertTrue(mock_set_teardown.called)
        self.assertTrue(mock_sub_activate.called)

    # EBSLProfile execute_flow tests

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_users')
    def test_good_execute_flow__successfully(self, mock_create_users):
        self.ebsl_profile.execute_flow()
        self.assertTrue(mock_create_users.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_users')
    def test_execute_flow__with_kwargs(self, mock_create_users):
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_profile.execute_flow(netex_query=netex_qeury)
        self.assertTrue(mock_create_users.called)
        self.assertEqual(netex_qeury, self.ebsl_profile.NETEX_QUERY)

    # EBSL05Profile execute_flow tests

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__with_evt_cluster(self, mock_create_sub, mock_superclass_flow,
                                                   mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__no_evt_cluster(self, mock_create_sub, mock_superclass_flow,
                                                 mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = False
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('evt')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__if_value_pack_ebs_ln_tag_exists_on_cloud_native(self,
                                                                                  mock_create_sub, mock_superclass_flow,
                                                                                  mock_is_cluster_configured,
                                                                                  mock_add_exception, *_):
        mock_is_cluster_configured.return_value = True
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        mock_is_cluster_configured.assert_has_calls([call('value_pack_ebs_ln')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__if_value_pack_ebs_ln_tag_not_exists_on_cloud_native(self,
                                                                                      mock_create_sub,
                                                                                      mock_superclass_flow,
                                                                                      mock_is_cluster_configured,
                                                                                      mock_add_exception, *_):
        mock_is_cluster_configured.return_value = False
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        mock_is_cluster_configured.assert_has_calls([call('value_pack_ebs_ln')])
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__superclass_flow_failure(self, mock_create_sub, mock_superclass_flow,
                                                          mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_superclass_flow.side_effect = Exception('Subscription creation failed')
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.identifier',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl05_execute_flow__create_sub_failure(self, mock_create_sub, mock_superclass_flow,
                                                     mock_is_evt_cluster_configured, mock_add_exception, *_):
        mock_is_evt_cluster_configured.return_value = True
        mock_create_sub.side_effect = Exception('Subscription creation failed')
        netex_qeury = ("select networkelement where neType=ERBS or neType=RadioNode and "
                       "managedelement has child eNodeBFunction and "
                       "managedelement has child NodeBFunction")
        self.ebsl_05_profile.execute_flow(netex_qeury=netex_qeury)
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertTrue(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSL05Profile.execute_flow')
    def test_run__in_ebsl_05_is_successful(self, mock_flow):
        profile = ebsl_05.EBSL_05()
        profile.run()
        mock_flow.assert_called_with(netex_query="select networkelement where neType=ERBS or neType=RadioNode and "
                                                 "managedelement has child eNodeBFunction and "
                                                 "managedelement has child NodeBFunction")

    # EBSL06Profile execute_flow tests

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__with_both_clusters(self, mock_create_sub, mock_superclass_flow,
                                                     mock_is_evt_cluster_configured, mock_add_exception):
        mock_is_evt_cluster_configured.side_effect = [True, True]
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('str'), call('ebs')])
        self.assertTrue(mock_create_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__with_str_clusters(self, mock_create_sub, mock_superclass_flow,
                                                    mock_is_evt_cluster_configured, mock_add_exception):
        mock_is_evt_cluster_configured.side_effect = [True, False]
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__with_ebs_clusters(self, mock_create_sub, mock_superclass_flow,
                                                    mock_is_evt_cluster_configured, mock_add_exception):
        mock_is_evt_cluster_configured.side_effect = [False, True]
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__no_cluster(self, mock_create_sub, mock_superclass_flow,
                                             mock_is_evt_cluster_configured, mock_add_exception):
        mock_is_evt_cluster_configured.side_effect = [False, False]
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__superclass_flow_failure(self, mock_create_sub, mock_superclass_flow,
                                                          mock_is_evt_cluster_configured, mock_add_exception):
        mock_superclass_flow.side_effect = Exception('Subscription creation failed')
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertFalse(mock_is_evt_cluster_configured.called)
        self.assertFalse(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.is_cluster_configured')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.execute_flow')
    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSLProfile.create_celltrace_ebsl_subscription')
    def test_ebsl06_execute_flow__create_sub_failure(self, mock_create_sub, mock_superclass_flow,
                                                     mock_is_evt_cluster_configured, mock_add_exception):
        mock_is_evt_cluster_configured.side_effect = [True, True]
        mock_create_sub.side_effect = Exception('Subscription creation failed')
        self.ebsl_06_profile.execute_flow()
        self.assertTrue(mock_superclass_flow.called)
        self.assertTrue(mock_is_evt_cluster_configured.called)
        mock_is_evt_cluster_configured.assert_has_calls([call('str'), call('ebs')])
        self.assertTrue(mock_create_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile.EBSL06Profile.execute_flow')
    def test_run__in_ebsl_06_is_successful(self, mock_flow):
        profile = ebsl_06.EBSL_06()
        profile.run()
        self.assertTrue(mock_flow.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
