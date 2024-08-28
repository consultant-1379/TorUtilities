#!/usr/bin/env python
from datetime import datetime, date

import unittest2
from enmutils.lib import filesystem
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.pm_flows import pm_eniq_flow2
from enmutils_int.lib.workload import pm_44
from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils


class PmEniqFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.pm_flow = pm_eniq_flow2.PmEniqFlow()
        unit_test_utils.setup()
        self.user = Mock()
        self.test_dir = "/var/tmp/test_dir"
        self.test_dir2 = "/var/tmp/test_dir/test_dir2"
        self.test_file = "/var/tmp/test_dir/testfile"
        self.pm_flow.NUM_USERS = 1
        self.pm_flow.USER_ROLES = ['some_role']
        self.pm_flow.mount_point_list = ["/var/tmp/test1", "/var/tmp/test2"]
        self.pm_flow.file_system_list = ["/vx/ENM335-pm1", "/vx/ENM335-pm2"]
        self.pm_flow.PMLINKS_DIR_NAME = "/pmlinks1"
        self.pm_flow.fs_mounts = dict(zip(self.pm_flow.mount_point_list, self.pm_flow.file_system_list))
        self.pm_flow.fls_15_min_time_stamp = "some_time_stamp"
        self.pm_flow.NODE_TYPES = ['RadioNode', 'SGSN-MME']
        self.pm_flow.DATA_TYPES = ['PM_STATISTICAL', 'PM_STATISTICAL_1MIN']

    def tearDown(self):
        unit_test_utils.tear_down()
        if filesystem.does_dir_exist(self.test_dir):
            filesystem.remove_dir(self.test_dir)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.umount_shared_file_system")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.set_pib_parameters")
    def test_set_teardown_objects__appends_callables_to_list(
            self, mock_set_pib_parameters, mock_partial, mock_picklable_boundmethod,
            mock_umount_shared_file_system, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.teardown_list = []
        pm_flow.set_teardown_objects()
        mock_partial.assert_called_with(mock_set_pib_parameters, "false")
        mock_picklable_boundmethod.assert_called_with(mock_umount_shared_file_system)
        self.assertEqual(pm_flow.teardown_list, [mock_partial.return_value, mock_picklable_boundmethod.return_value])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.create_dir")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.does_dir_exist", side_effect=[False, True])
    def test_create_mount_points__is_successful_if_profile_pm44_is_used(self, *_):
        mountpoints = ["ee_mountpoint1", "ee_mountpoint2"]
        self.pm_flow.ES_MOUNT_POINT_LIST = mountpoints
        self.pm_flow.NAME = "PM_44"
        self.pm_flow.create_mount_points()
        self.assertEqual(mountpoints, self.pm_flow.mount_point_list)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.periodic_fls_pm_query")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.perform_prechecks_and_execute_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.set_teardown_objects")
    def test_execute_flow__is_successful(self, mock_set_teardown_objects, mock_perform_and_execute_tasks,
                                         mock_create_profile_users, mock_sleep_until_time, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.USER_ROLES = ["SOME_ROLE"]
        pm_flow.NUM_USERS = 1
        pm_flow.NODE_TYPES = ['RadioNode', 'SGSN-MME']
        pm_flow.DATA_TYPES = ['PM_STATISTICAL', 'PM_STATISTICAL_1MIN']
        mock_create_profile_users.return_value = [self.user]
        pm_flow.execute_flow()
        self.assertTrue(mock_set_teardown_objects.called)
        self.assertTrue(mock_perform_and_execute_tasks.called)
        self.assertTrue(mock_sleep_until_time.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.perform_pm44_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.perform_cmexport19_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.integrate_eniq")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    def test_perform_prechecks_and_execute_tasks__successful(self, mock_exception, mock_integrate_eniq,
                                                             mock_cmexport19_tasks, mock_pm44_tasks):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_prechecks_and_execute_tasks()
        self.assertTrue(mock_integrate_eniq.called)
        self.assertTrue(mock_cmexport19_tasks.called)
        self.assertTrue(mock_pm44_tasks.called)
        self.assertFalse(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.perform_pm44_tasks", side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.perform_cmexport19_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.integrate_eniq")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    def test_perform_prechecks_and_execute_tasks__raises_exception(self, mock_exception, mock_integrate_eniq,
                                                                   mock_cmexport19_tasks, mock_pm44_tasks):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_prechecks_and_execute_tasks()
        self.assertTrue(mock_integrate_eniq.called)
        self.assertTrue(mock_cmexport19_tasks.called)
        self.assertTrue(mock_pm44_tasks.called)
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.check_eniq_exports_enabled")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.confirm_export_configured")
    def test_perform_cmexport19_tasks__successful(self, mock_confirm_export_configured, mock_eniq_exports_enabled,
                                                  mock_add_error, _):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_cmexport19_tasks()
        self.assertTrue(mock_confirm_export_configured.called)
        self.assertTrue(mock_eniq_exports_enabled.called)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.check_eniq_exports_enabled")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.confirm_export_configured",
           side_effect=Exception)
    def test_perform_cmexport19_tasks__raises_error(self, mock_confirm_export_configured, mock_eniq_exports_enabled,
                                                    mock_add_error, _):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_cmexport19_tasks()
        self.assertTrue(mock_confirm_export_configured.called)
        self.assertFalse(mock_eniq_exports_enabled.called)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.set_file_system_paths")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.create_mount_points")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.mount_file_systems")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow."
           "check_and_toggle_pmic_symbolic_link_creation")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug")
    def test_perform_pm44_tasks__successful(self, mock_log_debug, mock_toggle_symbolic_link_creation,
                                            mock_mount_file_systems, mock_add_exception, mock_update_pib_parameter, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_pm44_tasks()
        mock_toggle_symbolic_link_creation.assert_called_with("disable")
        self.assertTrue(mock_mount_file_systems.called)
        self.assertFalse(mock_add_exception.called)
        mock_update_pib_parameter.assert_called_with("pmserv", "useStatsSymlinks", "false")
        self.assertTrue(mock_log_debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.set_file_system_paths")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.create_mount_points")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.mount_file_systems")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow."
           "check_and_toggle_pmic_symbolic_link_creation", side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug")
    def test_perform_pm44_tasks__raises_exception(self, mock_log_debug, mock_toggle_symbolic_link_creation,
                                                  mock_mount_file_systems, mock_add_exception,
                                                  mock_update_pib_parameter, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.perform_pm44_tasks()
        mock_toggle_symbolic_link_creation.assert_called_with("disable")
        self.assertFalse(mock_mount_file_systems.called)
        self.assertTrue(mock_add_exception.called)
        mock_update_pib_parameter.assert_called_with("pmserv", "useStatsSymlinks", "false")
        self.assertTrue(mock_log_debug.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.run_litp_command", return_value="blah")
    def test_set_file_system_paths__is_successful(self, _):
        self.pm_flow.NFS_SHARES = ["share1", "share2"]
        self.pm_flow.file_system_list = []
        self.pm_flow.set_file_system_paths()
        self.assertEqual(self.pm_flow.file_system_list, ["blah", "blah"])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.run_litp_command", return_value="")
    def test_set_file_systems__raises_environ_error_if_litp_share_not_set(self, _):
        self.pm_flow.NFS_SHARES = ["share1", "share2"]
        self.pm_flow.file_system_list = []
        self.assertRaises(EnvironError, self.pm_flow.set_file_system_paths)
        self.assertEqual(self.pm_flow.file_system_list, [])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_local_cmd")
    def test_mount_file_systems__is_successful_if_mounts_dont_exist(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.side_effect = [Mock(stdout='mount does not exists', rc=1),
                                          Mock(stdout='mounted successfully', rc=0)] * 3
        self.pm_flow.mount_file_systems()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_local_cmd")
    def test_mount_file_systems__is_successful_if_mounts_exist(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(stdout='mount ok blah', rc=0)

        self.pm_flow.mount_file_systems()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_local_cmd")
    def test_mount_file_systems__raises_runtimeerror_if_mount_command_fails(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.side_effect = [Mock(stdout='mount does not exists', rc=1), RuntimeError]
        self.assertRaises(EnvironError, self.pm_flow.mount_file_systems)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_run_litp_command__is_successful(self, mock_run_cmd_on_ms):
        mock_run_cmd_on_ms.return_value = Mock(stdout="blah\n")
        self.assertEqual("blah", self.pm_flow.run_litp_command("some_commmand"))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_run_litp_command__sleeps_if_litp_unavailable(self, mock_run_cmd_on_ms, mock_sleep):
        server_unavailable_entries = [Mock(stdout="ServerUnavailableError blah1\n") for _ in xrange(13)]
        mock_run_cmd_on_ms.side_effect = server_unavailable_entries + [Mock(stdout="blah2\n")]
        self.assertEqual("blah2", self.pm_flow.run_litp_command("some_commmand"))
        self.assertEqual(mock_sleep.call_count, 13)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_local_cmd')
    def test_umount_shared_file_systems__is_successful(self, mock_run_local_cmd, *_):
        mock_run_local_cmd.side_effect = [Mock(stdout='mount success', rc=0)] * 2
        self.pm_flow.umount_shared_file_system()
        self.assertEqual(mock_run_local_cmd.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_local_cmd')
    def test_umount_shared_file_system__is_successful_if_problems_occurred_unmounting(
            self, mock_run_local_cmd, mock_debug, *_):
        mock_run_local_cmd.side_effect = [Mock(stdout='mount point is busy', rc=1), RuntimeError, RuntimeError]
        self.pm_flow.umount_shared_file_system()
        self.assertEqual(mock_run_local_cmd.call_count, 2)
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.wait_for_litp_plan_to_complete')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.check_if_eniq_integrated',
           side_effect=[False, True])
    def test_integrate_eniq__successful_if_eniq_not_already_integrated(
            self, mock_check_if_eniq_integrated, mock_wait_for_litp_plan_to_complete, mock_execute_setup_commands):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.integrate_eniq()
        self.assertEqual(mock_check_if_eniq_integrated.call_count, 2)
        self.assertTrue(mock_wait_for_litp_plan_to_complete.called)
        self.assertTrue(mock_execute_setup_commands.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.wait_for_litp_plan_to_complete')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.check_if_eniq_integrated',
           return_value=True)
    def test_integrate_eniq__successful_if_eniq_already_integrated(
            self, mock_check_if_eniq_integrated, mock_wait_for_litp_plan_to_complete, mock_execute_setup_commands):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.integrate_eniq()
        self.assertEqual(mock_check_if_eniq_integrated.call_count, 1)
        self.assertFalse(mock_wait_for_litp_plan_to_complete.called)
        self.assertFalse(mock_execute_setup_commands.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.wait_for_litp_plan_to_complete')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.check_if_eniq_integrated',
           return_value=False)
    def test_integrate_eniq__unsuccessful_if_eniq_cannot_be_integrated(
            self, mock_check_if_eniq_integrated, mock_wait_for_litp_plan_to_complete, mock_execute_setup_commands):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        self.assertRaises(EnvironError, pm_flow.integrate_eniq)
        self.assertEqual(mock_check_if_eniq_integrated.call_count, 2)
        self.assertTrue(mock_wait_for_litp_plan_to_complete.called)
        self.assertTrue(mock_execute_setup_commands.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname",
           return_value=("some_ip1", "some_host"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_check_if_eniq_integrated__successful(self, mock_run_cmd_on_ms, mock_command, _):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        output = ("Checking pmserv and impexpserv are available.\n"
                  "Listing down the integrated Eniq system, Please wait....\n"
                  " ENM has been integrated to eniq_oss_1 with the following IP(s)... ['some_ip1']\n"
                  " ENM has been integrated to events_oss_1 with the following IP(s)... ['some_ip1']\n")
        mock_run_cmd_on_ms.return_value = Mock(stdout=output, rc=0)
        self.assertTrue(pm_flow.check_if_eniq_integrated())
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value, get_pty=True)
        cmd = "/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py list_eniqs"
        mock_command.assert_called_with(cmd, timeout=300)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname",
           return_value=("some_ip1", "some_host"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.re.search", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_check_if_eniq_integrated__raises_enverror_for_multiple_ips(self, mock_run_cmd_on_ms, mock_command, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        output = ("Checking pmserv and impexpserv are available.\n"
                  "Listing down the integrated Eniq system, Please wait....\n"
                  " ENM has been integrated to eniq_oss_1 with the following IP(s)... ['some_ip1', 'some_ip2]\n"
                  " ENM has been integrated to events_oss_1 with the following IP(s)... ['some_ip1']\n")
        mock_run_cmd_on_ms.return_value = Mock(stdout=output, rc=0)
        self.assertRaises(EnvironError, pm_flow.check_if_eniq_integrated)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value, get_pty=True)
        cmd = "/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py list_eniqs"
        mock_command.assert_called_with(cmd, timeout=300)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname",
           return_value=("some_ip1", "some_host"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.re.search", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_check_if_eniq_integrated__raises_enverror_if_no_stdout(self, mock_run_cmd_on_ms, mock_command, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        mock_run_cmd_on_ms.return_value.stdout = None
        self.assertRaises(EnvironError, pm_flow.check_if_eniq_integrated)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value, get_pty=True)
        cmd = "/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py list_eniqs"
        mock_command.assert_called_with(cmd, timeout=300)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname",
           return_value=("some_ip1", "some_host"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_ms")
    def test_check_if_eniq_integrated__no_ip_match(self, mock_run_cmd_on_ms, mock_command, _):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        output = ("Checking pmserv and impexpserv are available.\n"
                  "Listing down the integrated Eniq system, Please wait....\n"
                  " ENM has been integrated to eniq_oss_1 with the following IP(s)... ['some_ip11']\n"
                  " ENM has been integrated to events_oss_1 with the following IP(s)... ['some_ip11']\n")
        mock_run_cmd_on_ms.return_value = Mock(stdout=output, rc=0)
        pm_flow.check_if_eniq_integrated()
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value, get_pty=True)
        cmd = "/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py list_eniqs"
        mock_command.assert_called_with(cmd, timeout=300)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.check_for_active_litp_plan",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.sleep")
    def test_wait_for_litp_plan_to_complete(self, mock_sleep, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.wait_for_litp_plan_to_complete()
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.confirm_eniq_topology_export_enabled',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.set_pib_parameters_topology_export')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.toggle_pib_inventory_export')
    def test_confirm_export_configured__successful(
            self, mock_toggle_pib_inventory_export, mock_set_pib_parameters_topology_export, mock_add_error, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.confirm_export_configured()
        self.assertTrue(mock_toggle_pib_inventory_export.called)
        self.assertTrue(mock_set_pib_parameters_topology_export.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.confirm_eniq_topology_export_enabled',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.set_pib_parameters_topology_export')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.toggle_pib_inventory_export', side_effect=Exception)
    def test_confirm_export_configured__unsuccessful(
            self, mock_toggle_pib_inventory_export, mock_set_pib_parameters_topology_export, mock_add_error, *_):
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.confirm_export_configured()
        self.assertTrue(mock_toggle_pib_inventory_export.called)
        self.assertFalse(mock_set_pib_parameters_topology_export.called)
        self.assertTrue(mock_add_error.called)

    def test_manage_password__if_no_prompt(self):
        child = Mock()
        child.expect_exact.return_value = None
        self.pm_flow.manage_password_prompt(child, "user", "pass")
        self.assertEqual(2, child.send.call_count)

    def test_manage_password_prompt__success(self):
        child = Mock()
        child.expect_exact.return_value = "password: "
        self.pm_flow.manage_password_prompt(child, "user", "pass")
        self.assertEqual(1, child.send.call_count)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.filesystem.touch_file')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.filesystem.create_dir')
    def test_create_status_file__success(self, mock_create_dir, mock_touch_file, *_):
        self.pm_flow.create_status_file()
        self.assertEqual(1, mock_create_dir.call_count)
        self.assertEqual(1, mock_touch_file.call_count)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.create_status_file')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_ms_host', return_value="lms")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname',
           return_value=("ip", "host"))
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_workload_vm_credentials',
           return_value=("Test", "Test"))
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.manage_password_prompt')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.pexpect.spawn')
    def test_execute_setup_commands__execution_successful(
            self, mock_spawn, mock_password_prompt, mock_add_error_as_exception, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect_exact.return_value = 0
        child.expect.return_value = 0
        mock_password_prompt.return_value.expect.return_value = 0
        self.pm_flow.execute_setup_commands()
        self.assertEqual(1, child.send.call_count)
        self.assertEqual(1, mock_password_prompt.call_count)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.create_status_file')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_local_ip_and_hostname',
           return_value=("ip", "Host"))
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_ms_host', return_value="lms")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_workload_vm_credentials',
           return_value=("Test", "Test"))
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.pexpect.spawn')
    def test_execute_setup_commands__if_no_prompt_exists(self, mock_spawn, mock_add_error_as_exception, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect_exact.return_value = None
        child.expect.side_effect = [0, 1, None]
        self.pm_flow.execute_setup_commands()
        self.assertEqual(1, child.send.call_count)
        self.assertTrue(mock_add_error_as_exception.called)

    # check_and_toggle_pmic_symbolic_link_creation test cases

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__cannot_get_pib_value_on_enm_service(self, mock_add_error,
                                                                                               mock_get_pib_value,
                                                                                               mock_update_pib_value,
                                                                                               mock_debug_log):
        message = 'Unable to get PIB parameter pmicSymbolicLinkCreationEnabled. See profile log for details'
        mock_get_pib_value.side_effect = Exception(EnvironError(message))
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("enable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertFalse(mock_update_pib_value.called)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__if_get_pib_value_is_true(self, mock_add_error,
                                                                                    mock_get_pib_value,
                                                                                    mock_update_pib_value,
                                                                                    mock_debug_log):
        mock_get_pib_value.return_value = "true"
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("enable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertFalse(mock_add_error.called)
        self.assertFalse(mock_update_pib_value.called)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__if_get_pib_value_is_false(self, mock_add_error,
                                                                                     mock_get_pib_value,
                                                                                     mock_update_pib_value,
                                                                                     mock_debug_log):
        mock_get_pib_value.return_value = "false"
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("enable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_update_pib_value.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__cannot_update_pib_parameter_on_enm(self, mock_add_error,
                                                                                              mock_get_pib_value,
                                                                                              mock_update_pib_value,
                                                                                              mock_debug_log):
        message = 'Unable to update PIB parameter pmicSymbolicLinkCreationEnabled - see profile log for details'
        mock_update_pib_value.side_effect = Exception(EnvironError(message))
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("enable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_update_pib_value.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__update_pib_parameter_on_enm_successful(self, mock_add_error,
                                                                                                  mock_get_pib_value,
                                                                                                  mock_update_pib_value,
                                                                                                  mock_debug_log):
        mock_get_pib_value.return_value = "false"
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("enable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertFalse(mock_add_error.called)
        self.assertEqual(mock_update_pib_value.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__if_get_pib_value_is_false_action_is_disable(
            self, mock_add_error, mock_get_pib_value, mock_update_pib_value, mock_debug_log):
        mock_get_pib_value.return_value = "false"
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("disable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_update_pib_value.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__if_get_pib_value_is_true_action_is_disable(
            self, mock_add_error, mock_get_pib_value, mock_update_pib_value, mock_debug_log):
        mock_get_pib_value.return_value = "true"
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("disable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        mock_update_pib_value.assert_called_with("pmserv", "pmicSymbolicLinkCreationEnabled", "false")
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    def test_check_and_toggle_pmic_symbolic_link_creation__cannot_update_pib_parameter_on_enm_action_is_disable(
            self, mock_add_error, mock_get_pib_value, mock_update_pib_value, mock_debug_log):
        message = 'Unable to update PIB parameter pmicSymbolicLinkCreationEnabled - see profile log for details'
        mock_get_pib_value.return_value = "true"
        mock_update_pib_value.side_effect = Exception(EnvironError(message))
        self.pm_flow.check_and_toggle_pmic_symbolic_link_creation("disable")
        self.assertEqual(mock_get_pib_value.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_update_pib_value.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_emp_or_ms')
    def test_confirm_eniq_topology_export_enabled__returns_false_if_failure(self, mock_run_cmd_on_emp_or_ms):
        response = Mock()
        response.rc = 177
        response.stdout = " "
        mock_run_cmd_on_emp_or_ms.return_value = response
        self.assertFalse(pm_eniq_flow2.confirm_eniq_topology_export_enabled())

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_emp_or_ms')
    def test_confirm_eniq_topology_export_enabled__is_successful(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 0
        response.stdout = "ENIQ Daily Topology export is currently enabled"
        mock_run_cmd_on_ms.return_value = response
        self.assertTrue(pm_eniq_flow2.confirm_eniq_topology_export_enabled())
        self.assertTrue(mock_run_cmd_on_ms.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_emp_or_ms')
    def test_confirm_eniq_historical_export_enabled__returns_false_if_failure(self, mock_run_cmd_on_emp_or_ms):
        response = Mock()
        response.rc = 177
        response.stdout = " "
        mock_run_cmd_on_emp_or_ms.return_value = response
        self.assertFalse(pm_eniq_flow2.confirm_eniq_topology_export_enabled(historical=True))

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.shell.run_cmd_on_emp_or_ms')
    def test_confirm_eniq_historical_export_enabled__is_successful(self, mock_run_cmd_on_ms):
        response = Mock()
        response.rc = 0
        response.stdout = "ENIQ Historical CM Export is currently enabled"
        mock_run_cmd_on_ms.return_value = response
        self.assertTrue(pm_eniq_flow2.confirm_eniq_topology_export_enabled(historical=True))
        self.assertTrue(mock_run_cmd_on_ms.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.toggle_pib_inventorymoexport')
    def test_toggle_pib_inventory_export__is_enabled(self, mock_historical):
        pm_eniq_flow2.toggle_pib_inventory_export()
        mock_historical.assert_called_with('true')

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    def test_set_pib_parameters_topology_export__successful(self, mock_update_pib_parameter_on_enm):
        pm_eniq_flow2.set_pib_parameters_topology_export("true")
        self.assertEqual([call(enm_service_name='impexpserv', pib_parameter_name="topologyExportCreationEnabledStats",
                               pib_parameter_value="true", service_identifier="eniq-topology-service-impl"),
                          call(enm_service_name='impexpserv', pib_parameter_name="topologyExportCreationEnabled",
                               pib_parameter_value="true", service_identifier="eniq-topology-service-impl")],
                         mock_update_pib_parameter_on_enm.mock_calls)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.toggle_pib_inventorymoexport')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.set_pib_parameters_topology_export')
    def test_set_pib_parameters__successful(
            self, mock_set_pib_parameters_topology_export, mock_toggle_pib_inventorymoexport,
            mock_update_pib_parameter_on_enm):
        pm_eniq_flow2.set_pib_parameters("false")
        mock_set_pib_parameters_topology_export.assert_called_with("false")
        mock_toggle_pib_inventorymoexport.assert_called_with("false")
        calls = [call("pmserv", "useStatsSymlinks", "false"),
                 call("pmserv", "pmicSymbolicLinkCreationEnabled", "false")]
        self.assertEqual(calls, mock_update_pib_parameter_on_enm.mock_calls)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    def test_toggle_pib_inventorymoexport__is_successful(
            self, mock_update_pib_parameter, mock_logger_debug):
        pm_eniq_flow2.toggle_pib_inventorymoexport('true')
        self.assertTrue(mock_update_pib_parameter.called)
        mock_logger_debug.assert_called_with("Inventory MO Export is enabled. ")

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.update_pib_parameter_on_enm')
    def test_toggle_pib_inventorymoexport__is_successful_when_toggled_to_false(
            self, mock_update_pib_parameter, mock_logger_debug):
        pm_eniq_flow2.toggle_pib_inventorymoexport('false')
        self.assertTrue(mock_update_pib_parameter.called)
        mock_logger_debug.assert_called_with("Inventory MO Export is disabled. ")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.__init__", return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.date')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.datetime')
    def test_check_eniq_exports_enabled__with_export_confirmation(self, mock_datetime, mock_date,
                                                                  mock_confirm_export_configured, _):
        mock_datetime.now.return_value = datetime(2021, 1, 5, 2, 50, 0)
        mock_date.today.return_value = date(2021, 1, 5)
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.start_time = datetime(2021, 1, 4, 10, 10, 30)
        pm_flow.SCHEDULE_SLEEP = 60 * 15
        pm_flow.CHECK_EXPORT_TIME = "03:00:00"
        pm_flow.check_eniq_exports_enabled()
        self.assertTrue(mock_confirm_export_configured.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.__init__", return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.date')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.datetime')
    def test_check_eniq_exports_enabled__without_export_confirmation(self, mock_datetime, mock_date,
                                                                     mock_confirm_export_configured, _):
        mock_datetime.now.return_value = datetime(2021, 1, 5, 12, 50, 00)
        mock_date.today.return_value = date(2021, 1, 5)
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.start_time = datetime(2021, 1, 4, 10, 10, 30)
        pm_flow.SCHEDULE_SLEEP = 60 * 15
        pm_flow.CHECK_EXPORT_TIME = "03:00:00"
        pm_flow.check_eniq_exports_enabled()
        self.assertFalse(mock_confirm_export_configured.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.execute_flow')
    def test_run__in_pm_profiles_that_call_execute_flow_is_successful(self, mock_execute_flow):
        profile = pm_44.PM_44()
        profile.run()
        self.assertTrue(mock_execute_flow.called)

    # read_files test cases
    @patch("__builtin__.open")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    def test_read_files__is_successful_if_no_errors_occurred_during_read(self, mock_debug, mock_open):
        files = ["/ericsson/A20180917.1730-1745.xml"]
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        mock_open.return_value.read.side_effect = True
        running_totals = {'read_success': 1, 'read_failure': 0}
        pm_flow.read_files(files)
        mock_debug.assert_called_with("Total files read summary:{0}".format(running_totals))

    @patch("__builtin__.open")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log.logger.debug')
    def test_read_files__is_successful_if_errors_occurred_during_read(self, mock_debug, mock_open):
        files = ["/ericsson/A20180917.1730-1745.xml"]
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        mock_open.return_value = Mock()
        mock_open.return_value.read.side_effect = Exception
        running_totals = {'read_success': 0, 'read_failure': 1}
        pm_flow.read_files(files)
        mock_debug.assert_called_with("Total files read summary:{0}".format(running_totals))

    # sleep_for_wait_time test case
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.datetime")
    def test_sleep_for_wait_time__successful(self, mock_datetime, mock_sleep, _):
        mock_datetime.now.return_value.strftime.return_value = 59
        self.pm_flow.sleep_for_wait_time(3, 2)
        mock_sleep.assert_called_with(1)

    # periodic_fls_pm_query test cases
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.sleep", return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.pm_nbi')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.read_files')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.datetime')
    def test_periodic_fls_pm_query__successful(self, mock_datetime, mock_read_files, mock_log, mock_pm_nbi, *_):
        fls = mock_pm_nbi.Fls
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.INITIAL_FILE_CREATION_TIME = 3
        pm_flow.node_data_type_file_id_dict = {'RadioNode': {'PM_STATISTICAL': [0, None], 'PM_STATISTICAL_1MIN': [0, None]},
                                               'SGSN-MME': {'PM_STATISTICAL': [0, None], 'PM_STATISTICAL_1MIN': [0, None]}}
        mock_datetime.now.return_value.strftime.side_effect = [15, 15]
        fls.get_pmic_rop_files_location.side_effect = [(['file1', 'file2'], 2, "T1"), ([], 0, None), (['file1'], 1, "T2"), (['file1', 'file2'], 2, "T3")]
        pm_flow.periodic_fls_pm_query(fls)
        self.assertEqual(fls.get_pmic_rop_files_location.call_count, 4)
        self.assertTrue(mock_read_files.called)
        self.assertEqual(mock_log.logger.debug.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.sleep", return_value=0)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.pm_nbi')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.log")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.PmEniqFlow.read_files')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2.datetime')
    def test_periodic_fls_pm_query__add_error_exception(self, mock_datetime, mock_read_files, mock_add_error,
                                                        mock_log, mock_pm_nbi, *_):
        fls = mock_pm_nbi.Fls
        pm_flow = pm_eniq_flow2.PmEniqFlow()
        pm_flow.INITIAL_FILE_CREATION_TIME = 3
        pm_flow.node_data_type_file_id_dict = {'RadioNode': {'PM_STATISTICAL': [0, None], 'PM_STATISTICAL_1MIN': [0, None]}}
        mock_datetime.now.return_value.strftime.side_effect = [15, 15]
        fls.get_pmic_rop_files_location.side_effect = [(['file1', 'file2', 2, "T1"]), ([], 0, None)]
        pm_flow.periodic_fls_pm_query(fls)
        self.assertEqual(fls.get_pmic_rop_files_location.call_count, 2)
        self.assertTrue(mock_read_files.called)
        self.assertEqual(mock_log.logger.debug.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
