import unittest2
from mock import Mock, PropertyMock, patch

from enmutils.lib.exceptions import ShellCommandReturnedNonZero
from enmutils_int.lib.profile_flows.shm_flows.shm_06_flow import Shm06Flow
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP
from enmutils_int.lib.shm_utilities import SHMLicense
from enmutils_int.lib.workload.shm_06 import SHM_06
from testslib import unit_test_utils


class Shm06FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.users = [Mock(), Mock()]
        self.node = Mock(primary_type='ERBS', node_id='testNode')
        self.nodes = [self.node]
        self.flow = Shm06Flow()
        self.flow.NUM_USERS, self.flow.USER_ROLES = 1, ["SomeRole"]
        self.flow.SCHEDULE_SLEEP = 1
        self.flow.TOTAL_NODES = 1
        self.mock_sleep = (1, 1)
        self.exception = Exception("Shm06 Exception")
        self.user_node_tuple = (Mock(), Mock(), 1)
        self.licence = SHMLicense(user=self.users, node=self.node, fingerprint_id="ABC")
        self.backupjobcpp = BackupJobCPP(user=self.users[0], nodes=self.nodes, file_name="abcdef", platform="CPP",
                                         repeat_count="0")
        self.flow.SCHEDULED_TIMES_STRINGS = ["04:00:00"]
        self.flow.SHM_JOB_SCHEDULED_TIME_STRINGS = ["05:00:00"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.execute_flow")
    def test_shm_profile_shm_06_execute_flow__successful(self, mock_flow):
        SHM_06().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.keep_running', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_synced_nodes', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_nodes_list_by_attribute', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.install_license_script_dependencies')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.load_mgr.wait_for_setup_profile')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmFlow.check_and_update_pib_values_for_backups")
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_profile_users')
    def test_execute_flow(self, mock_create_users, mock_ce_thread, mock_pib_update, *_):
        mock_create_users.return_value = [self.users]
        self.flow.execute_flow()
        self.assertEqual(3, len(mock_ce_thread.call_args_list))
        self.assertTrue(mock_pib_update.called)
        self.assertIn("tasksetlicense", str(mock_ce_thread.call_args_list[0]).split(", ")[4])
        self.assertNotIn("tasksetlicense", str(mock_ce_thread.call_args_list[1]).split(", ")[4])
        self.assertNotIn("tasksetlicense", str(mock_ce_thread.call_args_list[2]).split(", ")[4])
        self.assertIn("taskset", str(mock_ce_thread.call_args_list[1]).split(", ")[4])
        self.assertIn("taskset", str(mock_ce_thread.call_args_list[2]).split(", ")[4])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_synced_nodes', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_nodes_list_by_attribute', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.install_license_script_dependencies')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_profile_users')
    def test_execute_flow__nodes_failed_to_prepare_usable_state(self, mock_create_users, mock_start_nodes, *_):
        mock_create_users.return_value = [self.users]
        mock_start_nodes.side_effect = self.exception
        self.flow.execute_flow()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.log')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.node_pool_mgr')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_synced_nodes', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_nodes_list_by_attribute', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_started_annotated_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense')
    def test_execute_flow__adds_shell_exception_to_error_and_continue(self, mock_shm_license, mock_create_users,
                                                                      mock_add_error, *_):
        mock_create_users.return_value = [self.users]
        mock_shm_license.install_license_script_dependencies.side_effect = ShellCommandReturnedNonZero(msg="Test", response="Test")
        self.flow.execute_flow()
        self.assertTrue(isinstance(mock_add_error.call_args[0][0], ShellCommandReturnedNonZero))
        self.assertFalse(self.flow.LICENSE_PRE_CHECK)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.download_tls_certs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_synced_nodes', return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.install_license_script_dependencies')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmFlow.check_and_update_pib_values_for_backups",
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_profile_users')
    def test_execute_flow__raises_exception_at_backup_pib_update(self, mock_create_users, mock_exception, *_):
        mock_create_users.return_value = [self.users]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense')
    def test_geneate_and_assign_license__raises_exception_for_shell_exception(self, mock_shm_license, *_):
        mock_shm_license.install_license_script_dependencies.side_effect = ShellCommandReturnedNonZero(msg="Test", response="Test")
        with self.assertRaises(ShellCommandReturnedNonZero):
            self.flow.geneate_and_assign_license(Mock(), [Mock()], Mock())

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.process_user_request_errors')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense')
    def test_geneate_and_assign_license__updates_license_check_values_for_successful_execution(self, *_):
        self.flow.geneate_and_assign_license(Mock(), [Mock()], Mock())
        self.assertTrue(self.flow.LICENSE_PRE_CHECK)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.generate')
    def test_tasksetlicense(self, mock_generate, *_):
        self.flow.tasksetlicense(self.user_node_tuple, self.flow)
        self.assertTrue(mock_generate.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.generate', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmFlow.add_error_as_exception')
    def test_tasksetlicense_error(self, mock_error, mock_generate, *_):
        self.flow.tasksetlicense(self.user_node_tuple, self.flow)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_import_software_package')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_license_inventory_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_import_license_keys')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.import_keys')
    def test_taskset_license_actions_success(self, mock_import_license, *_):
        license_key = Mock()
        license_key.path_to_license_key = '/root/'
        license_key.import_keys = mock_import_license
        self.flow.taskset_license_actions(license_key, self.users[0], self.flow)
        self.assertTrue(mock_import_license.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_license_inventory_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_import_license_keys')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.import_keys', side_effect=Exception)
    def test_taskset_license_actions_exception(self, mock_import_license, *_):
        license_key = Mock()
        license_key.path_to_license_key = '/root/'
        license_key.import_keys = mock_import_license
        self.flow.taskset_license_actions(license_key, self.users[0], self.flow)
        self.assertTrue(mock_import_license.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_administration_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_import_license_keys')
    def test_taskset_license_actions_skip_import(self, *_):
        license_key = Mock()
        license_key.path_to_license_key = None
        self.flow.taskset_license_actions(license_key, self.users[0], self.flow)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.delete')
    def test_taskset_license_delete(self, mock_license_delete):
        license_key = Mock()
        license_key.fingerprint_id = 'ABC'
        license_key.get_imported_keys.return_value = ['ABC', 'DEF', 'GEH']
        license_key.delete = mock_license_delete
        self.flow.taskset_license_delete(license_key, self.users[0], self.flow)
        self.assertTrue(mock_license_delete.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.SHMLicense.delete', side_effect=Exception)
    def test_taskset_license_delete_exception(self, mock_license_delete, mock_error):
        license_key = Mock()
        license_key.fingerprint_id = 'ABC'
        license_key.get_imported_keys.return_value = ['ABC', 'DEF', 'GEH']
        license_key.delete = mock_license_delete
        self.flow.taskset_license_delete(license_key, self.users[0], self.flow)
        self.assertTrue(mock_license_delete.called)
        self.assertTrue(mock_error.called)

    def test_taskset_license_skip_delete(self):
        license_key = Mock()
        license_key.fingerprint_id = 'PQR'
        license_key.get_imported_keys.return_value = ['ABC', 'DEF', 'GEH']
        self.flow.taskset_license_delete(license_key, self.users[0], self.flow)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup')
    def test_taskset_create_and_delete_erbs_backup(self, backup_mock, mock_cleanup_create, mock_cleanup, *_):
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.side_effect = backup_mock
        mock_cleanup.create.return_value = Mock()
        self.flow.taskset_create_and_delete_backup(self.users[0], self.node, "abcdef", self.flow)
        self.assertTrue(backup_mock.called)
        self.assertTrue(mock_cleanup_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup')
    def test_taskset_create_and_delete_radionode_backup(self, backup_mock, mock_cleanup_create, mock_cleanup, *_):
        node = Mock()
        node.primary_type = "RadioNode"
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.side_effect = backup_mock
        mock_cleanup.create.return_value = Mock()
        self.flow.taskset_create_and_delete_backup(self.users[0], node, "abcdef", self.flow)
        self.assertTrue(backup_mock.called)
        self.assertTrue(mock_cleanup_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.DeleteBackupOnNodeJobBSC')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup')
    def test_taskset_create_and_delete_bsc_node_backup(self, backup_mock, mock_cleanup_create, *_):
        node = Mock()
        node.primary_type = "BSC"
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.side_effect = backup_mock
        mock_cleanup_create.create.return_value = Mock()
        self.flow.taskset_create_and_delete_backup(self.users[0], node, "abcdef", self.flow)
        self.assertTrue(backup_mock.called)
        self.assertTrue(mock_cleanup_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup')
    def test_taskset_create_and_delete_unknown_backup(self, backup_mock, mock_cleanup_create, mock_cleanup, *_):
        node = Mock()
        node.primary_type = "Unknown"
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.side_effect = backup_mock
        mock_cleanup.create.return_value = None
        self.flow.taskset_create_and_delete_backup(self.users[0], node, "abcdef", self.flow)
        self.assertTrue(backup_mock.called)
        self.assertFalse(mock_cleanup_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup',
           side_effect=Exception, return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_taskset_create_and_delete_backup_exception1(self, mock_error, backup_mock, *_):
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.side_effect = backup_mock
        self.flow.taskset_create_and_delete_backup(self.users[0], Mock(), "abcdef", self.flow)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.download_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_software_help')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.backup_setup')
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utility_jobs.ShmBackUpCleanUpJob.create', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmFlow.add_error_as_exception')
    def test_taskset_create_and_delete_backup_exception2(self, mock_error, *_):
        upgrade_backup_util_mock = Mock()
        upgrade_backup_util_mock.backup_setup.return_value = self.backupjobcpp
        self.backupjobcpp.exists = Mock()
        self.flow.taskset_create_and_delete_backup(self.users[0], self.node, "abcdef", self.flow)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_actions')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_create_and_delete_backup')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_delete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmManagement.supervise')
    def test_taskset_success(self, mock_supervise, mock_license_delete, mock_create_and_delete_upgrade,
                             mock_create_and_delete_backup, *_):
        mock_user = Mock()
        mock_user.username = 'u1_u1_u1_u1'
        mock_tuple = (mock_user, Mock(), self.licence)
        self.flow.taskset(mock_tuple, self.flow)
        self.assertTrue(mock_supervise.called)
        self.assertTrue(mock_license_delete.called)
        self.assertTrue(mock_create_and_delete_upgrade.called)
        self.assertTrue(mock_create_and_delete_backup.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_create_and_delete_backup')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_delete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_actions')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    def test_taskset_success_licence_and_home_called(self, mock_home, mock_license_actions, *_):
        mock_user = Mock()
        mock_user.username = 'u1_u1_u1_u1'
        mock_tuple = (mock_user, Mock(), self.licence)
        self.flow.taskset(mock_tuple, self.flow)
        self.assertTrue(mock_home.called)
        self.assertTrue(mock_license_actions.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_actions')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.Shm06Flow.taskset_license_delete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.shm_home')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_details')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.view_job_logs')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_06_flow.ShmManagement.supervise')
    def test_taskset_success_without_nodes(self, mock_supervise, *_):
        mock_user = Mock()
        mock_user.username = 'u1_u1_u1_u1'
        mock_tuple = (mock_user, Mock(), self.licence)
        self.flow.taskset(mock_tuple, self.flow)
        self.assertTrue(mock_supervise.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
