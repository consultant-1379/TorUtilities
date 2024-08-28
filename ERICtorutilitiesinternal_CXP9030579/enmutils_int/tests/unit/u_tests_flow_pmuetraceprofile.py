#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile import PmUETraceProfile
from enmutils_int.lib.workload import pm_16, pm_19, pm_24
from enmutils.lib.exceptions import EnmApplicationError
from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils


class PmUETraceProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.profile = PmUETraceProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {"ERBS": 1}
        self.profile.UE_INFO = {"type": "IMSI", "value": "00000"}
        self.profile.USER_ROLES = ["TestRole"]
        self.profile.USER_ROLES_CM = ["TestRoleCM"]

    def tearDown(self):
        unit_test_utils.tear_down()

    # enable_uetrace_collection tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.disable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.picklable_boundmethod")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.update_pib_parameter_on_enm")
    def test_enable_uetrace_collection__is_successful(self, mock_update_pib_parameter_on_enm, mock_debug_log,
                                                      mock_teardown_append, mock_picklable_boundmethod,
                                                      mock_disable_config_collection, mock_partial):
        self.profile.enable_config_collection("ctumCollectionEnabled")
        mock_update_pib_parameter_on_enm.assert_called_with(enm_service_name="pmserv",
                                                            pib_parameter_name="ctumCollectionEnabled",
                                                            pib_parameter_value="true")
        self.assertTrue(mock_debug_log.called)
        mock_picklable_boundmethod.assert_called_with(mock_disable_config_collection)
        mock_partial.assert_called_with(mock_picklable_boundmethod.return_value, "ctumCollectionEnabled")
        self.assertTrue(call(mock_partial.return_value) in mock_teardown_append.mock_calls)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.disable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.picklable_boundmethod")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.update_pib_parameter_on_enm")
    def test_enable_uetrace_collection__raises_enm_application_error(self, mock_update_pib_parameter_on_enm,
                                                                     mock_debug_log, mock_teardown_append,
                                                                     mock_picklable_boundmethod,
                                                                     mock_disable_config_collection, mock_partial):
        mock_update_pib_parameter_on_enm.side_effect = EnmApplicationError(
            "Unable to update PIB parameter ctumCollectionEnabled - see profile log for details")
        self.assertRaises(EnmApplicationError, self.profile.enable_config_collection, "ctumCollectionEnabled")
        self.assertTrue(mock_update_pib_parameter_on_enm.called)
        self.assertFalse(mock_debug_log.called)
        self.assertFalse(mock_teardown_append.called)
        self.assertFalse(mock_picklable_boundmethod.called)
        self.assertFalse(mock_disable_config_collection.called)
        self.assertFalse(mock_partial.called)

    # disable_config_collection tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.update_pib_parameter_on_enm")
    def test_disable_uetrace_collection__is_successful(self, mock_update_pib_parameter_on_enm, mock_debug_log):
        self.profile.disable_config_collection("ctumCollectionEnabled")
        mock_update_pib_parameter_on_enm.assert_called_with(enm_service_name="pmserv",
                                                            pib_parameter_name="ctumCollectionEnabled",
                                                            pib_parameter_value="false")
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.update_pib_parameter_on_enm")
    def test_disable_uetrace_collection__raises_enm_application_error(self, mock_update_pib_parameter_on_enm,
                                                                      mock_debug_log):
        mock_update_pib_parameter_on_enm.side_effect = EnmApplicationError(
            "Unable to update PIB parameter ctumCollectionEnabled - see profile log for details")
        self.assertRaises(EnmApplicationError, self.profile.disable_config_collection, "ctumCollectionEnabled")
        self.assertFalse(mock_debug_log.called)

    # check_uetrace_system_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm", return_value="false")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile."
           "check_and_enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription")
    def test_check_uetrace_system_subscription__is_successful(
            self, mock_uetrace_sub, mock_check_system_sub_activation, mock_add_exception, mock_debug_log,
            mock_check_enable_config_collection, *_):
        self.profile.user = Mock()
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        system_subscription = mock_uetrace_sub.return_value = Mock()
        system_subscription.sgsn_mme_exists_and_is_synchronized.return_value = True
        mock_check_enable_config_collection.return_value = True

        self.profile.check_uetrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.user)
        self.assertTrue(system_subscription.sgsn_mme_exists_and_is_synchronized.called)
        self.assertTrue(mock_check_system_sub_activation.called)
        self.assertTrue(mock_check_enable_config_collection.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm", return_value="true")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile."
           "check_and_enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription")
    def test_check_uetrace_system_subscription__if_already_ctum_enabled(
            self, mock_uetrace_sub, mock_check_system_sub_activation, mock_add_exception, mock_debug_log,
            mock_check_enable_config_collection, *_):
        self.profile.user = Mock()
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        system_subscription = mock_uetrace_sub.return_value = Mock()
        system_subscription.sgsn_mme_exists_and_is_synchronized.return_value = True
        mock_check_enable_config_collection.return_value = True

        self.profile.check_uetrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.user)
        self.assertTrue(system_subscription.sgsn_mme_exists_and_is_synchronized.called)
        self.assertTrue(mock_check_enable_config_collection.called)
        self.assertTrue(mock_check_system_sub_activation.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm", return_value="false")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile."
           "check_and_enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription")
    def test_check_uetrace_system_subscription__is_successful_if_ctum_disabled(
            self, mock_uetrace_sub, mock_check_system_sub_activation, mock_add_exception, mock_debug_log,
            mock_check_enable_config_collection, *_):
        self.profile.user = Mock()
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        system_subscription = mock_uetrace_sub.return_value = Mock()
        system_subscription.sgsn_mme_exists_and_is_synchronized.return_value = True
        mock_check_enable_config_collection.return_value = True

        self.profile.check_uetrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.user)
        self.assertTrue(system_subscription.sgsn_mme_exists_and_is_synchronized.called)
        self.assertTrue(mock_check_system_sub_activation.called)
        self.assertTrue(mock_check_enable_config_collection.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm", return_value="false")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile."
           "check_and_enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription")
    def test_check_uetrace_system_subscription__return_False_if_enable_of_ctum_fails(
            self, mock_uetrace_sub, mock_check_system_sub_activation, mock_add_exception,
            mock_debug_log, mock_check_and_enable_config_collection, *_):
        self.profile.user = Mock()
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        system_subscription = mock_uetrace_sub.return_value = Mock()
        system_subscription.sgsn_mme_exists_and_is_synchronized.return_value = False
        mock_check_and_enable_config_collection.return_value = False
        self.assertFalse(self.profile.check_uetrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN,
                                                                        self.profile.user))
        self.assertFalse(system_subscription.sgsn_mme_exists_and_is_synchronized.called)
        self.assertFalse(mock_check_system_sub_activation.called)
        self.assertTrue(mock_check_and_enable_config_collection.called)
        self.assertTrue(mock_debug_log.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm", return_value="false")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.Subscription.get_system_subscription_name_by_pattern")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile."
           "check_and_enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "check_system_subscription_activation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription")
    def test_check_uetrace_system_subscription__adds_error_if_sgsn_missing(
            self, mock_uetrace_sub, mock_check_system_sub_activation, mock_add_exception,
            mock_check_and_enable_config_collection, mock_debug_log, *_):
        self.profile.user = Mock()
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        system_subscription = mock_uetrace_sub.return_value = Mock()
        system_subscription.sgsn_mme_exists_and_is_synchronized.return_value = False
        mock_check_and_enable_config_collection.return_value = True
        self.profile.check_uetrace_system_subscription(self.profile.SYS_DEF_SUB_PATTERN, self.profile.user)
        self.assertTrue(system_subscription.sgsn_mme_exists_and_is_synchronized.called)
        self.assertFalse(mock_check_system_sub_activation.called)
        self.assertTrue(mock_check_and_enable_config_collection.called)
        self.assertEqual(1, mock_add_exception.call_count)
        self.assertTrue(mock_debug_log.called)

    # check_and_enable_config_collection tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    def test_check_and_enable_config_collection__is_executed_successfully(self, mock_add_exception,
                                                                          mock_enable_config_collection,
                                                                          mock_get_pib_value_on_enm):
        mock_get_pib_value_on_enm.return_value = "false"
        self.profile.check_and_enable_config_collection()
        mock_enable_config_collection.assert_called_with("ctumCollectionEnabled")
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_get_pib_value_on_enm.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    def test_check_and_enable_config_collection__if_ctum_already_enabled(self, mock_add_exception,
                                                                         mock_enable_config_collection,
                                                                         mock_get_pib_value_on_enm):
        mock_get_pib_value_on_enm.return_value = "true"
        self.profile.check_and_enable_config_collection()
        self.assertFalse(mock_enable_config_collection.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_get_pib_value_on_enm.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    def test_check_and_enable_config_collection__if_ctum_enable_fails(self, mock_add_exception,
                                                                      mock_enable_config_collection,
                                                                      mock_get_pib_value_on_enm):
        mock_get_pib_value_on_enm.return_value = "false"
        mock_enable_config_collection.side_effect = EnmApplicationError(
            "Unable to update PIB parameter ctumCollectionEnabled - see profile log for details")
        self.profile.check_and_enable_config_collection()
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_get_pib_value_on_enm.called)

    # create_uetrace_subscription tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.create")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.sgsn_mme_exists_and_is_synchronized")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile."
           "set_subscription_description")
    def test_create_non_existing_uetrace_subscription(self, mock_sub_description, mock_sgsn_exist, mock_activate_subs,
                                                      mock_create_subs, mock_add_exception):
        mock_sub_description.return_value = "PmUETraceProfile_cbs_load_profile_Project"
        mock_sgsn_exist.return_value = True

        self.profile.create_uetrace_subscription()
        self.assertTrue(mock_sgsn_exist.called)
        self.assertTrue(mock_create_subs.called)
        self.assertTrue(mock_activate_subs.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.create")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.activate")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.sgsn_mme_exists_and_is_synchronized")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "set_subscription_description")
    def test_create_uetrace_subscription_missing_sgsn(self, mock_sub_description, mock_sgsn_exist, mock_activate_subs,
                                                      mock_create_subs, mock_add_exception):
        mock_sub_description.return_value = "PmUETraceProfile_cbs_load_profile_Project"
        mock_sgsn_exist.return_value = False
        self.profile.create_uetrace_subscription()
        self.assertTrue(mock_sgsn_exist.called)
        self.assertFalse(mock_create_subs.called)
        self.assertFalse(mock_activate_subs.called)
        self.assertTrue(mock_add_exception.called)

    # execute_flow tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.check_uetrace_system_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.create_uetrace_subscription")
    def test_execute_flow__is_successful_creating_user_subscription(
            self, mock_create_uetrace_sub, mock_add_exception, *_):
        self.profile.user = Mock()
        self.profile.execute_flow()
        self.assertTrue(mock_create_uetrace_sub.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.check_uetrace_system_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.create_uetrace_subscription")
    def test_execute_flow__adds_error_if_user_subscription_creation_results_in_exception(
            self, mock_create_uetrace_sub, mock_add_exception, *_):
        self.profile.user = Mock()
        mock_create_uetrace_sub.side_effect = Exception("Failed subscription")
        self.profile.execute_flow()
        self.assertTrue(mock_create_uetrace_sub.called)
        self.assertTrue(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.create_uetrace_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.check_uetrace_system_subscription")
    def test_execute_flow__is_successful_creating_system_subscription_(
            self, mock_check_uetrace_system_subscription,
            mock_create_uetrace_sub, mock_add_exception, *_):
        self.profile.SYS_DEF_SUB_PATTERN = 'CTUM'
        self.profile.user = Mock()
        self.profile.execute_flow()
        self.assertFalse(mock_create_uetrace_sub.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_check_uetrace_system_subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.UETraceSubscription.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.create_uetrace_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.enable_config_collection")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.check_uetrace_system_subscription")
    def test_execute_flow__adds_error_if_exception_occurs_checking_subscription(
            self, mock_check_uetrace_system_subscription, mock_add_exception,
            mock_enable_config_collection, mock_create_uetrace_subscription, *_):
        self.profile.SYS_DEF_SUB_PATTERN = "CTUM"
        self.profile.user = Mock()
        mock_check_uetrace_system_subscription.side_effect = Exception("Failed system subscription")
        self.profile.execute_flow()
        self.assertTrue(mock_check_uetrace_system_subscription.called)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(mock_enable_config_collection.called)
        self.assertFalse(mock_create_uetrace_subscription.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile.PmUETraceProfile.execute_flow')
    def test_run__in_pm_profiles_that_call_execute_flow_is_successful(self, mock_flow):
        profile = pm_16.PM_16()
        profile.run()
        profile = pm_19.PM_19()
        profile.run()
        profile = pm_24.PM_24()
        profile.run()
        self.assertEqual(mock_flow.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
