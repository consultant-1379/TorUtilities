#!/usr/bin/env python
import json
import time
from datetime import datetime, timedelta

import responses
import unittest2
from enmutils.lib.exceptions import TimeOutError, EnmApplicationError, EnvironError
from enmutils_int.lib.pm_rest_nbi_subscriptions import StatisticalSubscription, Subscription, SubscriptionCreationError
from mock import patch, Mock, PropertyMock, call, MagicMock
from requests.exceptions import HTTPError
from testslib import unit_test_utils

URL = 'http://localhost'


class PmSubscriptionsUnitTests(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nok_response = None
        cls.nok_response_to_delete_request_in__delete = None
        cls.nok_response_to_get_in__get_counters = None
        cls.nok_response_to_get_in__get_by_id__sub_inactive = None
        cls.nok_response_to_get_in__get_events = None
        cls.nok_response_to_post_in___post = None
        cls.nok_response_to_post_in__create_subscription_on_enm = None
        cls.nok_response_to_post_in__fetch_subscription_id = None
        cls.nok_response_to_get_in__get_all = None

        cls.ok_response_to_put_in__update = None
        cls.ok_response_to_get_in__fetch_subscription_id = None
        cls.ok_response_to_get_in__fetch_subscription_id__sub_uetrace = None
        cls.ok_response_to_get_in__fetch_subscription_id__with_events = None
        cls.ok_response_to_get_in__get_all = None
        cls.ok_response_to_get_in__get_by_id__sub_active = None
        cls.ok_response_to_get_in__get_by_id__sub_inactive = None
        cls.ok_response_to_get_in__get_counters = None
        cls.ok_response_to_get_in__get_events = None
        cls.ok_response_to_get_in__getCellTrafficEvents = None
        cls.ok_response_to_get_in__getWcdmaEvents = None
        cls.ok_response_to_get_in__moinstances = None
        cls.ok_response_to_get_in__wait_for_state__sub_activating = None
        cls.ok_response_to_post_in___get_pos_by_poids = None
        cls.ok_response_to_post_in___get_pos_by_poids__no_ossModelIdentity = None
        cls.ok_response_to_post_in___post = None
        cls.ok_response_to_post_in__fetch_subscription_id = None
        cls.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on = None
        cls.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_off = None
        cls.ok_response_to_post_in__get_nodes_pm_function__empty = None
        cls.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_mixed = None
        cls.ok_response_to_post_in__get_nodes_pm_function__empty_json_json = None
        cls.ok_response_to_get_in__get_all__subs_inactive = None
        cls.nok_response_to_get_in__get_counters = None
        cls.nok_response_to_post_in__get_nodes_pm_function = None
        cls.ok_response_to_post_in__get_nodes_pm_function__empty_json = None
        cls.ok_response_to_get_in__get_mo_instances = None
        cls.ok_response_to_get_in__get_wcdma_events = None
        cls.get_counters_on_enm_response = None
        cls.ok_response_to_post_in___post_sub_deactive = None

    def create_mock_responses(self):
        mock_attributes = {'json.return_value': [], 'ok': 0}
        self.nok_response = Mock()
        self.nok_response.configure_mock(**mock_attributes)

        self.nok_response_to_post_in___post = self.nok_response
        self.nok_response_to_get_in__get_events = self.nok_response
        self.nok_response_to_get_in__get_counters = self.nok_response
        self.nok_response_to_delete_request_in__delete = self.nok_response
        self.nok_response_to_get_in__get_all = self.nok_response

        # POST '/managedObjects/getPosByPoIds' - OK
        json_response = [
            {"moName": "netsimlin537_ERBS0001", "moType": "NetworkElement", "poId": "181477779763365",
             "mibRootName": "netsimlin537_ERBS0001", "parentRDN": "", "fullMoType": "NetworkElement",
             "attributes": {"neType": "ERBS", "technologyDomain": ["EPS"], "ossModelIdentity": "16B-G.1.301"}}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in___get_pos_by_poids = Mock()
        self.ok_response_to_post_in___get_pos_by_poids.configure_mock(**mock_attributes)

        # POST '/managedObjects/getPosByPoIds' - OK but Invalid Node (Missing ossModelIdentity)
        json_response = [
            {"moName": "netsimlin537_ERBS0001", "moType": "NetworkElement", "poId": "181477779763365",
             "mibRootName": "netsimlin537_ERBS0001", "parentRDN": "", "fullMoType": "NetworkElement",
             "attributes": {"neType": "ERBS", "technologyDomain": ["EPS"]}}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in___get_pos_by_poids__no_ossModelIdentity = Mock()
        self.ok_response_to_post_in___get_pos_by_poids__no_ossModelIdentity.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - OK - pmFunction: ON
        json_response = [
            {"nodeType": "ERBS", "fdn": "NetworkElement=netsimlin537_ERBS0001", "poid": "181477779763365",
             "mimInfo": "16B-G.1.301", "technologyDomain": ["EPS"], "pmFunction": "ON"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on = Mock()
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - OK - pmFunction: OFF
        json_response = [
            {"nodeType": u"ERBS", "fdn": u"NetworkElement=netsimlin537_ERBS0001", "poid": u"181477779763365",
             "mimInfo": u"16B-G.1.301", "technologyDomain": [u"EPS"], "pmFunction": u"OFF"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_off = Mock()
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_off.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - OK - but - empty
        json_response = []
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__get_nodes_pm_function__empty = Mock()
        self.ok_response_to_post_in__get_nodes_pm_function__empty.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - OK - pmFunction: Mixed
        json_response = [
            {"nodeType": u"ERBS", "fdn": u"NetworkElement=netsimlin537_ERBS0001", "poid": u"181477779763365",
             "mimInfo": u"16B-G.1.301", "technologyDomain": [u"EPS"], "pmFunction": u"OFF"},
            {"nodeType": u"ERBS", "fdn": u"NetworkElement=netsimlin537_ERBS0002", "poid": u"181477779763366",
             "mimInfo": u"16B-G.1.301", "technologyDomain": [u"EPS"], "pmFunction": u"ON"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_mixed = Mock()
        self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_mixed.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - NOK
        json_response = []
        mock_attributes = {'json.return_value': json_response, 'raise_for_status.side_effect': HTTPError, 'ok': 0}
        self.nok_response_to_post_in__get_nodes_pm_function = Mock()
        self.nok_response_to_post_in__get_nodes_pm_function.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/nodePmEnabled' - Empty JSON
        json_response = []
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__get_nodes_pm_function__empty_json = Mock()
        self.ok_response_to_post_in__get_nodes_pm_function__empty_json.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/' - OK
        json_response = {"url": "/pm-service/rest/subscription/status/e6a52bad-e633-48c7-b5c6-34afb9550c3d"}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in__fetch_subscription_id = Mock()
        self.ok_response_to_post_in__fetch_subscription_id.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/' - NOK
        json_response = 'Not Found'
        mock_attributes = {'json.return_value': json_response, 'ok': 0}
        self.nok_response_to_post_in__create_subscription_on_enm = Mock()
        self.nok_response_to_post_in__create_subscription_on_enm.configure_mock(**mock_attributes)

        # GET /pm-service/rest/subscription/' - OK
        json_response = [
            {"id": ' + _id + ', "name": "Test_01", "nextVersionName": "null", "prevVersionName": "null", "owner": "",
             "description": "pm_03_load_profile_16B-normal_priority_cell-trace", "userType": "null",
             "type": "CELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVE", "operationalState": "null",
             "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1470159209809,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281475216504429", "name": "test-sub1", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "test-sub", "userType": "null",
             "type": "STATISTICAL", "scheduleInfo": "null", "administrationState": "ACTIVE", "operationalState": "null",
             "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1471855999321,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281475216504430", "name": "test-sub2", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "test-sub2", "userType": "null", "type": "STATISTICAL", "scheduleInfo": "null",
             "administrationState": "INACTIVE", "operationalState": "null",
             "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1471855999321,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281475216504431", "name": "test-sub3", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "test-sub2", "userType": "null", "type": "STATISTICAL", "scheduleInfo": "null",
             "administrationState": "DEACTIVATING", "operationalState": "null",
             "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1471855999321,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281475216504429", "name": "test-sub4", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "test-sub", "userType": "null",
             "type": "OTHER", "scheduleInfo": "null", "administrationState": "ACTIVE", "operationalState": "null",
             "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1471855999321,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281474986314202", "name": "ContinuousCellTraceSubscription", "nextVersionName": "null",
             "prevVersionName": "null", "owner": "PMIC",
             "description": "Continuous Cell Trace (CCTR) System Defined Subscription", "userType": "SYSTEM_DEF",
             "type": "CONTINUOUSCELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVE",
             "operationalState": "null", "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null",
             "rop": "FIFTEEN_MIN", "userActivationDateTime": "null", "userDeActivationDateTime": "null",
             "persistenceTime": 1470162240482, "pnpEnabled": "null", "filterOnManagedFunction": "null",
             "filterOnManagedElement": "null", "nodes": [], "cbs": "null", "criteriaSpecification": [],
             "nodeListIdentity": 0, "selectedNeTypes": "null", "nodeFilter": "null", "events": [], "outputMode": "null",
             "streamInfoList": [], "ueFraction": "null", "asnEnabled": "null", "ebsCounters": []},
            {"accessType": "FULL", "activationTime": 1515519610856, "administrationState": "ACTIVE", "cbs": "false",
             "counters": [], "criteriaSpecification": [], "deactivationTime": 1515518563519, "description": "",
             "filterOnManagedElement": "false", "filterOnManagedFunction": "false", "id": "281475216504428",
             "name": "test-sub", "nextVersionName": "", "nodeFilter": "NODE_TYPE", "nodeListIdentity": 0,
             "nodes": [], "numberOfNodes": 555, "operationalState": "NA", "owner": "administrator",
             "persistenceTime": 1521200080012, "pnpEnabled": "false", "prevVersionName": "", "rop": "FIFTEEN_MIN",
             "scheduleInfo": {"endDateTime": "null", "startDateTime": "null"},
             "selectedNeTypes": ["SGSN-MME", "RadioNode"],
             "taskStatus": "OK", "type": "STATISTICAL", "userActivationDateTime": 1515519609591,
             "userDeActivationDateTime": "null", "userType": "USER_DEF"},
            {"id": "1000001", "name": "test_celltrace", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "pm_03_load_profile_16B-normal_priority_cell-trace", "userType": "null",
             "type": "CELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVE", "operationalState": "null",
             "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1470159209809,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "1000002", "name": "test_uetrace", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "administrator", "description": "null", "userType": "USER_DEF", "type": "UETRACE",
             "scheduleInfo": {"startDateTime": "null", "endDateTime": "null"}, "administrationState": "INACTIVE",
             "operationalState": "NA", "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null",
             "rop": "FIFTEEN_MIN", "userActivationDateTime": "null", "userDeActivationDateTime": "null",
             "persistenceTime": 1470642821943, "outputMode": "FILE", "streamInfo": "null",
             "ueInfo": {"type": "IMSI", "value": "12345"},
             "nodeInfoList": [{"nodeGrouping": "ENODEB", "traceDepth": "MINIMUM", "interfaceTypes": []},
                              {"nodeGrouping": "MME", "traceDepth": "null", "interfaceTypes": []}],
             "traceReference": "111111010001"},
            {"accessType": "FULL", "activationTime": 1522680129243, "administrationState": "ACTIVE", "cbs": "false",
             "cellInfoList": [], "criteriaSpecification": [], "deactivationTime": "null",
             "description": "PM_29_load_profile_18A", "events": [], "filterOnManagedElement": "false",
             "filterOnManagedFunction": "false", "id": "281476900818149", "name": "test_celltraffic",
             "nextVersionName": "", "nodeFilter": "NODE_TYPE", "nodeListIdentity": 0, "nodes": [], "numberOfNodes": 20,
             "operationalState": "NA", "outputMode": "null", "owner": "PM_29_0402-15411795_u0",
             "persistenceTime": 1522680139898, "pnpEnabled": "false", "prevVersionName": "", "rop": "FIFTEEN_MIN",
             "scheduleInfo": {"endDateTime": "null", "startDateTime": "null"}, "selectedNeTypes": "null",
             "streamInfoList": [], "taskStatus": "OK", "triggerEventInfo": "null", "type": "CELLTRAFFIC",
             "userActivationDateTime": 1522680128603, "userDeActivationDateTime": "null", "userType": "USER_DEF"},
            {"accessType": "FULL", "activationTime": 1522676222017, "administrationState": "ACTIVE", "cbs": "false",
             "criteriaSpecification": [], "deactivationTime": "null", "description": "PM_47_load_profile_18A",
             "events": [], "filterOnManagedElement": "false", "filterOnManagedFunction": "false",
             "id": "281476865243020", "name": "test_uetr", "nextVersionName": "", "nodeFilter": "NODE_TYPE",
             "nodeListIdentity": 0, "nodes": [], "numberOfNodes": 20, "operationalState": "NA", "outputMode": "null",
             "owner": "PM_47_0402-14361527_u0", "persistenceTime": 1522676249743, "pnpEnabled": "false",
             "prevVersionName": "", "rop": "FIFTEEN_MIN",
             "scheduleInfo": {"endDateTime": "null", "startDateTime": "null"}, "selectedNeTypes": "null",
             "streamInfoList": [], "taskStatus": "OK", "type": "UETR", "ueInfoList": [],
             "userActivationDateTime": 1522676221425, "userDeActivationDateTime": "null", "userType": "USER_DEF"},
            {"accessType": "FULL", "activationTime": 1522556973885, "administrationState": "ACTIVE", "cbs": "false",
             "compressionEnabled": "null", "criteriaSpecification": [], "deactivationTime": "null",
             "description": "ebsm_04_load_profile_18A", "ebsCounters": [], "ebsEnabled": "false",
             "ebsOutputInterval": "null", "ebsOutputStrategy": "null", "events": [], "filterOnManagedElement": "false",
             "filterOnManagedFunction": "false", "id": "281475629117949", "name": "test_ebm",
             "nextVersionName": "", "nodeFilter": "NODE_TYPE", "nodeListIdentity": 0, "nodes": [], "numberOfNodes": 80,
             "operationalState": "NA", "outputMode": "null", "owner": "EBSM_04_0401-05274799_u0",
             "persistenceTime": 1522761130952, "pnpEnabled": "false", "prevVersionName": "", "rop": "ONE_MIN",
             "scheduleInfo": {"endDateTime": "null", "startDateTime": "null"}, "selectedNeTypes": "null",
             "streamInfoList": [], "taskStatus": "OK", "type": "EBM", "userActivationDateTime": 1522556911958,
             "userDeActivationDateTime": "null", "userType": "USER_DEF"},
            {"accessType": "FULL", "activationTime": 1523996496959, "administrationState": "ACTIVE",
             "applyOnAllCells": "null", "cbs": "false", "cellInfoList": [], "cellsSupported": "null",
             "criteriaSpecification": [], "deactivationTime": "null", "description": "PM_51_cbs_load_profile_18A",
             "events": [], "filterOnManagedElement": "false", "filterOnManagedFunction": "false",
             "id": "281475022995249", "name": "PM_51_0417-21211906", "nextVersionName": "", "nodeFilter": "NODE_TYPE",
             "nodeListIdentity": 0, "nodes": [], "numberOfNodes": 1, "operationalState": "NA", "outputMode": "null",
             "owner": "PM_51_0417-21211710_u0", "persistenceTime": 1523997053880, "pnpEnabled": "false",
             "prevVersionName": "", "rop": "FIFTEEN_MIN",
             "scheduleInfo": {"endDateTime": "null", "startDateTime": "null"}, "selectedNeTypes": "null",
             "streamInfoList": [], "taskStatus": "OK", "type": "GPEH", "ueFraction": "null",
             "userActivationDateTime": 1523996496379, "userDeActivationDateTime": "null", "userType": "USER_DEF"},

        ]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_all = Mock()
        self.ok_response_to_get_in__get_all.configure_mock(**mock_attributes)

        # GET /pm-service/rest/subscription/' - OK, Subscriptions INACTIVE
        json_response = [
            {"id": ' + _id + ', "name": "Test_01", "nextVersionName": "null", "prevVersionName": "null", "owner": "",
             "description": "pm_03_load_profile_16B-normal_priority_cell-trace", "userType": "null",
             "type": "CELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVE", "operationalState": "null",
             "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1470159209809,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281475216504428", "name": "test-sub", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "test-sub", "userType": "null",
             "type": "STATISTICAL", "scheduleInfo": "null", "administrationState": "INACTIVE",
             "operationalState": "null",
             "taskStatus": "OK", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
             "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": 1471855999321,
             "pnpEnabled": "null", "filterOnManagedFunction": "null", "filterOnManagedElement": "null", "nodes": [],
             "cbs": "null", "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": "null",
             "nodeFilter": "null", "events": [], "outputMode": "null", "streamInfoList": [], "ueFraction": "null",
             "asnEnabled": "null", "ebsCounters": []},
            {"id": "281474986314202", "name": "ContinuousCellTraceSubscription", "nextVersionName": "null",
             "prevVersionName": "null", "owner": "PMIC",
             "description": "Continuous Cell Trace (CCTR) System Defined Subscription", "userType": "null",
             "type": "CONTINUOUSCELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVE",
             "operationalState": "null", "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null",
             "rop": "FIFTEEN_MIN", "userActivationDateTime": "null", "userDeActivationDateTime": "null",
             "persistenceTime": 1470162240482, "pnpEnabled": "null", "filterOnManagedFunction": "null",
             "filterOnManagedElement": "null", "nodes": [], "cbs": "null", "criteriaSpecification": [],
             "nodeListIdentity": 0, "selectedNeTypes": "null", "nodeFilter": "null", "events": [], "outputMode": "null",
             "streamInfoList": [], "ueFraction": "null", "asnEnabled": "null", "ebsCounters": []}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_all__subs_inactive = Mock()
        self.ok_response_to_get_in__get_all__subs_inactive.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/281475216504428/' - INACTIVE
        json_response = ({
            "@class": "statistical", "id": "281475216504428", "name": "test-sub", "nextVersionName": "null",
            "prevVersionName": "null", "owner": "null", "description": "WORKLOAD TESTING", "userType": "USER_DEF",
            "type": "STATISTICAL", "scheduleInfo": {"startDateTime": "null", "endDateTime": "null"},
            "administrationState": "INACTIVE", "operationalState": "NA", "taskStatus": "OK", "activationTime": "null",
            "deactivationTime": "null", "rop": "FIFTEEN_MIN", "userActivationDateTime": "null",
            "userDeActivationDateTime": "null", "persistenceTime": 1454491812336, "pnpEnabled": False,
            "filterOnManagedFunction": False, "filterOnManagedElement": False, "nodes":
                [{"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00004",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00004",
                  "id": "281474977246413", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00007",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00007",
                  "id": "281474977284447", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00009",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00009",
                  "id": "281474977552281", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00008",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00008",
                  "id": "281474977207447", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00001",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00001",
                  "id": "281474977121930", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00005",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00005",
                  "id": "281474977013155", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00010",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00010",
                  "id": "281474977124031", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00003",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00003",
                  "id": "281474977388985", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00006",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00006",
                  "id": "281474976903951", "pmFunction": "OFF"},
                 {"neType": "ERBS", "fdn": "NetworkElement=ieatnetsimv5051-04_LTE16ERBS00002",
                  "ossModelIdentity": "6824-690-779", "name": "ieatnetsimv5051-04_LTE16ERBS00002",
                  "id": "281474977101562", "pmFunction": "OFF"}], "cbs": False, "criteriaSpecification": [],
            "nodeListIdentity": 0,
            "counters": [{"name": "pmAdmNrRrcUnknownArpRatio", "moClassType": "AdmissionControl"},
                         {"name": "pmLicDlCapActual", "moClassType": "BbProcessingResource"},
                         {"name": "pmLicDlCapDistr", "moClassType": "BbProcessingResource"}]})
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_by_id__sub_inactive = Mock()
        self.ok_response_to_get_in__get_by_id__sub_inactive.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/281475216504428/' - ACTIVE
        json_response = (
            {"@class": "statistical", "id": "281475216504428", "name": "test-sub", "nextVersionName": "null",
             "prevVersionName": "null", "owner": "null", "description": "WORKLOAD TESTING", "userType": "USER_DEF",
             "type": "STATISTICAL", "scheduleInfo": {"startDateTime": "null", "endDateTime": "null"},
             "administrationState": "ACTIVE", "operationalState": "NA", "taskStatus": "OK", "activationTime": "null",
             "deactivationTime": "null", "rop": "FIFTEEN_MIN", "userActivationDateTime": "null",
             "userDeActivationDateTime": "null", "persistenceTime": 1454491812336, "pnpEnabled": "false",
             "filterOnManagedFunction": "false", "filterOnManagedElement": "false", "nodes": ["blah-blah"],
             "cbs": "false", "criteriaSpecification": [],
             "nodeListIdentity": 0,
             "counters": [{"name": "pmAdmNrRrcUnknownArpRatio", "moClassType": "AdmissionControl"},
                          {"name": "pmLicDlCapActual", "moClassType": "BbProcessingResource"},
                          {"name": "pmLicDlCapDistr", "moClassType": "BbProcessingResource"}]})
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_by_id__sub_active = Mock()
        self.ok_response_to_get_in__get_by_id__sub_active.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/281475216504428/' - INACTIVE
        json_response = {}
        mock_attributes = {'json.return_value': json_response, 'ok': 0, 'status_code': 500}
        self.nok_response_to_get_in__get_by_id__sub_inactive = Mock()
        self.nok_response_to_get_in__get_by_id__sub_inactive.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/' - ACTIVATING
        json_response = [
            {"id": "281475216504428", "name": "test-sub", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "", "description": "pm_03_load_profile_17A-normal_priority_cell-trace", "userType": "null",
             "type": "CELLTRACE", "scheduleInfo": "null", "administrationState": "ACTIVATING",
             "operationalState": "null", "taskStatus": "ERROR", "activationTime": "null", "deactivationTime": "null",
             "rop": "FIFTEEN_MIN", "userActivationDateTime": "null", "userDeActivationDateTime": "null",
             "persistenceTime": 1471855999321, "pnpEnabled": "null", "filterOnManagedFunction": "null",
             "filterOnManagedElement": "null", "nodes": [], "cbs": "null", "criteriaSpecification": [],
             "nodeListIdentity": 0, "selectedNeTypes": "null", "nodeFilter": "null", "events": [], "outputMode": "null",
             "streamInfoList": [], "ueFraction": "null", "asnEnabled": "null", "ebsCounters": []}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__wait_for_state__sub_activating = Mock()
        self.ok_response_to_get_in__wait_for_state__sub_activating.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/counters' - OK
        json_response = [
            {"counterName": "pmLbMeasuredUe", "sourceObject": "UtranFreqRelation",
             "description": "Number of UE selected for measurement qualifying for load balancing action to cells on "
                            "the related UTRAN frequency\nValues are accumulated in each ROP and used to calculate the "
                            "LB measurement success rate for the related cells."},
            {"counterName": "pmOutDroppedPacketsPolicyControl", "sourceObject": "VpnInterface",
             "description": "The number of transmitted inner IP datagrams which are dropped due to mismatch of the "
                            "policy rules for any tunnel."}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_counters = Mock()
        self.ok_response_to_get_in__get_counters.configure_mock(**mock_attributes)

        counters_from_enm = [
            {'scannerType': 'USER_DEFINED', 'sourceObject': 'CounterClassA', 'description': 'Testing.',
             'counterName': 'counter1'},
            {'scannerType': 'USER_DEFINED', 'sourceObject': 'CounterClassB', 'description': 'Testing.',
             'counterName': 'counter2'},
            {'scannerType': 'SYSTEM_DEFINED', 'sourceObject': 'CounterClassC', 'description': 'Testing.',
             'counterName': 'counter3'},
            {'scannerType': 'USER_DEFINED', 'sourceObject': 'CounterClassD', 'description': 'Testing.',
             'counterName': 'counter4'},
            {'scannerType': 'USER_DEFINED', 'sourceObject': 'CounterClassE', 'description': 'Testing.',
             'counterName': 'counter5'}
        ]
        self.get_counters_on_enm_response = Mock()
        self.get_counters_on_enm_response.ok = True
        self.get_counters_on_enm_response.json.return_value = counters_from_enm

        # GET '/pm-service/rest/pmsubscription/counters' - NOK
        self.nok_response_to_get_in__get_counters = self.nok_response

        # GET '/pm-service/rest/subscription/status/e6a52bad-e633-48c7-b5c6-34afb9550c3d' - OK
        json_response = {
            "@class": "Subscription", "id": "999999999999999", "name": "test-me", "nextVersionName": "null",
            "prevVersionName": "null", "owner": "null", "description": "null", "userType": "null",
            "type": "STATISTICAL", "scheduleInfo": "null", "administrationState": "null", "operationalState": "null",
            "taskStatus": "null", "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
            "userActivationDateTime": "null", "userDeActivationDateTime": "null", "persistenceTime": "null"}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__fetch_subscription_id = Mock()
        self.ok_response_to_get_in__fetch_subscription_id.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/2814/activate' - OK
        json_response = {"name": "profile_name", "persistenceTime": 1613543621447,
                         "administrationState": "ACTIVATING", "userActivationDateTime": 1613543621434,
                         "userDeactivationDateTime": None, "id": 2814}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in___post = Mock()
        self.ok_response_to_post_in___post.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/subscription/2814/deactivate' - OK
        json_response = {"name": "profile_name", "persistenceTime": 1613543621447,
                         "administrationState": "DEACTIVATING", "userActivationDateTime": 1613543621434,
                         "userDeactivationDateTime": None, "id": 2814}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_post_in___post_sub_deactive = Mock()
        self.ok_response_to_post_in___post_sub_deactive.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/getEvent*' - OK
        json_response = [
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRING", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_RESET", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_STARTED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_CAP_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PRB_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PROCESSOR_LOAD", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_events = Mock()
        self.ok_response_to_get_in__get_events.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/getWcdmaEvents*' - OK
        json_response = [
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRING", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_RESET", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_STARTED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_CAP_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PRB_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PROCESSOR_LOAD", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_wcdma_events = Mock()
        self.ok_response_to_get_in__get_wcdma_events.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/cells' - OK
        json_response = [
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS01-1"},
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS01-2"},
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS01-3"},
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS02-1"},
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS02-2"},
            {"nodeName": "RNC12345", "moInstanceName": "UtranCellId=RNC12345RBS02-3"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__get_mo_instances = Mock()
        self.ok_response_to_get_in__get_mo_instances.configure_mock(**mock_attributes)

        # POST '/pm-service/rest/pmsubscription' - NOK
        json_response = {
            "url": ""}
        mock_attributes = {'json.return_value': json_response, 'ok': 0}
        self.nok_response_to_post_in__fetch_subscription_id = Mock()
        self.nok_response_to_post_in__fetch_subscription_id.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/status/e6a52bad-e633-48c7-b5c6-34afb9550c3d' - OK
        json_response = {
            "@class": "class_blah", "id": "999999999999999", "name": "Test_01", "nextVersionName": "null",
            "prevVersionName": "null", "owner": "administrator", "description": "null", "userType": "USER_DEF",
            "type": "type_BLAH", "scheduleInfo": {"startDateTime": "null", "endDateTime": "null"},
            "administrationState": "INACTIVE", "operationalState": "NA", "taskStatus": "OK", "activationTime": "null",
            "deactivationTime": "null", "rop": "FIFTEEN_MIN", "userActivationDateTime": "null",
            "userDeActivationDateTime": "null", "persistenceTime": 1470641663184, "pnpEnabled": False,
            "filterOnManagedFunction": False, "filterOnManagedElement": False, "nodes": [], "cbs": False,
            "criteriaSpecification": [], "nodeListIdentity": 0, "selectedNeTypes": [], "nodeFilter": "NODE_TYPE",
            "events": [
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRED"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRING"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_EVENT_LIC_GRACE_PERIOD_RESET"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_EVENT_LIC_GRACE_PERIOD_STARTED"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_PER_CAP_LICENSE_UTIL_REP"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_PER_PRB_LICENSE_UTIL_REP"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_PER_PROCESSOR_LOAD"},
                {"groupName": "CAPACITY_MANAGEMENT_EVALUATION", "name": "INTERNAL_PER_RADIO_UTILIZATION"}],
            "outputMode": "FILE", "streamInfoList": [], "ueFraction": 1000, "asnEnabled": False, "ebsCounters": []}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__fetch_subscription_id__with_events = Mock()
        self.ok_response_to_get_in__fetch_subscription_id__with_events.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/subscription/status/e46d8b0a-274a-4921-982d-c2c31a06d65b' - OK
        json_response = {"@class": "uetrace", "id": "281478003419189", "name": "Test_02", "nextVersionName": "null",
                         "prevVersionName": "null", "owner": "administrator", "description": "null",
                         "userType": "USER_DEF", "type": "UETRACE",
                         "scheduleInfo": {"startDateTime": "null", "endDateTime": "null"},
                         "administrationState": "INACTIVE", "operationalState": "NA", "taskStatus": "OK",
                         "activationTime": "null", "deactivationTime": "null", "rop": "FIFTEEN_MIN",
                         "userActivationDateTime": "null", "userDeActivationDateTime": "null",
                         "persistenceTime": 1470642821943, "outputMode": "FILE", "streamInfo": "null",
                         "ueInfo": {"type": "IMSI", "value": "12345"},
                         "nodeInfoList": [{"nodeGrouping": "ENODEB", "traceDepth": "MINIMUM", "interfaceTypes": []},
                                          {"nodeGrouping": "MME", "traceDepth": "null", "interfaceTypes": []}],
                         "traceReference": "111111010001"}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__fetch_subscription_id__sub_uetrace = Mock()
        self.ok_response_to_get_in__fetch_subscription_id__sub_uetrace.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/getCellTrafficEvents',
        json_response = {
            "triggerEvents": [{"eventProducerId": "BLAH",
                               "eventName": "NBAP_COMPRESSED_MODE_COMMAND", "sourceObject": "EXTERNAL_EVENTS"},
                              {"eventProducerId": "BLAH",
                               "eventName": "NBAP_DEDICATED_MEASUREMENT_FAILURE_INDICATION",
                               "sourceObject": "EXTERNAL_EVENTS"},
                              {"eventProducerId": "BLAH",
                               "eventName": "NBAP_DEDICATED_MEASUREMENT_INITIATION_FAILURE",
                               "sourceObject": "EXTERNAL_EVENTS"}],
            "nonTriggerEvents": [{"eventProducerId": "BLAH",
                                  "eventName": "NBAP_AUDIT_FAILURE", "sourceObject": "EXTERNAL_EVENTS"},
                                 {"eventProducerId": "BLAH",
                                  "eventName": "NBAP_AUDIT_REQUEST", "sourceObject": "EXTERNAL_EVENTS"}]}
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__getCellTrafficEvents = Mock()
        self.ok_response_to_get_in__getCellTrafficEvents.configure_mock(**mock_attributes)

        # GET '/pm-service/rest/pmsubscription/moinstances' - OK
        json_response = [{"nodeName": "netsimlin537_ERBS0001", "moInstanceName": "UtranCell=RNC02-1-1"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__moinstances = Mock()
        self.ok_response_to_get_in__moinstances.configure_mock(**mock_attributes)

        # GET, 'http://localhost/pm-service/rest/pmsubscription/getWcdmaEvents*' - OK
        json_response = [
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_EXPIRING", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_RESET", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_EVENT_LIC_GRACE_PERIOD_STARTED", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_CAP_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PRB_LICENSE_UTIL_REP", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"},
            {"eventProducerId": "BLAH",
             "eventName": "INTERNAL_PER_PROCESSOR_LOAD", "sourceObject": "CAPACITY_MANAGEMENT_EVALUATION"}]
        mock_attributes = {'json.return_value': json_response, 'ok': 200}
        self.ok_response_to_get_in__getWcdmaEvents = Mock()
        self.ok_response_to_get_in__getWcdmaEvents.configure_mock(**mock_attributes)

        # PUT '/pm-service/rest/subscription/281478003419189/' - OK
        json_response = {"url": "/pm-service/rest/subscription/status/e6a52bad-e633-48c7-b5c6-34afb9550c3d"}
        mock_attributes = {'json.return_value': json_response, 'ok': 202}
        self.ok_response_to_put_in__update = Mock()
        self.ok_response_to_put_in__update.configure_mock(**mock_attributes)

    @staticmethod
    def setup_nodes():
        nodes = unit_test_utils.setup_test_node_objects(2, primary_type="ERBS")
        nodes[0].poid, nodes[1].poid = "181477779763365", "281477779763363"
        return nodes


class SubscriptionUnitTests(PmSubscriptionsUnitTests):
    @classmethod
    def setUpClass(cls):
        super(SubscriptionUnitTests, cls).setUpClass()

    def setUp(self):
        unit_test_utils.setup()
        PmSubscriptionsUnitTests.create_mock_responses(self)
        nodes = PmSubscriptionsUnitTests.setup_nodes()

        self.mock_user = Mock()
        self.mock_user.username = "blah"

        self.stats_sub = StatisticalSubscription('test-sub', nodes=nodes, user=self.mock_user)
        self.stats_sub.parsed_nodes = [{'fdn': "NetworkElement=ieatnetsimv5051-01_LTE01ERBS00001",
                                        'id': "181477779763365",
                                        'ossModelIdentity': "1094-174-285",
                                        'neType': "ERBS",
                                        'pmFunction': '',
                                        'technologyDomain': ["EPS"]}]

        self.sub_user = Mock()
        self.NUM_NODES = {"ERBS": -1}
        self.sub = StatisticalSubscription('test-sub', nodes=nodes, user=self.mock_user,
                                           node_types=self.NUM_NODES.keys())
        self.sub.parsed_nodes = self.stats_sub.parsed_nodes
        self.sub.lte_reserved_counters = 4

        self.counters = [{'moClassType': u'CounterClass{0}'.format(_), 'name': u'pmCounter{0}'.format(_)}
                         for _ in xrange(10)]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_nodes_attached_to_subscription_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_nodes_attached_to_subscription_object_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_poll_scanners_profile_setting",
           return_value=True)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.__init__", return_value=None)
    def test_is_scanner_poll_required__returns_true_if_poll_scanners_set(self, *_):
        stats_sub = Subscription(name="TEST_01")
        stats_sub.poll_scanners = True
        self.assertTrue(stats_sub._is_scanner_poll_required())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_nodes_attached_to_subscription_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_nodes_attached_to_subscription_object_exceeds_threshold", return_value=True)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_poll_scanners_profile_setting",
           return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.__init__", return_value=None)
    def test_is_scanner_poll_required__returns_true_when_node_count_attached_to_subscription_object_is_above_threshold(
            self, *_):
        stats_sub = Subscription(name="TEST_01")
        stats_sub.poll_scanners = False
        stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        stats_sub.nodes = [Mock()] * 11

        self.assertTrue(stats_sub._is_scanner_poll_required())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.__init__", return_value=None)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_poll_scanners_profile_setting",
           return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_nodes_attached_to_subscription_object_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_nodes_attached_to_subscription_exceeds_threshold", return_value=True)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold", return_value=False)
    def test_is_scanner_poll_required__returns_True_when_node_count_on_enm_is_above_threshold(
            self, *_):
        stats_sub = Subscription(name="TEST_01")
        self.assertTrue(stats_sub._is_scanner_poll_required())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.__init__", return_value=None)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_poll_scanners_profile_setting",
           return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_nodes_attached_to_subscription_object_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_nodes_attached_to_subscription_exceeds_threshold", return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold", return_value=False)
    def test_is_scanner_poll_required__returns_False_if_all_checks_fail(self, *_):
        stats_sub = Subscription(name="TEST_01")
        self.assertFalse(stats_sub._is_scanner_poll_required())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test__check_poll_scanners_profile_setting__returns_true(self, _):
        self.stats_sub.poll_scanners = True
        self.assertTrue(self.stats_sub.check_poll_scanners_profile_setting())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test__check_poll_scanners_profile_setting__returns_false(self, _):
        self.stats_sub.poll_scanners = False
        self.assertFalse(self.stats_sub.check_poll_scanners_profile_setting())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_nodes_attached_to_subscription_object_exceeds_threshold__returns_true(self, _):
        self.stats_sub.nodes = [Mock()] * 11
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertTrue(self.stats_sub.check_nodes_attached_to_subscription_object_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_nodes_attached_to_subscription_object_exceeds_threshold__returns_false(self, _):
        self.stats_sub.nodes = [Mock()] * 9
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertFalse(self.stats_sub.check_nodes_attached_to_subscription_object_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription")
    def test_get_number_of_nodes_attached_to_subscription_on_enm__is_successful(self, mock_get_subscription, _):
        nodes = [Mock()] * 10
        mock_get_subscription.return_value = {"nodes": nodes}
        self.assertEqual(self.stats_sub.get_number_of_nodes_attached_to_subscription_on_enm(), 10)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription")
    def test_get_number_of_nodes_attached_to_subscription_on_enm__returns_zero_if_no_nodes_in_subscription(
            self, mock_get_subscription, _):
        mock_get_subscription.return_value = {"other": "blah"}
        self.assertEqual(self.stats_sub.get_number_of_nodes_attached_to_subscription_on_enm(), 0)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "get_number_of_nodes_attached_to_subscription_on_enm", return_value=11)
    def test_check_number_of_nodes_attached_to_subscription_exceeds_threshold__returns_true(self, *_):
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertTrue(self.stats_sub.check_number_of_nodes_attached_to_subscription_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "get_number_of_nodes_attached_to_subscription_on_enm", return_value=9)
    def test_check_number_of_nodes_attached_to_subscription_exceeds_threshold__returns_false(self, *_):
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertFalse(self.stats_sub.check_number_of_nodes_attached_to_subscription_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           return_value=11)
    def test__check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold__returns_true(self, *_):
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertTrue(self.stats_sub.check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           return_value=9)
    def test__check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold__returns_false(self, *_):
        self.stats_sub.NODE_COUNT_THRESHOLD_FOR_SCANNER_POLL_FEATURE = 10
        self.assertFalse(self.stats_sub.check_number_of_scanners_tied_to_subscription_on_enm_exceeds_threshold())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription."
           "get_number_of_nodes_attached_to_subscription_on_enm", return_value=10000)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_if_scanner_polling_complete",
           side_effect=[False, False, True])
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           side_effect=[7000, 8000, 9100])
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_scanners__is_successful_when_scanner_threshold_count_reached(
            self, mock_datetime, mock_timedelta, mock_sleep, mock_get_number_of_active_scanner,
            mock_check_if_scanner_polling_complete, *_):
        self.stats_sub.number_of_nodes_attached_to_subscription = 0
        self.stats_sub.MAX_MINUTES_TO_WAIT_FOR_SCANNERS = 10

        time_now = datetime(2020, 1, 1, 1, 0, 0)
        expiry_time = datetime(2020, 1, 1, 1, self.stats_sub.MAX_MINUTES_TO_WAIT_FOR_SCANNERS, 0)

        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now

        self.stats_sub._wait_for_scanners("activation")

        self.assertEqual(2, mock_sleep.call_count)
        self.assertEqual(mock_get_number_of_active_scanner.call_count, 3)
        self.assertEqual(mock_check_if_scanner_polling_complete.call_count, 3)
        self.assertTrue(call("activation", 7000, 0) in mock_check_if_scanner_polling_complete.mock_calls)
        self.assertTrue(call("activation", 8000, 0) in mock_check_if_scanner_polling_complete.mock_calls)
        self.assertTrue(call("activation", 9100, 0) in mock_check_if_scanner_polling_complete.mock_calls)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_if_scanner_polling_complete",
           return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           return_value=7000)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_scanners__is_successful_when_scanner_threshold_count_never_reached(
            self, mock_datetime, mock_timedelta, mock_sleep, mock_get_number_of_active_scanner,
            mock_check_if_scanner_polling_complete, *_):
        self.stats_sub.number_of_nodes_attached_to_subscription = 10000
        self.stats_sub.MAX_MINUTES_TO_WAIT_FOR_SCANNERS = 10

        time_now = datetime(2020, 1, 1, 1, 0, 0)
        expiry_time = datetime(2020, 1, 1, 1, self.stats_sub.MAX_MINUTES_TO_WAIT_FOR_SCANNERS, 0)

        time_now_within_loop = [time_now, time_now, time_now, expiry_time]

        mock_datetime.now.side_effect = [time_now] + time_now_within_loop
        mock_timedelta.return_value = expiry_time - time_now

        self.stats_sub._wait_for_scanners("activation")

        self.assertEqual(3, mock_sleep.call_count)
        self.assertEqual(mock_get_number_of_active_scanner.call_count, 3)
        self.assertEqual(mock_check_if_scanner_polling_complete.call_count, 3)
        self.assertTrue(call("activation", 7000, 0) in mock_check_if_scanner_polling_complete.mock_calls)
        self.assertTrue(call("activation", 7000, 1) in mock_check_if_scanner_polling_complete.mock_calls)
        self.assertTrue(call("activation", 7000, 2) in mock_check_if_scanner_polling_complete.mock_calls)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__returns_true_if_scanner_count_is_zero_during_deactivation(self, _):
        self.assertTrue(self.stats_sub.check_if_scanner_polling_complete("deactivation", 0, 1))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__returns_false_if_scanner_count_is_zero_during_activation(self, _):
        self.assertFalse(self.stats_sub.check_if_scanner_polling_complete("activation", 0, 1))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__scanner_count_exceeds_threshold_during_activation(self, _):
        self.stats_sub.number_of_nodes_attached_to_subscription = 1000
        self.assertTrue(self.stats_sub.check_if_scanner_polling_complete("activation", 901, 1))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__scanner_count_exceeds_threshold_during_deactivation(self, _):
        self.stats_sub.number_of_nodes_attached_to_subscription = 1000
        self.assertTrue(self.stats_sub.check_if_scanner_polling_complete("deactivation", 99, 1))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__scanner_count_doesnt_change_during_activation(self, _):
        self.stats_sub.number_of_nodes_attached_to_subscription = 1000
        self.assertFalse(self.stats_sub.check_if_scanner_polling_complete("activation", 800, 4))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_if_scanner_polling_complete__scanner_count_doesnt_change_during_activation_after_max_tries(self, _):
        self.stats_sub.number_of_nodes_attached_to_subscription = 1000
        self.assertTrue(self.stats_sub.check_if_scanner_polling_complete("activation", 800, 5))

    # get_active_scanners_based_on_node_type test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.error')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_get_active_scanners_based_on_node_type__returns_zero_if_cmedit_returns_unexpected_result(self, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = "some_response\n"
        self.stats_sub.user.enm_execute.return_value = mock_response
        self.stats_sub.get_active_scanners_based_on_node_type("ERBS")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.error')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_get_active_scanners_based_on_node_type__returns_zero_if_cmedit_returns_non_number(self, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = ["PMICScannerInfo no instances", "Found"]
        self.stats_sub.user.enm_execute.return_value = mock_response
        self.assertEqual(0, self.stats_sub.get_active_scanners_based_on_node_type("RadioNode"))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.error')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_get_active_scanners_based_on_node_type__returns_number_of_nodes(self, *_):
        mock_response = Mock()
        mock_response.get_output.return_value = [u'PMICScannerInfo 3 instance(s) found', u'', u'', u'3 instance(s)']
        self.stats_sub.user.enm_execute.return_value = mock_response
        self.assertEqual(3, self.stats_sub.get_active_scanners_based_on_node_type("ERBS"))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.error')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_get_active_scanners_based_on_node_type__returns_zero_if_cmedit_returns_exception(self, *_):
        self.stats_sub.user.enm_execute.side_effect = Exception
        self.assertEqual(0, self.stats_sub.get_active_scanners_based_on_node_type("RadioNode"))

    # _get_number_of_active_scanners test cases
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.ne_types", new_callable=PropertyMock)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_active_scanners_based_on_node_type")
    def test_get_number_of_active_scanners__if_node_types_not_existed(self,
                                                                      mock_get_active_scanners_based_on_node_type,
                                                                      mock_ne_types, mock_debug_log):
        mock_ne_types.return_value = []
        self.stats_sub._get_number_of_active_scanners()
        self.assertFalse(mock_get_active_scanners_based_on_node_type.called)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_active_scanners_based_on_node_type")
    def test_get_number_of_active_scanners__is_successful(self, mock_get_active_scanners_based_on_node_type,
                                                          mock_debug_log):
        self.stats_sub.node_types = ["ERBS", "RadioNode"]
        mock_get_active_scanners_based_on_node_type.return_value = 3
        self.assertEqual(6, self.stats_sub._get_number_of_active_scanners())
        self.assertEqual(2, mock_get_active_scanners_based_on_node_type.call_count)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_active_scanners_based_on_node_type")
    def test_get_number_of_active_scanners__returns_zero_scanners(self, mock_get_active_scanners_based_on_node_type,
                                                                  mock_debug_log):
        self.stats_sub.node_types = ["ERBS"]
        mock_get_active_scanners_based_on_node_type.return_value = 0
        self.assertEqual(0, self.stats_sub._get_number_of_active_scanners())
        self.assertEqual(1, mock_get_active_scanners_based_on_node_type.call_count)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.__init__", return_value=None)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._activate")
    def test_activate__scanner_polling_doesnt_occur_if_poll_scanners_is_false(self, *_):
        stats_sub = Subscription(name="TEST_01")
        stats_sub.activate()

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           return_value=True)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._wait_for_scanners")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_active_scanners__if_scanners_are_active(self, mock_debug_log, mock_wait_for_scanners, *_):
        stats_sub = Subscription(name="TEST_01")
        stats_sub.check_scanner_status()
        self.assertTrue(mock_wait_for_scanners.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._get_number_of_active_scanners",
           return_value=False)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._wait_for_scanners")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_check_active_scanners__if_no_active_scanners(self, mock_debug_log, mock_wait_for_scanners, *_):
        stats_sub = Subscription(name="TEST_01")
        stats_sub.check_scanner_status()
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertFalse(mock_wait_for_scanners.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.'
           'remove_subscriptions_from_enm_via_pmserv')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_all')
    def test_clean_subscriptions_success_without_activation(self, *_):
        try:
            StatisticalSubscription.clean_subscriptions(name="Test_01", user=self.sub_user)
        except Exception as e:
            raise AssertionError("Shouldn't have raised exception: {0}".format(str(e)))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.'
           'remove_subscriptions_from_enm_via_pmserv')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_all')
    def test_clean_subscriptions__success_delete_all(self, *_):
        try:
            StatisticalSubscription.clean_subscriptions(name="Test_01", user=self.sub_user, delete_all=True)
        except Exception as e:
            raise AssertionError("Shouldn't have raised exception: {0}".format(str(e)))

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils.lib.enm_user_2.User')
    @patch('enmscripting.terminal.terminal.EnmTerminal.execute')
    def test_clean_subscriptions__is_successful_with_fast_set(self, mock_enm_execute, mock_user, _):
        mock_enm_execute.return_value = Mock(json_response='{}', http_code=200, success=True)

        mock_user.get.return_value = self.ok_response_to_get_in__get_all

        StatisticalSubscription.clean_subscriptions(name="Test_01", user=mock_user, fast=True)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_pos_by_poids(self, _):

        mock_response = Mock()
        json_dump = json.dumps([{"moName": "netsimlin537_ERBS0001",
                                 "moType": "NetworkElement",
                                 "poId": "181477779763365",
                                 "mibRootName": "netsimlin537_ERBS0001",
                                 "parentRDN": "",
                                 "fullMoType": "NetworkElement",
                                 "attributes": {"neType": "ERBS",
                                                "technologyDomain": ["EPS"],
                                                "ossModelIdentity": "16B-G.1.301"}}])
        mock_response.json.return_value = json.loads(json_dump)
        mock_response.status = 200
        self.mock_user.post.return_value = mock_response
        resp = self.sub._get_pos_by_poids(["181477779763365"])
        self.assertEqual(resp, {181477779763365: {u'attributes': {u'neType': u'ERBS',
                                                                  u'ossModelIdentity': u'16B-G.1.301',
                                                                  u'technologyDomain': [u'EPS']},
                                                  u'fullMoType': u'NetworkElement',
                                                  u'mibRootName': u'netsimlin537_ERBS0001',
                                                  u'moName': u'netsimlin537_ERBS0001',
                                                  u'moType': u'NetworkElement',
                                                  u'parentRDN': u'',
                                                  u'poId': u'181477779763365'}})

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_pos_by_poids_raise_error_for_status(self, _):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        self.mock_user.post.return_value = mock_response
        mock_response.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.sub._get_pos_by_poids, ["181477779763365"])

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__is_successful(self, *_):
        self.stats_sub.user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                                self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on]
        self.stats_sub.get_nodes_pm_function()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__raises_environerror_if_ossmodelidentity_missing(self, *_):
        self.stats_sub.user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids__no_ossModelIdentity]

        self.assertRaises(EnvironError, self.stats_sub.get_nodes_pm_function)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__raises_environerror_if_no_nodes_found_with_pmfunction_enabled(self, *_):
        self.stats_sub.user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                                self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_off]

        with self.assertRaises(EnvironError) as environ_error:
            self.stats_sub.get_nodes_pm_function()
        self.assertEqual("No valid nodes available with PmFunction enabled", environ_error.exception.message)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__raises_environerror_if_no_nodes_returned_when_trying_to_get_pmfunction_states(
            self, *_):
        self.stats_sub.user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                                self.ok_response_to_post_in__get_nodes_pm_function__empty]

        with self.assertRaises(EnvironError) as environ_error:
            self.stats_sub.get_nodes_pm_function()
        self.assertEqual("No valid nodes available with PmFunction enabled", environ_error.exception.message)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__raises_environerror_if_some_nodes_found_with_pmfunction_disabled(self, *_):
        self.stats_sub.user.post.side_effect = [
            self.ok_response_to_post_in___get_pos_by_poids,
            self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_mixed]

        self.assertEqual(len(self.stats_sub.get_nodes_pm_function()), 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    def test_get_nodes_pm_function__raises_HTTPError_if_post_operation_fails(self, *_):
        self.stats_sub.user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                                self.nok_response_to_post_in__get_nodes_pm_function]
        self.assertRaises(HTTPError, self.stats_sub.get_nodes_pm_function)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.check_subscription_state")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_state__is_successful(self, mock_datetime, mock_timedelta, *_):
        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)

        self.stats_sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.stats_sub._wait_for_state('ACTIVE')

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_state__raises_timeout_error(self, mock_datetime, mock_timedelta, *_):
        self.stats_sub.id = "281475216504428"

        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"name": "test", "administrationState": "ACTIVE"}

        self.stats_sub.user.get.side_effect = [self.nok_response_to_get_in__get_all,
                                               mock_response,
                                               Exception]

        self.assertRaises(TimeOutError, self.stats_sub._wait_for_state, 'ACTIVE')

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_create__raises_timeout_error(self, mock_datetime, mock_timedelta, *_):
        self.stats_sub.id = "281475216504428"

        gap_in_time = -10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)

        self.stats_sub.user.get.side_effect = [self.nok_response_to_get_in__get_all,
                                               self.ok_response_to_get_in__get_all__subs_inactive,
                                               Exception]

        self.assertRaises(TimeOutError, self.stats_sub._wait_for_create)

    def test__fetch_subscription__if_get_error_response(self):
        self.mock_user.get.side_effect = Exception("Simulated error")
        result = self.sub._fetch_subscriptions()
        self.assertIsNone(result)

    def test_get_system_subscription_name_by_pattern__is_successful(self):
        self.mock_user.get.return_value = Mock()

        erbs_sub_name = "ERBS System Defined Statistical Subscription"
        rbs_sub_name = "RBS System Defined Statistical Subscription"
        rnc_sub_name = "RNC Primary System Defined Statistical Subscription"
        epg_sub_name = "(v)EPG Statistical Subscription"
        cctr_sub_name = "ContinuousCellTraceSubscription"

        subscription_data = [
            {"id": "111", "name": erbs_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "ERBS system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"},
            {"id": "222", "name": rbs_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "RBS system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"},
            {"id": "333", "name": "RBS User Defined Subscription", "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "RBS user defined", "userType": "USER_DEF", "type": "STATISTICAL"},
            {"id": "444", "name": rnc_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "RNC user defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"},
            {"id": "555", "name": epg_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "EPG and vEPG system defined", "userType": "SYSTEM_DEF",
             "type": "STATISTICAL"},
            {"id": "666", "name": cctr_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "Continuous Cell Trace (CCTR) System Defined Subscription",
             "userType": "SYSTEM_DEF", "type": "CONTINUOUSCELLTRACE"}]

        self.mock_user.get.return_value.ok = 1

        self.mock_user.get.return_value.json.return_value = subscription_data

        self.assertEqual(erbs_sub_name, Subscription.get_system_subscription_name_by_pattern("ERBS", self.mock_user))
        self.assertEqual(rbs_sub_name, Subscription.get_system_subscription_name_by_pattern("RBS", self.mock_user))
        self.assertEqual(rnc_sub_name, Subscription.get_system_subscription_name_by_pattern("RNC Primary",
                                                                                            self.mock_user))
        self.assertEqual(epg_sub_name, Subscription.get_system_subscription_name_by_pattern("vEPG", self.mock_user))
        self.assertEqual(cctr_sub_name, Subscription.get_system_subscription_name_by_pattern("CCTR", self.mock_user))

    def test_get_system_subscription_name_by_pattern__raises_EnmApplicationError_if_match_not_found(self):
        self.mock_user.get.return_value = Mock()

        subscription_data = []

        self.mock_user.get.return_value.ok = 1
        self.mock_user.get.return_value.json.return_value = subscription_data

        self.assertRaises(EnmApplicationError, Subscription.get_system_subscription_name_by_pattern, "RNC",
                          self.mock_user)

    def test_get_system_subscription_name_by_pattern__raises_EnmApplicationError_if_more_than_one_match_found(self):
        self.mock_user.get.return_value = Mock()

        erbs1_sub_name = "ERBS type-1 System Defined Statistical Subscription"
        erbs2_sub_name = "ERBS type-2 System Defined Statistical Subscription"

        subscription_data = [
            {"id": "111", "name": erbs1_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"},
            {"id": "222", "name": erbs2_sub_name, "nextVersionName": "null", "prevVersionName": "null",
             "owner": "PMIC", "description": "system defined", "userType": "SYSTEM_DEF", "type": "STATISTICAL"}]

        self.mock_user.get.return_value.ok = 1
        self.mock_user.get.return_value.json.return_value = subscription_data

        self.assertRaises(EnmApplicationError, Subscription.get_system_subscription_name_by_pattern, "ERBS",
                          self.mock_user)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_unique_entities__is_successful(self, _):
        self.sub.parsed_nodes = [{'fdn': "NetworkElement=LTE01ERBS00001",
                                  'id': "281544319551806",
                                  'ossModelIdentity': "M19.Q3-669x-1.10",
                                  'neType': "ERBS",
                                  'pmFunction': '',
                                  'technologyDomain': ''}]
        model_ids_string = self.sub._unique_entities()
        self.assertEqual(model_ids_string, "ERBS:M19.Q3-669x-1.10,")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_unique_entities__is_successful_if_technology_domain_specified(self, _):
        self.sub.parsed_nodes = [{'fdn': "NetworkElement=LTE01ERBS00003",
                                  'id': "281544319551806",
                                  'ossModelIdentity': "18.Q4-R57A02",
                                  'neType': "RadioNode",
                                  'pmFunction': '',
                                  'technologyDomain': ["EPS"]}]
        technology_domain = 'EPS'
        model_ids_string = self.sub._unique_entities(technology_domain=technology_domain)
        self.assertEqual("RadioNode:18.Q4-R57A02:EPS,", model_ids_string)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_create')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_create_subscription_on_enm__fail(self, mock_debug_log, *_):
        self.ok_response_to_post_in__fetch_subscription_id.ok = 1
        self.sub.user.post.return_value = self.ok_response_to_post_in__fetch_subscription_id
        self.sub.user.get.return_value = self.ok_response_to_get_in__fetch_subscription_id
        parse_ebs_counters = [{"name": "pmEbsCuUpExampleCounter", "moClassType": "GNBCUUPFunction"}]
        nodes_for_subscription = [
            {"fdn": "NetworkElement=NR01gNodeBRadio00001", "id": "101601036", "pmFunction": "ON"}]
        parse_events = [{"groupName": "CCTR", "name": "CuUpTestEventEnm", "eventProducerId": "CUUP"}]
        data = {'scheduleInfo': {}, 'userType': 'USER_DEF', 'ebsEvents': parse_events, 'filterOnManagedFunction': False,
                'rop': 'FIFTEEN_MIN', 'id': None, '@class': 'Subscription', 'selectedNeTypes': ['RadioNode'],
                'ebsCounters': parse_ebs_counters, 'nodes': nodes_for_subscription, 'type': 'STATISTICAL',
                'events': parse_events, 'nodeFilter': 'NODE_TYPE', 'pnpEnabled': False,
                'description': 'WORKLOAD TESTING', 'administrationState': 'INACTIVE', 'criteriaSpecification': [],
                'streamInfoList': [], 'outputMode': 'FILE', 'name': 'test-me', 'cbs': False,
                'filterOnManagedElement': False, 'asnEnabled': False, 'operationalState': 'NA',
                'nextVersionName': None}
        self.sub.name = "PM_REST_NBI_02"
        self.sub.create_subscription_on_enm(data)
        self.sub.name = "PM_REST_NBI_01"
        self.sub.create_subscription_on_enm(data)
        self.assertEqual(7, mock_debug_log.call_count)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_create_subscription_on_enm__raises_http_error(self, mock_debug_log, _):
        self.sub.user.post.return_value = self.nok_response
        parse_ebs_counters = [{"name": "pmEbsCuUpExampleCounter", "moClassType": "GNBCUUPFunction"}]
        nodes_for_subscription = [
            {"fdn": "NetworkElement=NR01gNodeBRadio00001", "id": "101601036", "pmFunction": "ON"}]
        parse_events = [{"groupName": "CCTR", "name": "CuUpTestEventEnm", "eventProducerId": "CUUP"}]
        data = {'scheduleInfo': {}, 'userType': 'USER_DEF', 'ebsEvents': parse_events, 'filterOnManagedFunction': False,
                'rop': 'FIFTEEN_MIN', 'id': None, '@class': 'Subscription', 'selectedNeTypes': ['RadioNode'],
                'ebsCounters': parse_ebs_counters, 'nodes': nodes_for_subscription, 'type': 'STATISTICAL',
                'events': parse_events, 'nodeFilter': 'NODE_TYPE', 'pnpEnabled': False,
                'description': 'WORKLOAD TESTING', 'administrationState': 'INACTIVE', 'criteriaSpecification': [],
                'streamInfoList': [], 'outputMode': 'FILE', 'name': 'test-me', 'cbs': False,
                'filterOnManagedElement': False, 'asnEnabled': False, 'operationalState': 'NA',
                'nextVersionName': None}
        self.assertRaises(HTTPError, self.sub.create_subscription_on_enm, data)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_all')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test__teardown__returns_if_sub_id_is_not_set(self, mock_debug, *_):
        self.sub.id = None
        self.sub._teardown()
        mock_debug.assert_called_with('No id set for pm subsription. Not tearing down')

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.state', new_callable=PropertyMock,
           return_value="ACTIVE")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test__teardown__is_successful_if_Subscription_is_Active(
            self, mock_get_user, mock_deactivate, mock_delete, mock_clean_subscriptions, *_):
        self.sub.id = "123"
        self.sub.user = None
        self.stats_sub.name = "PM_REST_28147"
        self.sub._teardown()
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_get_user.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.state', new_callable=PropertyMock,
           return_value="ACTIVATING")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test__teardown__is_successful_if_Subscription_is_Activating(
            self, mock_get_user, mock_deactivate, mock_delete, mock_clean_subscriptions, *_):
        self.sub.id = "123"
        self.sub.user = None
        self.stats_sub.name = "PM_REST_28147"
        self.sub._teardown()
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_get_user.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.state', new_callable=PropertyMock,
           return_value="DEACTIVATING")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test__teardown__is_successful_if_Subscription_is_Deactivating(
            self, mock_get_user, mock_deactivate, mock_delete, mock_clean_subscriptions, *_):
        self.sub.id = "123"
        self.sub.user = None
        self.stats_sub.name = "PM_REST_28147"
        self.sub._teardown()
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertFalse(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_get_user.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.state', new_callable=PropertyMock,
           return_value="INACTIVATING")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test__teardown__is_successful_if_Subscription_is_inactivating(
            self, mock_get_user, mock_deactivate, mock_delete, mock_clean_subscriptions, *_):
        self.sub.id = "123"
        self.sub.user = Mock()
        self.stats_sub.name = "PM_REST_28147"
        self.sub._teardown()
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertFalse(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertFalse(mock_get_user.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.clean_subscriptions')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.state', new_callable=PropertyMock,
           return_value="ACTIVE")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.delete')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.deactivate')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test__teardown__raises_exception(
            self, mock_get_user, mock_deactivate, mock_delete, mock_clean_subscriptions, *_):
        self.sub.id = "123"
        self.sub.user = Mock()
        self.stats_sub.name = "PM_REST_28147"
        mock_deactivate.side_effect = [Exception("error")]
        self.sub._teardown()
        self.assertTrue(mock_clean_subscriptions.called)
        self.assertTrue(mock_deactivate.called)
        self.assertFalse(mock_delete.called)
        self.assertFalse(mock_get_user.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test_clean_subscriptions__is_successful_if_no_user_set(self, *_):
        self.stats_sub.name = "test-sub1"
        self.stats_sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.stats_sub.clean_subscriptions(self.stats_sub.name, True)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    def test_clean_subscriptions__is_successful_with_fast_set_to_true(self, *_):
        self.stats_sub.name = "test-sub1"
        self.stats_sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.stats_sub.clean_subscriptions(self.stats_sub.name, True, self.stats_sub.user)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_all')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.remove_subscriptions_from_enm_via_pmserv')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.get_workload_admin_user')
    def test_clean_subscriptions_is_successful_if_exists_same_profile_name_subscriptions(
            self, mock_get_user, mock_remove_subscriptions_from_enm_via_pmserv, mock_get_all, *_):
        self.stats_sub.name = "PM_67_281475"
        user = mock_get_user.return_value
        mock_get_all.return_value = [
            {u'scheduleInfo': {u'endDateTime': None, u'startDateTime': None}, u'accessType': u'FULL',
             u'nextVersionName': None, u'userType': u'USER_DEF', u'filterOnManagedFunction': False,
             u'rop': u'FIFTEEN_MIN', u'nodeListIdentity': 0, u'activationTime': 1565070969011,
             u'selectedNeTypes': [u'CISCO-ASR9000'], u'id': u'6160156', u'prevVersionName': None,
             u'owner': u'administrator', u'taskStatus': u'OK', u'nodes': [], u'userActivationDateTime': 1565070968446,
             u'numberOfNodes': 4, u'counters': [], u'nodeFilter': u'NODE_TYPE', u'pnpEnabled': False,
             u'description': u'PM_67_cbs_load_profile', u'administrationState': u'ACTIVE', u'deactivationTime': None,
             u'criteriaSpecification': [], u'name': u'PM_67_0801-18413620', u'cbs': False, u'type': u'STATISTICAL',
             u'persistenceTime': 1565070969357, u'filterOnManagedElement': False, u'operationalState': u'NA',
             u'userDeActivationDateTime': None},
            {u'scheduleInfo': {u'endDateTime': None, u'startDateTime': None}, u'accessType': u'FULL',
             u'nextVersionName': None, u'userType': u'USER_DEF', u'filterOnManagedFunction': False,
             u'rop': u'FIFTEEN_MIN', u'nodeListIdentity': 0, u'activationTime': 1565070941431,
             u'selectedNeTypes': [u'CISCO-ASR9000'], u'id': u'6160155', u'prevVersionName': None,
             u'owner': u'administrator', u'taskStatus': u'OK', u'nodes': [], u'userActivationDateTime': 1565070940822,
             u'numberOfNodes': 4, u'counters': [], u'nodeFilter': u'NODE_TYPE', u'pnpEnabled': False,
             u'description': u'PM_67_cbs_load_profile', u'administrationState': u'ACTIVE', u'deactivationTime': None,
             u'criteriaSpecification': [], u'name': u'PM_67_0801-18413619', u'cbs': False, u'type': u'STATISTICAL',
             u'persistenceTime': 1565070942016, u'filterOnManagedElement': False, u'operationalState': u'NA',
             u'userDeActivationDateTime': None}]
        self.stats_sub.clean_subscriptions(self.stats_sub.name[:6], user=user)
        self.assertTrue(mock_remove_subscriptions_from_enm_via_pmserv.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    def test_remove_subscriptions_from_enm_via_cmedit__fails_to_delete_subscription_via_cmcli(self, *_):
        subscriptions = [Mock()]
        self.stats_sub.user.enm_execute.side_effect = Exception()
        self.stats_sub.remove_subscriptions_from_enm_via_cmcli(self.stats_sub.user, subscriptions)

    # remove_subscriptions_from_enm_via_pmserv test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_remove_subscriptions_from_enm_via_pmserv__fails_to_delete_inactive_sub_via_pmserv(self, mock_log_info, *_):
        subscription = Mock(state="INACTIVE")
        subscription.name = "test_sub"
        subscription.delete.side_effect = Exception()

        self.stats_sub.remove_subscriptions_from_enm_via_pmserv(self.stats_sub.user, [subscription])
        self.assertTrue(subscription.delete.called)
        self.assertEqual(1, self.stats_sub.user.enm_execute.call_count)
        mock_log_info.assert_any_call("Subscription test_sub being deleted")
        self.assertEqual(2, mock_log_info.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_remove_subscriptions_from_enm_via_pmserv__fails_to_deactivate_active_sub_via_pmserv(self, mock_log_info,
                                                                                                 *_):
        subscription = Mock(state="ACTIVE")
        subscription.name = "test_sub"
        subscription.deactivate.side_effect = Exception()

        self.stats_sub.remove_subscriptions_from_enm_via_pmserv(self.stats_sub.user, [subscription])
        self.assertTrue(subscription.deactivate.called)
        mock_log_info.assert_any_call("Deactivating test_sub")
        self.assertEqual(2, mock_log_info.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    def test_remove_subscriptions_from_enm_via_pmserv__if_sub_is_activating(self, mock_log_info, *_):
        subscription = Mock(state="ACTIVATING")
        subscription.name = "test_sub"
        self.stats_sub.remove_subscriptions_from_enm_via_pmserv(self.stats_sub.user, [subscription])
        self.assertTrue(subscription.deactivate.called)
        self.assertTrue(subscription.delete.called)
        self.assertEqual(1, self.stats_sub.user.enm_execute.call_count)
        mock_log_info.assert_any_call("Subscription test_sub has been deleted")
        self.assertEqual(3, mock_log_info.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_create__if_sub_is_created(self, mock_datetime, mock_timedelta, *_):
        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)

        self.stats_sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.stats_sub._wait_for_create()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_create__if_sub_is_created_ok(self, mock_datetime, mock_timedelta, *_):
        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)
        res = Mock(ok=0)
        res.json.return_value = [{"name": "test", "id": "1"}]
        res1 = Mock(ok=1)
        res1.json.return_value = [{"name": "test", "id": "1"}]

        self.stats_sub.name = "test"
        self.stats_sub.user.get.side_effect = [res, self.ok_response_to_get_in__get_all, res1]
        self.stats_sub._wait_for_create()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_check_subscription_state(self, mock_datetime, mock_timedelta, *_):
        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)
        subscriptions = Mock(ok=0)
        subscriptions.json.return_value = {"name": "test", "administrationState": "ACTIVE"}

        self.stats_sub.name = "test"
        self.stats_sub.check_subscription_state(subscriptions, "ACTIVE", time.time())

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.time")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    def test_wait_for_create__if_sub_is_created_not_ok(self, mock_datetime, mock_timedelta, *_):
        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        time_now_values_for_while_loop = [time_now, time_now, time_now, expiry_time]
        mock_datetime.now.side_effect = [time_now] + time_now_values_for_while_loop

        mock_timedelta.return_value = timedelta(0, gap_in_time)
        self.ok_response_to_get_in__get_all.ok = 1
        self.stats_sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.stats_sub._wait_for_create()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.remove_subscriptions_from_enm_via_pmserv')
    def test_clean_subscriptions__is_successful_with_fast_set_to_false_and_subscriptions_are_active(
            self, mock_remove_subscriptions_from_enm_via_pmserv, mock_timedelta, mock_datetime, *_):
        sub_name = 'test-sub1'
        subscription_activating = Mock(ok=1)
        subscription_activating.json.return_value = {'name': sub_name, 'administrationState': 'ACTIVATING'}

        subscription_active = Mock(ok=1)
        subscription_active.json.return_value = {'name': sub_name, 'administrationState': 'ACTIVE'}

        subscription_deactivating = Mock(ok=1)
        subscription_deactivating.json.return_value = {'name': sub_name, 'id': '_',
                                                       'administrationState': 'DEACTIVATING'}

        subscriptions_inactive = Mock(ok=1)
        subscriptions_inactive.json.return_value = [{'name': sub_name, 'id': '_', 'administrationState': 'INACTIVE'}]

        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        mock_datetime.now.side_effect = [time_now, time_now, expiry_time, time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(0, gap_in_time)

        self.stats_sub.user.get.side_effect = [self.ok_response_to_get_in__get_all,
                                               subscription_active,
                                               subscription_deactivating,
                                               subscriptions_inactive]

        self.stats_sub.clean_subscriptions(name="test-sub1", fast=False, user=self.stats_sub.user, delete_all=False)
        self.assertTrue(mock_remove_subscriptions_from_enm_via_pmserv.called)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep", return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.info')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.datetime")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.datetime.timedelta")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.remove_subscriptions_from_enm_via_pmserv')
    def test_clean_subscriptions__is_successful_with_fast_set_to_false_and_subscriptions_are_activating(
            self, mock_remove_subscriptions_from_enm_via_pmserv, mock_timedelta, mock_datetime, *_):
        sub_name = 'test-sub1'
        subscription_activating = Mock(ok=1)
        subscription_activating.json.return_value = {'name': sub_name, 'administrationState': 'ACTIVATING'}

        subscriptions_active = Mock(ok=1)
        subscriptions_active.json.return_value = [{'name': sub_name, 'administrationState': 'ACTIVE'}]

        subscription_deactivating = Mock(ok=1)
        subscription_deactivating.json.return_value = {'name': sub_name, 'id': '_',
                                                       'administrationState': 'DEACTIVATING'}

        subscriptions_inactive = Mock(ok=1)
        subscriptions_inactive.json.return_value = [{'name': sub_name, 'id': '_', 'administrationState': 'INACTIVE'}]

        gap_in_time = 10
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=gap_in_time)

        mock_datetime.now.side_effect = [time_now, time_now, expiry_time, time_now, time_now, expiry_time, ]
        mock_timedelta.return_value = timedelta(0, gap_in_time)

        self.stats_sub.user.get.side_effect = [self.ok_response_to_get_in__get_all,
                                               subscription_activating,
                                               subscriptions_active,
                                               subscription_deactivating,
                                               subscriptions_inactive]

        self.stats_sub.clean_subscriptions(name="test-sub1", fast=False, user=self.stats_sub.user, delete_all=False)
        self.assertTrue(mock_remove_subscriptions_from_enm_via_pmserv.called)

    @responses.activate
    def test_delete__does_not_remove_id(self):
        self.sub.id = "281475216504428"
        responses.add(responses.DELETE, URL + '/pm-service/rest/subscription/281475216504428/',
                      body='',
                      status=200,
                      content_type='application/json')
        self.sub.delete()
        self.assertNotEquals(self.sub.id, None)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription')
    def test_delete__raises_HTTPError_if_get_response_not_ok(self, *_):
        self.stats_sub.user.delete_request.return_value = self.nok_response_to_delete_request_in__delete
        self.assertRaises(HTTPError, self.stats_sub.delete)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_by_name")
    def test_get_subscription__is_successful_if_name_not_set(self, mock_get_by_name, _):
        self.stats_sub.get_subscription()
        mock_get_by_name.assert_called_with("test-sub", self.stats_sub.user)
        self.assertTrue(mock_get_by_name.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_by_name")
    def test_get_subscription__is_successful_if_id_set(self, mock_get_by_name, _):
        self.stats_sub.id = 123
        self.stats_sub.get_subscription()
        self.assertFalse(mock_get_by_name.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_all__raises_HTTPError_if_get_response_not_ok(self, _):
        self.mock_user.get.return_value = self.nok_response_to_get_in__get_all
        self.assertRaises(HTTPError, Subscription.get_all, self.stats_sub.user)

    def test_get_by_name__raises_enm_application_error_if_subscription_does_not_exist(self):
        self.mock_user.get.return_value = self.ok_response_to_get_in__get_all
        self.assertRaises(EnmApplicationError, Subscription.get_by_name, "XXX", self.mock_user)

    def test_get_by_name__if_subscription_is_exist(self):
        self.mock_user.get.side_effect = [self.ok_response_to_get_in__get_all,
                                          self.ok_response_to_get_in__get_by_id__sub_active]
        expected_output = {'scheduleInfo': {'endDateTime': 'null', 'startDateTime': 'null'},
                           'accessType': 'FULL', 'userDeActivationDateTime': 'null', 'cbs': 'false',
                           'rop': 'FIFTEEN_MIN', 'filterOnManagedFunction': 'false', 'owner': 'administrator',
                           'nodeListIdentity': 0, 'taskStatus': 'OK', 'id': '281475216504428',
                           'selectedNeTypes': ['SGSN-MME', 'RadioNode'], 'prevVersionName': '',
                           'activationTime': 1515519610856, 'nodes': [], 'type': 'STATISTICAL', 'numberOfNodes': 555,
                           'counters': [], 'nodeFilter': 'NODE_TYPE', 'pnpEnabled': 'false', 'description': '',
                           'administrationState': 'ACTIVE', 'deactivationTime': 1515518563519,
                           'criteriaSpecification': [], 'name': 'test-sub', 'userType': 'USER_DEF',
                           'userActivationDateTime': 1515519609591, 'persistenceTime': 1521200080012,
                           'filterOnManagedElement': 'false', 'operationalState': 'NA', 'nextVersionName': ''}
        self.assertEqual(expected_output, Subscription.get_by_name("test-sub", self.mock_user))

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_get_by_id__is_successful(self, mock_debug_log):
        self.mock_user.get.return_value = self.ok_response_to_get_in__get_by_id__sub_active
        Subscription.get_by_id("281475216504428", self.mock_user)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_get_by_id__raises_http_error(self, mock_debug_log):
        self.mock_user.get.return_value = self.nok_response
        self.assertRaises(HTTPError, Subscription.get_by_id, "281475216504428", self.mock_user)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_validate_nodes_oss_model_identity__is_successful_with_non_sync_msc_nodes(self, _):
        nodes = [
            {u'attributes': {u'neType': u'MSC', u'technologyDomain': None, u'ossModelIdentity': None},
             u'managementState': None, u'poId': u'281475055436558', u'id': u'281475055436558'}]
        valid_nodes = self.sub._validate_nodes_oss_model_identity(nodes)
        self.assertEqual(valid_nodes[0]['attributes']['neType'], 'MSC')

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_validate_nodes_oss_model_identity__is_successful_with_non_sync_cudb_nodes(self, _):
        nodes = [
            {u'attributes': {u'neType': u'CUDB', u'technologyDomain': None, u'ossModelIdentity': None},
             u'managementState': None, u'poId': u'281475055436558', u'id': u'281475055436558'}]
        valid_nodes = self.sub._validate_nodes_oss_model_identity(nodes)
        self.assertEqual(valid_nodes[0]['attributes']['neType'], 'CUDB')

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_validate_nodes_oss_model_identity__is_successful_with_non_sync_minlink_6352_nodes(self, _):
        nodes = [
            {u'attributes': {u'neType': u'MINI-LINK-6352', u'technologyDomain': None, u'ossModelIdentity': None},
             u'managementState': None, u'poId': u'281475055436559', u'id': u'281475055436559'}]
        valid_nodes = self.sub._validate_nodes_oss_model_identity(nodes)
        self.assertEqual(valid_nodes[0]['attributes']['neType'], "MINI-LINK-6352")

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_validate_nodes_oss_model_identity__is_successful_with_non_sync_minlink_indoor_nodes(self, _):
        nodes = [
            {u'attributes': {u'neType': u'MINI-LINK-Indoor', u'technologyDomain': None, u'ossModelIdentity': None},
             u'managementState': None, u'poId': u'281475055436560', u'id': u'281475055436560'}]
        valid_nodes = self.sub._validate_nodes_oss_model_identity(nodes)
        self.assertEqual(valid_nodes[0]['attributes']['neType'], "MINI-LINK-Indoor")

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_validate_nodes_oss_model_identity__raises_environerror_if_node_deleted_on_enm(self, _):
        nodes = [{u'fdn': None, u'mibRootName': None, u'parentNeType': None, u'radioAccessTechnology': None,
                  u'ossModelIdentity': None, u'moName': u'Deleted', u'parentRDN': None, u'fullMoType': None,
                  u'moType': u'Deleted', u'attributes': None, u'managementState': None, u'poId': u'16903899',
                  u'id': u'16903899'}]
        self.assertRaises(EnvironError, self.sub._validate_nodes_oss_model_identity, nodes)

    # get_counters test cases
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    def test_get_counters__calls_get_counters_based_on_profile_if_tech_limits_set(
            self, mock_get_counters_based_on_profile, _):
        counters = Mock()
        mock_get_counters_based_on_profile.return_value = counters
        self.sub.technology_domain_counter_limits = {"EPS": 2}
        self.assertEqual(counters, self.sub.get_counters())
        self.assertTrue(mock_get_counters_based_on_profile.called)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._unique_entities")
    def test_get_counters__returns_after_excluding_counters(self, *_):
        self.sub.technology_domain_counter_limits = None
        self.mock_user.get.return_value = self.get_counters_on_enm_response
        self.sub.mo_class_counters_excluded = ['CounterClassD', 'CounterClassE']
        expected_counters = [{'moClassType': 'CounterClassA', 'name': 'counter1'},
                             {'moClassType': 'CounterClassB', 'name': 'counter2'},
                             {'moClassType': 'CounterClassC', 'name': 'counter3'}]
        self.assertEqual(expected_counters, self.sub.get_counters())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._unique_entities")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    def test_get_counters__returns_counters_if_definer_is_ebm_subscription_attributes(self, mock_debug_log, *_):
        self.sub.technology_domain_counter_limits = None
        self.mock_user.get.return_value = self.get_counters_on_enm_response
        self.sub.mo_class_counters_excluded = ['CounterClassD', 'CounterClassE']
        expected_counters = [{'moClassType': 'CounterClassA', 'name': 'counter1'},
                             {'moClassType': 'CounterClassB', 'name': 'counter2'},
                             {'moClassType': 'CounterClassC', 'name': 'counter3'}]
        self.assertEqual(expected_counters, self.sub.get_counters(definer="EBM_SubscriptionAttributes"))
        self.assertEqual(2, mock_debug_log.call_count)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._unique_entities")
    def test_get_counters__returns_if_no_counters_excluded_but_certain_counters_included(self, *_):
        self.sub.technology_domain_counter_limits = None
        self.mock_user.get.return_value = self.get_counters_on_enm_response
        self.sub.mo_class_counters_excluded = None
        self.sub.mo_class_counters_included = ['CounterClassA', 'CounterClassB']
        expected_counters = [{'moClassType': 'CounterClassA', 'name': 'counter1'},
                             {'moClassType': 'CounterClassB', 'name': 'counter2'}]
        self.assertEqual(expected_counters, self.sub.get_counters())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._unique_entities")
    def test_get_counters__raises_http_error(self, *_):
        self.sub.technology_domain_counter_limits = None
        self.mock_user.get.return_value = self.nok_response
        self.sub.mo_class_counters_excluded = None
        self.sub.mo_class_counters_included = ['CounterClassA', 'CounterClassB']
        self.assertRaises(HTTPError, self.sub.get_counters)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters_based_on_profile")
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._unique_entities")
    def test_get_counters__returns_if_no_counters_excluded_and_included(self, *_):
        self.sub.technology_domain_counter_limits = None
        self.mock_user.get.return_value = self.get_counters_on_enm_response
        self.sub.mo_class_counters_excluded = None
        self.sub.mo_class_counters_included = None
        expected_counters = [{'moClassType': 'CounterClassA', 'name': 'counter1'},
                             {'moClassType': 'CounterClassB', 'name': 'counter2'},
                             {'moClassType': 'CounterClassC', 'name': 'counter3'},
                             {'moClassType': 'CounterClassD', 'name': 'counter4'},
                             {'moClassType': 'CounterClassE', 'name': 'counter5'}]
        self.assertEqual(expected_counters, self.sub.get_counters())

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.get_tech_domain_counters_based_on_profile")
    def test_get_counters_based_on_profile__is_successful(self, mock_get_tech_domain_counters_based_on_profile):
        self.sub.get_counters_based_on_profile("NE")
        mock_get_tech_domain_counters_based_on_profile.assert_called_with(self.sub)

    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.get_tech_domain_counters_based_on_profile", return_value=[])
    def test_get_counters_based_on_profile__raises_environerror_if_no_counters_available(self, _):
        self.assertRaises(EnvironError, self.sub.get_counters_based_on_profile, "NE")

    # parse_counters test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__based_on_num_counters_float_value(self, mock_debug_log, mock_get_counters,
                                                               mock_filter_included_mo_class_sub_counters,
                                                               mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = 1.0
        self.sub.parse_counters()
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 0)
        self.assertEqual(mock_get_counters.call_count, 1)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__based_on_num_counters(self, mock_debug_log, mock_get_counters,
                                                   mock_filter_included_mo_class_sub_counters,
                                                   mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = 2
        mock_get_required_num_of_counters.return_value = 2
        self.sub.parse_counters()
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_counters.call_count, 1)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__if_num_counters_is_none(self, mock_debug_log, mock_get_counters,
                                                     mock_filter_included_mo_class_sub_counters,
                                                     mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = None
        mock_get_required_num_of_counters.return_value = 3
        self.sub.parse_counters()
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_counters.call_count, 1)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__if_definer_is_ebm_subscription_attributes(self, mock_debug_log, mock_get_counters,
                                                                       mock_filter_included_mo_class_sub_counters,
                                                                       mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = 2
        mock_get_required_num_of_counters.return_value = 2
        self.sub.parse_counters(definer="EBM_SubscriptionAttributes")
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_counters.call_count, 1)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_subscriptions.log.logger.debug')
    def test_parse_counters__if_sub_is_pm_76(self, mock_debug_log, mock_get_counters,
                                             mock_filter_included_mo_class_sub_counters,
                                             mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyByte'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = 2
        self.sub.name = "PM_76_18042419"
        mock_get_required_num_of_counters.return_value = 2
        self.sub.parse_counters()
        self.assertEqual(mock_debug_log.call_count, 6)
        self.assertEqual(mock_get_counters.call_count, 0)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__if_sub_is_pm_67(self, mock_debug_log, mock_get_counters,
                                             mock_filter_included_mo_class_sub_counters,
                                             mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyByte'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.num_counters = 2
        self.sub.name = "PM_67_18042419"
        mock_get_required_num_of_counters.return_value = 2
        self.sub.parse_counters()
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_get_counters.call_count, 1)
        self.assertEqual(mock_filter_included_mo_class_sub_counters.call_count, 0)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 1)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_required_num_of_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.filter_included_mo_class_sub_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_parse_counters__if_mo_class_sub_counters_included_is_available(self, mock_debug_log, mock_get_counters,
                                                                            mock_filter_included_mo_class_sub_counters,
                                                                            mock_get_required_num_of_counters):
        response = Mock()
        response.ok = True
        response.json.return_value = [{'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPkt64'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                       'counterName': u'cbQosIPHCTcpSentPktOverflow'},
                                      {'sourceObject': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
                                       'counterName': u'cbQosMatchPrePolicyBitRate'}]
        self.mock_user.get.return_value = response
        mock_get_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosMatchStmtStatsTable_Group',
             'name': u'cbQosMatchPrePolicyBitRate'}]
        self.sub.mo_class_sub_counters_included = {
            "CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group": ["cbQosIPHCTcpSentPktOverflow",
                                                                    "cbQosIPHCTcpSentPkt64"]}
        mock_filter_included_mo_class_sub_counters.return_value = [
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group', 'name': u'cbQosIPHCTcpSentPkt64'},
            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
             'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.sub.num_counters = 1.0
        self.assertEqual(mock_filter_included_mo_class_sub_counters.return_value, self.sub.parse_counters())
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_counters.call_count, 1)
        mock_filter_included_mo_class_sub_counters.assert_called_with(mock_get_counters.return_value)
        self.assertEqual(mock_get_required_num_of_counters.call_count, 0)

    def test_get_required_num_of_counters__when_num_counter_is_none(self):
        self.sub.num_counters = None
        counters = [{'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                     'name': u'cbQosIPHCTcpSentPkt64'},
                    {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                     'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.assertEqual(2, self.sub.get_required_num_of_counters(counters))

    def test_get_required_num_of_counters__is_successful(self):
        self.sub.num_counters = 1
        counters = [{'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                     'name': u'cbQosIPHCTcpSentPkt64'},
                    {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                     'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.assertEqual(1, self.sub.get_required_num_of_counters(counters))

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_log_pm_disabled_nodes__correctly_filters_nodes(self, mock_debug):
        json_data = {
            u'NetworkElement=netsim_LTE05ERBS00004': {
                u'nodeType': u'ERBS', u'pmFunction': u'OFF', u'fdn': u'NetworkElement=netsim_LTE05ERBS00004',
                u'mimInfo': u'19.Q2-J.2.650', u'technologyDomain': [u'EPS'], u'poid': u'4517985'},
            u'NetworkElement=netsim_LTE05ERBS00005': {
                u'nodeType': u'ERBS', u'pmFunction': u'OFF', u'fdn': u'NetworkElement=netsim_LTE05ERBS00005',
                u'mimInfo': u'19.Q2-J.2.650', u'technologyDomain': [u'EPS'], u'poid': u'4518004'},
            u'NetworkElement=netsim_LTE05ERBS00006': {
                u'nodeType': u'ERBS', u'pmFunction': u'ON', u'fdn': u'NetworkElement=netsim_LTE05ERBS00006',
                u'mimInfo': u'19.Q2-J.2.650', u'technologyDomain': [u'EPS'], u'poid': u'4517999'}}
        self.sub.log_pm_disabled_nodes(json_data)
        mock_debug.assert_called_with("A total of 2 nodes have returned a PMFunction not equal to 'ON'.\n"
                                      "{u'NetworkElement=netsim_LTE05ERBS00004': u'OFF', "
                                      "u'NetworkElement=netsim_LTE05ERBS00005': u'OFF'}\n")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_log_pm_disabled_nodes__only_logs_if_pm_function_is_disabled(self, mock_debug):
        json_data = {
            u'NetworkElement=netsim_LTE05ERBS00006': {
                u'nodeType': u'ERBS', u'pmFunction': u'ON', u'fdn': u'NetworkElement=netsim_LTE05ERBS00006',
                u'mimInfo': u'19.Q2-J.2.650', u'technologyDomain': [u'EPS'], u'poid': u'4517999'}}
        self.sub.log_pm_disabled_nodes(json_data)
        mock_debug.assert_called_with("Total number of nodes in response received\t1.")

    # _activate test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._post')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_activate__is_successful_if_validate_is_true(self, mock_debug_log, mock_post, mock_wait_for_state):
        self.sub.user.post.return_value = self.ok_response_to_post_in___post
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.sub._activate()
        mock_post.assert_called_with(state=True)
        mock_wait_for_state.assert_called_with("ACTIVE")
        mock_debug_log.assert_any_call("Checking ENM to determine if subscription test-sub is ACTIVE")
        self.assertEqual(3, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._post')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_activate__is_successful_if_validate_is_false(self, mock_debug_log, mock_post, mock_wait_for_state):
        self.sub.user.post.return_value = self.ok_response_to_post_in___post
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.sub._activate(validate=False)
        mock_post.assert_called_with(state=True)
        self.assertFalse(mock_wait_for_state.called)
        mock_debug_log.assert_any_call("Performing activation")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._post')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_deactivate__is_successful_if_validate_is_true(self, mock_debug_log, mock_post, mock_wait_for_state):
        self.sub.user.post.return_value = self.ok_response_to_post_in___post_sub_deactive
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.sub.deactivate()
        mock_post.assert_called_with(state=False)
        mock_wait_for_state.assert_called_with("INACTIVE")
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._post')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_deactivate__is_successful_if_validate_is_false(self, mock_debug_log, mock_post, mock_wait_for_state):
        self.sub.user.post.return_value = self.ok_response_to_post_in___post_sub_deactive
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_all
        self.sub.deactivate(validate=False)
        mock_post.assert_called_with(state=False)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_wait_for_state.call_count)

    # _post test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_post__is_successful(self, mock_debug_log, mock_get_subscription):

        self.sub.user.post.return_value = self.ok_response_to_post_in___post
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_by_id__sub_active
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        self.sub._post("activate")
        self.assertEqual(1, mock_get_subscription.call_count)
        self.assertEqual(4, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_post__if_sub_id_exist(self, mock_debug_log, mock_get_subscription):
        self.sub.user.post.return_value = self.ok_response_to_post_in___post
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_by_id__sub_active
        self.sub.id = "281475216504428"
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        self.sub._post("activate")
        # self.assertEqual(0, mock_get_subscription.call_count)
        self.assertEqual(4, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_post__raises_http_error_if_sub_activation_failed(self, mock_debug_log, mock_get_subscription):
        self.sub.user.get.return_value = self.ok_response_to_get_in__get_by_id__sub_active
        self.sub.user.put.return_value = Mock(ok=False, json="error")
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        self.assertRaises(HTTPError, self.sub._post, "activate")
        self.assertEqual(1, mock_get_subscription.call_count)
        self.assertEqual(3, mock_debug_log.call_count)

    # ne_types test cases
    def test_ne_types__is_successful(self):
        self.sub.nodes = [Mock(primary_type="ERBS", node_id=1, NE_TYPE="ERBS"),
                          Mock(primary_type="RadioNode", node_id=2, NE_TYPE="RadioNode")]
        self.assertEqual(['ERBS', 'RadioNode'], self.sub.ne_types)

    def test_ne_types__if_nodes_doesnt_exist(self):
        self.sub.nodes = []
        self.assertEqual([], self.sub.ne_types)

    # create test cases
    def test_create__raises_not_implemented_error(self):
        stats_sub = Subscription(name="TEST_01")
        self.assertRaises(NotImplementedError, stats_sub.create)

    # get_nodes_for_subscription test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.nodes_list', new_callable=PropertyMock,
           return_value=[Mock()])
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_nodes_for_subscription__is_successful(self, mock_debug_log, _):
        self.sub.get_nodes_for_subscription()
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.nodes_list', new_callable=PropertyMock,
           return_value=[])
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_nodes_for_subscription__raises_environ_error(self, mock_debug_log, _):
        self.assertRaises(EnvironError, self.sub.get_nodes_for_subscription)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_get_nodes_for_subscription__raises_environ_error_if_nodes_not_exist(self, mock_debug_log, _):
        self.sub.nodes = []
        self.assertRaises(EnvironError, self.sub.get_nodes_for_subscription)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._wait_for_state')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_wait_for_state2__is_successful(self, mock_debug_log, mock_wait_for_state):
        self.sub.wait_for_state("active")
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_wait_for_state.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription._wait_for_create')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_wait_for_create__is_successful(self, mock_debug_log, mock_wait_for_create):
        self.sub.wait_for_create()
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_wait_for_create.call_count)

    # sgsn_mme_exists_and_is_synchronized test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_sgsn_mme_exists_and_is_synchronized__is_successful(self, mock_debug_log):
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = [u'CmFunction 4 instance(s) found', u'', u'', u'4 instance(s)']
        self.mock_user.enm_execute.return_value = mock_enm_response
        self.assertEqual(True, self.sub.sgsn_mme_exists_and_is_synchronized(self.mock_user))
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_sgsn_mme_exists_and_is_synchronized__if_sgsn_synced_nodes_not_existed(self, mock_debug_log):
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = [u'CmFunction 0 instance(s) found', u'', u'', u'0 instance(s)']
        self.mock_user.enm_execute.return_value = mock_enm_response
        self.assertEqual(False, self.sub.sgsn_mme_exists_and_is_synchronized(self.mock_user))
        self.assertEqual(3, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_sgsn_mme_exists_and_is_synchronized__if_match_pattern_not_existed(self, mock_debug_log):
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = [u'', u'', u'0 instance(s)']
        self.mock_user.enm_execute.return_value = mock_enm_response
        self.assertEqual(False, self.sub.sgsn_mme_exists_and_is_synchronized(self.mock_user))
        self.assertEqual(3, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_sgsn_mme_exists_and_is_synchronized__raises_exception(self, mock_debug_log):
        self.mock_user.enm_execute.side_effect = Exception()
        self.assertEqual(False, self.sub.sgsn_mme_exists_and_is_synchronized(self.mock_user))
        self.assertEqual(1, mock_debug_log.call_count)

    # fetch_subscription_id test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.datetime')
    def test_fetch_subscription_id__is_successful(self, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 1
        mock_datetime.timedelta.return_value = 2
        self.mock_user.get.return_value = self.ok_response_to_get_in__fetch_subscription_id
        self.sub.fetch_subscription_id(self.ok_response_to_post_in__fetch_subscription_id)
        self.assertEqual('999999999999999', self.sub.id)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.datetime')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_fetch_subscription_id__if_not_get_response(self, mock_debug_log, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 1
        mock_datetime.timedelta.return_value = 2
        self.nok_response._content = "error"
        self.mock_user.get.side_effect = [self.nok_response, self.ok_response_to_get_in__fetch_subscription_id]

        self.sub.fetch_subscription_id(self.ok_response_to_post_in__fetch_subscription_id)
        self.assertEqual(1, mock_debug_log.call_count)
        mock_debug_log.assert_called_with('Failed to fetch subscription id of test-sub, error. Retrying again..')

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.datetime')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_fetch_subscription_id__if_get_error_response(self, mock_debug_log, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 1
        mock_datetime.timedelta.return_value = 2
        self.nok_response._content = "could not be created"
        self.mock_user.get.side_effect = [self.nok_response, self.ok_response_to_get_in__fetch_subscription_id]
        self.assertRaises(SubscriptionCreationError, self.sub.fetch_subscription_id,
                          self.ok_response_to_post_in__fetch_subscription_id)
        self.assertEqual(0, mock_debug_log.call_count)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.datetime')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_fetch_subscription_id__logs_if_exception_occurs_during_request(self, mock_debug_log, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 1
        mock_datetime.timedelta.return_value = 2
        self.nok_response._content = "could not be created"
        self.mock_user.get.side_effect = [KeyError('some_error'), self.ok_response_to_get_in__fetch_subscription_id]
        self.sub.fetch_subscription_id(self.ok_response_to_post_in__fetch_subscription_id)
        mock_debug_log.assert_called_with(
            'Sleeping for 15 seconds before retrying to get the ID of the subscription test-sub')

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.time.sleep', return_value=0)
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.datetime')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_fetch_subscription_id__raises_timeout_error(self, mock_debug_log, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 1
        mock_datetime.timedelta.return_value = -1
        response = Mock()
        self.assertRaises(TimeOutError, self.sub.fetch_subscription_id, response)

    # filter_included_mo_class_sub_counters test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_filter_included_mo_class_sub_counters__is_successful(self, mock_debug_log):
        counters = [{"moClassType": "Class1", "name": "counter1"},
                    {"moClassType": "Class2", "name": "counter2"},
                    {"moClassType": "Class2", "name": "counter5"},
                    {"moClassType": "Class3", "name": "counter1"},
                    {"moClassType": "Class3", "name": "counter2"},
                    {"moClassType": "Class4", "name": "counter1"}]
        self.sub.mo_class_sub_counters_included = {"Class1": ["counter1"], "Class2": ["counter5"],
                                                   "Class3": ["counter1"], "Class4": ["counter1"]}

        filtered_counters = [{"moClassType": "Class1", "name": "counter1"},
                             {"moClassType": "Class2", "name": "counter5"},
                             {"moClassType": "Class3", "name": "counter1"},
                             {"moClassType": "Class4", "name": "counter1"}]
        self.assertEqual(filtered_counters, self.sub.filter_included_mo_class_sub_counters(counters))
        self.assertEqual(mock_debug_log.call_count, 1)


class StatsSubscriptionsUnitTests(PmSubscriptionsUnitTests):
    @classmethod
    def setUpClass(cls):
        super(StatsSubscriptionsUnitTests, cls).setUpClass()

    def setUp(self):
        unit_test_utils.setup()
        PmSubscriptionsUnitTests.create_mock_responses(self)
        nodes = PmSubscriptionsUnitTests.setup_nodes()

        self.mock_user = Mock()
        self.mock_user.username = "blah"

        self.stats_sub = StatisticalSubscription('test-sub', nodes=nodes, user=self.mock_user)
        self.stats_sub.parsed_nodes = [{'fdn': "NetworkElement=ieatnetsimv5051-01_LTE01ERBS00001",
                                        'id': "181477779763365",
                                        'ossModelIdentity': "1094-174-285",
                                        'neType': "ERBS",
                                        'pmFunction': '',
                                        'technologyDomain': ["EPS"]}]

        self.sub = StatisticalSubscription('test-sub', nodes=nodes, user=Mock())
        self.sub.parsed_nodes = self.stats_sub.parsed_nodes

        self.stats_sub_with_definer = StatisticalSubscription('test-sub', nodes=nodes, user=self.mock_user,
                                                              definer="STATISTICAL_SubscriptionAttributes")
        self.stats_sub_with_definer.parsed_nodes = self.stats_sub.parsed_nodes

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.create_subscription_on_enm')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__adds_job_id_to_instance(self, mock_annotate, *_):
        mock_annotate.return_value = self.stats_sub.nodes
        mock_user = self.stats_sub.user

        mock_user.get.side_effect = [self.ok_response_to_get_in__get_counters,
                                     self.ok_response_to_get_in__fetch_subscription_id]
        mock_user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                      self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on,
                                      self.ok_response_to_post_in__fetch_subscription_id]

        self.stats_sub.create()
        self.assertEqual(self.stats_sub.name, "test-sub")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.create_subscription_on_enm')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__stats_subscription__if_definer_is_not_none(self, mock_annotate, *_):
        mock_annotate.return_value = self.stats_sub_with_definer.nodes
        mock_user = self.stats_sub_with_definer.user

        mock_user.get.side_effect = [self.ok_response_to_get_in__get_counters,
                                     self.ok_response_to_get_in__fetch_subscription_id]
        mock_user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                      self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on,
                                      self.ok_response_to_post_in__fetch_subscription_id]

        self.stats_sub.create()
        self.assertEqual(self.stats_sub.name, "test-sub")

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.create_subscription_on_enm')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__stats_subscription_raises_environ_error_if_parse_counters_fails(self, mock_annotate, *_):
        mock_annotate.return_value = self.stats_sub.nodes
        mock_user = self.stats_sub.user

        mock_user.get.side_effect = [self.nok_response_to_get_in__get_counters]
        mock_user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                      self.ok_response_to_post_in__get_nodes_pm_function__with_pmfunction_on]

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__stats_subscription_raises_EnvironError_if_nodes_list_fails(self, mock_annotate):
        mock_annotate.return_value = self.stats_sub.nodes
        mock_user = self.stats_sub.user

        mock_user.post.side_effect = [Exception]

        self.assertRaises(EnvironError, self.stats_sub.create)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.log_pm_disabled_nodes')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__stats_subscription_raises_environ_error_if_nodes_list_empty(self, mock_annotate, _):
        mock_annotate.return_value = self.stats_sub.nodes

        mock_user = self.stats_sub.user
        mock_user.get.side_effect = [self.ok_response_to_get_in__get_counters]
        mock_user.post.side_effect = [self.ok_response_to_post_in___get_pos_by_poids,
                                      self.ok_response_to_post_in__get_nodes_pm_function__empty_json]

        self.assertRaises(EnvironError, self.stats_sub.create)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.create_subscription_on_enm')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch("enmutils_int.lib.pm_rest_nbi_subscriptions.Subscription.get_nodes_for_subscription")
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create__stats_subscription_raises_http_error_if_create_fails(self, mock_annotate, *_):
        mock_annotate.return_value = self.stats_sub.nodes
        mock_user = self.stats_sub.user
        response_post = Mock()
        response_post.ok = False
        mock_user.post.return_value = response_post
        response_post.raise_for_status.side_effect = HTTPError
        self.stats_sub.create()

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.annotate_fdn_poid_return_node_objects')
    def test_create_stats_subscription_raises_EnmApplicationError_if_no_nodes_available(self, _):
        self.stats_sub.nodes = []
        self.assertRaises(EnvironError, self.stats_sub.create)

    # update test cases
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.nodes_list', new_callable=PropertyMock())
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.fetch_subscription_id')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_update_statistical_subscription__is_successful(self, mock_debug_log, mock_fetch_subscription_id,
                                                            mock_get_subscription, mock_parse_counters, _):
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        mock_parse_counters.return_value = [{'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPkt64'},
                                            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.sub.nodes_list = ["ERBS01", "ERBS02"]
        self.sub.id = "281475216504428"
        response = Mock(ok=True)
        self.sub.user.put.return_value = response
        self.sub.update(counters=2)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_subscription.call_count, 1)
        mock_fetch_subscription_id.assert_called_with(response)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.nodes_list', new_callable=PropertyMock())
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.fetch_subscription_id')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_update_statistical_subscription__raises_http_error(self, mock_debug_log, mock_fetch_subscription_id,
                                                                mock_get_subscription, mock_parse_counters, _):
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        mock_parse_counters.return_value = [{'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPkt64'},
                                            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.sub.id = "281475216504428"
        self.sub.nodes_list = ["ERBS01", "ERBS02"]
        response = Mock(ok=False)
        self.sub.user.put.return_value = response
        self.assertRaises(HTTPError, self.sub.update, counters=2)
        self.assertEqual(mock_get_subscription.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 0)
        self.assertFalse(mock_fetch_subscription_id.called)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.nodes_list',
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.parse_counters')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_subscription')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.fetch_subscription_id')
    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.log.logger.debug')
    def test_update_statistical_subscription__if_nodes_existed(self, mock_debug_log, mock_fetch_subscription_id,
                                                               mock_get_subscription, mock_parse_counters, _):
        mock_get_subscription.return_value = self.ok_response_to_get_in__get_by_id__sub_active.json.return_value
        mock_parse_counters.return_value = [{'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPkt64'},
                                            {'moClassType': u'CISCO-CLASS-BASED-QOS-MIB_cbQosIPHCStatsTable_Group',
                                             'name': u'cbQosIPHCTcpSentPktOverflow'}]
        self.sub.id = "281475216504428"
        response = Mock(ok=True)
        self.sub.user.put.return_value = response
        self.sub.nodes_list = ["ERBS01", "ERBS02"]
        self.sub.update(counters=2, nodes=self.sub.nodes_list)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_get_subscription.call_count, 1)
        mock_fetch_subscription_id.assert_called_with(response)

    def test_statistical_subscription_num_counters_parameterized(self):
        subscription = StatisticalSubscription("sub", num_counters=1.0, description="pm_10_load_profile_16B",
                                               user="enm_user")
        self.assertEqual(subscription.num_counters, 1.0)

    def test_statistical_subscription_num_counters_default(self):
        subscription = StatisticalSubscription("sub", description="pm_10_load_profile_16B", user="enm_user")
        self.assertEqual(subscription.num_counters, 3)

    @patch('enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription.get_subscription')
    def test_state__is_successful(self, _):
        self.sub.state()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
