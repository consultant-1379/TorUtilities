#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest2

from mock import patch, Mock
from requests.exceptions import HTTPError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.asr_flows.asrl_flow import ASRL01Profile
from enmutils_int.lib.asr_management import (get_asr_config_status, EnmApplicationError, update_asr_record,
                                             get_all_asr_records_info, get_asr_record_info_based_on_id,
                                             get_asr_record_info_based_on_type, activate_and_deactivate_asr_record,
                                             perform_asr_preconditions, perform_asr_postconditions,
                                             wait_asr_record_to_active_state, EnvironError, TimeOutError,
                                             check_if_asr_record_nb_ip_port_configured,
                                             check_if_asr_record_nb_ip_port_configured_in_enm,
                                             check_if_asr_record_nb_ip_port_configured_in_network_file,
                                             wait_asr_record_to_deactivate_state,
                                             perform_asr_preconditions_and_postconditions)


class ASR_managementUnitTests(unittest2.TestCase):

    asrl_config_status = ("FDN : ASRLConfiguration=ASR-L\nadministrationState : INACTIVE\n"
                          "asrConfigurationId : ASR-L\ncbs : false\ncriteriaSpecification : []\n"
                          "description : Analytic Session Record for LTE Radio\n"
                          "fields : [{name=dataRadioBearerSetupTime}]\noperationalState : OK\n"
                          "owner : ASR\npmicSubscriptionPoid : 12100\nscheduleInfo : null\n"
                          "streamInfo : {ipAddress=141.137.172.163, port=443}\ntype : ASR_L\n1 instance(s)")
    asrn_config_status = ("FDN : ASRNConfiguration=ASR-N\nadministrationState : INACTIVE\n"
                          "asrConfigurationId : ASR-N\ncbs : false\ncriteriaSpecification : []\n"
                          "description : Analytic Session Record for LTE Radio\n"
                          "fields : [{name=dataRadioBearerSetupTime}]\noperationalState : OK\n"
                          "owner : ASR\npmicSubscriptionPoid : 12100\nscheduleInfo : null\n"
                          "streamInfo : {ipAddress=141.137.172.163, port=443}\ntype : ASR_N\n1 instance(s)")
    asrl_record = {u'lastActivationTime': 1607594689712, u'pmicSubscriptionPoid': 12100,
                   u'scheduleInfo': None, u'name': u'ASR-L', u'resourcesPoIds': [27246, 27227, 27389],
                   u'asrConfigurationId': u'ASR-L', u'administrationState': u'INACTIVE',
                   u'streamInfo': {u'ipAddress': u'141.137.172.163', u'port': 443},
                   u'fdn': u'ASRLConfiguration=ASR-L', u'poid': 9100, u'cbs': False,
                   u'lastModifiedUser': u'ASR_L_01_1210-10410041_u0',
                   u'persistenceTime': 1607596869055, u'criteriaSpecification': None,
                   u'fields': [{u'name': u'dataRadioBearerSetupTime'}, {u'name': u'hoCompletionTimeTgtCell'},
                               {u'name': u'initCtxtSetupTime'}], u'owner': u'ASR', u'lastModifiedTime': 1607596869001,
                   u'operationalState': u'NA', u'type': u'ASR_L', u'lastDeactivationTime': 1607596785583,
                   u'description': u'Analytic Session Record for LTE Radio'}
    asrn_record = {"poid": 9101, "asrConfigurationId": "ASR-N", "fdn": "ASRNConfiguration=ASR-N",
                   "description": "Analytic Session Record for NR",
                   "streamInfo": {"ipAddress": "141.137.232.57", "port": 14432},
                   "fields": [{"name": "systemWriteTime"}, {"name": "sessionStatus"}, {"name": "numEvents"}],
                   "administrationState": "INACTIVE", "operationalState": "NA", "scheduleInfo": None, "cbs": False,
                   "criteriaSpecification": None, "lastActivationTime": 1605858588018,
                   "lastDeactivationTime": 1605859357340, "lastModifiedTime": 1605859357340,
                   "lastModifiedUser": "administrator", "persistenceTime": 1605859362577,
                   "pmicSubscriptionPoid": 12113, "resourcesPoIds": [21012], u'type': u'ASR_N'}
    asrl_record_updated_response = {u'lastActivationTime': 1607594689712, u'pmicSubscriptionPoid': 12100,
                                    u'scheduleInfo': None, u'name': u'ASR-L', u'resourcesPoIds': [27246, 27227, 27389],
                                    u'asrConfigurationId': u'ASR-L', u'administrationState': u'INACTIVE',
                                    u'streamInfo': {u'ipAddress': u'141.137.172.163', u'port': 443},
                                    u'fdn': u'ASRLConfiguration=ASR-L', u'poid': 9100,
                                    u'cbs': False, u'lastModifiedUser': u'ASR_L_01_1210-10410041_u0',
                                    u'persistenceTime': 1607596869055, u'criteriaSpecification': None,
                                    u'fields': [{u'name': u'dataRadioBearerSetupTime'},
                                                {u'name': u'hoCompletionTimeTgtCell'},
                                                {u'name': u'initCtxtSetupTime'}], u'owner': u'ASR',
                                    u'lastModifiedTime': 1607596869001, u'operationalState': u'NA', u'type': u'ASR_L',
                                    u'lastDeactivationTime': 1607596785583,
                                    u'description': u'Analytic Session Record for LTE Radio'}

    def setUp(self):
        unit_test_utils.setup()
        self.profile = Mock()
        self.asrl01flow = ASRL01Profile
        self.USER = Mock()
        self.ASRL_CONFIG_STATUS_CMD = "cmedit get ASRLConfiguration=ASR-L"
        self.ALL_ASR_RECORDS = "/session-record/v1/record-configs"
        self.ASR_RECORD = self.ALL_ASR_RECORDS + "/{record_id}"
        self.ASR_RECORD_TYPES = ["ASR_L", "ASR_N"]
        self.SUPPORTED_ASR_RECORD_STATES = ['ACTIVATING', 'DEACTIVATING']
        self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS = 5
        self.SLEEP_TIME = 60
        self.teardown_list = []
        self.NB_IP = unit_test_utils.generate_configurable_ip()
        self.PORT = "443"
        self.nodes_list = [Mock(poid="27246", primary_type="RadioNode", node_id="LTE98dg2ERBS00001",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27227", primary_type="RadioNode", node_id="LTE98dg2ERBS00002",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27389", primary_type="RadioNode", node_id="LTE98dg2ERBS00003",
                                profiles=["ASR_L_01"])]

    def tearDown(self):
        unit_test_utils.tear_down()

    # get_asr_config_status test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_config_status__is_successful_if_asrl(self, mock_debug_log):
        response = Mock()
        response.get_output.return_value = self.asrl_config_status
        self.USER.enm_execute.return_value = response
        self.assertEqual(True, get_asr_config_status(self.USER, "ASR-L"))
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, self.USER.enm_execute.call_count)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_config_status__if_not_configured_if_asrl(self, mock_debug_log):
        response = Mock()
        response.get_output.return_value = " \n0 instance(s)"
        self.USER.enm_execute.return_value = response
        self.assertEqual(False, get_asr_config_status(self.USER, "ASR-L"))
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, self.USER.enm_execute.call_count)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_config_status__is_successful_if_asrn(self, mock_debug_log):
        response = Mock()
        response.get_output.return_value = self.asrn_config_status
        self.USER.enm_execute.return_value = response
        self.assertEqual(True, get_asr_config_status(self.USER, "ASR-N"))
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, self.USER.enm_execute.call_count)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_config_status__if_not_configured_if_asrn(self, mock_debug_log):
        response = Mock()
        response.get_output.return_value = " \n0 instance(s)"
        self.USER.enm_execute.return_value = response
        self.assertEqual(False, get_asr_config_status(self.USER, "ASR-N"))
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, self.USER.enm_execute.call_count)

    # get_asr_record_info_based_on_id test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_record_info_based_on_id__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.asrl_record
        self.USER.get.return_value = response
        get_asr_record_info_based_on_id(self.USER, "9100")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_record_info_based_on_id__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError({"userMessage": "something is wrong"})
        self.USER.get.return_value = response
        self.assertRaises(HTTPError, get_asr_record_info_based_on_id, self.USER, "9100")
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    # get_all_asr_records_info test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_all_asr_records_info__is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = [self.asrl_record, self.asrn_record]
        self.USER.get.return_value = response
        get_all_asr_records_info(self.USER)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_all_asr_records_info__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError({"userMessage": "Internal Server Error server error"})
        self.USER.get.return_value = response
        self.assertRaises(HTTPError, get_all_asr_records_info, self.USER)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    # get_asr_record_info_based_on_type test cases
    @patch("enmutils_int.lib.asr_management.get_all_asr_records_info")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_record_info_based_on_type__asrl_type_is_successful(self, mock_debug_log,
                                                                        mock_get_all_asr_records_info):
        mock_get_all_asr_records_info.return_value = [self.asrl_record, self.asrn_record]
        self.assertEqual([self.asrl_record], get_asr_record_info_based_on_type(self.USER, self.ASR_RECORD_TYPES[0]))
        mock_get_all_asr_records_info.assert_called_with(self.USER)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.get_all_asr_records_info")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_record_info_based_on_type__asrn_type_is_successful(self, mock_debug_log,
                                                                        mock_get_all_asr_records_info):
        mock_get_all_asr_records_info.return_value = [self.asrl_record, self.asrn_record]
        self.assertEqual([self.asrn_record], get_asr_record_info_based_on_type(self.USER, self.ASR_RECORD_TYPES[1]))
        mock_get_all_asr_records_info.assert_called_with(self.USER)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.get_all_asr_records_info")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_get_asr_record_info_based_on_type__raises_env_error_if_asr_records_not_found(
            self, mock_debug_log, mock_get_all_asr_records_info):
        mock_get_all_asr_records_info.return_value = []
        self.assertRaises(EnvironError, get_asr_record_info_based_on_type, self.USER, self.ASR_RECORD_TYPES[0])
        mock_get_all_asr_records_info.assert_called_with(self.USER)
        self.assertEqual(mock_debug_log.call_count, 1)

    # update_asr_record test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_update_asr_record__is_successful_for_asrl_record(self, mock_debug_log):
        self.asrl_record.update({"resourcesPoIds": ["24212", "25467"]})
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.asrl_record
        self.USER.put.return_value = response
        self.assertEqual(self.asrl_record, update_asr_record(self.USER, self.asrl_record))
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_update_asr_record__is_successful_for_asrn_record(self, mock_debug_log):
        self.asrn_record.update({"resourcesPoIds": ["24216", "25487"]})
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.asrn_record
        self.USER.put.return_value = response
        self.assertEqual(self.asrn_record, update_asr_record(self.USER, self.asrn_record))
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_update_asr_record__raises_http_error(self, mock_debug_log):
        self.asrl_record.update({"resourcesPoIds": ["24212", "25467"]})
        response = Mock()
        response.ok = False
        response.status_code = 422
        response.raise_for_status.side_effect = HTTPError({"userMessage": "Received ASR configuration is invalid"})
        self.USER.put.return_value = response
        self.assertRaises(HTTPError, update_asr_record, self.USER, self.asrl_record)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_update_asr_record__raises_enm_application_error(self, mock_debug_log):
        self.asrl_record.update({"resourcesPoIds": ["24212", "25467"]})
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {}
        self.USER.put.return_value = response
        self.assertRaises(EnmApplicationError, update_asr_record, self.USER, self.asrl_record)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(response.raise_for_status.called)

    # activate_and_deactivate_asr_record test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_activate_and_deactivate_asr_record__activate_asr_record_is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        self.asrl_record.update({"administrationState": "ACTIVATING"})
        response.json.return_value = self.asrl_record
        self.USER.put.return_value = response
        self.assertEqual(self.asrl_record, activate_and_deactivate_asr_record(self.USER, self.asrl_record,
                                                                              self.SUPPORTED_ASR_RECORD_STATES[0]))
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_activate_and_deactivate_asr_record__deactivate_asr_record_is_successful(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        self.asrl_record.update({"administrationState": "DEACTIVATING"})
        response.json.return_value = self.asrl_record
        self.USER.put.return_value = response
        self.assertEqual(self.asrl_record, activate_and_deactivate_asr_record(self.USER, self.asrl_record,
                                                                              self.SUPPORTED_ASR_RECORD_STATES[0]))
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_activate_and_deactivate_asr_record__raises_http_error(self, mock_debug_log):
        response = Mock()
        response.ok = False
        response.status_code = 422
        self.asrl_record.update({"administrationState": "ACTIVATING"})
        response.raise_for_status.side_effect = HTTPError({"userMessage": "Forbidden transition for old "
                                                                          "administrationState=ACTIVE and new "
                                                                          "administrationState=ACTIVE"})
        self.USER.put.return_value = response
        self.assertRaises(HTTPError, activate_and_deactivate_asr_record, self.USER,
                          self.asrl_record, self.SUPPORTED_ASR_RECORD_STATES[0])
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_activate_and_deactivate_asr_record__raises_enm_application_error(self, mock_debug_log):
        response = Mock()
        response.ok = True
        response.status_code = 200
        self.asrl_record.update({"administrationState": "ACTIVATING"})
        response.json.return_value = {}
        self.USER.put.return_value = response
        self.assertRaises(EnmApplicationError, activate_and_deactivate_asr_record, self.USER,
                          self.asrl_record, self.SUPPORTED_ASR_RECORD_STATES[0])
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.asr_management.perform_asr_postconditions")
    @patch("enmutils_int.lib.asr_management.perform_asr_preconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.add_error_as_exception")
    def test_perform_asr_preconditions_and_postconditions(self, mock_add_error, mock_perform_preconditions,
                                                          mock_perform_postconditions):
        mock_perform_preconditions.return_value = self.asrl_record_updated_response
        perform_asr_preconditions_and_postconditions(self.asrl01flow, self.nodes_list, "ASR_L")
        mock_perform_preconditions.assert_called_with(self.asrl01flow, ["27246", "27227", "27389"], "ASR_L")
        mock_perform_postconditions.assert_called_with(self.asrl01flow, self.asrl_record_updated_response, "ASR_L")
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.asr_management.perform_asr_postconditions")
    @patch("enmutils_int.lib.asr_management.perform_asr_preconditions")
    @patch("enmutils_int.lib.profile_flows.asr_flows.asrl_flow.ASRL01Profile.add_error_as_exception")
    def test_perform_asr_preconditions_and_postconditions_exception(self, mock_add_error, mock_preconditions, *_):
        mock_preconditions.side_effect = Exception
        perform_asr_preconditions_and_postconditions(self.asrl01flow, self.nodes_list, "ASR_L")
        self.assertTrue(mock_add_error.called)

    # perform_asr_postconditions test cases
    @patch("enmutils_int.lib.asr_management.wait_asr_record_to_deactivate_state")
    @patch("enmutils_int.lib.asr_management.partial")
    @patch("enmutils_int.lib.asr_management.wait_asr_record_to_active_state")
    @patch("enmutils_int.lib.asr_management.activate_and_deactivate_asr_record")
    def test_perform_asr_postconditions__is_successful(self, mock_activate_and_deactivate_asr_record,
                                                       mock_wait_asr_record_to_active_state, mock_partial, *_):
        self.asrl_record.update({"administrationState": "ACTIVATING"})
        mock_activate_and_deactivate_asr_record.return_value = self.asrl_record
        self.asrl_record.update({"administrationState": "ACTIVE"})
        mock_wait_asr_record_to_active_state.return_value = self.asrl_record
        self.asrl_record.update({"administrationState": "INACTIVE"})
        perform_asr_postconditions(self, self.asrl_record, "ASR_L")
        mock_activate_and_deactivate_asr_record.assert_called_with(self.USER, self.asrl_record,
                                                                   self.SUPPORTED_ASR_RECORD_STATES[0])
        mock_wait_asr_record_to_active_state.assert_called_with(self.USER, self.asrl_record["poid"], self.SLEEP_TIME)
        self.assertTrue(mock_partial.called)
        self.assertEqual(2, len(self.teardown_list))

    @patch("enmutils_int.lib.asr_management.wait_asr_record_to_deactivate_state")
    @patch("enmutils_int.lib.asr_management.partial")
    @patch("enmutils_int.lib.asr_management.wait_asr_record_to_active_state")
    @patch("enmutils_int.lib.asr_management.activate_and_deactivate_asr_record")
    def test_perform_asr_postconditions__raises_env_error(self, mock_activate_and_deactivate_asr_record,
                                                          mock_wait_asr_record_to_active_state, mock_partial, *_):
        mock_activate_and_deactivate_asr_record.return_value = {}
        self.assertRaises(EnvironError, perform_asr_postconditions, self, self.asrl_record, "ASR_L")
        mock_activate_and_deactivate_asr_record.assert_called_with(self.USER, self.asrl_record,
                                                                   self.SUPPORTED_ASR_RECORD_STATES[0])
        self.assertFalse(mock_wait_asr_record_to_active_state.called)
        self.assertFalse(mock_partial.called)
        self.assertEqual(0, len(self.teardown_list))

    # perform_asr_preconditions test cases
    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.update_asr_record")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_perform_asr_preconditions__is_successful(self, mock_get_asr_record_info_based_on_type,
                                                      mock_update_asr_record, mock_debug_log, *_):
        nodes_poids = ["24212", "25467"]
        mock_get_asr_record_info_based_on_type.return_value = [self.asrn_record]
        self.asrn_record.update({"resourcesPoIds": nodes_poids})
        mock_update_asr_record.return_value = self.asrn_record
        perform_asr_preconditions(self, nodes_poids, "ASR_N")
        self.assertEqual(3, mock_debug_log.call_count)
        mock_update_asr_record.assert_called_with(self.USER, self.asrn_record)
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, "ASR_N")

    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.update_asr_record")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_perform_asr_preconditions__if_asr_record_update_status_is_empty(self,
                                                                             mock_get_asr_record_info_based_on_type,
                                                                             mock_update_asr_record,
                                                                             mock_debug_log, *_):
        nodes_poids = ["24212", "25467"]
        mock_get_asr_record_info_based_on_type.return_value = [self.asrn_record]
        self.asrn_record.update({"resourcesPoIds": nodes_poids})
        mock_update_asr_record.return_value = {}
        self.assertRaises(EnvironError, perform_asr_preconditions, self, nodes_poids, "ASR_N")
        self.assertEqual(3, mock_debug_log.call_count)
        mock_update_asr_record.assert_called_with(self.USER, self.asrn_record)
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, "ASR_N")

    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.update_asr_record")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_perform_asr_preconditions__if_asr_record_not_exist(self, mock_get_asr_record_info_based_on_type,
                                                                mock_update_asr_record, mock_debug_log, *_):
        nodes_poids = ["24212", "25467"]
        mock_get_asr_record_info_based_on_type.return_value = []
        self.assertRaises(EnvironError, perform_asr_preconditions, self, nodes_poids, "ASR_N")
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertFalse(mock_update_asr_record.called)
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, "ASR_N")

    # wait_asr_record_to_active_state test cases
    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch('enmutils_int.lib.asr_management.datetime.timedelta')
    @patch('enmutils_int.lib.asr_management.datetime.datetime')
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_id")
    def test_wait_asr_record_to_active_state__is_successful(self, mock_get_asr_record_info_based_on_id, mock_datetime,
                                                            mock_timedelta, mock_debug_log, *_):
        time_now = datetime(2020, 12, 11, 9, 0, 0)
        expiry_time = datetime(2020, 12, 11, 9, self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        self.asrl_record.update({"administrationState": "ACTIVE"})
        mock_get_asr_record_info_based_on_id.return_value = self.asrl_record
        wait_asr_record_to_active_state(self.USER, "9100", self.SLEEP_TIME)
        mock_get_asr_record_info_based_on_id.assert_called_with(self.USER, "9100")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch('enmutils_int.lib.asr_management.datetime.timedelta')
    @patch('enmutils_int.lib.asr_management.datetime.datetime')
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_id")
    def test_wait_asr_record_to_active_state__raises_timeout_error(self, mock_get_asr_record_info_based_on_id,
                                                                   mock_datetime, mock_timedelta, mock_debug_log, *_):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
        self.asrl_record.update({"administrationState": "ACTIVATING"})
        mock_get_asr_record_info_based_on_id.return_value = self.asrl_record
        self.assertRaises(TimeOutError, wait_asr_record_to_active_state, self.USER, "9100", self.SLEEP_TIME)
        mock_get_asr_record_info_based_on_id.assert_called_with(self.USER, "9100")
        self.assertEqual(mock_debug_log.call_count, 2)

    # check_if_asr_record_nb_ip_port_configured test cases
    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_enm")
    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_network_file")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asr_record_nb_ip_port_configured__configured_in_network_file(
            self, mock_debug_log, mock_check_nbip_port_network_file, mock_mock_check_nbip_port_enm):
        mock_mock_check_nbip_port_enm.return_value = False
        mock_check_nbip_port_network_file.return_value = True
        self.assertEqual(True, check_if_asr_record_nb_ip_port_configured(self, "ASR_N"))
        self.assertEqual(mock_debug_log.call_count, 2)
        mock_check_nbip_port_network_file.assert_called_with(self.USER, "ASR_N")
        self.assertTrue(mock_mock_check_nbip_port_enm.called)

    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_enm")
    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_network_file")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asr_record_nb_ip_port_configured__not_configured_in_network_file(
            self, mock_debug_log, mock_check_nbip_port_network_file, mock_mock_check_nbip_port_enm):
        mock_check_nbip_port_network_file.return_value = False
        mock_mock_check_nbip_port_enm.return_value = False
        self.assertEqual(False, check_if_asr_record_nb_ip_port_configured(self, "ASR_L"))
        self.assertEqual(mock_debug_log.call_count, 2)
        mock_check_nbip_port_network_file.assert_called_with(self.USER, "ASR_L")
        self.assertTrue(mock_mock_check_nbip_port_enm.called)

    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_enm")
    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_network_file")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asr_record_nb_ip_port_configured__configured_in_enm(
            self, mock_debug_log, mock_check_nbip_port_network_file, mock_mock_check_nbip_port_enm):
        mock_check_nbip_port_network_file.return_value = False
        mock_mock_check_nbip_port_enm.return_value = True
        self.assertEqual(True, check_if_asr_record_nb_ip_port_configured(self, "ASR_L"))
        self.assertEqual(2, mock_debug_log.call_count)
        mock_mock_check_nbip_port_enm.assert_called_with(self, "ASR_L")
        self.assertFalse(mock_check_nbip_port_network_file.called)

    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_enm")
    @patch("enmutils_int.lib.asr_management.check_if_asr_record_nb_ip_port_configured_in_network_file")
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asr_record_nb_ip_port_configured__not_configured_in_enm(
            self, mock_debug_log, mock_check_nbip_port_network_file, mock_mock_check_nbip_port_enm):
        mock_check_nbip_port_network_file.return_value = False
        mock_mock_check_nbip_port_enm.return_value = False
        self.assertEqual(False, check_if_asr_record_nb_ip_port_configured(self, "ASR_L"))
        self.assertEqual(2, mock_debug_log.call_count)
        mock_mock_check_nbip_port_enm.assert_called_with(self, "ASR_L")
        self.assertTrue(mock_check_nbip_port_network_file.called)

    # check_if_asr_record_nb_ip_port_configured_in_enm test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_check_if_asr_record_nb_ip_port_configured_in_enm__is_successful(
            self, mock_get_asr_record_info_based_on_type, mock_debug_log):
        self.asrl_record.update({"streamInfo": {"ipAddress": "141.137.172.163", "port": "443"}})
        mock_get_asr_record_info_based_on_type.return_value = [self.asrl_record]
        self.assertEqual(True, check_if_asr_record_nb_ip_port_configured_in_enm(self, self.ASR_RECORD_TYPES[0]))
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, self.ASR_RECORD_TYPES[0])
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_check_if_asr_record_nb_ip_port_configured_in_enm__if_not_configured(
            self, mock_get_asr_record_info_based_on_type, mock_debug_log):
        self.asrl_record.update({"streamInfo": {"ipAddress": "", "port": ""}})
        mock_get_asr_record_info_based_on_type.return_value = [self.asrl_record]
        self.assertEqual(False, check_if_asr_record_nb_ip_port_configured_in_enm(self, self.ASR_RECORD_TYPES[0]))
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, self.ASR_RECORD_TYPES[0])
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_type")
    def test_check_if_asr_record_nb_ip_port_configured_in_enm__if_asr_record_not_exist(
            self, mock_get_asr_record_info_based_on_type, mock_debug_log):
        mock_get_asr_record_info_based_on_type.return_value = []
        self.assertEqual(False, check_if_asr_record_nb_ip_port_configured_in_enm(self, self.ASR_RECORD_TYPES[0]))
        mock_get_asr_record_info_based_on_type.assert_called_with(self.USER, self.ASR_RECORD_TYPES[0])
        self.assertEqual(mock_debug_log.call_count, 3)

    # check_if_asr_record_nb_ip_port_configured_in_network_file test cases
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asrl_record_nb_ip_port_configured__configured_in_network_file(self, mock_debug_log):
        self.assertEqual(True, check_if_asr_record_nb_ip_port_configured_in_network_file(self, "ASR_L"))
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    def test_check_if_asrl_record_nb_ip_port_configured__not_configured_in_network_file(self, mock_debug_log):
        self.NB_IP = ""
        self.PORT = ""
        self.assertEqual(False, check_if_asr_record_nb_ip_port_configured_in_network_file(self, "ASR_L"))
        self.assertEqual(2, mock_debug_log.call_count)

    # wait_asr_record_to_deactivate_state test cases
    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch('enmutils_int.lib.asr_management.datetime.timedelta')
    @patch('enmutils_int.lib.asr_management.datetime.datetime')
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_id")
    def test_wait_asr_record_to_deactivate_state__is_successful(self, mock_get_asr_record_info_based_on_id,
                                                                mock_datetime, mock_timedelta, mock_debug_log, *_):
        time_now = datetime(2020, 12, 30, 9, 0, 0)
        expiry_time = datetime(2020, 12, 30, 11, 9, self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        self.asrl_record.update({"administrationState": "INACTIVE"})
        mock_get_asr_record_info_based_on_id.return_value = self.asrl_record
        wait_asr_record_to_deactivate_state(self.USER, "9100", self.SLEEP_TIME)
        mock_get_asr_record_info_based_on_id.assert_called_with(self.USER, "9100")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.asr_management.time.sleep", return_value=0)
    @patch("enmutils_int.lib.asr_management.log.logger.debug")
    @patch('enmutils_int.lib.asr_management.datetime.timedelta')
    @patch('enmutils_int.lib.asr_management.datetime.datetime')
    @patch("enmutils_int.lib.asr_management.get_asr_record_info_based_on_id")
    def test_wait_asr_record_to_deactivate_state__raises_timeout_error(self, mock_get_asr_record_info_based_on_id,
                                                                       mock_datetime, mock_timedelta, mock_debug_log,
                                                                       *_):
        time_now = datetime.now()
        expiry_time = time_now + timedelta(minutes=self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
        self.asrl_record.update({"administrationState": "DEACTIVATING"})
        mock_get_asr_record_info_based_on_id.return_value = self.asrl_record
        self.assertRaises(TimeOutError, wait_asr_record_to_deactivate_state, self.USER, "9100", self.SLEEP_TIME)
        mock_get_asr_record_info_based_on_id.assert_called_with(self.USER, "9100")
        self.assertEqual(mock_debug_log.call_count, 2)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
