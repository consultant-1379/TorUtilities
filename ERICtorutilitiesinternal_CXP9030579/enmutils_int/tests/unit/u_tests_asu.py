#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest2
from mock import Mock, patch, mock_open
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import EnmApplicationError, TimeOutError, JobValidationError, EnvironError
from enmutils_int.lib.asu import FlowAutomation
from testslib import unit_test_utils


class AsuJobUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        node = Mock()
        node.node_id = "A"
        self.nodes = [node, node]
        self.NAME = "ASU_01"
        self.flow = FlowAutomation(nodes=self.nodes, flow_name='test', user=self.user)
        self.flow.JOB_WAIT_TIME = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.asu.Environment.get_template')
    def test_get_template(self, *_):
        self.flow.get_template(Mock())

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.asu.FlowAutomation.get_template')
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_prepare_asu_user_input_json_file_success(self, mock_log, mock_template, *_):
        test_software_pack = [{"nodeType": "RadioNode", "runningNodeVariant": "CXP9024418",
                               "targetPackageName": "CXP9024418_6_R54A04091345"}]
        self.flow.prepare_asu_user_input_json_file(test_software_pack)
        self.assertEqual(mock_log.call_count, 4)
        self.assertEqual(mock_template.call_count, 1)

    def test_prepare_software_package_json_for_asu_json_file__success(self):
        self.flow.node_variants = ["CXP9024418/6"]
        test_res = self.flow.prepare_software_package_json_for_asu_json_file("CXP9024418_6_R54A04091345")
        self.assertEqual(test_res, [{"runningNodeVariant": "CXP9024418/6", "nodeType": "RadioNode",
                                     "targetPackageName": "CXP9024418_6_R54A04091345"}])

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.asu.raise_for_status')
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_create_flow_success(self, mock_log, *_):
        self.user.post.return_value.json.return_value = {"name": "ABC"}
        self.assertEqual("ABC", self.flow.create_flow("ABC", "/tmp/ABC"))
        self.assertEqual(mock_log.call_count, 3)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.asu.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_create_flow_exception(self, mock_log, *_):
        self.assertRaises(HTTPError, self.flow.create_flow, "ABC", "/tmp/ABC")
        self.assertEqual(mock_log.call_count, 2)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.asu.raise_for_status')
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_create_flow_raises_EnmApplicationError(self, mock_log, *_):
        self.user.post.return_value.json.return_value = {"namesss": "ABC"}
        self.assertRaises(EnmApplicationError, self.flow.create_flow, "ABC", "/tmp/ABC")
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.asu.filesystem.does_dir_exist', return_value=False)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.filesystem.create_dir')
    def test_create_directory_structure__success(self, mock_create, mock_log, mock_dir, *_):
        self.flow.create_directory_structure("mock/path")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_dir.called)

    @patch('enmutils_int.lib.asu.filesystem.does_dir_exist', return_value=True)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_create_directory_structure__directory_exists(self, mock_log, mock_dir):
        self.flow.create_directory_structure("mock/path")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_dir.called)

    @patch('enmutils_int.lib.asu.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.asu.shell.run_cmd_on_vm')
    def test_execute_commands_in_scripting_vm_in_phy_or_cloud__create_dir_and_copy_install_scripts(self, mock_run_cmd_on_vm, _):
        mock_run_cmd_on_vm.return_value = Mock(rc=0)
        self.flow.execute_commands_in_scripting_vm_in_phy_or_cloud("scp-1-scripting")
        self.assertTrue(mock_run_cmd_on_vm.called)

    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.shell.run_remote_cmd')
    def test_execute_commands_in_scripting_vm_in_cloud_native__create_dir_and_copy_install_scripts(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=0)
        self.flow.execute_commands_in_scripting_vm_in_cloud_native("scp-1-scripting")
        self.assertTrue(mock_run_remote_cmd.called)

    @patch('enmutils_int.lib.asu.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.shell.run_cmd_on_vm')
    def test_execute_commands_in_scripting_vm_in_phy_or_cloud__dir_exists_and_copy_install_scripts(self, mock_run_cmd_on_vm, *_):
        mock_run_cmd_on_vm.side_effect = [Mock(rc=1), Mock(rc=0), Mock(rc=1)]
        self.assertRaises(EnvironError, self.flow.execute_commands_in_scripting_vm_in_phy_or_cloud, "scp-1-scripting")

    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.shell.run_remote_cmd')
    def test_execute_commands_in_scripting_vm_in_cloud_native__dir_exists_and_copy_install_scripts(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.side_effect = [Mock(rc=1), Mock(rc=0), Mock(rc=1)]
        self.assertRaises(EnvironError, self.flow.execute_commands_in_scripting_vm_in_cloud_native, "scp-1-scripting")

    @patch('enmutils_int.lib.asu.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.shell.run_cmd_on_vm')
    def test_execute_commands_in_scripting_vm_in_phy_or_cloud__dir_failed_to_create(self, mock_run_cmd_on_vm, *_):
        mock_run_cmd_on_vm.return_value = Mock(rc=1)
        self.assertRaises(EnvironError, self.flow.execute_commands_in_scripting_vm_in_phy_or_cloud, "scp-1-scripting")

    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.shell.run_remote_cmd')
    def test_execute_commands_in_scripting_vm_in_cloud_native__dir_failed_to_create(self, mock_run_remote_cmd, *_):
        mock_run_remote_cmd.return_value = Mock(rc=1)
        self.assertRaises(EnvironError, self.flow.execute_commands_in_scripting_vm_in_cloud_native, "scp-1-scripting")

    def test_execute_commands_in_scripting_vm_environ_error(self):
        self.assertRaises(EnvironError, self.flow.execute_commands_in_scripting_vm, [])

    @patch('enmutils_int.lib.asu.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.asu.FlowAutomation.execute_commands_in_scripting_vm_in_phy_or_cloud")
    def test_execute_commands_in_scripting_vm__on_phy_or_cloud(self, mock_run_cmd_on_vm, _):
        self.flow.execute_commands_in_scripting_vm(["scripting1", "scripting2"])
        self.assertTrue(mock_run_cmd_on_vm.called)

    @patch('enmutils_int.lib.asu.is_enm_on_cloud_native', return_value=True)
    @patch("enmutils_int.lib.asu.FlowAutomation.execute_commands_in_scripting_vm_in_cloud_native")
    def test_execute_commands_in_scripting_vm__on_cloud_native(self, mock_run_cmd_on_host, _):
        self.flow.execute_commands_in_scripting_vm(["scripting1", "scripting2"])
        self.assertTrue(mock_run_cmd_on_host.called)

    @patch('enmutils_int.lib.asu.FlowAutomation.execute_commands_in_scripting_vm')
    @patch("enmutils_int.lib.asu.get_list_of_scripting_service_ips")
    def test_create_install_scripts_in_scripting_vm_successful(self, mock_get_list_of_scripting_service_ips, mock_exec_commands):
        self.flow.create_install_scripts_in_scripting_vm()
        self.assertTrue(mock_get_list_of_scripting_service_ips.called)
        self.assertTrue(mock_exec_commands.called)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete(self, mock_response, mock_log, mock_datetime, mock_timedelta, *_):
        profile_obj = Mock()
        profile_obj.JOB_WAIT_TIME = 60
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=60)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.flow.JOB_WAIT_TIME)
        mock_response.return_value.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "COMPLETED"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 5,
                    "numNodesFailed": 0
                }
            }
        }
        self.flow.check_status_and_wait_flow_to_complete(self.flow, "ABC")
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete__raises_exception_for_failed_state(self, mock_response, mock_datetime, mock_timedelta, *_):
        profile_obj = Mock()
        profile_obj.JOB_WAIT_TIME = 60
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=60)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.flow.JOB_WAIT_TIME)
        mock_response.return_value.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "FAILED_EXECUTE"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 5,
                    "numNodesFailed": 0
                }
            }
        }
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, self.flow, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete__raises_exception_for_other_states(self, mock_response, mock_datetime, mock_timedelta, *_):
        profile_obj = Mock()
        profile_obj.JOB_WAIT_TIME = 60
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=60)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.flow.JOB_WAIT_TIME)
        mock_response.return_value.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "OTHER_STATE"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 5,
                    "numNodesFailed": 0
                }
            }
        }
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, self.flow, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete__total_and_success_nodes_differ(self, mock_response, mock_datetime,
                                                                                    mock_timedelta, *_):
        profile_obj = Mock()
        profile_obj.JOB_WAIT_TIME = 60
        time_now = datetime.now()
        expiry_time = time_now + timedelta(seconds=60)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = timedelta(minutes=self.flow.JOB_WAIT_TIME)
        mock_response.return_value.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "COMPLETED"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 4,
                    "numNodesFailed": 0
                }
            }
        }
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, self.flow, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete_total_nodes_dont_match_success_nodes(self, mock_response, *_):
        profile_obj = Mock()
        mock_response.return_value.json.side_effect = [
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "EXECUTING"
                },
                "body": {
                    "reportSummary": {
                        "numberOfNodes": 5,
                        "numNodesSuccess": 0,
                        "numNodesFailed": 0
                    }
                }
            },
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "COMPLETED"},
                "body": {
                    "reportSummary": {
                        "numberOfNodes": 5,
                        "numNodesSuccess": 4,
                        "numNodesFailed": 0}
                }
            }]
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, profile_obj, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete_raise_EnmApplicationError(self, mock_response, *_):
        profile_obj = Mock()
        mock_response.return_value.json.side_effect = [
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "FAILED_EXECUTE"
                }
            },
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "FAILED_EXECUTE"
                }
            }
        ]
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, profile_obj, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete_raise_EnmApplicationError_unexpected_status(self,
                                                                                                mock_response, *_):
        profile_obj = Mock()
        mock_response.return_value.json.side_effect = [
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "UNEXPECTED_STATUS"
                }
            },
            {
                "header": {
                    "reportTime": "2019-06-25T06:45:32+0100",
                    "flowId": "com.ericsson.oss.services.shm.asu.flow",
                    "flowVersion": "1.9.5",
                    "flowName": "Automated Software Upgrade",
                    "flowExecutionName": "ASU0106250643",
                    "startedBy": "ASU_01_0625-06434027_u0",
                    "startTime": "2019-06-25T06:44:32+0100",
                    "status": "UNEXPECTED_STATUS"
                }
            }
        ]
        self.assertRaises(EnmApplicationError, self.flow.check_status_and_wait_flow_to_complete, profile_obj, "ABC")

    @patch('enmutils_int.lib.asu.time.sleep', return_value=0)
    @patch("enmutils_int.lib.asu.datetime.timedelta")
    @patch("enmutils_int.lib.asu.datetime.datetime")
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.asu.FlowAutomation._get_flow_response')
    def test_check_status_and_wait_flow_to_complete_raise_TimeOutError(self, mock_response, mock_log, mock_datetime,
                                                                       mock_timedelta, *_):
        profile_obj = Mock()
        time_now = datetime.now()
        mock_datetime.now.side_effect = [time_now + timedelta(-1), time_now + timedelta(-1), time_now + timedelta(0)]
        mock_timedelta.return_value = timedelta(1)

        mock_response.return_value.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "EXECUTING"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 0,
                    "numNodesFailed": 0
                }
            }
        }
        self.assertRaises(TimeOutError, self.flow.check_status_and_wait_flow_to_complete, profile_obj, "ABC")
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_get_flow_response_success(self, mock_log, *_):
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "header": {
                "reportTime": "2019-06-25T06:45:32+0100",
                "flowId": "com.ericsson.oss.services.shm.asu.flow",
                "flowVersion": "1.9.5",
                "flowName": "Automated Software Upgrade",
                "flowExecutionName": "ASU0106250643",
                "startedBy": "ASU_01_0625-06434027_u0",
                "startTime": "2019-06-25T06:44:32+0100",
                "status": "EXECUTING"},
            "body": {
                "reportSummary": {
                    "numberOfNodes": 5,
                    "numNodesSuccess": 0,
                    "numNodesFailed": 0
                }
            }
        }

        self.user.get.return_value = response
        self.flow._get_flow_response("ABC")
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_get_flow_response_raises_JobValidationError(self, mock_log, *_):
        response = Mock()
        response.ok = False
        self.user.get.side_effect = [response, response, response]
        self.assertRaises(JobValidationError, self.flow._get_flow_response, "ABC")
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=None)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_get_flow_response_raises_JobValidationError_retries(self, mock_log, *_):
        response = Mock()
        response.ok = True
        response.json.return_value = {}
        self.user.get.side_effect = [response, response, response, response]
        self.assertRaises(JobValidationError, self.flow._get_flow_response, "ABC")
        self.assertEqual(mock_log.call_count, 9)

    @patch('enmutils_int.lib.asu.SHMUtils.create_and_import_software_package')
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_get_new_radio_node_pkg_success(self, mock_log, mock_create_and_import):
        mock_software_package = Mock()
        mock_software_package.new_package = "ABC"
        mock_create_and_import.return_value = {"software_package": mock_software_package}
        self.assertEqual("ABC", self.flow.get_new_radio_node_pkg(self.NAME))
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.asu.SHMUtils.create_and_import_software_package', side_effect=Exception)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_get_new_radio_node_pkg_raises_EnmApplicationError(self, mock_log, mock_create_and_import):
        self.assertRaises(EnmApplicationError, self.flow.get_new_radio_node_pkg, self.NAME)
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create_and_import.called)

    @patch('enmutils_int.lib.asu.time.sleep', return_value=0)
    @patch('enmutils_int.lib.asu.FlowAutomation.create_install_scripts_in_scripting_vm')
    @patch('enmutils_int.lib.asu.FlowAutomation.prepare_software_package_json_for_asu_json_file')
    @patch('enmutils_int.lib.asu.FlowAutomation.prepare_asu_user_input_json_file')
    @patch('enmutils_int.lib.asu.FlowAutomation.create_flow', return_value="ABC")
    @patch('enmutils_int.lib.asu.FlowAutomation.check_status_and_wait_flow_to_complete')
    @patch('enmutils_int.lib.asu.FlowAutomation.get_new_radio_node_pkg', return_value="ABC")
    @patch('enmutils_int.lib.asu.FlowAutomation.create_directory_structure')
    @patch('enmutils_int.lib.asu.log.logger.debug')
    def test_create_flow_automation__success(self, mock_log, mock_create, mock_pkg, mock_status, mock_create_flow, *_):
        self.flow.create_flow_automation(self)
        self.assertEqual(mock_log.call_count, 4)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_pkg.called)
        self.assertTrue(mock_status.called)
        self.assertTrue(mock_create_flow.called)

    @patch('enmutils_int.lib.asu.FlowAutomation.create_directory_structure')
    @patch('enmutils_int.lib.asu.FlowAutomation.get_new_radio_node_pkg', side_effect=EnmApplicationError)
    @patch('enmutils_int.lib.asu.log.logger.debug')
    @patch('enmutils_int.lib.profile.Profile')
    def test_create_flow_automation__add_error_as_exception(self, mock_profile_object, mock_log, *_):
        mock_profile_object.add_error_as_exception.return_value = Mock()
        self.flow.create_flow_automation(mock_profile_object)
        self.assertEqual(mock_log.call_count, 1)
        self.assertTrue(mock_profile_object.add_error_as_exception.called)

    @patch('enmutils_int.lib.asu.filesystem.remove_dir')
    @patch('enmutils_int.lib.asu.filesystem.does_dir_exist', return_value=True)
    def test_delete_directory_structure__success(self, mock_dir_check, mock_rem_dir):
        self.flow.delete_directory_structure()
        self.assertTrue(mock_dir_check.called)
        self.assertTrue(mock_rem_dir.called)

    @patch('enmutils_int.lib.asu.filesystem.does_dir_exist', return_value=False)
    def test_delete_directory_structure__folder_does_not_exists(self, mock_dir_check):
        self.flow.delete_directory_structure()
        self.assertTrue(mock_dir_check.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
