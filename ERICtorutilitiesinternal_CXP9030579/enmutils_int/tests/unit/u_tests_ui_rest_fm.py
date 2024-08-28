#!/usr/bin/env python
# -*- coding: utf8 -*-
from datetime import datetime
import unittest2
from mock import Mock, patch
from requests.exceptions import HTTPError, ConnectionError
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnvironError
from enmutils_int.lib.fm import (_fetch_alarms, acknowledge_alarms, alarmsearch_help, alarmviewer_help,
                                 collect_erbs_network_logs, collect_mgw_network_logs, collect_sgsn_network_logs,
                                 enable_alarm_supervision, get_alarm_hist, initiate_alarm_sync,
                                 network_explorer_search_for_nodes, alarm_overview, create_workspace_payload,
                                 create_alarm_overview_dashboards, alarm_overview_home,
                                 get_list_of_routing_policies_poids, get_routing_policy_poid_by_name, FmAlarmRoute,
                                 create_empty_workspaces_for_given_users, generate_payload_for_workspace,
                                 add_nodes_to_given_workspace_for_a_user, delete_nodes_from_a_given_workspace_for_a_user,
                                 alarm_search_for_open_alarms, alarm_search_for_historical_alarms,
                                 fetch_response_for_given_search_type, collect_eNodeB_network_logs,
                                 create_empty_workspace_for_a_user)
from testslib import unit_test_utils

URL = 'http://test.com'
OPEN, HISTORICAL = range(2)
to_datetime = datetime.now()
from_datetime = datetime.now().replace(year=2018, day=01, hour=0, minute=0)


class FMUiRestUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(primary_type='ERBS', node_id='123'), Mock(primary_type='ERBS', node_id='124')]
        self.mock_response = Mock()
        self.fm_route = FmAlarmRoute(self.user, self.nodes, "some_name", "some_name")

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_enable_alarm_supervision_is_success(self):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        enable_alarm_supervision(self.user, self.nodes)
        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.fm.raise_for_status")
    def test_enable_alarm_supervision_raises_HTTP_error(self, mock_raise_for_status):
        self.user.post.return_value = Mock()
        mock_raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, enable_alarm_supervision, self.user, self.nodes)

    def test_initiate_alarm_sync_is_success(self):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        initiate_alarm_sync(self.user, self.nodes)
        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.fm.raise_for_status")
    def test_initiate_alarm_sync_raises_HTTP_error(self, mock_raise_for_status):
        self.user.post.return_value = Mock()
        mock_raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, initiate_alarm_sync, self.user, self.nodes)

    @patch('enmutils_int.lib.fm.log.logger.debug')
    def test_acknowledge_alarms_is_success(self, *_):
        response = Mock()
        response.json.return_value = [{"header": [{"content_type": "application/json"}]}, {"eventPoIds": ["281486172947712", "281486172587586"]}]
        self.user.post.return_value = response
        acknowledge_alarms(self.user, self.nodes)

    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.raise_for_status')
    def test_acknowledge_alarms_logs_index_error(self, mock_raise_for_status, mock_logger_debug):
        response = Mock()
        self.user.ui_responses = Mock()
        response.json.side_effect = IndexError("Missing Index")
        self.user.post.return_value = response
        mock_raise_for_status.return_value = response
        acknowledge_alarms(self.user, self.nodes)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm._fetch_alarms')
    @patch('enmutils_int.lib.fm.log.logger.info')
    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.raise_for_status')
    def test_acknowledge_alarms__retries_if_http_error(self, mock_raise_for_status, mock_logger_debug,
                                                       mock_logger_info, mock_fetch_alarms, _):
        response = Mock()
        response.json.return_value = [{"header": [{"content_type": "application/json"}]},
                                      {"eventPoIds": ["281486172947712", "281486172587586"]}]
        response.text = "TEST"
        mock_fetch_alarms.return_value = response
        self.user.post.side_effect = [HTTPError, response]
        mock_raise_for_status.side_effect = [HTTPError, response]
        self.assertRaises(HTTPError, acknowledge_alarms, self.user, self.nodes)
        self.assertEqual(mock_raise_for_status.call_count, 1)
        self.assertEqual(mock_logger_debug.call_count, 1)
        self.assertEqual(mock_logger_info.call_count, 2)

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm._fetch_alarms')
    @patch('enmutils_int.lib.fm.log.logger.info')
    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.raise_for_status')
    def test_acknowledge_alarms__retries_if_connection_error(self, mock_raise_for_status, mock_logger_debug,
                                                             mock_logger_info, mock_fetch_alarms, _):
        response = Mock()
        response.json.return_value = [{"header": [{"content_type": "application/json"}]},
                                      {"eventPoIds": ["281486172947712", "281486172587586"]}]
        response.text = "TEST"
        mock_fetch_alarms.return_value = response
        self.user.post.side_effect = [ConnectionError, response]
        mock_raise_for_status.side_effect = [ConnectionError, response]
        self.assertRaises(ConnectionError, acknowledge_alarms, self.user, self.nodes)
        self.assertEqual(mock_raise_for_status.call_count, 1)
        self.assertEqual(mock_logger_debug.call_count, 1)
        self.assertEqual(mock_logger_info.call_count, 2)

    def test_network_explorer_search_for_nodes_is_success(self):
        response = Mock()
        response.status_code = 200
        self.user.get.side_effect = [response, response]
        network_explorer_search_for_nodes(self.user)

    def test_network_explorer_search_for_nodes_raises_HTTP_error(self):
        response = Mock()
        response.status_code = 200
        self.user.get.side_effect = [response, HTTPError]
        self.assertRaises(HTTPError, network_explorer_search_for_nodes, self.user)

    def test_fetch_alarms_is_success(self):
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        _fetch_alarms(self.user, self.nodes)
        self.assertTrue(self.user.post.called)

    @patch("enmutils_int.lib.fm.raise_for_status")
    def test_fetch_alarms_raises_HTTP_error(self, mock_raise_for_status):
        self.user.post.return_value = Mock()
        mock_raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, _fetch_alarms, self.user, self.nodes)

    def tests_alarm_viewer_help_success(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        alarmviewer_help(self.user)
        self.assertTrue(self.user.get.call_count, 4)

    def tests_alarm_search_help_success(self):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        alarmsearch_help(self.user)
        self.assertTrue(self.user.get.call_count, 3)

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_erbs_network_logs_is_success(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'LTE02ERBS00010-1', u'LTE02ERBS00010-2']
        mock_request_execute.return_value = response
        collect_erbs_network_logs(self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_erbs_network_logs_raises_ScriptEngineResponseValidationError(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [0]
        mock_request_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, collect_erbs_network_logs, self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_enodeB_network_logs_is_success(self, mock_request_execute):
        response = Mock()
        response.get_output.return_value = [u'LTE02ERBS00010-1', u'LTE02ERBS00010-2']
        mock_request_execute.return_value = response
        collect_eNodeB_network_logs(self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_enodeB_network_logs_raises_ScriptEngineResponseValidationError(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [0]
        mock_request_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, collect_eNodeB_network_logs, self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_sgsn_network_logs_is_success(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'LTE02ERBS00010-1', u'LTE02ERBS00010-2']
        mock_request_execute.return_value = response
        collect_sgsn_network_logs(self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_sgsn_network_logs_raises_ScriptEngineResponseValidationError(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [0]
        mock_request_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, collect_sgsn_network_logs, self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_mgw_network_logs_is_success(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [u'LTE02ERBS00010-1', u'LTE02ERBS00010-2']
        mock_request_execute.return_value = response
        collect_mgw_network_logs(self.user, self.nodes[0])

    @patch('enmutils_int.lib.fm.time.sleep')
    @patch('enmutils_int.lib.fm.log.logger.debug')
    @patch('enmutils_int.lib.fm.Request.execute')
    def test_collect_mgw_network_logs_raises_ScriptEngineResponseValidationError(self, mock_request_execute, *_):
        response = Mock()
        response.get_output.return_value = [0]
        mock_request_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, collect_mgw_network_logs, self.user, self.nodes[0])

    @patch("enmutils_int.lib.fm.time.sleep")
    @patch('enmutils_int.lib.fm.log.logger.debug')
    def test_get_alarm_hist(self, mock_log_debug, *_):

        output = ['»alarm hist * --begin 2017-10-05T10:09:00',
                  u'presentSeverity\tNodeName\tspecificProblem\teventTime\tobjectOfReference\tproblemText\talarmState\talarmId\tprobableCause\teventType\trecordType',
                  u'MINOR\tENM\tFile System Threshold exceeded\t2017-10-06T05:30:32\tESM Service\tUsed Percentage is 70.0 %\tACTIVE_UNACKNOWLEDGED\t-2\t(Linux) ieatrcxb5272 - (File System) /ericsson/versant_data -\tFile System - Used Percentage\tALARM',
                  u'MAJOR\tENM\tFile System Threshold exceeded\t2017-10-06T05:25:32\tESM Service\tUsed Percentage is 83.0 %\tACTIVE_UNACKNOWLEDGED\t-2\t(Linux) ieatrcxb5272 - (File System) /ericsson/versant_bur -\tFile System - Used Percentage\tALARM',
                  u'', u'Total number of alarms fetched for the given query is :2']
        response = Mock()
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        get_alarm_hist(45, self.user)
        self.assertTrue(mock_log_debug.called)
        self.assertTrue(self.user.enm_execute.called)

    @patch("enmutils_int.lib.fm.time.sleep")
    def test_get_alarm_hist_exception_called(self, *_):
        output = ['']
        response = Mock()
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, get_alarm_hist, 45, self.user)

    @patch("enmutils_int.lib.fm.time.sleep")
    def test_get_alarm_hist_returns_expected_output(self, *_):
        output = ['>>alarm hist * --begin 2017-10-10T11:40:00',
                  u'presentSeverity\tNodeName\tspecificProblem\teventTime\tobjectOfReference\tproblemText\talarmState\talarmId\tprobableCause\teventType\trecordType',
                  u'CRITICAL\tnetsim_LTE03ERBS00037\tHeartbeat Failure\t2017-10-09T19:52:14\tSubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00037\tFailed to resolve Notification IRP\tACTIVE_UNACKNOWLEDGED\t-2\tLAN Error/Communication Error\tCommunications alarm\tHEARTBEAT_ALARM',
                  u'', u'Total number of alarms fetched for the given query is :1']
        response = Mock()
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response

        expected_output = [u'presentSeverity\tNodeName\tspecificProblem\teventTime\tobjectOfReference\tproblemText\talarmState\talarmId\tprobableCause\teventType\trecordType',
                           u'CRITICAL\tnetsim_LTE03ERBS00037\tHeartbeat Failure\t2017-10-09T19:52:14\tSubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00037\tFailed to resolve Notification IRP\tACTIVE_UNACKNOWLEDGED\t-2\tLAN Error/Communication Error\tCommunications alarm\tHEARTBEAT_ALARM',
                           u'', u'Total number of alarms fetched for the given query is :1']
        self.assertEqual(expected_output, get_alarm_hist(45, self.user))

    @patch('enmutils_int.lib.fm.raise_for_status')
    def test_alarm_overview_home(self, mock_raise_for_status):
        mock_user = Mock()

        alarm_overview_home(mock_user)
        self.assertTrue(mock_user.get.called)
        self.assertTrue(mock_raise_for_status.called)

    @patch('enmutils_int.lib.fm.log.logger')
    @patch("enmutils_int.lib.fm.time.sleep")
    @patch('enmutils_int.lib.fm.timedelta')
    @patch('enmutils_int.lib.fm.datetime')
    def test_alarm_overview(self, mock_datetime, mock_timedelta, mock_sleep, mock_logger):
        mock_timedelta.return_value = 0
        mock_datetime.now.side_effect = [1, 0, 2]
        mock_user = Mock()
        alarm_overview(mock_user, 0, 0)

        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_user.post.called)
        self.assertTrue(mock_logger.info.called)

    def test_create_workspace_payload(self):
        ret = create_workspace_payload(10, 10, 'some_user', 10, 10)

        expected_return = {'id': 'workspace_10',
                           'value': '{"topology":true,"nodesImported":10,"id":"workspace_10","groupName":'
                                    '"alarmviewer:some_user_importedNodes_10;alarmviewer:some_user_selectedNodes_10",'
                                    '"date":10,"workspaceName":"Workspace10"}'}
        self.assertTrue(ret == expected_return)

    @patch('enmutils_int.lib.fm.time.sleep', return_value=0)
    @patch('enmutils_int.lib.fm.log.logger')
    def test_create_alarm_overview_dashboards(self, mock_logger, _):
        mock_user = Mock()
        mock_node = Mock()
        mock_node.poid = 777
        create_alarm_overview_dashboards([mock_user], [mock_node])

        self.assertTrue(mock_logger.info.called)
        self.assertTrue(mock_user.put.called)
        self.assertTrue(mock_user.post.called)

    @patch('enmutils_int.lib.fm.time.sleep', return_value=0)
    @patch('enmutils_int.lib.fm.log.logger')
    def test_create_alarm_overview_dashboards_retry(self, mock_logger, _):
        mock_user = Mock()
        mock_user.put.side_effect = [HTTPError, Mock(), HTTPError, Mock(), Mock(), Mock()]
        mock_node = Mock()
        mock_node.poid = 777
        create_alarm_overview_dashboards([mock_user], [mock_node])

        self.assertTrue(mock_logger.info.called)
        self.assertTrue(mock_user.put.called)
        self.assertTrue(mock_user.post.called)

    # Unit test FM alarm routing saved to file

    @patch("enmutils_int.lib.fm.EnvironError")
    def test_get_routing_policy_by_name_success(self, mock_env_error):
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = [{"fileName": "some_name", "routeIdAsString": "some_string_id"}]
        self.user.post.return_value = self.mock_response

        get_routing_policy_poid_by_name(self.user, ["12345"], "some_name")
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.mock_response.raise_for_status.called)
        self.assertTrue(self.mock_response.json.called)
        self.assertFalse(mock_env_error.called)

    def test_get_routing_policy_by_name_throwing_env_error(self):
        self.mock_response.status_code = 500
        self.user.post.return_value = self.mock_response

        self.assertRaises(EnvironError, get_routing_policy_poid_by_name, self.user, ["12345"], "some_name")
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.mock_response.raise_for_status.called)

    @patch("enmutils_int.lib.fm.EnvironError")
    def test_get_routing_policy_by_name_no_policy_found(self, mock_env_error):
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = [{"fileName": "other_name", "routeIdAsString": "some_string_id"}]
        self.user.post.return_value = self.mock_response

        ret = get_routing_policy_poid_by_name(self.user, ["12345"], "some_name")
        self.assertTrue(ret == "")
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.mock_response.raise_for_status.called)
        self.assertTrue(self.mock_response.json.called)
        self.assertFalse(mock_env_error.called)

    @patch("enmutils_int.lib.fm.EnvironError")
    def test_get_list_of_routing_policies_poids_success(self, mock_env_error):
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = [Mock(), {"poIds": [{"routeIdAsString": "some_string_id"}]}]
        self.user.post.return_value = self.mock_response

        ret = get_list_of_routing_policies_poids(self.user)

        self.assertTrue(ret == ["some_string_id"])
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.mock_response.raise_for_status.called)
        self.assertFalse(mock_env_error.called)

    def test_get_list_of_routing_policies_poids_throwing_env_error(self):
        self.mock_response.status_code = 500
        self.user.post.return_value = self.mock_response

        self.assertRaises(EnvironError, get_list_of_routing_policies_poids, self.user)
        self.assertTrue(self.user.post.called)
        self.assertTrue(self.mock_response.raise_for_status.called)

    @patch("enmutils_int.lib.fm.EnvironError")
    @patch("enmutils_int.lib.fm.get_routing_policy_poid_by_name")
    @patch("enmutils_int.lib.fm.get_list_of_routing_policies_poids")
    def test_fm_alarm_route_get_route_id_success(self, mock_get_poids, mock_get_name, mock_env_error):
        mock_get_poids.return_value = ["53453463"]
        mock_get_name.return_value = ["somename"]

        self.fm_route._get_the_route_id("some_name")

        self.assertTrue(mock_get_name.called)
        self.assertTrue(mock_get_poids.called)
        self.assertFalse(mock_env_error.called)

    @patch("enmutils_int.lib.fm.get_routing_policy_poid_by_name")
    @patch("enmutils_int.lib.fm.get_list_of_routing_policies_poids")
    def test_fm_alarm_route_get_route_id_no_poids_returned(self, mock_get_poids, mock_get_name):
        mock_get_poids.return_value = []

        self.assertRaises(EnvironError, self.fm_route._get_the_route_id, "some_name")
        self.assertTrue(mock_get_poids.called)
        self.assertFalse(mock_get_name.called)

    @patch("enmutils_int.lib.fm.get_routing_policy_poid_by_name")
    @patch("enmutils_int.lib.fm.get_list_of_routing_policies_poids")
    def test_fm_alarm_route_get_route_id_no_route_id_found(self, mock_get_poids, mock_get_name):
        mock_get_poids.return_value = ["53453463"]
        mock_get_name.return_value = []

        self.assertRaises(EnvironError, self.fm_route._get_the_route_id, "some_name")

        self.assertTrue(mock_get_name.called)
        self.assertTrue(mock_get_poids.called)

    def test_create_request_payload_success(self):
        mock_node_1 = Mock()
        mock_node_1.primary_type = "ERBS"
        mock_node_1.node_id = "001"
        mock_node_2 = Mock()
        mock_node_2.primary_type = "ERBS"
        mock_node_2.node_id = "002"
        mock_nodes_list = [mock_node_1, mock_node_2]
        expected_output = {'description': 'some_description',
                           'enablePolicy': True,
                           'fileHeaders': ['fdn', 'alarmingObject', 'presentSeverity', 'eventTime', 'insertTime',
                                           'specificProblem', 'probableCause', 'eventType', 'objectOfReference',
                                           'commentText', 'repeatCount', 'alarmState'],
                           'fileName': 'some_name',
                           'fileType': 'TXT',
                           'name': 'some_name',
                           'neFdn': 'ERBS#001,002;',
                           'neType': 'ERBS,',
                           'outputType': 'file',
                           'routeType': 'FILE',
                           'subordinateType': 'All_SUBORDINATES'}
        ret = self.fm_route._create_request_payload(mock_nodes_list, "some_name", "some_name", "some_description")

        self.assertTrue(ret == expected_output)

    @patch("enmutils_int.lib.fm.FmAlarmRoute._get_the_route_id")
    @patch("enmutils_int.lib.fm.FmAlarmRoute._create_request_payload")
    def test_fm_alarm_route_create_success(self, mock_create_paload, mock_get_route_id):
        mock_create_paload.return_value = {"some": "value"}
        self.fm_route.create()
        self.assertTrue(mock_create_paload.called)
        self.assertTrue(mock_get_route_id.called)

    @patch("enmutils_int.lib.fm.log")
    def test_fm_alarm_route_teardown_success(self, mock_log):
        self.fm_route._teardown()
        self.assertTrue(self.user.post.called)
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.fm.log")
    def test_fm_alarm_route_teardown_error(self, mock_log):
        self.user.post.side_effect = Exception()
        self.assertRaises(Exception, self.fm_route._teardown)
        self.assertTrue(mock_log.logger.debug.called)
        self.assertTrue(mock_log.logger.error.called)

    @patch("time.sleep")
    def test_fm_alarm_route_create_error(self, _):
        self.mock_response.raise_for_status.side_effect = [HTTPError(), HTTPError(), HTTPError(), HTTPError()]
        self.user.post.side_effect = [self.mock_response, self.mock_response, self.mock_response, self.mock_response]
        self.fm_route.user = self.user
        self.assertRaises(HTTPError, self.fm_route.create)

    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.create_empty_workspace_for_a_user")
    def test_create_empty_workspaces_for_given_users__is_successful(self, mock_create_empty_workspace_for_user, *_):
        users = [Mock(), Mock()]
        mock_create_empty_workspace_for_user.side_effect = [(Mock(), Mock()), (Mock(), Mock())]
        user_dict = create_empty_workspaces_for_given_users(users, 'alarmviewer')
        self.assertEqual(len(user_dict.keys()), 2)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_create_empty_workspace_for_a_user__is_successful_for_alarmviewer(self, mock_log, *_):
        create_empty_workspace_for_a_user(Mock(), 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_create_empty_workspace_for_a_user__retries_if_HTTP_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.put.side_effect = [HTTPError, Mock(), Mock(), Mock()]
        create_empty_workspace_for_a_user(user, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_create_empty_workspace_for_a_user__retries_if_Connection_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.put.side_effect = [ConnectionError, Mock(), Mock(), Mock()]
        create_empty_workspace_for_a_user(user, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_create_empty_workspace_for_a_user__is_successful_for_alarmsearch(self, mock_log, *_):
        create_empty_workspace_for_a_user(Mock(), 'alarmsearch')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    def test_generate_payload_for_workspace__is_successful_for_alarmviewer(self):
        payload = generate_payload_for_workspace(1032456789, 10, 'FM_08_1301202015489', 8456123795, '15765490000',
                                                 'alarmviewer')
        self.assertEqual(len(payload.keys()), 2)
        self.assertTrue('alarmviewer' in payload['value'])

    def test_generate_payload_for_workspace__is_successful_for_alarmsearch(self):
        payload = generate_payload_for_workspace(1032456789, 10, 'FM_14_1301202015489', 24561123595, '19547890000',
                                                 'alarmsearch')
        self.assertEqual(len(payload.keys()), 2)
        self.assertTrue('alarmsearch' in payload['value'])

    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_add_nodes_to_given_workspace_for_a_user__is_successful_for_alarmviewer(self, mock_log, *_):
        add_nodes_to_given_workspace_for_a_user(Mock(), {Mock(): Mock()}, 12345687, 789546213, 10, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_add_nodes_to_given_workspace_for_a_user__retries_if_HTTP_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.post.side_effect = [HTTPError, Mock(), Mock()]
        add_nodes_to_given_workspace_for_a_user(user, {Mock(): Mock()}, 12345687, 789546213, 10, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_add_nodes_to_given_workspace_for_a_user__retries_if_Connection_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.post.side_effect = [ConnectionError, Mock(), Mock()]
        add_nodes_to_given_workspace_for_a_user(user, {Mock(): Mock()}, 12345687, 789546213, 10, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_add_nodes_to_given_workspace_for_a_user__is_successful_for_alarmsearch(self, mock_log, *_):
        add_nodes_to_given_workspace_for_a_user(Mock(), {Mock(): Mock()}, 12345687, 789546213, 10, 'alarmsearch')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_delete_nodes_from_a_given_workspace_for_a_user__is_successful_for_alarmviewer(self, mock_log, *_):
        delete_nodes_from_a_given_workspace_for_a_user(Mock(), {Mock(): Mock()}, 12345687, 789546213, 'alarmviewer')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_delete_nodes_from_a_given_workspace_for_a_user__is_successful_for_alarmsearch(self, mock_log, *_):
        delete_nodes_from_a_given_workspace_for_a_user(Mock(), {Mock(): Mock()}, 12345687, 789546213, 'alarmsearch')
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_delete_nodes_from_a_given_workspace_for_a_user__retries_when_HTTP_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.post.side_effect = [HTTPError, Mock(), Mock()]
        delete_nodes_from_a_given_workspace_for_a_user(user, {Mock(): Mock()}, 12345687, 789546213, 'alarmsearch')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.uuid")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.time")
    @patch("enmutils_int.lib.fm.randint")
    @patch("enmutils_int.lib.fm.generate_payload_for_workspace")
    @patch("enmutils_int.lib.fm.log")
    def test_delete_nodes_from_a_given_workspace_for_a_user__retries_when_Connection_error_is_encountered(self,
                                                                                                          mock_log, *_):
        user = Mock()
        user.post.side_effect = [ConnectionError, Mock(), Mock()]
        delete_nodes_from_a_given_workspace_for_a_user(user, {Mock(): Mock()}, 12345687, 789546213, 'alarmsearch')
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_historical_alarms__is_succesful(self, mock_fetch_response, *_):
        mock_fetch_response.return_value = Mock()
        alarm_search_for_historical_alarms(Mock(), [Mock()], 123456879, 789456213, HISTORICAL)
        self.assertTrue(mock_fetch_response.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_historical_alarms__retries_if_HTTP_error_is_encountered(self, mock_fetch_response, *_):
        user = Mock()
        mock_fetch_response.side_effect = [HTTPError, Mock()]
        alarm_search_for_historical_alarms(user, [Mock()], 123456879, 789456213, HISTORICAL)
        self.assertTrue(mock_fetch_response.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_historical_alarms__retries_if_Connection_error_is_encountered(self, mock_fetch_response,
                                                                                            *_):
        user = Mock()
        mock_fetch_response.side_effect = [ConnectionError, Mock()]
        alarm_search_for_historical_alarms(user, [Mock()], 123456879, 789456213, HISTORICAL)
        self.assertTrue(mock_fetch_response.call_count, 1)

    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    def test_fetch_response_for_given_search_type__is_successful(self, mock_log, *_):
        fetch_response_for_given_search_type(Mock(), [Mock(node_id='LTE01ERBS0001')])
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    def test_fetch_response_for_given_search_type__retries_if_HTTP_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.post.side_effect = [HTTPError, Mock()]
        fetch_response_for_given_search_type(user, [Mock(node_id='LTE01ERBS0001')])
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    def test_fetch_response_for_given_search_type__retries_if_Connection_error_is_encountered(self, mock_log, *_):
        user = Mock()
        user.post.side_effect = [ConnectionError, Mock()]
        fetch_response_for_given_search_type(user, [Mock(node_id='LTE01ERBS0001')])
        self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__is_successful(self, mock_fetch_response, mock_log, *_):
        mock_fetch_response.return_value.json.return_value = [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                              {"alarms": [{"insertTime": 1578300347529, "eventPoId": 52588343},
                                                                          {"insertTime": 1578300330571, "eventPoId": 52588327}]},
                                                              {"poIds": ["52588343", "52588327", "52588305", "52588282", "52587330"]}]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__retries_if_HTTP_error_encountered(self, mock_fetch_response, mock_log, *_):
        mock_fetch_response.return_value.json.side_effect = [HTTPError, [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                                         {"alarms": [{"insertTime": 1578300347529, "eventPoId": 52588343},
                                                                                     {"insertTime": 1578300330571, "eventPoId": 52588327}]},
                                                                         {"poIds": ["52588343", "52588327", "52588305", "52588282", "52587330"]}]]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__retries_if_Connection_error_encountered(self, mock_fetch_response, mock_log,
                                                                                   *_):
        mock_fetch_response.return_value.json.side_effect = [ConnectionError, [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                                               {"alarms": [{"insertTime": 1578300347529, "eventPoId": 52588343},
                                                                                           {"insertTime": 1578300330571, "eventPoId": 52588327}]},
                                                                               {"poIds": ["52588343", "52588327", "52588305", "52588282", "52587330"]}]]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__returns_if_there_are_no_alarms(self, mock_fetch_response, mock_log, *_):
        mock_fetch_response.return_value.json.return_value = [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                              {"alarms": []}, {"poIds": []}]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__logs_index_error(self, mock_fetch_response, mock_log, *_):
        mock_fetch_response.return_value.json.return_value = [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                              {"poIds": []}]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.fm.json")
    @patch("enmutils_int.lib.fm.raise_for_status")
    @patch("enmutils_int.lib.fm.log")
    @patch("enmutils_int.lib.fm.fetch_response_for_given_search_type")
    def test_alarm_search_for_open_alarms__logs_value_error(self, mock_fetch_response, mock_log, *_):
        mock_fetch_response.return_value.json.return_value = [{"headers": [{"id": "fdn", "key": "fdn", "index": 0, "header": "Network Element", "enabled": 'true', "width": 25, "pinned": 'false'}]},
                                                              {"poIds": []}]
        alarm_search_for_open_alarms(Mock(), [Mock()], 123456, 789456, OPEN)
        self.assertEqual(mock_log.logger.info.call_count, 1)

if __name__ == '__main__':
    unittest2.main(verbosity=2)
