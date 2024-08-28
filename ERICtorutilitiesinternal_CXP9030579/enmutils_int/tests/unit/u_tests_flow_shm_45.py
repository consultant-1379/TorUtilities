from enmutils.lib.enm_node import MGWNode
from enmutils.lib.exceptions import EnvironError
import unittest2
from mock import Mock, patch

from enmutils_int.lib.profile_flows.shm_flows.shm_45_flow import Shm45Flow
from enmutils_int.lib.workload.shm_45 import SHM_45
from testslib import unit_test_utils


class Shm45FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.flow = Shm45Flow()
        self.nodes = {"MGW": [MGWNode('testNode1', primary_type='MGW')]}
        self.flow.BACKUP_SIZES = {"MGW": "600M"}
        self.flow.SLEEP_TIMES = {"DSC": 200, "FRONTHAUL-6020": 20, "MGW": 30, "MTAS": 100, "SGSN-MME": 100}
        self.flow.SLEEP = self.flow.SLEEP_TIMES["MGW"]
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_flow")
    def test_shm_45_run__execute_flow_successful(self, mock_flow):
        SHM_45().run()
        self.assertTrue(mock_flow.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.set_smrs_filetransfer_service_location")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.perform_iteration_actions")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.get_nodes_list_by_attribute")
    def test_execute_flow__calls_as_expected(self, mock_get_nodes, mock_get_nodes_dict, mock_sleep, mock_perform,
                                             mock_pib_update, mock_set, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_get_nodes.called)
        self.assertTrue(mock_get_nodes_dict.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_pib_update.called)
        self.assertTrue(mock_set.called)
        self.assertTrue(mock_perform.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.set_smrs_filetransfer_service_location")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.install_zip_on_pod")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.perform_iteration_actions")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.get_nodes_list_by_attribute")
    def test_execute_flow__calls_as_expected_on_cenm(self, mock_get_nodes, mock_get_nodes_dict, mock_perform,
                                                     mock_pib_update, mock_install_zip, mock_set, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_pib_update.called)
        self.assertTrue(mock_get_nodes.called)
        self.assertTrue(mock_get_nodes_dict.called)
        self.assertTrue(mock_perform.called)
        self.assertTrue(mock_set.called)
        self.assertTrue(mock_install_zip.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.set_smrs_filetransfer_service_location")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.install_zip_on_pod")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.perform_iteration_actions",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.add_error_as_exception")
    def test_execute_flow__raises_exception_perform_iteration_actions(self, mock_exception, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.add_error_as_exception")
    def test_execute_flow__raises_exception_at_backup_pib_update(self, mock_exception, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.set_smrs_filetransfer_service_location",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.generate_basic_dictionary_from_list_of_objects")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.add_error_as_exception")
    def test_execute_flow__raises_exception_at_set_serv_location(self, mock_exception, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_enm_service_locations")
    def test_set_smrs_filetransfer_service_location__successful(self, mock_enm_service):
        self.flow.set_smrs_filetransfer_service_location()
        self.assertEqual(mock_enm_service.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_enm_service_locations")
    def test_set_smrs_filetransfer_service_location__failed(self, mock_enm_service):
        mock_enm_service.side_effect = [EnvironError, ["filetransferservice-0", "filetransferserv-1"]]
        self.flow.set_smrs_filetransfer_service_location()
        self.assertEqual(mock_enm_service.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_cmd_on_host")
    def test_perform_iteration_actions__calls_as_expected(self, mock_execute_cmd, _):
        self.flow.perform_iteration_actions(self.nodes)
        expected_call = [
            'for i in testNode1;do mkdir -p /home/smrs/smrsroot/backup/mgw/$i;chown -R jboss_user:mm-smrsusers /home/smrs/smrsroot/backup/mgw/$i;sleep 2;done',
            'for i in testNode1;do truncate -s 600M /home/smrs/smrsroot/backup/mgw/$i/${i}_12_06_21_11_50_52_691896.zip;chown -R jboss_user:mm-smrsusers /home/smrs/smrsroot/backup/mgw/$i;sleep 2;ls -larth /home/smrs/smrsroot/backup/mgw/$i;done',
            1
        ]
        self.assertTrue(mock_execute_cmd.called_with(expected_call))

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_emp", return_value="ieatemp")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_on_service_vm")
    def test_execute_cmd_on_host__works_for_cloud(self, mock_execute, mock_spawn, *_):
        mock_pexpect_child = Mock()
        mock_pexpect_child.expect.return_value = 0
        mock_spawn.return_value = mock_pexpect_child
        self.flow.execute_cmd_on_host("create_folder_cmd", "create_backup_cmd", 1)
        self.assertTrue(mock_execute.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_emp", return_value="ieatemp")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_on_service_vm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.pexpect.spawn")
    def test_execute_cmd_on_host__raises_env_error_for_cloud(self, mock_spawn, *_):
        mock_pexpect_child = Mock()
        mock_pexpect_child.expect.return_value = 1
        mock_spawn.return_value = mock_pexpect_child
        self.assertRaises(EnvironError, self.flow.execute_cmd_on_host, "create_folder_cmd", "create_backup_cmd", 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_ms_host", return_value="ieatlms")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.pexpect.spawn")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_on_service_vm")
    def test_execute_cmd_on_host__works_for_physical(self, mock_execute, mock_spawn, *_):
        mock_pexpect_child = Mock()
        mock_pexpect_child.expect.return_value = 0
        mock_spawn.return_value = mock_pexpect_child
        self.flow.execute_cmd_on_host("create_folder_cmd", "create_backup_cmd", 1)
        self.assertTrue(mock_execute.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.get_ms_host", return_value="ieatlms")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.execute_on_service_vm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.pexpect.spawn")
    def test_execute_cmd_on_host__raises_env_error_for_physical(self, mock_spawn, *_):
        mock_pexpect_child = Mock()
        mock_pexpect_child.expect.return_value = 1
        mock_spawn.return_value = mock_pexpect_child
        self.assertRaises(EnvironError, self.flow.execute_cmd_on_host, "create_folder_cmd", "create_backup_cmd", 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.shell.run_cmd_on_cloud_native_pod")
    def test_execute_cmd_on_host__works_for_cloud_native(self, mock_run_cmd, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_run_cmd.return_value = mock_response
        self.flow.execute_cmd_on_host("create_folder_cmd", "create_backup_cmd", 1)
        self.assertTrue(mock_run_cmd.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.shell.run_cmd_on_cloud_native_pod")
    def test_execute_cmd_on_host__raises_env_error_for_cloud_native_create_folder_failure(self, mock_run_cmd, *_):
        mock_response1 = Mock()
        mock_response1.rc = 1
        mock_response2 = Mock()
        mock_response2.rc = 0
        mock_run_cmd.side_effect = [mock_response1, mock_response2]
        self.assertRaises(EnvironError, self.flow.execute_cmd_on_host, "create_folder_cmd", "create_backup_cmd", 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.is_emp", return_value=False)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.shell.run_cmd_on_cloud_native_pod")
    def test_execute_cmd_on_host__raises_env_error_for_cloud_native_create_backup_failure(self, mock_run_cmd, *_):
        mock_response1 = Mock()
        mock_response1.rc = 0
        mock_response2 = Mock()
        mock_response2.rc = 1
        mock_run_cmd.side_effect = [mock_response1, mock_response2]
        self.assertRaises(EnvironError, self.flow.execute_cmd_on_host, "create_folder_cmd", "create_backup_cmd", 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log.logger.debug")
    def test_execute_on_service_vm__has_expected_number_of_calls(self, mock_log, _):
        mock_child = Mock()
        mock_child.expect.side_effect = [0] * 4
        self.flow.execute_on_service_vm(mock_child, "create_folder_cmd", "create_backup_cmd", 1)
        self.assertEqual(mock_log.call_count, 7)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log.logger.debug")
    def test_execute_on_service_vm__raises_env_error_when_connection_fails(self, mock_log, _):
        mock_child = Mock()
        mock_child.expect.return_value = 1
        self.assertRaises(EnvironError, self.flow.execute_on_service_vm, mock_child, "create_folder_cmd", "create_backup_cmd", 1)
        self.assertEqual(mock_log.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log.logger.debug")
    def test_execute_on_service_vm__raises_env_error_when_switch_to_root_fails(self, mock_log, _):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 1]
        self.assertRaises(EnvironError, self.flow.execute_on_service_vm, mock_child, "create_folder_cmd", "create_backup_cmd", 1)
        self.assertEqual(mock_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log.logger.debug")
    def test_execute_on_service_vm__raises_env_error_when_folder_creation_fails(self, mock_log, _):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 0, 1]
        self.assertRaises(EnvironError, self.flow.execute_on_service_vm, mock_child, "create_folder_cmd", "create_backup_cmd", 1)
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.log.logger.debug")
    def test_execute_on_service_vm__raises_env_error_when_backup_creation_fails(self, mock_log, _):
        mock_child = Mock()
        mock_child.expect.side_effect = [0, 0, 0, 1]
        self.assertRaises(EnvironError, self.flow.execute_on_service_vm, mock_child, "create_folder_cmd", "create_backup_cmd", 1)
        self.assertEqual(mock_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.shell.run_cmd_on_cloud_native_pod")
    def test_install_zip_on_pod__successful(self, mock_run_cmd):
        response = Mock()
        response.rc = 0
        mock_run_cmd.return_value = response
        self.flow.install_zip_on_pod()
        self.assertTrue(mock_run_cmd.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.Shm45Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_45_flow.shell.run_cmd_on_cloud_native_pod")
    def test_install_zip_on_pod__fails(self, mock_run_cmd, mock_exception):
        response = Mock()
        response.rc = 1
        mock_run_cmd.return_value = response
        self.flow.install_zip_on_pod()
        self.assertTrue(mock_run_cmd.called)
        self.assertTrue(mock_exception.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
