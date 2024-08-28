#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2

from mock import Mock, patch
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import TimeOutError, EnmApplicationError
from enmutils_int.lib.federated_identity_management import FIDM_interface

from testslib import unit_test_utils


class FidmInterfaceUnitTests(unittest2.TestCase):

    federate_identity_last_sync_sucesss_report = {
        "actionReport": {"startTime": "2020-07-17 11:12:30", "duration": "00:01:33.027", "result": "successful",
                         "action": "forcedSync"},
        "taskReports": [{"startTime": "2020-07-17 11:12:30", "duration": "00:00:00.243", "result": "successful",
                         "task": "externalSearch",
                         "counters": {"numSearchResultsSuccess": {"value": 1, "diagnosticMessages": []},
                                      "numLdapEntries": {"value": 1000, "diagnosticMessages": []},
                                      "numSearchRequestsSuccess": {"value": 1, "diagnosticMessages": []}}},
                        {"startTime": "2020-07-17 11:12:30", "duration": "00:00:03.084", "result": "successful",
                         "task": "internalSearch",
                         "counters": {"numSearchRequestsSuccess": {"value": 1, "diagnosticMessages": []},
                                      "numSearchResultsEmpty": {"value": 1, "diagnosticMessages": []}}},
                        {"startTime": "2020-07-17 11:12:33", "duration": "00:00:00.000", "result": "successful",
                         "task": "merge",
                         "counters": {"numEnmFederatedUsers": {"value": 0, "diagnosticMessages": []},
                                      "numUsersInCommon": {"value": 0, "diagnosticMessages": []},
                                      "numExtFederatedUsers": {"value": 1000, "diagnosticMessages": []},
                                      "numUserCreate": {"value": 1000, "diagnosticMessages": []},
                                      "numUserUpdate": {"value": 0, "diagnosticMessages": []},
                                      "numUserDelete": {"value": 0, "diagnosticMessages": []}}},
                        {"startTime": "2020-07-17 11:12:33", "duration": "00:01:29.567", "result": "successful",
                         "task": "performCrud",
                         "counters": {"numUserCreateErrorDueToEntityNotFound": {"value": 1000,
                                                                                "diagnosticMessages": []},
                                      "numUserCreateSuccess": {"value": 1000, "diagnosticMessages": []},
                                      "numUserCreateError": {"value": 1000, "diagnosticMessages": []}}}],
        "privilegesReport": {"requiredEnmRoles": ["ACME_NodeSecurity_Operator", "ACME_SecGW_Operator",
                                                  "ACME_PKI_Operator"],
                             "requiredTGs": ["ACMESOUTH", "NORTH"], "unmappedRoles": []}}

    federate_identity_last_sync_fail_report = {
        "actionReport": {"startTime": "2020-07-17 11:12:30", "duration": "00:01:33.027", "result": "successful",
                         "action": "forcedSync"},
        "taskReports": [{"startTime": "2020-07-17 11:12:30", "duration": "00:00:00.243", "result": "successful",
                         "task": "externalSearch",
                         "counters": {"numSearchResultsSuccess": {"value": 1, "diagnosticMessages": []},
                                      "numLdapEntries": {"value": 1000, "diagnosticMessages": []},
                                      "numSearchRequestsSuccess": {"value": 1, "diagnosticMessages": []}}},
                        {"startTime": "2020-07-17 11:12:30", "duration": "00:00:03.084", "result": "successful",
                         "task": "internalSearch",
                         "counters": {"numSearchRequestsSuccess": {"value": 1, "diagnosticMessages": []},
                                      "numSearchResultsEmpty": {"value": 1, "diagnosticMessages": []}}},
                        {"startTime": "2020-07-17 11:12:33", "duration": "00:00:00.000", "result": "successful",
                         "task": "merge",
                         "counters": {"numEnmFederatedUsers": {"value": 0, "diagnosticMessages": []},
                                      "numUsersInCommon": {"value": 0, "diagnosticMessages": []},
                                      "numExtFederatedUsers": {"value": 1000, "diagnosticMessages": []},
                                      "numUserCreate": {"value": 1000, "diagnosticMessages": []},
                                      "numUserUpdate": {"value": 0, "diagnosticMessages": []},
                                      "numUserDelete": {"value": 0, "diagnosticMessages": []}}}],
        "privilegesReport": {"requiredEnmRoles": ["ACME_NodeSecurity_Operator", "ACME_SecGW_Operator",
                                                  "ACME_PKI_Operator"],
                             "requiredTGs": ["ACMESOUTH", "NORTH"], "unmappedRoles": []}}

    last_sync_fail_report_of_fdim = {
        "actionReport": {"startTime": "2020-08-03 01: 00: 00", "duration": "00: 00: 00.348", "result": "failed",
                         "action": "periodicSync"},
        "taskReports": [{"startTime": "2020-08-03 01: 00: 00", "duration": "00: 00: 00.183", "result": "successful",
                         "task": "externalSearch",
                         "counters": {"numSearchResultsSuccess": {"value": 1, "diagnosticMessages": []},
                                      "numLdapEntries": {"value": 1000, "diagnosticMessages": []},
                                      "numSearchRequestsSuccess": {"value": 1, "diagnosticMessages": []}}},
                        {"startTime": "2020-08-03 01: 00: 00", "duration": "00: 00: 00.044", "result": "failed",
                         "task": "internalSearch",
                         "counters": {"numSearchRequestsError": {
                             "value": 1, "diagnosticMessages": ["Insufficient Access Rights"]}}}],
        "privilegesReport": {"requiredEnmRoles": ["ACME_NodeSecurity_Operator", "ACME_SecGW_Operator",
                                                  "ACME_PKI_Operator"], "requiredTGs": ["ACMESOUTH", "NORTH"],
                             "unmappedRoles": []}}

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.fidm_interface = FIDM_interface()
        self.fidm_interface.NETWORK_TYPE = "enm"
        self.fidm_interface.INTERVAL_DURATION = 24
        self.fidm_interface.INITIAL_EXPIRATION = "01:00",
        self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS = 15

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_import_federated_identity_synchronization__is_successful(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = True
        post_response.status_code = 200
        post_response.json.return_value = {"adminState": "disabled", "operState": "disabled",
                                           "progressReport": ""}
        self.user.post.return_value = post_response
        self.fidm_interface.import_federated_identity_synchronization(self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_import_federated_identity_synchronization__raises_http_error(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = False
        post_response.status_code = 422
        post_response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-5-28-20", "userMessage": "External IdP synchronization operation not "
                                                                 "allowed in current state."})
        self.user.post.return_value = post_response
        self.assertRaises(HTTPError, self.fidm_interface.import_federated_identity_synchronization, self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_import_federated_identity_synchronization__raises_enm_application_error(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = True
        post_response.status_code = 200
        post_response.json.return_value = {}
        self.user.post.return_value = post_response
        self.assertRaises(EnmApplicationError, self.fidm_interface.import_federated_identity_synchronization,
                          self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_period__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"intervalDurationInHours": 24, "initialExpiration": "01:00"}
        self.user.put.return_value = response
        self.fidm_interface.set_federated_identity_synchronization_period(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_period__raises_enm_application_error(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {}
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, self.fidm_interface.set_federated_identity_synchronization_period,
                          self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_period__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        self.user.put.return_value = response
        response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-5-28-39", "userMessage": "External IdP synchronization is still initializing."})
        self.assertRaises(HTTPError, self.fidm_interface.set_federated_identity_synchronization_period, self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_admin_state__if_enabled(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "enabled", "operState": "enabled", "progressReport": ""}
        self.user.put.return_value = response
        self.fidm_interface.set_federated_identity_synchronization_admin_state(self.user, "enabled")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_admin_state__if_disabled(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "disabled", "operState": "disabled", "progressReport": ""}
        self.user.put.return_value = response
        self.fidm_interface.set_federated_identity_synchronization_admin_state(self.user, "disabled")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_admin_state__if_not_enabled(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "disabled", "operState": "disabled", "progressReport": ""}
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, self.fidm_interface.set_federated_identity_synchronization_admin_state,
                          self.user, "enabled")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_set_federated_identity_synchronization_admin_state__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-5-28-42", "userMessage": "External IdP synchronization is in progress."})
        self.user.put.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.set_federated_identity_synchronization_admin_state, self.user,
                          "disabled")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_force_sync_federated_identity_synchronization__is_successful(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = True
        post_response.status_code = 200
        post_response.json.return_value = {"adminState": "enabled", "operState": "forcedSyncInProgress",
                                           "progressReport": ""}
        self.user.post.return_value = post_response
        self.fidm_interface.force_sync_federated_identity_synchronization(self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_force_sync_federated_identity_synchronization__raises_enm_application_error(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = True
        post_response.status_code = 200
        post_response.json.return_value = {}
        self.user.post.return_value = post_response
        self.assertRaises(EnmApplicationError, self.fidm_interface.force_sync_federated_identity_synchronization,
                          self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_force_sync_federated_identity_synchronization__raises_http_error(self, mock_debug_log):
        post_response = Mock()
        post_response.ok = False
        post_response.status_code = 422
        post_response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-5-28-20", "userMessage": "External IdP synchronization operation not "
                                                                 "allowed in current state."})
        self.user.post.return_value = post_response
        self.assertRaises(HTTPError, self.fidm_interface.force_sync_federated_identity_synchronization, self.user)
        self.assertTrue(post_response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_period_of_federated_identity_synchronization__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"intervalDurationInHours": 24, "initialExpiration": "01:00"}
        self.user.get.return_value = response
        self.fidm_interface.get_period_of_federated_identity_synchronization(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_period_of_federated_identity_synchronization__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-5-28-39", "userMessage": "External IdP synchronization is still initializing."})
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.get_period_of_federated_identity_synchronization, self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_synchronization_state__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "enabled", "operState": "idle", "progressReport": ""}
        self.user.get.return_value = response
        self.fidm_interface.get_federated_identity_synchronization_state(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_synchronization_state__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 403
        response.raise_for_status.side_effect = HTTPError(
            {"internalErrorCode": "FIDM-3-read", "userMessage": "The User does not have permissions to perform "
                                                                "this action."})
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.get_federated_identity_synchronization_state, self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_force_delete_federated_identity_synchronization__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "disabled", "operState": "forcedDeleteInProgress",
                                      "progressReport": ""}
        self.user.post.return_value = response
        self.fidm_interface.force_delete_federated_identity_synchronization(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_force_delete_federated_identity_synchronization__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError({"internalErrorCode": "FIDM-5-28-20",
                                                           "userMessage": "External IdP synchronization operation "
                                                                          "not allowed in current state."})
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.force_delete_federated_identity_synchronization, self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_restore_to_defaults_federated_identity_synchronization__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"adminState": "disabled", "operState": "forcedDeleteInProgress",
                                      "progressReport": ""}
        self.user.post.return_value = response
        self.fidm_interface.restore_to_defaults_federated_identity_synchronization(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_restore_to_defaults_federated_identity_synchronization__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError({"internalErrorCode": "FIDM-5-28-42",
                                                           "userMessage": "External IdP synchronization is "
                                                                          "in progress."})
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.restore_to_defaults_federated_identity_synchronization,
                          self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_last_synchronization_report__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.federate_identity_last_sync_sucesss_report
        self.user.get.return_value = response
        self.fidm_interface.get_federated_identity_last_synchronization_report(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_last_synchronization_report__if_getting_fail_report(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.federate_identity_last_sync_fail_report
        self.user.get.return_value = response
        self.fidm_interface.get_federated_identity_last_synchronization_report(self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_last_synchronization_report__if_action_report_status_failed(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.last_sync_fail_report_of_fdim
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.fidm_interface.get_federated_identity_last_synchronization_report,
                          self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_last_synchronization_report__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError({"internalErrorCode": "FIDM-5-28-39",
                                                           "userMessage": "External IdP synchronization is"
                                                                          " still initializing."})
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.fidm_interface.get_federated_identity_last_synchronization_report,
                          self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_get_federated_identity_last_synchronization_report__if_taskReports_not_found_in_response(self,
                                                                                                      mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {}
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.fidm_interface.get_federated_identity_last_synchronization_report,
                          self.user)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.federated_identity_management.datetime.timedelta')
    @patch('enmutils_int.lib.federated_identity_management.datetime.datetime')
    @patch('enmutils_int.lib.federated_identity_management.FIDM_interface.'
           'get_federated_identity_synchronization_state')
    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_wait_force_sync_fdi_synchronization_to_complete__is_successful(
            self, mock_debug_log, mock_get_fdi_sync_state, mock_datetime, mock_timedelta, *_):
        mock_get_fdi_sync_state.return_value = {"adminState": "enabled", "operState": "idle",
                                                "progressReport": ""}
        time_now = datetime(2020, 7, 21, 9, 0, 0)
        expiry_time = datetime(2020, 7, 21, 9, self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        self.fidm_interface.wait_force_sync_federated_identity_synchronization_to_complete(self.user)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.federated_identity_management.datetime.timedelta')
    @patch('enmutils_int.lib.federated_identity_management.datetime.datetime')
    @patch('enmutils_int.lib.federated_identity_management.FIDM_interface.'
           'get_federated_identity_synchronization_state')
    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_wait_force_sync_fdi_synchronization_to_complete__raises_timeout_error(
            self, mock_debug_log, mock_get_fdi_sync_state, mock_datetime, mock_timedelta, *_):
        mock_get_fdi_sync_state.return_value = {"adminState": "enabled", "operState": "forcedSyncInProgress",
                                                "progressReport": ""}
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        self.assertRaises(TimeOutError,
                          self.fidm_interface.wait_force_sync_federated_identity_synchronization_to_complete, self.user)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.federated_identity_management.datetime.timedelta')
    @patch('enmutils_int.lib.federated_identity_management.datetime.datetime')
    @patch('enmutils_int.lib.federated_identity_management.'
           'FIDM_interface.get_federated_identity_synchronization_state')
    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_wait_force_delete_federated_identity_synchronization_to_complete__is_successful(
            self, mock_debug_log, mock_get_fdi_sync_state, mock_datetime, mock_timedelta, *_):
        mock_get_fdi_sync_state.return_value = {"adminState": "disabled", "operState": "disabled",
                                                "progressReport": ""}
        time_now = datetime(2020, 7, 21, 9, 0, 0)
        expiry_time = datetime(2020, 7, 21, 9, self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        self.fidm_interface.wait_force_delete_federated_identity_synchronization_to_complete(self.user)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.federated_identity_management.time.sleep', return_value=0)
    @patch('enmutils_int.lib.federated_identity_management.datetime.timedelta')
    @patch('enmutils_int.lib.federated_identity_management.datetime.datetime')
    @patch('enmutils_int.lib.federated_identity_management.FIDM_interface.'
           'get_federated_identity_synchronization_state')
    @patch('enmutils_int.lib.federated_identity_management.log.logger.debug')
    def test_wait_force_delete_federated_identity_synchronization_to_complete__raises_timeout_error(
            self, mock_debug_log, mock_get_fdi_sync_state, mock_datetime, mock_timedelta, *_):
        mock_get_fdi_sync_state.return_value = {"adminState": "disabled", "operState": "forcedDeleteInProgress",
                                                "progressReport": ""}
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.fidm_interface.SLEEP_FOR_FORCE_SYNC_OR_DELETE_STATUS)
        self.assertRaises(TimeOutError,
                          self.fidm_interface.wait_force_delete_federated_identity_synchronization_to_complete,
                          self.user)
        self.assertEqual(mock_debug_log.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
