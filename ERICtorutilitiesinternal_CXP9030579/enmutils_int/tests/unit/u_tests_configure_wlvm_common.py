#!/usr/bin/env python
import unittest2

import enmutils_int.lib.configure_wlvm_common as common
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class ConfigureWLVMCommonUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, Mock()))
    def test_update_bashrc_file_with_env_variable__successful(self, mock_getstatusoutput, mock_does_file_exist):
        self.assertTrue(common.update_bashrc_file_with_env_variable("ENM_URL", "some_ip"))
        mock_does_file_exist.assert_called_with("/root/.bashrc")
        command = "/bin/sed -i '/export.*ENM_URL=/d' /root/.bashrc"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        command = "echo 'export ENM_URL=some_ip' >> /root/.bashrc"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, Mock()))
    def test_update_bashrc_file_with_env_variable__handles_bashrc_file_missing(
            self, mock_getstatusoutput, mock_does_file_exist):
        self.assertFalse(common.update_bashrc_file_with_env_variable("ENM_URL", "some_ip"))
        mock_does_file_exist.assert_called_with("/root/.bashrc")
        self.assertFalse(mock_getstatusoutput.called)

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, Mock()))
    def test_update_bashrc_file_with_env_variable__failed_to_remove_old_entry(
            self, mock_getstatusoutput, mock_does_file_exist):
        self.assertFalse(common.update_bashrc_file_with_env_variable("ENM_URL", "some_ip"))
        mock_does_file_exist.assert_called_with("/root/.bashrc")
        command = "/bin/sed -i '/export.*ENM_URL=/d' /root/.bashrc"
        self.assertEqual([call(command)], mock_getstatusoutput.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", side_effect=[(0, Mock()), (1, Mock())])
    def test_update_bashrc_file_with_env_variable__failed_to_add_new_entry(
            self, mock_getstatusoutput, mock_does_file_exist):
        self.assertFalse(common.update_bashrc_file_with_env_variable("ENM_URL", "some_ip"))
        mock_does_file_exist.assert_called_with("/root/.bashrc")
        command = "/bin/sed -i '/export.*ENM_URL=/d' /root/.bashrc"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        command = "echo 'export ENM_URL=some_ip' >> /root/.bashrc"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command")
    def test_restart_services__success(self, mock_exec_command, mock_debug):
        mock_exec_command.return_value = {"result": True, "output": ""}

        self.assertTrue(common.restart_services())

        self.assertTrue(call("/sbin/service usermanager restart") in mock_exec_command.mock_calls)
        self.assertTrue(call("/sbin/service deploymentinfomanager restart") in mock_exec_command.mock_calls)
        self.assertTrue(call("/sbin/service nodemanager restart") in mock_exec_command.mock_calls)
        self.assertTrue(call("/sbin/service profilemanager restart") in mock_exec_command.mock_calls)
        self.assertTrue(call("4 out of 4 services restarted.") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command")
    def test_restart_services__if_commands_fail(self, mock_exec_command, mock_debug):
        mock_exec_command.return_value = {"result": False, "output": ""}

        self.assertFalse(common.restart_services())

        self.assertTrue(call("0 out of 4 services restarted.") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, Mock()))
    def test_check_if_rpm_package_is_installed__return_true_if_rpm_installed(self, mock_getstatusoutput):
        self.assertTrue(common.check_if_rpm_package_is_installed("some_package", "some_version"))
        mock_getstatusoutput.assert_called_with("rpm -qa | egrep some_package.*some_version")

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, Mock()))
    def test_check_if_rpm_package_is_installed__return_false_if_rpm_not_installed(self, mock_getstatusoutput):
        self.assertFalse(common.check_if_rpm_package_is_installed("some_package"))
        mock_getstatusoutput.assert_called_with("rpm -qa | egrep some_package.*")

    @patch("enmutils_int.lib.configure_wlvm_common.extract_path_to_rpm_from_nexus_redirect")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput")
    def test_download_release_package_from_nexus__returns_true_if_download_successful(
            self, mock_getstatusoutput, mock_extract_path_to_rpm_from_nexus_redirect):
        mock_getstatusoutput.side_effect = [(0, "some_output"), (0, Mock())]
        mock_extract_path_to_rpm_from_nexus_redirect.return_value = "https://some_rpm_url"
        self.assertTrue(common.download_release_package_from_nexus("package_name", "nexus_path", "file_path", True))
        command = ("curl -s -x atproxy1.athtem.eei.ericsson.se:3128 "
                   "'https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?"
                   "r=releases&g=nexus_path&a=package_name&v=RELEASE&e=rpm'")
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        command = "curl -s -o file_path -x atproxy1.athtem.eei.ericsson.se:3128 'https://some_rpm_url'"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        mock_extract_path_to_rpm_from_nexus_redirect.assert_called_with("some_output")

    @patch("enmutils_int.lib.configure_wlvm_common.extract_path_to_rpm_from_nexus_redirect")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput")
    def test_download_release_package_from_nexus__returns_false_if_redirect_contains_unexpected_output(
            self, mock_getstatusoutput, mock_extract_path_to_rpm_from_nexus_redirect):
        mock_getstatusoutput.side_effect = [(0, "some_output"), (0, Mock())]
        mock_extract_path_to_rpm_from_nexus_redirect.return_value = None
        self.assertFalse(common.download_release_package_from_nexus("package_name", "nexus_path", "file_path", True))
        command = ("curl -s -x atproxy1.athtem.eei.ericsson.se:3128 "
                   "'https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?"
                   "r=releases&g=nexus_path&a=package_name&v=RELEASE&e=rpm'")
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        self.assertEqual(mock_getstatusoutput.call_count, 1)
        mock_extract_path_to_rpm_from_nexus_redirect.assert_called_with("some_output")

    @patch("enmutils_int.lib.configure_wlvm_common.extract_path_to_rpm_from_nexus_redirect")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput")
    def test_download_release_package_from_nexus__returns_false_if_rpm_download_fails(
            self, mock_getstatusoutput, mock_extract_path_to_rpm_from_nexus_redirect):
        mock_getstatusoutput.side_effect = [(0, "some_output"), (1, Mock())]
        mock_extract_path_to_rpm_from_nexus_redirect.return_value = "https://some_rpm_url"
        self.assertFalse(common.download_release_package_from_nexus("package_name", "nexus_path", "file_path", True))
        command = ("curl -s -x atproxy1.athtem.eei.ericsson.se:3128 "
                   "'https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?"
                   "r=releases&g=nexus_path&a=package_name&v=RELEASE&e=rpm'")
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        command = "curl -s -o file_path -x atproxy1.athtem.eei.ericsson.se:3128 'https://some_rpm_url'"
        self.assertTrue(call(command) in mock_getstatusoutput.mock_calls)
        mock_extract_path_to_rpm_from_nexus_redirect.assert_called_with("some_output")

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, Mock()))
    def test_download_release_package_from_nexus__returns_false_if_redirect_download_unsuccessful(
            self, mock_getstatusoutput):
        self.assertFalse(common.download_release_package_from_nexus("package_name", "nexus_path", "file_path", True))
        self.assertTrue(mock_getstatusoutput.called)

    def test_extract_path_to_rpm_from_nexus_redirect__successful(self):
        message = "If you are not automatically redirected use this url: https://some_url"
        self.assertEqual("https://some_url", common.extract_path_to_rpm_from_nexus_redirect(message))

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    def test_extract_path_to_rpm_from_nexus_redirect__unsuccessful(self, mock_debug):
        message = "Resource unavailable"
        self.assertEqual(None, common.extract_path_to_rpm_from_nexus_redirect(message))
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, Mock()))
    def test_install_rpm_package__successful(self, mock_getstatusoutput):
        self.assertTrue(common.install_rpm_package("file_path"))
        mock_getstatusoutput.assert_called_with("rpm -ivh file_path --nodeps")

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, Mock()))
    def test_install_rpm_package__unsuccessful(self, mock_getstatusoutput):
        self.assertFalse(common.install_rpm_package("file_path"))
        self.assertTrue(mock_getstatusoutput.called)

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, Mock()))
    def test_perform_service_operation__successful(self, mock_getstatusoutput):
        self.assertTrue(common.perform_service_operation("ddc", "status"))
        mock_getstatusoutput.assert_called_with("service ddc status")

    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, Mock()))
    def test_perform_service_operation__unsuccessful(self, mock_getstatusoutput):
        self.assertFalse(common.perform_service_operation("ddc", "status"))
        self.assertTrue(mock_getstatusoutput.called)

    @patch("enmutils_int.lib.configure_wlvm_common.check_if_ssh_keys_exist", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": "key"})
    def test_create_ssh_keys__successful(self, mock_execute_command, _):
        self.assertTrue(common.create_ssh_keys())
        mock_execute_command.assert_called_with("ssh-keygen -t rsa -N '' -f /root/.ssh/id_rsa")

    @patch("enmutils_int.lib.configure_wlvm_common.check_if_ssh_keys_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": "key"})
    def test_create_ssh_keys__returns_true_if_keys_already_created(self, mock_execute_command, _):
        self.assertTrue(common.create_ssh_keys())
        self.assertFalse(mock_execute_command.called)

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=True)
    def test_check_if_ssh_keys_exist__returns_true_if_keys_exist(self, mock_does_file_exist):
        self.assertTrue(common.check_if_ssh_keys_exist())
        self.assertEqual([call("/root/.ssh/id_rsa"), call("/root/.ssh/id_rsa.pub")], mock_does_file_exist.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=False)
    def test_check_if_ssh_keys_exist__returns_false_if_keys_do_not_exist(self, mock_does_file_exist):
        self.assertFalse(common.check_if_ssh_keys_exist())
        self.assertTrue(mock_does_file_exist.called)

    @patch("enmutils_int.lib.configure_wlvm_common.set_file_permissions")
    @patch("enmutils_int.lib.configure_wlvm_common.add_ssh_public_key_to_authorized_keys")
    @patch("enmutils_int.lib.configure_wlvm_common.remove_hostname_entries_from_ssh_authorized_keys")
    @patch("enmutils_int.lib.configure_wlvm_common.get_ssh_public_key")
    def test_update_ssh_authorized_keys__successful(
            self, mock_get_ssh_public_key, mock_remove_hostname_entries_from_ssh_authorized_keys,
            mock_add_ssh_public_key_to_authorized_keys, mock_set_file_permissions):
        self.assertTrue(common.update_ssh_authorized_keys())
        self.assertTrue(mock_remove_hostname_entries_from_ssh_authorized_keys)
        mock_add_ssh_public_key_to_authorized_keys.assert_called_with(mock_get_ssh_public_key.return_value)
        mock_set_file_permissions.assert_called_with("/root/.ssh/authorized_keys", "644")

    @patch("enmutils_int.lib.configure_wlvm_common.get_ssh_public_key", return_value="")
    @patch("enmutils_int.lib.configure_wlvm_common.set_file_permissions")
    @patch("enmutils_int.lib.configure_wlvm_common.add_ssh_public_key_to_authorized_keys")
    @patch("enmutils_int.lib.configure_wlvm_common.remove_hostname_entries_from_ssh_authorized_keys")
    def test_update_ssh_authorized_keys__unsuccessful(
            self, mock_remove_hostname_entries_from_ssh_authorized_keys,
            mock_add_ssh_public_key_to_authorized_keys, mock_set_file_permissions, _):
        self.assertFalse(common.update_ssh_authorized_keys())
        self.assertFalse(mock_remove_hostname_entries_from_ssh_authorized_keys.called)
        self.assertFalse(mock_add_ssh_public_key_to_authorized_keys.called)
        self.assertFalse(mock_set_file_permissions.called)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, "some_output"))
    def test_execute_command__successful_if_log_output_is_true(self, mock_getstatusoutput, mock_debug):
        self.assertEqual({"result": True, "output": "some_output"}, common.execute_command("command"))
        mock_getstatusoutput.assert_called_with("command")
        self.assertEqual(mock_debug.call_count, 2)
        self.assertTrue(call("Execution successful (rc=0). Output: some_output") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, "some_output"))
    def test_execute_command__unsuccessful_if_log_output_is_true(self, mock_getstatusoutput, mock_debug):
        self.assertEqual({"result": False, "output": "some_output"}, common.execute_command("command"))
        mock_getstatusoutput.assert_called_with("command")
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(0, "some_output"))
    def test_execute_command__successful_if_log_output_is_false(self, mock_getstatusoutput, mock_debug):
        self.assertEqual({"result": True, "output": "some_output"},
                         common.execute_command("command", log_output=False))
        mock_getstatusoutput.assert_called_with("command")
        self.assertFalse(mock_debug.called)

    @patch("enmutils_int.lib.configure_wlvm_common.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_common.commands.getstatusoutput", return_value=(1, "some_output"))
    def test_execute_command__unsuccessful_if_log_output_is_false(self, mock_getstatusoutput, mock_debug):
        self.assertEqual({"result": False, "output": "some_output"},
                         common.execute_command("command", log_output=False))
        mock_getstatusoutput.assert_called_with("command")
        self.assertFalse(mock_debug.called)

    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": "key"})
    def test_get_ssh_public_key__successful(self, mock_execute_command):
        self.assertEqual("key", common.get_ssh_public_key())
        mock_execute_command.assert_called_with("cat /root/.ssh/id_rsa.pub")

    @patch("enmutils_int.lib.configure_wlvm_common.socket.gethostname", return_value="some_host")
    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": Mock()})
    def test_remove_hostname_entries_from_ssh_authorized_keys__successful(
            self, mock_execute_command, mock_does_file_exist, _):
        self.assertTrue(common.remove_hostname_entries_from_ssh_authorized_keys())
        mock_execute_command.assert_called_with("sed -i '/some_host/d' /root/.ssh/authorized_keys")
        mock_does_file_exist.assert_called_with("/root/.ssh/authorized_keys")

    @patch("enmutils_int.lib.configure_wlvm_common.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": Mock()})
    def test_remove_hostname_entries_from_ssh_authorized_keys__returns_true_if_file_does_not_exist(
            self, mock_execute_command, mock_does_file_exist):
        self.assertTrue(common.remove_hostname_entries_from_ssh_authorized_keys())
        self.assertFalse(mock_execute_command.called)
        self.assertTrue(mock_does_file_exist.called)

    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": Mock()})
    def test_add_ssh_public_key_to_authorized_keys__successful(self, mock_execute_command):
        self.assertTrue(common.add_ssh_public_key_to_authorized_keys("public_key"))
        mock_execute_command.assert_called_with("echo 'public_key' >> /root/.ssh/authorized_keys")

    @patch("enmutils_int.lib.configure_wlvm_common.execute_command", return_value={"result": True, "output": Mock()})
    def test_set_ssh_authorized_keys_file_permissions__successful(self, mock_execute_command):
        self.assertTrue(common.set_file_permissions("some_file", "644"))
        mock_execute_command.assert_called_with("chmod 644 some_file")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
