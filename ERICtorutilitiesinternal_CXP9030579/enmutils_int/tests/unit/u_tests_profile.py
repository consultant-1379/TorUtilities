#!/usr/bin/env python
import json
import time

from functools import partial
from datetime import datetime, timedelta
from mock import patch, Mock, NonCallableMock, PropertyMock, call
from parameterizedtestcase import ParameterizedTestCase
from pytz import timezone
from requests.exceptions import HTTPError, ConnectionError

import unittest2
from enmutils.lib import persistence
from enmutils.lib.exceptions import (ProfileError, NoNodesAvailable, MoBatchCommandReturnedError, ENMJobStatusError,
                                     ScriptEngineResponseValidationError, EnmApplicationError,
                                     NoOuputFromScriptEngineResponseError, NetsimError, FailedNetsimOperation,
                                     ShellCommandReturnedNonZero, EnvironError, EnvironWarning, ValidationWarning)
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.nrm_default_configurations.profile_values import networks
from enmutils_int.lib.profile import (Profile, CMImportProfile, TeardownList,
                                      set_connection_error, extract_html_text, set_http_error, ExclusiveProfile)
from testslib import unit_test_utils


class ProfileUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        Profile.NAME = "TEST_PROFILE"
        self.base_profile = Profile()
        self.base_profile._iteration_number = 6
        self.base_profile.LOG_AFTER_COMPLETED = False
        self.base_profile.SUPPORTED = True
        self.max_rss_memory_allowed_mb = 10
        self.tz = timezone("Europe/Dublin")
        self.dst_activation_time_in_secs = 1553994000  # 2019-3-31 01:00 - DST activation time is 00:59 -> 02:00
        self.dst_deactivation_time_in_secs = 1572138000  # 2019-10-27 01:00 - DST de-activation time is 01:59 -> 01:00
        self.non_dst_time_in_secs = 1574730000  # 2019-11-26 01:00 (DST is de-active)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.common_utils.terminate_user_sessions")
    @patch("enmutils_int.lib.profile.Profile.run")
    @patch("enmutils_int.lib.profile.Profile.kill_completed_pid", side_effect=None)
    def test_call__sets_state_to_completed_if_no_exception_is_raised(
            self, mock_kill_completed_pid, mock_run, mock_sessions, *_):
        self.base_profile.run_profile = False
        self.base_profile.num_nodes = 0
        self.base_profile.__call__(teardown=False)
        self.assertTrue(mock_kill_completed_pid.called)
        self.assertFalse(mock_run.called)
        self.assertEqual(self.base_profile.pid, None)
        self.assertEqual(1, mock_sessions.call_count)

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.process.kill_spawned_process")
    @patch("enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string")
    @patch("enmutils_int.lib.profile.persistence")
    @patch("enmutils_int.lib.profile.common_utils")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.user_cleanup")
    @patch("enmutils_int.lib.profile.Profile.run")
    def test_call_invokes_run_and_sets_error_information_if_exception_is_raised(self, mock_run, *_):
        mock_run.side_effect = RuntimeError("nodes are on fire")
        self.base_profile()
        self.assertEqual(self.base_profile.state, "STARTING")
        self.assertTrue(self.base_profile.errors)

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.teardown")
    @patch("enmutils_int.lib.profile.persistence")
    @patch("enmutils_int.lib.profile.common_utils")
    @patch("enmutils_int.lib.profile.Profile.nodes_list", new_callable=PropertyMock)
    @patch("enmutils.lib.shell")
    @patch("enmutils_int.lib.profile.Profile.user_cleanup")
    @patch("enmutils_int.lib.profile.Profile.run")
    def test_call_invokes_run_and_sets_state_to_stopping_if_keyboardInterrupt_is_raised(self, mock_run, *_):
        mock_run.side_effect = KeyboardInterrupt()
        self.base_profile()
        self.assertEqual(self.base_profile.state, "STOPPING")

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.teardown")
    @patch("enmutils_int.lib.profile.persistence")
    @patch("enmutils_int.lib.profile.common_utils")
    @patch("enmutils.lib.shell")
    @patch("enmutils_int.lib.profile.Profile.user_cleanup")
    @patch("enmutils_int.lib.profile.Profile.run")
    @patch("enmutils_int.lib.profile.Profile.logger")
    def test_call_invokes_run_and_sets_state_to_stopping_if_generatorexit_is_raised(self, mock_logger, mock_run, *_):
        mock_run.side_effect = GeneratorExit("Some error msg")
        self.base_profile()
        mock_logger.info.assert_called_with("Abnormal condition encountered - profile now exiting: Some error msg")

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.teardown")
    @patch("enmutils_int.lib.profile.Profile.kill_completed_pid")
    @patch("enmutils_int.lib.profile.persistence")
    @patch("enmutils_int.lib.profile.common_utils")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.run")
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_call_does_not_deallocate_nodes_if_retain_after_completed(self, mock_deallocate_nodes, *_):
        self.base_profile.RETAIN_NODES_AFTER_COMPLETED = True
        self.base_profile.state = 'COMPLETED'
        self.base_profile.__call__()
        self.assertFalse(mock_deallocate_nodes.called)

    @patch("enmutils_int.lib.profile.common_utils.terminate_user_sessions")
    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.kill_completed_pid")
    @patch("enmutils_int.lib.profile.Profile.schedule", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.run")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.teardown")
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_call_does_deallocate_nodes_if_retain_after_completed_is_false_and_service_not_used(
            self, mock_deallocate_nodes, mock_teardown, *_):
        self.base_profile.RETAIN_NODES_AFTER_COMPLETED = False
        self.base_profile.EXCLUSIVE = False
        self.base_profile.SCHEDULED_TIMES_STRINGS = ["17:00:00"]
        self.base_profile.state = 'COMPLETED'
        self.base_profile.num_nodes = 1
        self.base_profile.__call__(teardown=False)
        self.assertTrue(mock_deallocate_nodes.called)
        self.assertFalse(mock_teardown.called)
        self.assertEqual(self.base_profile.pid, None)

    @patch("enmutils_int.lib.profile.Profile.cloud", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.persist")
    @patch("enmutils_int.lib.profile.Profile.teardown")
    def test_call_returns_if_teardown_is_true(self, mock_teardown, *_):
        self.base_profile.__call__(teardown=True)
        self.assertTrue(mock_teardown.called)
        self.assertEqual(self.base_profile.state, "STOPPING")

    @patch("enmutils_int.lib.profile.is_emp", return_value=True)
    def test_cloud__when_true(self, _):
        self.assertTrue(self.base_profile.cloud)

    @patch("enmutils_int.lib.profile.is_emp", return_value=False)
    def test_cloud__when_false(self, _):
        self.assertFalse(self.base_profile.cloud)

    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch('enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours')
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_sleep_sets_schedule_information(self, *_):
        self.base_profile.SCHEDULE_SLEEP = 1800
        time_string = time.gmtime(self.base_profile.SCHEDULE_SLEEP)
        self.base_profile.sleep()
        self.assertTrue("Every {}".format(time_string))

    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    def test_add_errors_adds_correct_error_information_to_errors_property(self, mock_persist_error, _):
        self.base_profile.add_error_as_exception(ProfileError("Node is on Fire"))
        self.base_profile.add_error_as_exception(ProfileError("Another nodes is also on Fire"))
        self.assertEqual(2, mock_persist_error.call_count)

    @patch("enmutils_int.lib.profile.process.os.getpid", return_value=12345)
    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid")
    def test_running__returns_true_if_called_by_profile(self, mock_get_profile_daemon_pid, *_):
        self.base_profile.pid = 12345
        self.assertTrue(self.base_profile.running)
        self.assertFalse(mock_get_profile_daemon_pid.called)

    @patch("enmutils_int.lib.profile.process.os.getpid", return_value=54321)
    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid", return_value=12345)
    def test_running__returns_true_if_not_called_by_profile_eg_workload_tool(self, mock_get_profile_daemon_pid, *_):
        self.base_profile.pid = 12345
        self.assertTrue(self.base_profile.running)
        self.assertTrue(mock_get_profile_daemon_pid.called)

    @patch("enmutils_int.lib.profile.process.os.getpid")
    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid")
    def test_running__returns_false_if_pid_not_set(self, mock_get_profile_daemon_pid, *_):
        self.base_profile.pid = None
        self.assertFalse(self.base_profile.running)
        self.assertFalse(mock_get_profile_daemon_pid.called)

    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="COMPLETED")
    @patch('enmutils_int.lib.profile.Profile.running', new_callable=PropertyMock, return_value=True)
    def test_daemon_died__in_profile_returns_true_if_daemon_dead(self, *_):
        self.assertFalse(self.base_profile.daemon_died)

    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="COMPLETED")
    @patch('enmutils_int.lib.profile.Profile.running', new_callable=PropertyMock, return_value=True)
    def test_daemon_died__in_profile_returns_false_if_daemon_not_dead(self, *_):
        self.assertFalse(self.base_profile.daemon_died)

    def test_ident_file_path__returns_correct_path(self):
        self.assertEqual(self.base_profile.ident_file_path, "/var/tmp/enmutils/daemon/TEST_PROFILE.pid")

    def test_supported__returns_true(self):
        self.assertTrue(self.base_profile.supported)

    def test_application__returns_profile_name_prefix(self):
        self.assertEqual("TEST", self.base_profile.application)

    def test_run_raises_not_implemented_error(self):
        self.assertRaises(NotImplementedError, self.base_profile.run)

    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    def test_http_error_classed_as_enm_application_error(self, mock_persist, _):
        request = Mock()
        request.url = "http://test.com"
        request.method = "GET"
        response = Mock()
        request.body = ["Some html"]
        response.request = request
        response.stdout = ['some msg']
        response.command = ["some command"]
        response.status_code = 402
        self.base_profile.add_error_as_exception(HTTPError(response=response))
        response.request.method = "POST"
        request.body = ["filename=test.zip"]
        response.status_code = 418
        self.base_profile.add_error_as_exception(HTTPError(response=response))
        mock_persist.assert_called_with("HTTPError: 'POST' request to http://test.com failed with status code: "
                                        "418Removed request body, as filename= found in response\nResponse: "
                                        "['filename=test.zip']", 'TEST_PROFILE-errors',
                                        error_type='EnmApplicationError')

    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    def test_duplicate_error_stacked(self, *_):
        errors = [{'TIMESTAMP': '2018/12/11 14:30:00', 'REASON': '[ProfileError] ProfileError: \'Something went wrong\''},
                  {'TIMESTAMP': '2017/12/11 15:30:00', 'REASON': '[ProfileError] ProfileError: \'Something else went wrong\'', "DUPLICATES": []}]
        persistence.set("%s-errors" % self.base_profile.NAME, errors, 5)
        self.base_profile.add_error_as_exception(ProfileError("Something went wrong"))
        self.assertEqual(len(self.base_profile.errors), 2)
        self.base_profile.add_error_as_exception(ProfileError("Something else went wrong"))
        self.assertEqual(len(self.base_profile.errors), 2)
        self.base_profile.add_error_as_exception(ProfileError("This is a similar error with a number 123"))
        self.base_profile.add_error_as_exception(ProfileError("This is a similar error with a number 456"))
        self.assertEqual(len(self.base_profile.errors), 3)

    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    @patch("enmutils_int.lib.profile.persistence.remove")
    def test_clear_errors__removes_all_profile_errors_from_persistence(self, mock_remove, _):
        self.base_profile.clear_errors()
        mock_remove.assert_any_call(self.base_profile._profile_error_key)
        mock_remove.assert_called_with(self.base_profile._profile_warning_key)

    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    @patch('enmutils.lib.script_engine_2.Response.get_output')
    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    def test_add_error_as_exception_function(self, mock_persist_error_or_warning_as_string, mock_get_output, *_):
        request = Mock()
        request.url = "http://test.com"
        request.method = "GET"
        response = Mock()
        request.text = "Some text"
        response.request = request
        mock_get_output.return_value = [u'ok', u'not ok', u'ok']
        response.get_output.return_value = [u'ok', u'not ok', u'ok']
        response.stdout = ['some msg']
        response.command = ["some command"]

        self.base_profile.add_error_as_exception(ConnectionError("Connection aborted", request=request))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(ConnectionError("Not aborted", request=request), log_trace=False)
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(HTTPError("Connection aborted", request=request, response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(MoBatchCommandReturnedError("no contact", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(MoBatchCommandReturnedError("opposite", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(MoBatchCommandReturnedError("Logfiles stored in ", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(ENMJobStatusError("Connection aborted", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(NoOuputFromScriptEngineResponseError(msg="No output from script engine response", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(ScriptEngineResponseValidationError("Script Engine Response Validation Error", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string)
        response.get_output.side_effect = TypeError("I am a type error")
        self.base_profile.add_error_as_exception(ScriptEngineResponseValidationError("Script Engine Response Validation Error", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string)
        self.base_profile.add_error_as_exception(ShellCommandReturnedNonZero("Shell Command Returned NonZero", response=response))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)
        self.base_profile.add_error_as_exception(EnvironWarning("No Nodes Available"))
        self.assertTrue(mock_persist_error_or_warning_as_string.called)

    def test_update_error__when_message_less_than_length_limit(self):
        error_message = "No nodes are available for the current profile"
        actual_message = "No nodes are available for the current profile"
        self.assertEqual(self.base_profile.update_error(actual_message, 200, error_message), error_message)

    def test_update_error__when_message_greater_than_length_limit(self):
        truncation_message = "...truncated output. See ENM application log on server for more details"
        error_message = "Failed to execute command: cmedit set LTE126dg2ERBS00006 " \
                        "EUtranCellFDD.EUtranCellFDDId==LTE126dg2ERBS00006-1 EUtranCellFDD.cfraEnable=true," \
                        "request_id: [st:de24a977-205b-4e68-8284-5a49c573f68d].Please"
        actual_message = "Failed to execute command: cmedit set LTE126dg2ERBS00006 EUtranCellFDD." \
                         "EUtranCellFDDId==LTE126dg2ERBS00006-1 EUtranCellFDD.cfraEnable=true, request_id: " \
                         "[st:de24a977-205b-4e68-8284-5a49c573f68d].Please check ENM logviewer for more information."
        self.assertEqual(self.base_profile.update_error(actual_message, 200, error_message), "{0}{1}".format(
            error_message, truncation_message))

    def test_update_error__updates_bumblebee_message(self):
        self.base_profile.NAME = "APT_01"
        exception = Exception("No nodes are available for the current profile")
        error_message = "No nodes are available for the current profile"
        actual_message = ("PLEASE CONTACT TEAM BumbleBee FOR QUERIES IN RELATION TO THIS PROFILE. No nodes are "
                          "available for the current profile")
        self.assertEqual(actual_message, self.base_profile.update_error(exception, 200, error_message))

    def test_update_error__updates_bravo_message(self):
        self.base_profile.NAME = "HA_01"
        exception = Exception("No nodes are available for the current profile")
        error_message = "No nodes are available for the current profile"
        actual_message = ("PLEASE CONTACT TEAM BRAVO FOR QUERIES IN RELATION TO THIS PROFILE. "
                          "Due to NRM constraints not all nodes are expected to be available for HA_01. "
                          "No nodes are available for the current profile")
        self.assertEqual(actual_message, self.base_profile.update_error(exception, 200, error_message))

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.Profile.persist")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    def test_teardown__invokes_teardown_and_removes_items_from_teardown_list(self, mock_state, *_):
        mock_workload_item = Mock()
        for _ in range(3):
            self.base_profile.teardown_list.append(mock_workload_item)
            mock_state.return_value = "STOPPING"
        self.base_profile.teardown()
        self.assertEqual(mock_workload_item.call_count, 3)
        self.assertFalse(self.base_profile.teardown_list)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.Profile.remove")
    def test_teardown_finally_remove_block_called(self, mock_remove, *_):
        self.base_profile.teardown(remove=True)
        self.assertTrue(mock_remove.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_if_exclusive_profile_then_dellocate_nodes_not_called(self, mock_deallocate_nodes, *_):
        self.base_profile.EXCLUSIVE = True
        self.base_profile.teardown()
        self.assertFalse(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_if_not_exclusive_profile_then_dellocate_nodes_is_called(self, mock_deallocate_nodes, *_):
        self.base_profile.EXCLUSIVE = False
        self.base_profile.is_completed = False
        setattr(self.base_profile, "TOTAL_NODES", [])
        self.base_profile.teardown()
        self.assertTrue(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_if_profile_is_completed_then_dellocate_nodes_not_called(self, mock_deallocate_nodes, *_):
        self.base_profile.EXCLUSIVE = False
        self.base_profile.is_completed = True
        self.base_profile.teardown()
        self.assertFalse(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_if_teardown_object_is_not_callable(self, mock_deallocate_nodes, *_):
        self.base_profile.is_completed = True
        obj = NonCallableMock()
        self.base_profile.teardown_list = [obj]
        self.base_profile.teardown()
        self.assertFalse(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_logs_exception(self, mock_deallocate_nodes, *_):
        self.base_profile.is_completed = True
        obj = Mock()
        obj.side_effect = Exception
        self.base_profile.teardown_list = [obj]
        self.base_profile.teardown()
        self.assertFalse(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch('enmutils_int.lib.profile.get_workload_admin_user')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown__logs__user__deleted__exception__if__no__user(self, mock_deallocate_nodes, mock_get_user, *_):
        self.base_profile.is_completed = True
        obj = Mock()
        obj.mock_add_spec([], spec_set=False)
        obj.side_effect = Exception("401 unauthorised")
        self.base_profile.teardown_list = [obj]
        self.base_profile.teardown()
        self.assertFalse(mock_get_user.called)
        self.assertFalse(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.get_workload_admin_user')
    def test_teardown_items__callable__user__deleted__exception(self, mock_get_user):
        obj = Mock()
        obj.mock_add_spec(['user'], spec_set=True)
        obj.side_effect = [Exception("401 unauthorised"), '']
        teardown_list = [obj]
        self.base_profile.teardown_items(teardown_list)
        self.assertTrue(mock_get_user.called)

    @patch('enmutils_int.lib.profile.get_workload_admin_user')
    def test_teardown_items__not__callable__user__deleted__exception(self, mock_get_user):
        obj = NonCallableMock(_teardown=Mock())
        obj._teardown.side_effect = [Exception("401 unauthorised"), ""]
        teardown_list = [obj]
        self.base_profile.teardown_items(teardown_list)
        self.assertTrue(mock_get_user.called)

    @patch('enmutils_int.lib.profile.os.getpid')
    @patch('enmutils_int.lib.profile.process.kill_spawned_process')
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.user_cleanup')
    @patch("enmutils_int.lib.profile.node_pool_mgr.deallocate_nodes")
    def test_teardown_add_error_if_profile_is_dead(self, mock_deallocate_nodes, *_):
        self.base_profile.is_completed = False
        self.base_profile.state = 'RUNNING'
        self.base_profile.teardown_list = [Mock()]
        setattr(self.base_profile, "NUM_NODES", {})
        self.base_profile.teardown()
        self.assertTrue(mock_deallocate_nodes.called)

    @patch('enmutils_int.lib.profile.Profile._extract_html_text')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_process_user_request_error_handling_adds_no_error_to_persistence_if_all_requests_are_successful(
            self, mock_add_error, *_):
        users = []
        for i in range(3):
            user = Mock(username="mock_user" + str(i), user_roles=["OPERATOR"])
            user.ui_response_info = {('GET', 'https://google.com'): {False: 0, True: 1},
                                     ('GET', 'https://facebook.com'): {False: 0, True: 1}}
            for response in [Mock()] * 2:
                user._process_safe_request(response)
            users.append(user)
        self.base_profile.process_user_request_errors(users)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile.Profile._extract_html_text')
    @patch('__builtin__.hasattr')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_profile_process_user_request_errors__adds_correct_error_to_persistence_with_no_sample_error_attribute(
            self, mock_add_error, mock_hasattr, *_):
        mock_hasattr.return_value = False
        # Setup
        users = []
        for i in range(3):
            user = Mock(username="mock_user" + str(i), user_roles=["OPERATOR"])
            user.ui_response_info = {('GET', 'https://google.com'): {False: 2, True: 1,
                                                                     'ERRORS': {404: Mock(text="google"),
                                                                                599: Mock(text="google")}},
                                     ('GET', 'https://facebook.com'): {False: 1, True: 1,
                                                                       'ERRORS': {400: Mock(text="fb")}}}
            for response in [Mock()] * 5:
                user._process_safe_request(response)
            users.append(user)
        # Test
        self.base_profile.process_user_request_errors(users)
        self.assertEqual(2, mock_hasattr.call_count)
        self.assertEqual(2, mock_add_error.call_count)
        mock_hasattr.return_value = True

    @patch('enmutils_int.lib.profile.Profile._extract_html_text')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_profile_process_user_request_errors_adds_correct_error_to_persistence_if_some_requests_fail(
            self, mock_add_error, *_):
        # Setup
        users = []
        for i in range(3):
            user = Mock(username="mock_user" + str(i), user_roles=["OPERATOR"])
            user.ui_response_info = {('GET', 'https://google.com'): {False: 2, True: 1,
                                                                     'ERRORS': {404: Mock(), 599: Mock()}},
                                     ('GET', 'https://facebook.com'): {False: 1, True: 1, 'ERRORS': {400: Mock()}}}
            for response in [Mock()] * 5:
                user._process_safe_request(response)
            users.append(user)
        # Test
        self.base_profile.process_user_request_errors(users)
        self.assertEqual(2, mock_add_error.call_count)

    @patch('enmutils.lib.thread_queue.ThreadQueue')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_process_thread_queue_errors_is_successful(self, mock_add_error, mock_tq):
        mock_tq.exceptions = [HTTPError, ProfileError, ENMJobStatusError]
        num_exceptions = self.base_profile.process_thread_queue_errors(mock_tq)
        self.assertEqual(num_exceptions, 3)
        self.assertTrue(mock_add_error.called, 3)

    @patch('enmutils.lib.thread_queue.ThreadQueue')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_process_thread_queue_errors_is_successful_when_last_error_only_is_true(self, mock_add_error, mock_tq):
        mock_tq.exceptions = [HTTPError, ProfileError, ENMJobStatusError]
        num_exceptions = self.base_profile.process_thread_queue_errors(mock_tq, last_error_only=True)
        self.assertEqual(num_exceptions, 3)
        self.assertTrue(mock_add_error.called, 1)

    @patch('enmutils.lib.thread_queue.ThreadQueue')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_process_thread_queue_errors_last_error_only_is_true_and_no_exceptions(self, mock_add_error, mock_tq):
        mock_tq.exceptions = []
        self.base_profile.process_thread_queue_errors(mock_tq, last_error_only=True)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile.time.daylight", 0)
    @patch("enmutils_int.lib.profile.time.localtime")
    def test_calculate_dst_offset_for_next_iteration__returns_0_if_not_in_dst_timezone(self, *_):
        self.assertEqual(self.base_profile.calculate_dst_offset_for_next_iteration(time.time(), time.time()), 0)

    @patch("enmutils_int.lib.profile.time.altzone", -3600)
    @patch("enmutils_int.lib.profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile.time.daylight")
    @patch("enmutils_int.lib.profile.time.localtime")
    def test_calculate_dst_offset_for_next_iteration__is_ok_when_comparing_dst_to_non_dst_times(
            self, mock_local_time, *_):
        iteration_start_time = datetime(2018, 10, 27, 1, 7, 0, 0)
        next_iteration_start_time = datetime(2018, 11, 3, 2, 7, 0, 0)
        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_next_iteration_start_time = self.tz.localize(next_iteration_start_time).timetuple()
        mock_local_time.side_effect = [time_struct_for_iteration_start_time, time_struct_for_next_iteration_start_time]
        self.assertEqual(self.base_profile.calculate_dst_offset_for_next_iteration(time.time(), time.time()), 3600)

    @patch("enmutils_int.lib.profile.time.altzone", -3600)
    @patch("enmutils_int.lib.profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile.time.daylight")
    @patch("enmutils_int.lib.profile.time.localtime")
    def test_calculate_dst_offset_for_next_iteration__is_ok_when_comparing_non_dst_to_dst_times(
            self, mock_local_time, *_):
        iteration_start_time = datetime(2019, 3, 30, 2, 7, 0, 0)
        next_iteration_start_time = datetime(2018, 3, 31, 7, 0, 0, 0)
        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_next_iteration_start_time = self.tz.localize(next_iteration_start_time).timetuple()
        mock_local_time.side_effect = [time_struct_for_iteration_start_time, time_struct_for_next_iteration_start_time]
        self.assertEqual(self.base_profile.calculate_dst_offset_for_next_iteration(time.time(), time.time()), -3600)

    @patch("enmutils_int.lib.profile.time.altzone", -3600)
    @patch("enmutils_int.lib.profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile.time.daylight")
    @patch("enmutils_int.lib.profile.time.localtime")
    def test_calculate_dst_offset_for_next_iteration__is_ok_when_comparing_dst_to_dst_times(
            self, mock_local_time, *_):
        iteration_start_time = datetime(2018, 3, 25, 2, 0, 0, 0)
        next_iteration_start_time = datetime(2018, 3, 26, 2, 0, 0, 0)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_next_iteration_start_time = self.tz.localize(next_iteration_start_time).timetuple()
        mock_local_time.side_effect = [time_struct_for_iteration_start_time, time_struct_for_next_iteration_start_time]
        self.assertEqual(self.base_profile.calculate_dst_offset_for_next_iteration(time.time(), time.time()), 0)

    @patch("enmutils_int.lib.profile.time.altzone", -3600)
    @patch("enmutils_int.lib.profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile.time.daylight")
    @patch("enmutils_int.lib.profile.time.localtime")
    def test_calculate_dst_offset_for_next_iteration__is_ok_when_comparing_non_dst_to_non_dst_times(
            self, mock_local_time, *_):
        iteration_start_time = datetime(2019, 3, 25, 2, 0, 0, 0)
        next_iteration_start_time = datetime(2019, 3, 26, 2, 0, 0, 0)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_next_iteration_start_time = self.tz.localize(next_iteration_start_time).timetuple()
        mock_local_time.side_effect = [time_struct_for_iteration_start_time, time_struct_for_next_iteration_start_time]
        self.assertEqual(self.base_profile.calculate_dst_offset_for_next_iteration(time.time(), time.time()), 0)

    @patch("enmutils_int.lib.profile.Profile._sleep_until")
    def test_sleep_until_day_in_future(self, *_):
        days = self._get_days()
        schedule = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 1, 0)

        profile = self.base_profile
        profile.SCHEDULED_DAYS = [days[1]]
        profile.SCHEDULED_TIMES = [schedule + timedelta(days=1)]

        profile.sleep_until_day(delay_secs=1800)
        self.assertTrue(profile.SCHEDULED_TIMES[0] == schedule + timedelta(days=1))

    @patch("enmutils_int.lib.profile.Profile._sleep_until")
    def test_sleep_until_day_which_has_already_passed(self, *_):
        days = self._get_days()
        schedule = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 1, 0)

        profile = self.base_profile
        profile.SCHEDULED_DAYS = [days[0]]
        profile.SCHEDULED_TIMES = [schedule - timedelta(days=90)]

        profile.sleep_until_day(delay_secs=0)
        self.assertTrue(profile.SCHEDULED_TIMES[0] == schedule + timedelta(days=7))

    @patch("enmutils_int.lib.profile.Profile._sleep_until")
    def test_sleep_until_day__multiple_scheduled_days(self, *_):
        days = self._get_days()
        schedule = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 1, 0)

        profile = self.base_profile
        profile.SCHEDULED_DAYS = [days[0], days[4]]
        profile.SCHEDULED_TIMES = [schedule - timedelta(days=90)]
        profile.sleep_until_day()
        self.assertTrue(profile.SCHEDULED_TIMES[0] + timedelta(days=3) == schedule + timedelta(days=7))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_dst_deactive_for_both_times(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs - 60 * 24 * 60 * 60  # 2019-1-30 01:00
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 1, 30, 1, 0)
        scheduled_time = datetime(
            2019, 2, 3, 2, 0)  # During period when DST is de-active (months before DST change)
        mock_calculate_dst_offset_for_next_iteration.return_value = 0  # DST de-active for both timestamps
        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        one_hour_in_secs = 60 * 60
        self.assertEqual(waiting_time, 4 * 24 * one_hour_in_secs + 1 * one_hour_in_secs)
        self.assertEqual(updated_scheduled_time, datetime(2019, 2, 3, 2, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__dst_deactive_for_both_times_but_scheduled_time_earlier(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs - 7 * 60 * 60   # 7 hours before DST
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 3, 30, 18, 0)  # 2019-3-30 18:00
        scheduled_time = datetime(
            2019, 3, 30, 16, 0)  # Before current time, during the day before DST is active)
        mock_calculate_dst_offset_for_next_iteration.return_value = 3600  # DST active for next iteration
        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time, (24 + 1 - 2) * 60 * 60)
        self.assertEqual(updated_scheduled_time, datetime(2019, 3, 31, 16, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_scheduled_time_occurs_at_dst_activation_time(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs - 5 * 60  # 2019-3-31 00:55
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 3, 31, 0, 55)
        scheduled_time = datetime(2019, 3, 31, 2, 0)  # Time when DST goes active (00:59 -> 02:00)
        mock_calculate_dst_offset_for_next_iteration.return_value = -60 * 60

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time / 60, 5)
        self.assertEqual(updated_scheduled_time, datetime(2019, 3, 31, 2, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_scheduled_time_doesnt_exist_as_dst_being_activated(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs - 5 * 60  # 2019-3-31, 00:55
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 3, 31, 0, 55)
        scheduled_time = datetime(2019, 3, 31, 1, 0)  # DST change occurs at 00:59 -> 02:00, so 01:00 = 02:00
        mock_calculate_dst_offset_for_next_iteration.return_value = -60 * 60

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time / 60, -55)
        self.assertEqual(updated_scheduled_time, datetime(2019, 3, 31, 1, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_scheduled_time_occurs_just_when_dst_deactivated(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs - 5 * 60  # 2019-10-27 01:55
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 10, 27, 1, 55)
        scheduled_time = datetime(2019, 10, 27, 1, 0)  # DST de-activation occurs at 01:59 -> 01:00
        mock_calculate_dst_offset_for_next_iteration.return_value = 0

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time, ((24 - 1) * 60 * 60) + (5 * 60))
        self.assertEqual(updated_scheduled_time, datetime(2019, 10, 28, 1, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_both_times_occur_after_dst_was_deactivated(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs + 55 * 60  # 2019-10-27 01:55
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 10, 27, 1, 55)
        scheduled_time = datetime(2019, 10, 27, 2, 0)  # 1 hour after DST has been de-activated
        mock_calculate_dst_offset_for_next_iteration.return_value = 0  # DST de-active for both timestamps

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time / 60, 5)
        self.assertEqual(updated_scheduled_time, datetime(2019, 10, 27, 2, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_both_times_occur_before_dst_is_deactivated(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs - 65 * 60  # 2019-10-27 00:55
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 10, 27, 0, 55)
        scheduled_time = datetime(2019, 10, 27, 1, 0)  # 1 hour before DST is de-activated
        mock_calculate_dst_offset_for_next_iteration.return_value = 0  # DST active for both timestamps

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time / 60, 5)
        self.assertEqual(updated_scheduled_time, datetime(2019, 10, 27, 1, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_both_times_occur_after_dst_activated(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs + 90 * 24 * 60 * 60  # 2019-6-29 02:00
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 6, 29, 2, 0)
        scheduled_time = datetime(2019, 6, 29, 0, 0)  # During period when DST is active (months after DST change)
        mock_calculate_dst_offset_for_next_iteration.return_value = 0  # DST active for both timestamps

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time, 60 * 60 * 22)
        self.assertEqual(updated_scheduled_time, datetime(2019, 6, 30, 0, 0))

    @patch("enmutils_int.lib.profile.datetime")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_offset_for_next_iteration")
    def test_calculate_dst_adjusted_diff_between_timestamps__ok_if_both_times_occur_either_side_of_dst_deactivation(
            self, mock_calculate_dst_offset_for_next_iteration, mock_datetime, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs + 22 * 60 * 60  # 2019-10-27 23:00
        mock_datetime.datetime.fromtimestamp.return_value = datetime(2019, 10, 27, 23, 0)
        scheduled_time = datetime(2019, 10, 27, 0, 0)  # some hours before DST is de-activated
        mock_calculate_dst_offset_for_next_iteration.return_value = 0  # DST inactive for next iteration

        waiting_time, _, updated_scheduled_time = profile.calculate_dst_adjusted_diff_between_timestamps(
            current_time_in_secs_since_epoch, scheduled_time)
        self.assertEqual(waiting_time, 60 * 60)
        self.assertEqual(updated_scheduled_time, datetime(2019, 10, 28, 0, 0))

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    @ParameterizedTestCase.parameterize(("days",), [(1,), (10,), (100,), (1000,)])
    def test_calculate_time_to_wait_until_next_iteration__is_ok_with_times_that_have_already_passed(
            self, days, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile
        current_time_in_secs_since_epoch = self.non_dst_time_in_secs
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_secs_since_epoch - days * 24 * 60 * 60,
                                   current_time_in_secs_since_epoch + days * 24 * 60 * 60]

        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [
            (-days * 24 * 60 * 60, 0, current_time_in_datetime_format - timedelta(days=days)),
            (days * 24 * 60 * 60, 0, current_time_in_datetime_format + timedelta(days=days))]

        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertEqual(profile._sleep_time, days * 24 * 60 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__does_not_change_sleep_time_if_all_times_occur_in_distant_past(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile
        days = 10
        current_time_in_secs_since_epoch = self.non_dst_time_in_secs
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_secs_since_epoch - days * 24 * 60 * 60]

        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [
            (-days * 24 * 60 * 60, 0, current_time_in_datetime_format - timedelta(days=days))]

        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertEqual(profile._sleep_time, None)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__handles_times_correctly_on_day_when_dst_activated(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile
        current_time_in_secs_since_epoch = self.dst_activation_time_in_secs - 5 * 60  # 5 min before DST is activated
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]

        offset_secs = -3600
        day_in_secs = 60 * 60 * 24
        time1 = current_time_in_datetime_format.replace(hour=0, minute=0)
        profile.recent_scheduled_times_for_dst = [time1]
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [(-55 * 60, 0 + day_in_secs, time1),
                                                                           (-55 * 60 + day_in_secs, offset_secs, _),
                                                                           (5 * 60, offset_secs, _),
                                                                           (65 * 60, offset_secs, _),
                                                                           ((22 * 60 + 5) * 60, offset_secs, _)]
        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertEqual(profile._sleep_time, 5 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__is_ok_if_dst_deactivation_doesnt_happen_for_some_time(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs - 65 * 60  # 5 min before DST is activated
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]

        day_in_secs = 60 * 60 * 24
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [(-55 * 60 + day_in_secs, 0, _),
                                                                           (5 * 60, 0, _),
                                                                           (125 * 60, 3600, _),
                                                                           (185 * 60, 3600, _),
                                                                           ((23 * 60 + 5) * 60, 3600, _)]
        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertTrue(profile._sleep_time == 5 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__is_ok_if_scheduled_time_already_occurred_but_dst_active(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = (self.dst_deactivation_time_in_secs -
                                            5 * 60)  # 2019-10-27 01:55, before DST ends
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]
        profile.recent_scheduled_times_for_dst = [profile.SCHEDULED_TIMES[1]]

        offset_secs = 3600
        day_in_secs = 60 * 60 * 24
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [(-55 * 60 + day_in_secs, 0, _),
                                                                           (5 * 60, offset_secs,
                                                                            profile.SCHEDULED_TIMES[1]),
                                                                           (65 * 60, offset_secs, _),
                                                                           (125 * 60, offset_secs, _),
                                                                           ((22 * 60 + 5) * 60, offset_secs, _)]
        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch, delay_secs=100 * 60)
        self.assertEqual(profile._sleep_time, 65 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__delay_secs_with_provided_sleep_value(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, _):
        profile = self.base_profile
        current_time_in_secs_since_epoch = (self.dst_deactivation_time_in_secs -
                                            5 * 60)  # 2019-10-27 01:55, before DST ends
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]
        profile.recent_scheduled_times_for_dst = [profile.SCHEDULED_TIMES[1]]

        offset_secs = 3600
        day_in_secs = 60 * 60 * 24
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [(-55 * 60 + day_in_secs, 0, _),
                                                                           (5 * 60, offset_secs,
                                                                            profile.SCHEDULED_TIMES[1]),
                                                                           (65 * 60, offset_secs, _),
                                                                           (125 * 60, offset_secs, _),
                                                                           ((22 * 60 + 5) * 60, offset_secs, _)]
        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch, delay_secs=30 * 60)
        self.assertEqual(profile._sleep_time, 35 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch('enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps')
    def test_calculate_time_to_wait_until_next_iteration__is_ok_if_dst_deactivation_has_happened(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs + 55 * 60  # 55 min after DST de-activated
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]

        offset_secs = 3600
        day_in_secs = 60 * 60 * 24
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [(-115 * 60 + day_in_secs, offset_secs, _),
                                                                           (-55 * 60 + day_in_secs, offset_secs, _),
                                                                           (5 * 60, 0, _),
                                                                           (65 * 60, 0, _),
                                                                           ((21 * 60 + 5) * 60, 0, _)]
        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertEqual(profile._sleep_time, 5 * 60)

    @patch("enmutils_int.lib.profile.Profile.update_recent_scheduled_times_for_dst")
    @patch("enmutils_int.lib.profile.Profile.calculate_dst_adjusted_diff_between_timestamps")
    def test_calculate_time_to_wait_until_next_iteration__is_ok_at_end_of_day_if_dst_deactivation_occurred_on_same_day(
            self, mock_calculate_dst_adjusted_diff_between_timestamps, *_):
        profile = self.base_profile

        current_time_in_secs_since_epoch = self.dst_deactivation_time_in_secs + 22 * 60 * 60  # 23:55
        current_time_in_datetime_format = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        profile.SCHEDULED_TIMES = [current_time_in_datetime_format.replace(hour=hour, minute=0)
                                   for hour in [0, 1, 2, 3, 23]]

        offset_secs = 3600
        day_in_secs = 60 * 60 * 24
        mock_calculate_dst_adjusted_diff_between_timestamps.side_effect = [
            (-23 * 60 * 60 - 55 * 60 + day_in_secs, offset_secs, _),
            (-22 * 60 * 60 - 55 * 60 + day_in_secs, offset_secs, _),
            (-21 * 60 * 60 - 55 * 60 + day_in_secs, 0, _),
            (-20 * 60 * 60 - 55 * 60 + day_in_secs, 0, _),
            (-55 * 60 + day_in_secs, 0, _)]

        profile.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch)
        self.assertEqual(profile._sleep_time, 5 * 60)

    @patch("enmutils_int.lib.profile.time.daylight")
    @patch("enmutils_int.lib.profile.time.altzone", -3600)
    @patch("enmutils_int.lib.profile.time.timezone", 0)
    def test_update_recent_scheduled_times_for_dst__is_successful_if_scheduled_time_is_not_in_list_of_recent_times(
            self, *_):
        profile = self.base_profile

        profile.next_run_time = datetime(2019, 10, 27, 1, 0)

        profile.update_recent_scheduled_times_for_dst()
        self.assertEqual([profile.next_run_time], profile.recent_scheduled_times_for_dst)

    @patch("enmutils_int.lib.profile.time")
    def test_update_recent_scheduled_times_for_dst__is_successful_if_scheduled_time_is_in_list_of_recent_times(
            self, mock_time, *_):
        mock_time.daylight = 1
        mock_time.timezone = 0
        mock_time.altzone = -3600
        profile = self.base_profile

        profile.next_run_time = datetime(2019, 10, 27, 1, 0)

        profile.recent_scheduled_times_for_dst = [datetime(2019, 10, 26, 22, 0), datetime(2019, 10, 27, 0, 30)]

        profile.update_recent_scheduled_times_for_dst()
        self.assertEqual(profile.recent_scheduled_times_for_dst, [datetime(2019, 10, 27, 0, 30), profile.next_run_time])

    @patch("enmutils_int.lib.profile.time")
    def test_update_recent_scheduled_times_for_dst__makes_no_changes_if_not_in_dst_timezone(self, mock_time, *_):
        mock_time.daylight = 0
        profile = self.base_profile

        profile.next_run_time = datetime(2019, 10, 27, 1, 0)

        profile.recent_scheduled_times_for_dst = []

        profile.update_recent_scheduled_times_for_dst()
        self.assertEqual(profile.recent_scheduled_times_for_dst, [])

    @patch('enmutils_int.lib.profile.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.profile.sys.getsizeof')
    @patch('enmutils_int.lib.profile.pickle.dumps')
    @patch('enmutils_int.lib.profile.persistence.set', side_effect=ConnectionError("Error"))
    def test_persist__raises_generator_exit(self, *_):
        self.assertRaises(GeneratorExit, self.base_profile.persist)

    @patch('enmutils_int.lib.profile.Profile.set_diff_object')
    @patch('enmutils_int.lib.profile.Profile.set_status_object')
    @patch("enmutils_int.lib.profile.sys.getsizeof")
    @patch("enmutils_int.lib.profile.Profile.get_last_run_time", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.priority", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.schedule", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.timestamp.get_current_time")
    @patch("enmutils_int.lib.profile.mutexer")
    @patch("enmutils_int.lib.profile.persistence")
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage", new_callable=PropertyMock)
    def test_persist__is_successful_if_profile_is_missing_user_count_attribute(
            self, mock_check_profile_memory_usage, mock_persistence, *_):
        profile = self.base_profile
        profile.__delattr__("user_count")
        mock_persistence.has_key.return_value = False
        profile.persist()
        self.assertTrue(mock_check_profile_memory_usage.called)

    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid", return_value=["9999"])
    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    def test_check_profile_memory_usage__is_successful_if_memory_doesnt_exceed_limit(
            self, mock_log_current_memory_usage, *_):
        mock_log_current_memory_usage.return_value = (self.base_profile.DEFAULT_MAX_RSS_MEMORY_MB - 1) * 1024
        self.base_profile.check_profile_memory_usage()

    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid", return_value=["9999"])
    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    def test_check_profile_memory_usage__raises_generatorexit_if_memory_exceeds_limit_and_autostop_enabled(
            self, mock_log_current_memory_usage, *_):
        mock_log_current_memory_usage.return_value = (self.base_profile.DEFAULT_MAX_RSS_MEMORY_MB + 1) * 1024
        self.assertRaises(GeneratorExit, self.base_profile.check_profile_memory_usage)

    @patch("enmutils_int.lib.profile.process.get_profile_daemon_pid", return_value=["9999"])
    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    def test_check_profile_memory_usage__does_not_raise_generatorexit_if_memory_exceeds_limit_but_autostop_disabled(
            self, mock_log_current_memory_usage, *_):
        self.base_profile.AUTOSTOP_ON_MAX_RSS_MEM_REACHED = False
        mock_log_current_memory_usage.return_value = (self.base_profile.DEFAULT_MAX_RSS_MEMORY_MB + 1) * 1024
        self.base_profile.check_profile_memory_usage()

    def _get_days(self):
        """
        Helper method for determining current day for sleep_until_day method

        :rtype: list
        :return: updated_days
        """
        DAYS = ["SATURDAY", "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

        time_now = datetime.now()
        current_day_index = DAYS.index(time_now.strftime('%A').upper())
        updated_days = DAYS[current_day_index:] + DAYS[0:current_day_index]
        return updated_days

    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    def test_add_error_as_exception_doesnt_raise_exception_when_response_is_supplied(self, *_):
        resp = Mock(status_code=200, method="GET", url="https://google.com", text="Google is on fire")
        err = HTTPError("Something went wrong and we need to specify why", response=resp)
        self.base_profile.add_error_as_exception(err)

    @patch("enmutils_int.lib.profile.Profile.schedule")
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    def test_append_teardown_list_updates_persistence(self, *_):
        persist_string = "Test if this gets persisted."
        profile = self.base_profile
        profile.teardown_list.append(persist_string)
        profile_obj = persistence.get(profile.NAME)

        self.assertEqual(persist_string, profile_obj.teardown_list[0])

    @patch("enmutils_int.lib.profile.Profile.set_time_stats_value")
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch('enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours')
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.common_utils.terminate_user_sessions")
    @ParameterizedTestCase.parameterize(
        ("days", "iterations"),
        [
            (1, 8), (2, 16), (7, 24), (14, 32)
        ]
    )
    def test_sleep_sets_correct_last_run_time_next_run_time_schedule_information(
            self, days, iterations, mock_sessions, *_):
        self.base_profile.SCHEDULE_SLEEP = days * 24 * 60 * 60
        self.base_profile.user_count = 1

        for i in xrange(iterations):
            self.base_profile.sleep()
            start_time = self.base_profile.start_time

            if i == 0:
                last_run = start_time
                next_run = start_time + timedelta(days=days)
            else:
                last_run = start_time + timedelta(days=days * i)
                next_run = start_time + timedelta(days=days * (i + 1))

            self.assertEqual(last_run.replace(second=0, microsecond=0),
                             self.base_profile._last_run.replace(second=0, microsecond=0))
            self.assertEqual(next_run.replace(second=0, microsecond=0),
                             self.base_profile._next_run.replace(second=0, microsecond=0))
        self.assertEqual(iterations, mock_sessions.call_count)
        mock_sessions.assert_called_with(self.base_profile.NAME)

    @patch("enmutils_int.lib.profile.Profile.daemon_died", new_callable=PropertyMock)
    def test_status__returns_dead_when_daemon_has_died(self, *_):
        self.assertEqual("DEAD", self.base_profile.status)

    @patch("enmutils_int.lib.profile.Profile.warnings", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.Profile.errors", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.Profile.daemon_died", new_callable=PropertyMock, return_value=False)
    def test_status__returns_ok_when_daemon_has_not_died(self, *_):
        self.assertEqual("OK", self.base_profile.status)

    @patch("enmutils_int.lib.profile.Profile.warnings", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.Profile.errors", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile.Profile.daemon_died", new_callable=PropertyMock, return_value=False)
    def test_status__returns_error_when_daemon_has_not_died_but_has_errors(self, *_):
        self.assertEqual("ERROR", self.base_profile.status)

    @patch("enmutils_int.lib.profile.Profile.warnings", new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile.Profile.errors", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.Profile.daemon_died", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.log.yellow_text")
    def test_status__returns_warning_text_when_daemon_has_not_died_but_has_warnings(self, mock_yellow_text, *_):
        self.assertEqual(mock_yellow_text.return_value, self.base_profile.status)
        mock_yellow_text.assert_called_with("WARNING")

    @patch("enmutils_int.lib.profile.Profile._profile_warning_key", new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile.persistence.get")
    def test_warnings__successful(self, mock_get, *_):
        self.assertEqual(mock_get.return_value, self.base_profile.warnings)

    def test_profile_values_dict_to_json(self):
        try:
            json.dumps(networks)
        except Exception as e:
            raise AssertionError("Failed to create json from profile_values dict. Exception: {0}".format(str(e)))

    def test_profile_values_json_to_dict(self):
        jsonified = json.dumps(networks)
        try:
            json.loads(jsonified)
        except Exception as e:
            raise AssertionError("Failed to create dict from profile_values json. Exception: {0}".format(str(e)))

    def test_parse_html_jboss_error_response(self):
        sample_jboss_html = '<html><head><title>JBWEB000065: HTTP Status 500 - </title><style><!--H1 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:22px;} H2 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:16px;} H3 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:14px;} BODY {font-family:Tahoma,Arial,sans-serif;color:black;background-color:white;} B {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;} P {font-family:Tahoma,Arial,sans-serif;background:white;color:black;font-size:12px;}A {color : black;}A.name {color : black;}HR {color : #525D76;}--></style> </head><body><h1>JBWEB000065: HTTP Status 500 - </h1><HR size="1" noshade="noshade"><p><b>JBWEB000309: type</b> JBWEB000067: Status report</p><p><b>JBWEB000068: message</b> <u></u></p><p><b>JBWEB000069: description</b> <u>JBWEB000145: The server encountered an internal error that prevented it from fulfilling this request.</u></p><HR size="1" noshade="noshade"></body></html>'
        expected_message = '[JBOSS] JBWEB000065: HTTP Status 500 - JBWEB000145: The server encountered an internal error that prevented it from fulfilling this request.'
        self.assertEqual(self.base_profile._extract_html_text(sample_jboss_html), expected_message)

    def test_parse_html_error_response(self):
        sample_jboss_html = '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">|<html><head>|<title>404 Not Found</title>|</head><body>|<h1>Not Found</h1>|<p>The requested URL /script-engine/services/command was not found on this server.</p>|</body></html>'
        expected_message = '[HTML] 404 Not Found >> Not Found >> The requested URL /script-engine/services/command was not found on this server.'
        self.assertEqual(self.base_profile._extract_html_text(sample_jboss_html), expected_message)

    def test_parse_html_empty_html_attribute(self):
        self.assertEqual(self.base_profile._extract_html_text(''), '')

    @ParameterizedTestCase.parameterize(
        ("keep_running", "result"),
        [
            (False, 10), (5, 10), (True, 10)
        ]
    )
    def test_generator_loop(self, keep_running, result):
        self.base_profile.KEEP_RUNNING = keep_running
        i = 0
        while self.base_profile.keep_running():
            i += 1
            if i == 10:
                break
        self.assertEqual(i, result)

    def test_set_schedule_times(self):
        self.base_profile.SCHEDULED_TIMES_STRINGS = ["05:50:00", "06:50:00"]
        times = self.base_profile.get_schedule_times()
        for t in times:
            self.assertTrue(isinstance(t, datetime))

    @patch('enmutils_int.lib.profile.Profile.set_time_stats_value')
    def test_schedule_when_schedule_sleep_is_zero(self, *_):
        profile = Profile()
        self.base_profile.SCHEDULE_SLEEP = 0
        setattr(profile, "SCHEDULE_SLEEP", 0)
        self.assertEqual(profile.schedule, self.base_profile.schedule)

    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    @patch("enmutils_int.lib.profile.is_emp")
    @patch('enmutils_int.lib.profile.time.sleep', return_value=None)
    def test_log_message_updated_if_no_nodes_set(self, mock_sleep, *_):
        profile = Profile()
        profile.NAME = "Test_01"
        err_msg = "No available nodes for {} ".format(profile.NAME)
        profile.add_error_as_exception(NoNodesAvailable(err_msg))
        mock_sleep.return_value = 0.1
        with patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock) as mock_state:
            mock_state.side_effect = ["COMPLETED", "STOPPED"]
            profile._log_after_completed()
            self.assertTrue(profile.no_nodes_available == err_msg)

    @patch('enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string')
    @patch("enmutils_int.lib.profile.is_emp")
    def test_process_error_for_netsim(self, *_):
        profile = Profile()
        profile.NAME = "Test_01"
        err_msg = "No netsim available: {}".format(profile.NAME)
        profile.add_error_as_exception(NetsimError(err_msg))

    @patch("enmutils_int.lib.profile.CMImportProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.CMImportProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.persistence.get")
    @patch("enmutils_int.lib.profile.CMImportProfile.get_nodes_list_by_attribute", return_value=[])
    def test_nodes_list__in_cmimport_profile_raises_environ_error_if_no_nodes_found(self, *_):
        cmimport_profile = CMImportProfile()
        dummy_obj = Mock()
        with self.assertRaises(EnvironError):
            dummy_obj.dummy = cmimport_profile.nodes_list

    @patch("enmutils_int.lib.profile.CMImportProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.CMImportProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.persistence.get")
    @patch("enmutils_int.lib.profile.CMImportProfile.get_nodes_list_by_attribute")
    def test_nodes_list__in_cmimport_profile_returns_successfully(self, mock_base_nodes, *_):
        cmimport_profile = CMImportProfile()
        cmimport_profile.NAME = 'TEST_00'
        cmimport_profile.TOTAL_NODES = 3
        nodes = unit_test_utils.get_nodes(3)
        mock_base_nodes.return_value = nodes
        persistence.set('TEST_00-mos', {n.node_id: n.mos for n in nodes}, -1)
        nodes_list = cmimport_profile.nodes_list
        self.assertEqual(nodes_list, nodes)
        persistence.remove('TEST_00-mos')

    @patch("enmutils_int.lib.profile.CMImportProfile._check_if_allocated_nodes_exceeds_total_nodes")
    @patch("enmutils_int.lib.profile.CMImportProfile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.CMImportProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.persistence.get")
    @patch("enmutils_int.lib.profile.CMImportProfile.get_nodes_list_by_attribute")
    def test_nodes_list__in_cmimport_profile_removes_node_that_is_not_found_in_persistence_on_key_error(
            self, mock_get_nodes_list_by_attribute, mock_get, *_):
        cmimport_profile = CMImportProfile()
        cmimport_profile.NAME = 'TEST_01'
        cmimport_profile.TOTAL_NODES = 3
        nodes = [Mock(node_id="node0", mos="mo0"),
                 Mock(node_id="node1", mos="mo1"),
                 Mock(node_id="node2", mos="mo2"),
                 Mock(node_id="node3", mos="mo3"),
                 Mock(node_id="node4", mos="mo4")]

        mock_get_nodes_list_by_attribute.return_value = nodes
        mos_in_persistence = {n.node_id: n.mos for n in nodes[0:3]}
        mock_get.return_value = mos_in_persistence

        nodes_list = cmimport_profile.nodes_list
        self.assertEqual([node.mos for node in nodes_list], ["mo0", "mo1", "mo2"])

    @patch("enmutils_int.lib.profile.CMImportProfile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.CMImportProfile.persist")
    @patch("enmutils_int.lib.profile.SHMUtils.deallocate_unused_nodes")
    def test__check_if_allocated_nodes_exceeds_total_nodes__removes_excess_nodes_if_num_allocated_exceeds_total_nodes(
            self, mock_deallocate_unused_nodes, *_):
        cmimport_profile = CMImportProfile()
        cmimport_profile.NAME = 'TEST_01'
        cmimport_profile.TOTAL_NODES = 4
        node0 = Mock(node_id="node0", mos="mo0")
        nodes = [node0,
                 Mock(node_id="node1", mos="mo1"),
                 Mock(node_id="node2", mos="mo2"),
                 Mock(node_id="node3", mos="mo3"),
                 Mock(node_id="node4", mos="mo4")]

        cmimport_profile._check_if_allocated_nodes_exceeds_total_nodes(nodes)

        mock_deallocate_unused_nodes.assert_called_with([node0], cmimport_profile)

    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    def test_cmimport_profile_accepts_num_nodes(self, *_):
        cmimport_profile = CMImportProfile()
        cmimport_profile.NAME = 'TEST_01'
        cmimport_profile.NUM_NODES = {"BSC": -1}
        nodes = unit_test_utils.get_nodes(5)
        persistence.set('TEST_01-mos', {n.node_id: n.mos for n in nodes}, -1)
        with patch("enmutils_int.lib.node_pool_mgr.get_pool") as mock_get_workload_pool:
            mock_get_workload_pool.return_value = node_pool_mgr.get_pool()
        with patch("enmutils_int.lib.node_pool_mgr.Pool.allocated_nodes") as mock_allocated_nodes:
            mock_allocated_nodes.return_value = nodes
            nodes_list = cmimport_profile.nodes_list
            self.assertEqual(len(nodes_list), len(nodes))
        persistence.remove('TEST_01-mos')

    def test_cm_import_profile_run__raises_not_implemented_error(self):
        cmimport_profile = CMImportProfile()
        self.assertRaises(NotImplementedError, cmimport_profile.run)

    @patch('enmutils_int.lib.profile.Profile.set_time_stats_value')
    def test_schedule_msg_is_not_none(self, *_):
        profile = Profile()
        profile.NAME = "Test_01"
        setattr(profile, "SCHEDULED_TIMES", [datetime.now(), datetime.now(), datetime.now(),
                                             datetime.now(), datetime.now(), datetime.now(),
                                             datetime.now(), datetime.now(), datetime.now(),
                                             datetime.now(), datetime.now()])
        setattr(profile, "SCHEDULED_DAYS", ["Monday"])
        self.assertTrue(profile.schedule != "NONE")
        setattr(profile, "SCHEDULED_TIMES", [datetime.now()])
        self.assertTrue(profile.schedule != "NONE")

    @patch('enmutils_int.lib.profile.Profile.logger')
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.time.sleep')
    @patch('enmutils_int.lib.profile.time.time')
    @patch('enmutils_int.lib.profile.Profile.calculate_time_to_wait_until_next_iteration')
    def test_sleep_until__does_not_perform_calculations_when_current_time_is_in_schedule_times(
            self, mock_calculate_time_to_wait_until_next_iteration, mock_time, *_):
        profile = Profile()
        profile.NAME = "Test_01"
        profile.state = "RUNNING"
        current_time_in_secs_since_epoch = time.time()
        current_local_time = datetime.fromtimestamp(current_time_in_secs_since_epoch)
        mock_time.return_value = current_time_in_secs_since_epoch
        setattr(profile, "SCHEDULED_TIMES", [current_local_time])
        profile._sleep_until()
        self.assertTrue(profile.state != "SLEEPING")
        self.assertFalse(mock_calculate_time_to_wait_until_next_iteration.called)

    @patch('enmutils_int.lib.profile.Profile._sleep_until')
    def test_sleep_until_time__sleep_until_specific_time(self, _):
        profile = Profile()
        schedule = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 1, 0)
        profile.SCHEDULED_TIMES = [schedule + timedelta(days=1)]
        profile.sleep_until_time()

    @patch('enmutils_int.lib.profile.Profile._sleep_until')
    def test_sleep_until_time__sleep_until_after_1_day_specific_time_(self, _):
        profile = Profile()
        profile.SCHEDULE_SLEEP_DAYS = 1
        schedule = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 1, 0)
        profile.SCHEDULED_TIMES = [schedule + timedelta(days=1)]
        profile.sleep_until_time()

    @patch('enmutils_int.lib.profile.Profile.logger')
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.time.time')
    @patch('enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours')
    @patch('enmutils_int.lib.profile.Profile.calculate_time_to_wait_until_next_iteration', return_value=0)
    def test_sleep_until__will_sleep_for_determined_time(
            self, mock_calculate_time_to_wait_until_next_iteration, mock_log_when_sleeping_for_gt_four_hours, *_):
        profile = Profile()
        setattr(profile, "SCHEDULED_TIMES", [datetime.now() + timedelta(days=6)])
        profile._sleep_time = 5
        profile._sleep_until()
        self.assertTrue(mock_calculate_time_to_wait_until_next_iteration.called)
        self.assertTrue(mock_log_when_sleeping_for_gt_four_hours.called)
        mock_log_when_sleeping_for_gt_four_hours.assert_called_with(5)

    @patch("enmutils_int.lib.profile.Profile.set_time_stats_value")
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch('enmutils_int.lib.profile.time.sleep')
    @patch('enmutils_int.lib.profile.log.logger.debug')
    @patch('enmutils_int.lib.profile.persistence')
    def test_sleep_during_upgrade_run_is_successful_when_upgrade_run_is_true(self, mock_persistence,
                                                                             mock_logger_debug, *_):
        profile = Profile()
        profile.NAME = 'CMEXPORT_03'
        mock_persistence.get.side_effect = ['True', 'False']
        profile.sleep_during_upgrade_run()
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile.time.sleep')
    @patch('enmutils_int.lib.profile.log.logger.debug')
    @patch('enmutils_int.lib.profile.persistence')
    def test_sleep_during_upgrade_run_is_successful_profile_name_not_in_sleeping_profiles(self, mock_persistence,
                                                                                          mock_logger_debug, *_):
        mock_persistence.get.side_effect = ['True', 'False']
        self.base_profile.sleep_during_upgrade_run()
        self.assertFalse(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile.log.logger.debug')
    @patch('enmutils_int.lib.profile.persistence')
    def test_sleep_during_upgrade_run_is_successful_when_upgrade_run_is_false(self, mock_persistence,
                                                                              mock_logger_debug, *_):
        mock_persistence.get.return_value = 'False'
        self.base_profile.sleep_during_upgrade_run()
        self.assertFalse(mock_logger_debug.called)

    # Profile.sleep_until_next_scheduled_iteration TESTS ###############################################################

    @patch('enmutils_int.lib.profile.Profile.sleep')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_day')
    @ParameterizedTestCase.parameterize(
        ("schedule_type", "value"),
        [
            ("SCHEDULED_DAYS", "MONDAY"), ("SCHEDULED_TIMES_STRINGS", "09:15:00"), ("SCHEDULE_SLEEP", 300)
        ]
    )
    def test_sleep_until_next_scheduled_iteration__successfully_selects_the_correct_sleep_calls(
            self, schedule_type, value, mock_sleep_until_day, mock_sleep_until_time, mock_sleep, *_):

        setattr(Profile, schedule_type, value)
        profile = Profile()
        profile.sleep_until_next_scheduled_iteration()

        if schedule_type == "SCHEDULED_DAYS":
            self.assertEqual(mock_sleep_until_day.call_count, 1)
        elif schedule_type == "SCHEDULED_TIMES_STRINGS":
            self.assertEqual(mock_sleep_until_time.call_count, 1)
        else:
            self.assertEqual(mock_sleep.call_count, 1)

        delattr(Profile, schedule_type)

    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @ParameterizedTestCase.parameterize(
        ("error", "value"),
        [
            (FailedNetsimOperation("Restart netsim", [Mock()], "some command"), "NetsimError"),
            (ValidationWarning("Error"), "ValidationWarning")
        ]
    )
    def test_process_error_for_type__success(self, error, value, _):
        profile = Profile()
        error_type = profile._process_error_for_type(error)
        self.assertEqual(error_type, value)

    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=False)
    @patch('enmutils_int.lib.profile.common_utils.delete_profile_users')
    def test_user_cleanup__is_successful_if_services_not_used(
            self, mock_delete_users, mock_check_if_service_can_be_used_by_profile, *_):
        profile = Profile()
        profile.user_count = 1
        profile.NAME = "SECUI_01"
        profile.user_cleanup()
        mock_delete_users.assert_called_with(profile.NAME)
        mock_check_if_service_can_be_used_by_profile.assert_called_with(profile)

    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=True)
    @patch('enmutils_int.lib.profile.usermanager_adaptor.delete_users_via_usermanager_service')
    def test_user_cleanup__is_successful_if_services_are_used(
            self, mock_delete_users_via_usermanager_service, mock_check_if_service_can_be_used_by_profile, *_):
        profile = Profile()
        profile.user_count = 1
        profile.NAME = "SECUI_01"
        profile.user_cleanup()
        mock_delete_users_via_usermanager_service.assert_called_with(profile.NAME)
        mock_check_if_service_can_be_used_by_profile.assert_called_with(profile)

    @patch('enmutils_int.lib.profile.usermanager_adaptor.delete_users_via_usermanager_service')
    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile')
    @patch("enmutils_int.lib.profile.log.logger.debug")
    def test_user_cleanup__does_nothing_if_profile_doesnt_have_user_count(
            self, mock_debug, mock_check_if_service_can_be_used_by_profile, *_):
        profile = Profile()
        profile.user_count = 0
        profile.user_cleanup()
        self.assertFalse(mock_check_if_service_can_be_used_by_profile.called)
        mock_debug.assert_called_with("Profile does not have user count value, so no users to be removed from ENM")

    @patch('enmutils_int.lib.profile.log.logger.debug')
    def test_teardown_list_handles_no_profile(self, mock_debug, *_):
        # TestCase where pickle load fails as the persisted object is the teardown list and the profile
        # attribute is missing
        profile = Profile()
        teardown = TeardownList(profile=profile)
        delattr(teardown, "profile")
        teardown.append([Mock()])
        self.assertEqual(1, mock_debug.call_count)

    def test_teardown__list_append(self, *_):
        profile = Mock()
        teardown = TeardownList(profile=profile)
        teardown.append([Mock()])
        self.assertEqual(1, len(teardown))

    @patch('enmutils_int.lib.profile.log.logger.debug')
    def test_teardown_list_append_logs_none_type(self, mock_debug, *_):
        profile = Profile()
        teardown = TeardownList(profile=profile)
        teardown.append([])
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=False)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile.common_utils.create_users_operation',
           side_effect=[([], []), ([], []), ([Mock()], [])])
    def test_create_users__is_successful_without_using_services(
            self, mock_create_users_operation, mock_add_error_as_exception, *_):
        self.base_profile.create_users(1, ["Admin"])
        self.assertEqual(3, mock_create_users_operation.call_count)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=True)
    @patch('enmutils_int.lib.profile.usermanager_adaptor.create_users_via_usermanager_service')
    def test_create_users__is_successful_if_service_are_used(self, mock_create_users_via_usermanager_service, *_):
        mock_user = Mock()
        mock_create_users_via_usermanager_service.return_value = [mock_user]
        self.assertEqual([mock_user], self.base_profile.create_users(1, ["Admin"]))
        mock_create_users_via_usermanager_service.assert_called_with("TEST_PROFILE", 1, ["Admin"])

    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=True)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile.usermanager_adaptor.create_users_via_usermanager_service')
    def test_create_users__adds_error_to_profile_if_not_all_users_created_when_using_services(
            self, mock_create_users_via_usermanager_service, mock_add_error_as_exception, *_):
        mock_user = Mock()
        mock_create_users_via_usermanager_service.return_value = [mock_user]
        self.assertEqual([mock_user], self.base_profile.create_users(3, ["Admin"]))
        mock_create_users_via_usermanager_service.assert_called_with("TEST_PROFILE", 3, ["Admin"])
        message = "Failed to create 2 users. TEST_PROFILE load will now only run with 1/3 users."
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(call(EnmApplicationError(message) in mock_add_error_as_exception.mock_calls))

    @patch('enmutils_int.lib.profile.common_utils.create_users_operation', return_value=([Mock()], [Mock()]))
    @patch('enmutils_int.lib.profile.usermanager_adaptor.check_if_service_can_be_used_by_profile', return_value=False)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_create_users__adds_failed_users_if_not_using_services(
            self, mock_add_error, mock_check_if_service_can_be_used_by_profile, *_):
        self.base_profile.create_users(2, ["Admin"], retry=False)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_check_if_service_can_be_used_by_profile.call_count, 1)

    def test_set_connection_error_no_request(self):
        e = Mock()
        e.request = None
        exception_msg = "Connection aborted"
        expected_msg = ("The REST call is terminated as the associated ENM service didn't respond within httpd's "
                        "timeout threshold of 2 minutes.\nConnectionError: 'None' request to None raised ConnectionErro"
                        "r {0}. No response given.".format(str(e)))
        error_msg = set_connection_error(e, exception_msg)
        self.assertEqual(error_msg, expected_msg)

    def test_set_connection_error_request(self):
        e, request = Mock(), Mock()
        request.method = "POST"
        request.url = "https://test.com"
        e.request = request
        exception_msg = "Connection Timedout"
        expected_msg = ("ConnectionError: 'POST' request to https://test.com raised ConnectionError {0}. "
                        "No response given.".format(str(e)))
        error_msg = set_connection_error(e, exception_msg)
        self.assertEqual(error_msg, expected_msg)

    @patch('enmutils_int.lib.profile.re.search', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile.log.logger.debug')
    def test_extract_html_body_none_type(self, mock_debug, *_):
        html = "<html> JBWEB </html>"
        extract_html_text(html)
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.profile.log.logger.debug')
    def test_extract_html_body_no_title(self, mock_debug, *_):
        html = "<html> JBWEB </html>"
        extract_html_text(html)
        self.assertEqual(0, mock_debug.call_count)

    def test_set_http_error__connection_aborted(self):
        request = Mock()
        request.url = "http://test.com"
        request.method = "GET"
        response = Mock()
        request.body = None
        response.request = request
        response.status_code = 402
        result = set_http_error(HTTPError(response=response), "Connection aborted")
        expected = "The REST call is terminated as the associated ENM service didn't respond within httpd's timeout"
        self.assertIn(expected, result)

    @patch('__builtin__.hasattr')
    def test_set_http_error__no_request_attribute(self, mock_hasattr):
        mock_hasattr.return_value = False
        request = Mock()
        request.url = "http://test.com"
        request.body = "success"
        response = Mock()
        response.request = request
        response.status_code = 402
        response.text = "sample test"
        result = set_http_error(HTTPError(response=response), "Connection aborted")
        self.assertIn("no attribute", result)
        mock_hasattr.return_value = True

    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.profile.node_pool_mgr.get_pool')
    def test_currently_allocated_nodes_calls_allocated(self, mock_get_pool, *_):
        profile = ExclusiveProfile(name="HA_01")
        self.assertNotEqual(profile.currently_allocated_nodes, None)
        self.assertEqual(1, mock_get_pool.return_value.allocated_nodes.call_count)

    @patch('enmutils_int.lib.profile.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.node_pool_mgr.get_pool')
    def test_used_nodes__is_successful_if_service_not_used(self, mock_get_pool, *_):
        profile = ExclusiveProfile(name="HA_01")
        node = Mock(used=True, is_exclusive=True)
        mock_get_pool.return_value.nodes = [node]
        self.assertEqual([node], profile.used_nodes)

    @patch('enmutils_int.lib.profile.nodemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service')
    def test_used_nodes__is_successful_if_service_is_used(self, mock_get_list_of_nodes_from_service, *_):
        profile = ExclusiveProfile(name="HA_01")
        node = Mock(profiles=["HA_01"], is_exclusive=True)
        mock_get_list_of_nodes_from_service.return_value = [node]
        self.assertEqual([node], profile.used_nodes)

    @patch('enmutils_int.lib.profile.CMImportProfile.nodes_list')
    def test_nodes_list__cm_profile(self, _):
        profile = ExclusiveProfile(name="CMSYNC_01")
        self.assertNotEqual([], profile.nodes_list)

    @patch('enmutils_int.lib.profile.ExclusiveProfile.used_nodes')
    def test_nodes_list__no_cm_profile(self, _):
        profile = ExclusiveProfile(name="HA_01")
        self.assertEqual([], profile.nodes_list)

    def test_exclusive_profile_application__returns_profile_name_prefix(self):
        profile = ExclusiveProfile(name="HA_01")
        self.assertEqual("HA", profile.application)

    def test_exclusive_profile_run_pass(self):
        profile = ExclusiveProfile(name="HA_01")
        profile.run()

    @patch("enmutils_int.lib.profile.common_utils.terminate_user_sessions")
    @patch('enmutils_int.lib.profile.Profile.set_time_stats_value')
    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch('enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours')
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_sleep_sets_correct_last_run_time_next_run_time_schedule_information_for_3_days(self, *_):
        self.base_profile.SCHEDULE_SLEEP = 3 * 24 * 60 * 60
        self.base_profile.sleep()
        start_time = self.base_profile.start_time
        last_run = start_time
        next_run = start_time + timedelta(seconds=self.base_profile.SCHEDULE_SLEEP)
        self.assertEqual(last_run.replace(second=0, microsecond=0),
                         self.base_profile._last_run.replace(second=0, microsecond=0))
        self.assertEqual(next_run.replace(second=0, microsecond=0),
                         self.base_profile._next_run.replace(second=0, microsecond=0))

    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch('enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours')
    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.log.logger.debug")
    def test_sleep_sets_with_zero(self, mock_debug_log, *_):
        self.base_profile.SCHEDULE_SLEEP = 0
        self.base_profile.sleep()
        start_time = self.base_profile.start_time
        last_run = start_time
        next_run = start_time + timedelta(seconds=self.base_profile.SCHEDULE_SLEEP)
        self.assertEqual(last_run.replace(second=0, microsecond=0),
                         self.base_profile._last_run.replace(second=0, microsecond=0))
        self.assertEqual(next_run.replace(second=0, microsecond=0),
                         self.base_profile._next_run.replace(second=0, microsecond=0))
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours")
    @patch("enmutils_int.lib.profile.time.sleep")
    @patch("enmutils_int.lib.profile.log.logger.debug")
    def test_sleep_is_it_last_iteration_or_not(self, mock_debug_log, *_):
        self.base_profile.SCHEDULE_SLEEP = 3 * 24 * 60 * 60
        self.base_profile.KEEP_RUNNING = 0
        self.base_profile.sleep()
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile.Profile._log_when_sleeping_for_gt_four_hours")
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_sleep_is_false_or_not(self, *_):
        self.base_profile.SCHEDULE_SLEEP = 60
        start_time = self.base_profile.start_time
        self.base_profile._next_run = start_time - timedelta(seconds=120)
        self.base_profile.sleep()
        self.assertTrue(self.base_profile.sleep)

    @patch("enmutils_int.lib.profile.log.logger.debug")
    @patch("enmutils_int.lib.profile.Profile.sleep_during_upgrade_run")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_log_when_sleeping_for_gt_four_hours__is_successful_if_duration_is_greater_than_four_hours(
            self, mock_sleep, mock_state, mock_sleep_during_upgrade_run, mock_debug, *_):
        duration_of_4hrs = 60 * 60 * 4
        self.base_profile._log_when_sleeping_for_gt_four_hours(60 * 60 * 9)
        self.assertTrue([call(duration_of_4hrs), call(duration_of_4hrs), call(60 * 60 * 1)] == mock_sleep.mock_calls)
        self.assertTrue(mock_state.call_count == 1)
        self.assertTrue(mock_sleep_during_upgrade_run.call_count == 1)
        self.assertTrue(mock_debug.call_count == 1)

    @patch("enmutils_int.lib.profile.log.logger.debug")
    @patch("enmutils_int.lib.profile.Profile.sleep_during_upgrade_run")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_log_when_sleeping_for_gt_four_hours__is_successful_if_duration_is_not_greater_than_four_hours(
            self, mock_sleep, mock_state, mock_sleep_during_upgrade_run, mock_debug, *_):
        duration_of_4hrs = 60 * 60 * 4
        self.base_profile._log_when_sleeping_for_gt_four_hours(duration_of_4hrs)
        self.assertTrue([call(duration_of_4hrs)] == mock_sleep.mock_calls)
        self.assertTrue(mock_state.call_count == 0)
        self.assertTrue(mock_sleep_during_upgrade_run.call_count == 1)
        self.assertTrue(mock_debug.call_count == 0)

    @patch("enmutils_int.lib.profile.log.logger.debug")
    @patch("enmutils_int.lib.profile.Profile.sleep_during_upgrade_run")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.time.sleep")
    def test_log_when_sleeping_for_gt_four_hours__is_successful_if_duration_is_negative_value(
            self, mock_sleep, mock_state, mock_sleep_during_upgrade_run, mock_debug, *_):
        duration_of_4hrs = 60 * 60 * 4
        self.base_profile._log_when_sleeping_for_gt_four_hours(-duration_of_4hrs)
        self.assertTrue(mock_sleep.call_count == 0)
        self.assertTrue(mock_state.call_count == 0)
        self.assertTrue(mock_sleep_during_upgrade_run.call_count == 1)
        self.assertTrue(mock_debug.call_count == 0)

    @patch('enmutils_int.lib.profile.os.getpid', return_value=9999)
    @patch('enmutils_int.lib.profile.os.path.exists')
    @patch('enmutils_int.lib.profile.os.remove')
    @patch('enmutils_int.lib.profile.process.kill_process_id')
    def test_kill_completed_pid__success(self, mock_kill, mock_os_remove, mock_path, *_):
        mock_path.return_value = False
        self.base_profile.kill_completed_pid()
        self.assertEqual(0, mock_os_remove.call_count)
        mock_kill.assert_called_with(9999, 15)

    @patch('enmutils_int.lib.profile.os.getpid', return_value=9999)
    @patch('enmutils_int.lib.profile.os.path.exists')
    @patch('enmutils_int.lib.profile.os.remove')
    @patch('enmutils_int.lib.profile.process.kill_process_id')
    def test_kill_completed_pid__os_error(self, mock_kill, mock_os_remove, mock_path, *_):
        mock_kill.side_effect = OSError("No such process")
        mock_path.return_value = True
        self.base_profile.kill_completed_pid()
        self.assertEqual(1, mock_os_remove.call_count)

    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.can_service_be_used", return_value=True)
    def test_service_to_be_used__return_true_if_service_can_be_used(self, mock_can_service_be_used, *_):
        profile = Profile()
        self.assertTrue(profile.nodemanager_service_can_be_used)
        mock_can_service_be_used.assert_called_with(profile=profile)

    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.can_service_be_used", return_value=False)
    def test_service_to_be_used__return_false_if_service_cant_be_used(self, *_):
        self.assertFalse(Profile().nodemanager_service_can_be_used)

    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.Profile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_nodes__is_successful_if_service_can_be_used(self, mock_get_list_of_nodes_from_service, mock_get_pool, *_):
        node1 = Mock(primary_type="ERBS")
        node2 = Mock(primary_type="RadioNode")
        node3 = Mock(primary_type="ERBS")
        mock_get_list_of_nodes_from_service.return_value = [node1, node2, node3]
        profile = Profile()
        profile.NAME = "DUMMY"
        nodes_as_a_dict = {"ERBS": [node1, node3], "RadioNode": [node2]}
        self.assertEqual(profile.nodes, nodes_as_a_dict)
        self.assertFalse(mock_get_pool.called)
        mock_get_list_of_nodes_from_service.assert_called_with(profile="DUMMY", node_attributes=["all"])

    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.Profile.__init__", return_value=None)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_nodes__is_successful_if_service_cant_be_used(self, mock_get_list_of_nodes_from_service, mock_get_pool, *_):
        profile = Profile()
        self.assertEqual(profile.nodes, mock_get_pool.return_value.allocated_nodes_as_dict.return_value)
        self.assertTrue(mock_get_pool.called)
        self.assertFalse(mock_get_list_of_nodes_from_service.called)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_nodes_list__is_successful_if_service_can_be_used(
            self, mock_get_list_of_nodes_from_service, mock_get_pool, *_):
        nodes = [Mock(), Mock()]
        mock_get_list_of_nodes_from_service.return_value = nodes
        profile = Profile()
        profile.NAME = "DUMMY"
        self.assertEqual(profile.nodes_list, nodes)
        self.assertFalse(mock_get_pool.called)
        mock_get_list_of_nodes_from_service.assert_called_with(profile="DUMMY")

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_pool")
    def test_nodes_list__is_successful_if_service_cant_be_used(
            self, mock_get_pool, mock_get_list_of_nodes_from_service, *_):
        nodes = [Mock(), Mock()]
        mock_get_pool.return_value.allocated_nodes.return_value = nodes
        profile = Profile()
        profile.node_attributes = ["abc"]
        profile.NAME = "TEST_PROFILE"
        self.assertEqual(profile.nodes_list, nodes)
        self.assertFalse(mock_get_list_of_nodes_from_service.called)
        mock_get_pool.return_value.allocated_nodes.assert_called_with(profile)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_allocated_nodes")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_get_nodes_list_by_attribute__is_successful_if_service_can_be_used(
            self, mock_get_list_of_nodes_from_service, mock_get_allocated_nodes, *_):
        nodes = [Mock(), Mock()]
        mock_get_list_of_nodes_from_service.return_value = nodes
        profile = Profile()
        profile.NAME = "DUMMY"
        self.assertEqual(profile.get_nodes_list_by_attribute(), nodes)
        self.assertFalse(mock_get_allocated_nodes.called)
        mock_get_list_of_nodes_from_service.assert_called_with(profile="DUMMY", node_attributes=None)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_allocated_nodes")
    def test_get_nodes_list_by_attribute__is_successful_if_service_cant_be_used(
            self, mock_get_allocated_nodes, mock_get_list_of_nodes_from_service, *_):
        nodes = [Mock(), Mock()]
        mock_get_allocated_nodes.return_value = nodes
        profile = Profile()
        profile.node_attributes = ["abc"]
        self.assertEqual(profile.get_nodes_list_by_attribute(node_attributes=["node_id"],
                                                             profile_name="TEST_PROFILE"), nodes)
        self.assertFalse(mock_get_list_of_nodes_from_service.called)
        mock_get_allocated_nodes.assert_called_with("TEST_PROFILE", node_attributes=["node_id"])

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_all_nodes_using_separate_process")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_all_nodes_in_workload_pool__is_successful_if_service_can_be_used(
            self, mock_get_list_of_nodes_from_service, mock_get_pool, *_):
        node1 = node3 = Mock(primary_type="ERBS")
        node2 = Mock(primary_type="RadioNode")
        mock_get_list_of_nodes_from_service.return_value = [node1, node2, node3]
        profile = Profile()
        profile.NUM_NODES = {"ERBS": -1}
        self.assertEqual(profile.all_nodes_in_workload_pool(), [node1, node3])
        self.assertEqual(profile.all_nodes_in_workload_pool(node_attributes=["primary_type"]), [node1, node3])
        self.assertFalse(mock_get_pool.called)
        mock_get_list_of_nodes_from_service.assert_called_with(node_attributes=["primary_type"])

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_all_nodes_using_separate_process")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_all_nodes_in_workload_pool__is_successful_if_service_can_be_used_but_profile_has_no_num_nodes_attr(
            self, mock_get_list_of_nodes_from_service, mock_get_pool, *_):
        node1, node3 = Mock(primary_type="ERBS"), Mock(primary_type="ERBS")
        node2 = Mock(primary_type="RadioNode")
        mock_get_list_of_nodes_from_service.return_value = [node1, node2, node3]
        profile = Profile()
        self.assertEqual(profile.all_nodes_in_workload_pool(), [node1, node2, node3])
        self.assertFalse(mock_get_pool.called)
        self.assertTrue(mock_get_list_of_nodes_from_service.called)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=False)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_all_nodes_using_separate_process")
    def test_all_nodes_in_workload_pool__is_successful_if_service_cant_be_used(self, mock_get_all_nodes,
                                                                               mock_get_list_of_nodes_from_service, *_):
        self.base_profile.NUM_NODES = {"ERBS": -1}
        self.base_profile.node_attributes = ["abc"]
        nodes = [Mock(primary_type="ERBS"), Mock(primary_type="ERBS")]
        mock_get_all_nodes.return_value = nodes
        self.assertEqual(self.base_profile.all_nodes_in_workload_pool(), nodes)
        self.assertTrue(mock_get_all_nodes.called)
        self.assertFalse(mock_get_list_of_nodes_from_service.called)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_all_nodes_using_separate_process")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_all_nodes_in_workload_pool__if_is_num_nodes_required_false(self, mock_get_list_of_nodes_from_service,
                                                                        mock_get_all_nodes, *_):
        self.base_profile.NUM_NODES = {"ERBS": -1}
        self.base_profile.node_attributes = ["abc"]
        nodes = [Mock(primary_type="ERBS"), Mock(primary_type="ERBS")]
        mock_get_list_of_nodes_from_service.return_value = nodes
        self.assertEqual(self.base_profile.all_nodes_in_workload_pool(is_num_nodes_required=False), nodes)
        self.assertTrue(mock_get_list_of_nodes_from_service.called)
        self.assertFalse(mock_get_all_nodes.called)

    @patch("enmutils_int.lib.profile.process.get_current_rss_memory_for_current_process")
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.node_pool_mgr.get_all_nodes_using_separate_process")
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_all_nodes_in_workload_pool__if_is_num_nodes_required_false_with_node_attribute(
            self, mock_get_list_of_nodes_from_service, mock_get_all_nodes, *_):
        self.base_profile.NUM_NODES = {"ERBS": -1}
        self.base_profile.node_attributes = ["abc"]
        nodes = [Mock(primary_type="ERBS"), Mock(primary_type="ERBS")]
        mock_get_list_of_nodes_from_service.return_value = nodes
        self.assertEqual(self.base_profile.all_nodes_in_workload_pool(node_attributes=['node_id'],
                                                                      is_num_nodes_required=False), nodes)
        self.assertTrue(mock_get_list_of_nodes_from_service.called)
        self.assertFalse(mock_get_all_nodes.called)

    @patch("enmutils_int.lib.profile.Profile.all_nodes_in_workload_pool")
    def test_get_all_nodes_in_workload_pool_based_on_node_filter(self, mock_all_nodes_in_workload_pool):
        self.base_profile.NUM_NODES = {"Radio": -1}
        self.base_profile.node_attributes = ["node_id", "managed_element_type"]
        self.base_profile.NODE_FILTER = {"RADIONODE": {"managed_element_type": ["ENodeB"]}}
        self.base_profile.get_all_nodes_in_workload_pool_based_on_node_filter()
        mock_all_nodes_in_workload_pool.assert_called_with(node_attributes=['node_id', 'managed_element_type', 'poid',
                                                                            'primary_type'])

    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_init__is_successful_for_exclusive_profile_if_service_can_be_used(
            self, mock_get_list_of_nodes_from_service, *_):
        node1 = Mock(primary_type="ERBS", profiles="PROFILE1", is_exclusive=True)
        node2 = Mock(primary_type="ERBS", profiles="", is_exclusive=True)
        node3 = Mock(primary_type="RadioNode", profiles="PROFILE3", is_exclusive=False)
        node4 = Mock(primary_type="RadioNode", profiles="PROFILE4", is_exclusive=True)
        mock_get_list_of_nodes_from_service.return_value = [node1, node2, node3, node4]
        profile = ExclusiveProfile(name="HA_01")
        self.assertEqual(profile.used_nodes, [node1, node4])

    @patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile.Profile.nodemanager_service_can_be_used", new_callable=PropertyMock,
           return_value=True)
    @patch("enmutils_int.lib.profile.nodemanager_adaptor.get_list_of_nodes_from_service")
    def test_currently_allocated_nodes__is_successful_for_exclusive_profile_if_service_can_be_used(
            self, mock_get_list_of_nodes_from_service, *_):
        node1 = Mock()
        node2 = Mock()
        node3 = Mock()
        mock_get_list_of_nodes_from_service.return_value = [node1, node2, node3]
        profile = ExclusiveProfile(name="HA_01")
        self.assertEqual(profile.currently_allocated_nodes, [node1, node2, node3])

    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=True)
    @patch("enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string")
    def test_add_error_as_exception__error_limit_reached(self, mock_persist_error, *_):
        self.base_profile.add_error_as_exception(Exception('Error'))
        self.assertEqual(mock_persist_error.call_count, 0)

    @patch("enmutils_int.lib.profile.Profile.update_error", return_value='Some Error')
    @patch("enmutils_int.lib.profile.Profile._process_error_for_type", return_value=Exception().__class__.__name__)
    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    @patch("enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string")
    def test_add_error_as_exception__error_limit_not_reached(self, mock_persist_error, *_):
        mock_some_exception = Exception("Some Error")
        self.assertIsNone(self.base_profile.add_error_as_exception(mock_some_exception, log_trace=False))
        self.assertEqual(mock_persist_error.call_count, 1)
        mock_persist_error.assert_called_once_with('Some Error', 'TEST_PROFILE-errors',
                                                   error_type=Exception().__class__.__name__)

    @patch("enmutils_int.lib.profile.Profile.update_error", return_value='Some Warning')
    @patch("enmutils_int.lib.profile.Profile._process_error_for_type", return_value=EnvironWarning().__class__.__name__)
    @patch("enmutils_int.lib.profile.Profile.check_if_error_limit_reached", return_value=False)
    @patch("enmutils_int.lib.profile.Profile._persist_error_or_warning_as_string")
    def test_add_error_as_exception__add_warning(self, mock_persist_error, *_):
        mock_some_exception = EnvironWarning("Some warning")
        self.base_profile.add_error_as_exception(mock_some_exception, log_trace=False)
        self.assertEqual(mock_persist_error.call_count, 1)
        mock_persist_error.assert_called_once_with('Some Warning', 'TEST_PROFILE-warnings',
                                                   error_type=EnvironWarning().__class__.__name__)

    def test_update_error_message_with_custom_length__script_engine_response_error(self):
        mock_response = Mock(command='Some command')
        mock_response.http_response_code.return_value = 400
        error = NoOuputFromScriptEngineResponseError('Some error', mock_response)
        error_length, error_message = self.base_profile.update_error_message_with_custom_length(error)
        self.assertEqual(error_length, 700)
        self.assertEqual(error_message, "NoOuputFromScriptEngineResponseError: ScriptEngineCommand"
                                        " 'Some command' failed with status code 400.")

    def test_update_error_message_with_custom_length__shell_command_non_zero_error(self):
        mock_response = Mock(command='Some command', rc=1, stdout='Some stdout')
        mock_response.http_response_code.return_value = 400
        error = ShellCommandReturnedNonZero('Some error', mock_response)
        error_length, error_message = self.base_profile.update_error_message_with_custom_length(error)
        self.assertEqual(error_length, 2000)
        self.assertEqual(error_message, "ShellError: Command 'Some command' gave rc '1'\nResponse: 'Some stdout'")

    def test_update_error_message_with_custom_length__default_handel_of_error(self):

        error_length, error_message = self.base_profile.update_error_message_with_custom_length(Exception('Some error'))
        self.assertEqual(error_length, 200)
        self.assertEqual(error_message, "Some error")

    @patch("enmutils_int.lib.profile.set_http_error", return_value='HttpError passed')
    def test_update_error_message_for_connection_error__http_error(self, mock_set_http_error):
        self.assertEqual('HttpError passed',
                         self.base_profile.update_error_message_for_connection_error(HTTPError('Some error'),
                                                                                     'Some error'))
        self.assertEqual(mock_set_http_error.call_count, 1)

    @patch("enmutils_int.lib.profile.set_connection_error", return_value='ConnectionError passed')
    def test_update_error_message_for_connection_error__connection_error(self, mock_set_connection_error):
        self.assertEqual('ConnectionError passed',
                         self.base_profile.update_error_message_for_connection_error(ConnectionError('Some error'),
                                                                                     'Some Error'))
        self.assertEqual(mock_set_connection_error.call_count, 1)

    @patch('enmutils_int.lib.profile.datetime.datetime')
    def test_reset_error_counter__reset_counter_on_new_day(self, mock_date_time, *_):
        mock_t1 = Mock()
        mock_t1.strftime.return_value = '25/12/2019'
        mock_date_time.now.return_value = mock_t1
        self.base_profile.daily_error_count = 2005
        self.base_profile.reset_date = '24/12/2019'
        self.assertTrue(self.base_profile.reset_error_counter())
        self.assertEqual(self.base_profile.daily_error_count, 0)
        self.assertEqual(self.base_profile.reset_date, '25/12/2019')

    @patch('enmutils_int.lib.profile.datetime.datetime')
    def test_reset_error_counter__counter_not_reset(self, mock_date_time, *_):
        mock_t1 = Mock()
        mock_t1.strftime.return_value = '24/12/2019'
        mock_date_time.now.return_value = mock_t1
        self.base_profile.daily_error_count = 2005
        self.base_profile.reset_date = '24/12/2019'
        self.assertFalse(self.base_profile.reset_error_counter())
        self.assertEqual(self.base_profile.daily_error_count, 2005)
        self.assertEqual(self.base_profile.reset_date, '24/12/2019')

    def test_error_limit_reached__not_reached(self):

        self.base_profile.daily_error_count = 1500

        self.assertFalse(self.base_profile.check_if_error_limit_reached())

    @patch("enmutils_int.lib.profile.Profile.reset_error_counter", return_value=False)
    def test_error_limit_reached__limit_reached_reached(self, *_):

        self.base_profile.daily_error_count = 2000

        self.assertTrue(self.base_profile.check_if_error_limit_reached())

    @patch("enmutils_int.lib.profile.Profile.reset_error_counter", return_value=False)
    @patch('enmutils_int.lib.profile.log.logger.debug')
    def test_error_limit_reached__warning_logged_once(self, mock_debug, *_):
        self.base_profile.daily_error_count = 2000
        self.assertTrue(self.base_profile.check_if_error_limit_reached())
        self.assertEqual(mock_debug.call_count, 1)
        self.assertTrue(self.base_profile.logged_exceeded_limit_message)
        self.assertTrue(self.base_profile.check_if_error_limit_reached())
        self.assertEqual(mock_debug.call_count, 1)
        mock_debug.assert_called_once_with('Profile has exceeded error logging limit of {0} '
                                           'for today: {1}'.format(self.base_profile.ERROR_LIMIT,
                                                                   self.base_profile.reset_date))

    @patch("enmutils_int.lib.profile.Profile.reset_error_counter", return_value=True)
    def test_error_limit_reached__reached_but_counter_reset(self, *_):

        self.base_profile.daily_error_count = 2000
        self.assertFalse(self.base_profile.check_if_error_limit_reached())

    @patch('enmutils_int.lib.profile.TeardownList')
    def test_remove_partial_items_from_teardown_list_if_instance_is_partial(self, mock_teardown_list):
        mock_teardown_list.return_value = [Mock(spec=partial)] * 2
        profile = Profile()
        self.assertNotEqual(profile.teardown_list, [])
        profile.remove_partial_items_from_teardown_list()
        self.assertEqual(profile.teardown_list, [])

    @patch('enmutils_int.lib.profile.TeardownList')
    def test_remove_partial_items_from_teardown_list_if_instance_is_not_partial(self, mock_teardown_list):
        mock_teardown_list.return_value = [Mock(spec=int)] * 2
        profile = Profile()
        self.assertNotEqual(profile.teardown_list, [])
        profile.remove_partial_items_from_teardown_list()
        self.assertNotEqual(profile.teardown_list, [])

    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="STARTING")
    @patch('enmutils_int.lib.profile.Profile.priority', new_callable=PropertyMock, return_value="1")
    @patch('enmutils_int.lib.profile.Profile.schedule', new_callable=PropertyMock, return_value="NOW")
    @patch('enmutils_int.lib.profile.Profile.get_last_run_time', return_value="Time")
    @patch('enmutils_int.lib.profile.persistence.set')
    def test_set_status__uses_legacy(self, mock_set, *_):
        profile = Profile()
        profile.NAME = "TEST_00"
        profile.start_time = "Time"
        profile.pid = "1234"
        profile.num_nodes = 10
        profile.user_count = 2
        profile.set_status_object()
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="STARTING")
    @patch('enmutils_int.lib.profile.Profile.priority', new_callable=PropertyMock, return_value="1")
    @patch('enmutils_int.lib.profile.Profile.schedule', new_callable=PropertyMock, return_value="NOW")
    @patch('enmutils_int.lib.profile.DiffProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.persistence.set')
    def test_set_diff_object__success(self, mock_set, *_):
        profile = Profile()
        profile.state = 'test'
        profile.start_time = 'NOW'
        profile.version = '1234'
        profile.update_version = '1234'
        profile.set_diff_object()
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils_int.lib.profile.os.path.exists', return_value=False)
    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="STARTING")
    @patch('enmutils_int.lib.profile.Profile.priority', new_callable=PropertyMock, return_value="1")
    @patch('enmutils_int.lib.profile.Profile.schedule', new_callable=PropertyMock, return_value="NOW")
    @patch('enmutils_int.lib.profile.Profile.get_last_run_time', return_value=datetime.now())
    @patch('enmutils_int.lib.profile.mutexer.mutex')
    @patch('enmutils_int.lib.profile.persistence.get', side_effect=[["TEST_00", "TEST_01"], ["TEST_01"]])
    @patch('enmutils_int.lib.profile.persistence.set')
    @patch('enmutils_int.lib.profile.Profile.clear_errors')
    @patch('enmutils_int.lib.profile.persistence.remove')
    def test_remove__success(self, mock_remove, mock_clear, *_):
        profile = Profile()
        profile.NAME = "TEST_00"
        profile.pidfile = "file"
        profile.remove()
        self.assertEqual(3, mock_remove.call_count)
        self.assertEqual(1, mock_clear.call_count)

    @patch('enmutils_int.lib.profile.os.path.exists', return_value=False)
    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="STARTING")
    @patch('enmutils_int.lib.profile.Profile.priority', new_callable=PropertyMock, return_value="1")
    @patch('enmutils_int.lib.profile.Profile.schedule', new_callable=PropertyMock, return_value="NOW")
    @patch('enmutils_int.lib.profile.Profile.get_last_run_time', return_value=datetime.now())
    @patch('enmutils_int.lib.profile.mutexer.mutex')
    @patch('enmutils_int.lib.profile.persistence.get', side_effect=[["TEST_01"], ["TEST_01"]])
    @patch('enmutils_int.lib.profile.persistence.set')
    @patch('enmutils_int.lib.profile.Profile.clear_errors')
    @patch('enmutils_int.lib.profile.persistence.remove')
    def test_remove__value_error_caught_if_not_in_active_list(self, mock_remove, mock_clear, *_):
        profile = Profile()
        profile.NAME = "TEST_00"
        profile.pidfile = "file"
        profile.remove()
        self.assertEqual(3, mock_remove.call_count)
        self.assertEqual(1, mock_clear.call_count)

    @patch('enmutils_int.lib.profile.Profile.check_for_repeating_error', return_value=None)
    @patch('enmutils_int.lib.profile.Profile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile.persistence.get')
    @patch('enmutils_int.lib.profile.persistence.set')
    def test_persist_error_or_warning_as_string__uses_persistence_set(self, mock_set, *_):
        profile = Profile()
        profile._persist_error_or_warning_as_string("Error", "TEST_00-errors", error_type="ProfileError")
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value="STARTING")
    def test_set_time_stats_value__last_run_never_next_run_now(self, _):
        self.base_profile._last_run = None
        self.base_profile.next_run_time = None
        self.base_profile._next_run = None
        self.base_profile._initial_start = None
        self.assertEqual("(last run: [NEVER], next run: [NOW])", self.base_profile.set_time_stats_value())

    @patch('enmutils_int.lib.profile.Profile.state', new_callable=PropertyMock, return_value=None)
    def test_set_time_stats_value__no_state(self, _):
        now = datetime.now()
        now_fmt = now.strftime("%d-%b %H:%M:%S")
        self.base_profile._last_run = now
        self.assertEqual("(last run: {0}, next run: [When Profile Starts])".format(now_fmt),
                         self.base_profile.set_time_stats_value())

    @patch('enmutils_int.lib.profile.Profile.set_time_stats_value', return_value=None)
    def test_schedule_property__no_schedule_days(self, _):
        now = datetime.now()
        now_fmt = now.strftime("%H:%M")
        profile = Profile()
        profile.SCHEDULED_TIMES = [datetime.now()]
        self.assertEqual("Runs at the following times: {0} None".format(now_fmt), profile.schedule)

    def test_check_for_repeating_error(self):
        self.base_profile.check_for_repeating_error([], "abc")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
