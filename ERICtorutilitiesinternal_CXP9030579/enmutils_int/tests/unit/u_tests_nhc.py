#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import Mock, patch
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnmApplicationError

from enmutils_int.lib.nhc import (create_nhc_request_body, get_time_from_enm_return_string_with_gtm_offset,
                                  nhc_profile_payload, create_nhc_profile, create_nhc_job, get_profile_rules,
                                  get_nhc_job_payload, get_radio_node_package, update_profile_rules_to_ignore_alarm_checks)

radio_node_package = {u'productRelease': None, u'packageName': u'CXP9024418_6_R2CXS2', u'productRevision': u'R2CXS2',
                      u'productData': u'CXP9024418/6_R2CXS2', u'productNumber': u'CXP9024418/6'}

rules = [{u'severity': u'CRITICAL', u'inputParameters': [{u'name': u'alarmThresholdCount', u'value': u'0'},
                                                         {u'name': u'inclusion', u'value': u'INCLUDED'},
                                                         {u'name': u'severity', u'value': u'CRITICAL'},
                                                         {u'name': u'ignoreSpecificProblems', u'value': u'None'}],
          u'technology': u'None', u'id': u'CRITICAL-ALARM-CHECK'},
         {u'id': u'GNBDUFunction_CheckNRCllDUStatus', u'technology': u'None'}]

profile_rules_response = {u'rules': [{u'description': u'Check for the GSM TRX status', u'name': u'Check TRX status',
                                      u'recommendedAction': u'Check availabilityStatus attribute',
                                      u'inputParameters': [{u'valueRange': None, u'defaultValue': u'INCLUDED',
                                                            u'name': u'inclusion',
                                                            u'enumerationValues': [u'INCLUDED', u'EXCLUDED'],
                                                            u'description': None},
                                                           {u'valueRange': None, u'defaultValue': u'WARNING',
                                                            u'name': u'severity',
                                                            u'enumerationValues': [u'WARNING', u'CRITICAL'],
                                                            u'description': None}], u'technology': u'GRAT',
                                      u'id': u'BtsFunction_CheckTrxStatus', u'categories': [u'ALL', u'POSTUPGRADE',
                                                                                            u'PREINSTALL',
                                                                                            u'PREUPGRADE',
                                                                                            u'SITE_ACCEPTANCE'],
                                      u'severity': u'WARNING'}]}

profile_payload = {"name": 'test_name',
                   "description": "",
                   "neType": 'RadioNode',
                   "packageName": radio_node_package['packageName'],
                   "productNumber": radio_node_package['productNumber'],
                   "productRevision": radio_node_package['productRevision'],
                   "productRelease": radio_node_package['productRelease'],
                   "createdBy": "administrator",
                   "profileRules": rules,
                   "userLabel": []}

job_payload = {"name": 'test_name',
               "description": "",
               "jobType": "NODE_HEALTH_CHECK",
               "configurations": [{"neType": "RadioNode",
                                   "properties": [{"key": "PROFILE_NAME",
                                                   "value": 'test_profile'}]}],
               "mainSchedule": {"scheduleAttributes": [{"name": "START_DATE", "value": "test_time"}],
                                "execMode": "SCHEDULED"},
               "activitySchedules": [{"platformType": "ECIM",
                                      "value": [{"neType": 'RadioNode',
                                                 "value": [{"activityName": "nodehealthcheck", "execMode": "IMMEDIATE",
                                                            "order": 1, "scheduleAttributes": []}]}]}],
               "neNames": [],
               "collectionNames": [],
               "savedSearchIds": []}

json_data = [radio_node_package,
             {u'productRelease': None, u'packageName': u'CXP9024418_6-R43B36', u'productRevision': u'R43B36',
              u'productData': u'CXP9024418/6-R43B36', u'productNumber': u'CXP9024418/6'}]


class NHCUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username='NHC_04')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.nhc.log.logger.debug')
    def test_get_radio_node_package__success(self, mock_log):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = json_data
        self.user.get.return_value = response
        expected_package_dict = radio_node_package
        actual_output = get_radio_node_package(self.user)
        self.assertEqual(expected_package_dict, actual_output)
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.nhc.log.logger.debug')
    def test_get_radio_node_package__response_not_200(self, mock_log):
        response = Mock(status_code=500, ok=False)
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, get_radio_node_package, self.user)
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.nhc.log.logger.debug')
    def test_get_radio_node_package__if_not_response_json(self, mock_log):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = []
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, get_radio_node_package, self.user)
        self.assertEqual(mock_log.call_count, 1)

    def test_get_time_from_enm_return_string_with_gtm_offset_success(self):
        user = self.user
        time = "05:00:00"
        response = Mock()
        response.json.return_value = {u'date': 1534950498956, u'serverLocation': u'Europe/Dublin', u'offset': 3600000}
        user.get.return_value = response

        ret = get_time_from_enm_return_string_with_gtm_offset(user, time)
        self.assertTrue(ret == "2018-08-22 05:00:00 GTM+0100")

    def test_get_time_from_enm_return_string_with_gtm_offset_success_on_retry(self):
        user = self.user
        time = "05:00:00"
        response = Mock()
        response.json.return_value = {u'date': 1534950498956, u'serverLocation': u'Europe/Dublin', u'offset': 3600000}
        user.get.side_effect = [HTTPError(), response]

        ret = get_time_from_enm_return_string_with_gtm_offset(user, time)
        self.assertTrue(ret == "2018-08-22 05:00:00 GTM+0100")

    def test_create_request_body(self):
        ne_names = [Mock(), Mock(), Mock()]

        nhc_payload_body = {"name": 'test_name',
                            "description": "",
                            "jobType": "NODE_HEALTH_CHECK",
                            "configurations": [{"neType": "RadioNode",
                                                "properties": [{"key": "NODE_HEALTH_CHECK_TEMPLATE",
                                                                "value": "PREUPGRADE"}]}],
                            "mainSchedule": {"scheduleAttributes": [{"name": "START_DATE",
                                                                     "value": "test_time"}],
                                             "execMode": "SCHEDULED"},
                            "activitySchedules": [{"platformType": "ECIM",
                                                   "value": [{"neType": "RadioNode",
                                                              "value": [{"activityName": "nodehealthcheck",
                                                                         "execMode": "IMMEDIATE",
                                                                         "order": 1,
                                                                         "scheduleAttributes": []}]}]}],
                            "neNames": ne_names,
                            "collectionNames": [],
                            "savedSearchIds": []}

        self.assertTrue(nhc_payload_body == create_nhc_request_body(name='test_name', ne_elements=ne_names,
                                                                    time='test_time'))

    @patch("enmutils_int.lib.nhc.nhc_profile_payload")
    @patch("enmutils_int.lib.nhc.get_profile_rules")
    def test_create_nhc_profile__success(self, mock_get_profile_rules, mock_nhc_profile_payload):
        mock_get_profile_rules.return_value = rules
        mock_nhc_profile_payload.return_value = profile_payload
        response = Mock(ok=True)
        response.json.return_value = {"name": "HealthCheckProfile_administrator_03082020133401", "poId": 132167249,
                                      "status": "success"}
        self.user.post.return_value = response
        expected_profile_name = "HealthCheckProfile_administrator_03082020133401"
        actual_output = create_nhc_profile(user=self.user, ne_type="RadioNode", package_dict=radio_node_package,
                                           name="test_name")
        self.assertEqual(expected_profile_name, actual_output)

    @patch("enmutils_int.lib.nhc.nhc_profile_payload")
    @patch("enmutils_int.lib.nhc.get_profile_rules")
    def test_create_nhc_profile__raises_error(self, mock_get_profile_rules, mock_nhc_profile_payload):
        mock_get_profile_rules.return_value = rules
        mock_nhc_profile_payload.return_value = profile_payload
        response = Mock(ok=False)
        self.user.post.return_value = response
        self.assertRaises(HTTPError, create_nhc_profile, user=self.user, ne_type="RadioNode",
                          package_dict=radio_node_package, name="test_name")

    def test_nhc_profile_payload(self):

        payload = {"name": 'test_name',
                   "description": "",
                   "neType": 'RadioNode',
                   "packageName": radio_node_package['packageName'],
                   "productNumber": radio_node_package['productNumber'],
                   "productRevision": radio_node_package['productRevision'],
                   "productRelease": radio_node_package['productRelease'],
                   "createdBy": self.user.username,
                   "profileRules": rules,
                   "userLabel": []}

        self.assertTrue(payload == nhc_profile_payload(user=self.user, name='test_name', ne_type='RadioNode',
                                                       package=radio_node_package, rules=rules))

    @patch("enmutils_int.lib.nhc.update_profile_rules_to_ignore_alarm_checks")
    def test_get_profile_rules__success(self, mock_update_profile_rules):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = profile_rules_response
        self.user.post.return_value = response
        expected_rules = mock_update_profile_rules.return_value = rules
        actual_output = get_profile_rules(user=self.user, ne_type="RadioNode",
                                          package_dict=radio_node_package)
        self.assertEqual(expected_rules, actual_output)

    def test_get_profile_rules__response_not_ok(self):
        response = Mock(status_code=500, ok=False)
        response.json.return_value = profile_rules_response
        self.user.post.return_value = response
        self.assertRaises(HTTPError, get_profile_rules, self.user, "RadioNode", package_dict=radio_node_package)

    def test_update_profile_rules_to_ignore_alarm_checks(self):
        expected_output = rules
        actual_output = update_profile_rules_to_ignore_alarm_checks(rules)
        self.assertEqual(expected_output, actual_output)

    def test_get_nhc_job_payload(self):
        nhc_payload_body = job_payload
        actual_payload = get_nhc_job_payload(name='test_name', ne_elements=[], time='test_time',
                                             profile_name='test_profile', ne_type='RadioNode')
        self.assertEqual(nhc_payload_body, actual_payload)

    @patch('enmutils_int.lib.nhc.log')
    @patch("enmutils_int.lib.nhc.get_nhc_job_payload")
    def test_create_nhc_job__success(self, mock_get_nhc_job_payload, mock_log):
        ne_names = [Mock(), Mock()]
        time = "05:00:00"
        mock_get_nhc_job_payload.return_value = job_payload
        response = Mock(ok=True)
        self.user.post.return_value = response
        create_nhc_job(user=self.user, profile_name='test1_name', ne_elements=ne_names, scheduled_time=time,
                       ne_type="RadioNode", name="test2_name")
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.nhc.get_nhc_job_payload")
    def test_create_nhc_job__response_not_ok(self, mock_get_nhc_job_payload):
        ne_names = [Mock(), Mock()]
        time = "05:00:00"
        mock_get_nhc_job_payload.return_value = job_payload
        response = Mock(ok=False)
        self.user.post.return_value = response
        create_nhc_job(user=self.user, profile_name='test1_name', ne_elements=ne_names, scheduled_time=time,
                       ne_type="RadioNode", name="test2_name")
        self.assertTrue(response.raise_for_status.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
