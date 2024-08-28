#!/usr/bin/env python
import unittest2

import enmutils_int.lib.configure_wlvm_cenm as configure
from mock import patch, mock_open, call, Mock
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class ConfigureWlvmCENMUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("enmutils_int.lib.configure_wlvm_cenm.json.dumps")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_document_content_from_dit")
    def test_create_kube_config_file__successful(
            self, mock_get_document_content_from_dit, mock_open_file, mock_dumps, *_):
        documents_info_dict = {"cloud_native_enm_kube_config": "some_id"}
        mock_get_document_content_from_dit.return_value = "some_content"
        self.assertTrue(configure.create_kube_config_file(documents_info_dict, "deployment_name"))
        mock_open_file.return_value.write.assert_called_with(mock_dumps.return_value)
        mock_dumps.assert_called_with("some_content")

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.json.dumps")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_document_content_from_dit")
    def test_create_kube_config_file__handles_failure_to_write(
            self, mock_get_document_content_from_dit, mock_open_file, *_):
        mock_open_file.return_value.write.side_effect = Exception()
        documents_info_dict = {"cloud_native_enm_kube_config": "some_id"}
        mock_get_document_content_from_dit.return_value = "some_content"
        self.assertFalse(configure.create_kube_config_file(documents_info_dict, "deployment_name"))

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_document_content_from_dit")
    def test_create_kube_config_file__handles_no_content_in_document(
            self, mock_get_document_content_from_dit, mock_open_file, *_):
        documents_info_dict = {"cloud_native_enm_kube_config": "some_id"}
        mock_get_document_content_from_dit.return_value = ""
        self.assertFalse(configure.create_kube_config_file(documents_info_dict, "deployment_name"))
        self.assertFalse(mock_open_file.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_document_content_from_dit")
    def test_create_kube_config_file__handles_no_document_id(self, mock_get_document_content_from_dit, *_):
        documents_info_dict = {"cloud_native_enm_kube_config": ""}
        self.assertFalse(configure.create_kube_config_file(documents_info_dict, "deployment_name"))
        self.assertFalse(mock_get_document_content_from_dit.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.warn")
    def test_create_kube_config_file__logs_if_document_id_not_in_dict(self, mock_warn, mock_create_dir, *_):
        documents_info_dict = {"cloud_native_enm_kube_config": ""}
        self.assertFalse(configure.create_kube_config_file(documents_info_dict, "deployment_name"))
        self.assertTrue(mock_create_dir.called)
        self.assertEqual(2, mock_warn.call_count)
        mock_warn.assert_any_call("Unable to find document 'cloud_native_enm_kube_config' on DIT for"
                                  " deployment deployment_name")
        mock_warn.assert_any_call('Unable to create kube config file: /root/.kube/config')

    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.debug")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_document_content_from_dit", return_value=None)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_dir")
    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger.warn")
    def test_create_kube_config_file__logs_when_document_not_retrieved_from_dit(self, mock_warn, mock_create_dir, *_):
        documents_info_dict = {"cloud_native_enm_kube_config": "1"}
        self.assertFalse(configure.create_kube_config_file(documents_info_dict, "deployment_name"))
        self.assertTrue(mock_create_dir.called)
        self.assertEqual(2, mock_warn.call_count)
        mock_warn.assert_any_call("The document 'cloud_native_enm_kube_config' from DIT contains no content")
        mock_warn.assert_called_with('Unable to create kube config file: /root/.kube/config')

    # download_kubectl_client test cases
    @patch("enmutils_int.lib.configure_wlvm_cenm.compare_kubectl_client_and_server_version", return_value="1.2.3")
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    def test_download_kubectl_client__successful(self, mock_getstatusoutput, _):
        mock_getstatusoutput.side_effect = [(0, Mock())]
        self.assertTrue(configure.download_kubectl_client(True))
        curl2 = ("curl -s -o /usr/local/bin/kubectl -x atproxy1.athtem.eei.ericsson.se:3128 "
                 "'https://arm.sero.gic.ericsson.se/artifactory/proj-iopensrc-dev-generic-local/"
                 "com/storage.googleapis/kubernetes-release/release/1.2.3/bin/linux/amd64/kubectl'")
        self.assertEqual(mock_getstatusoutput.mock_calls, [call(curl2)])

    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    @patch("enmutils_int.lib.configure_wlvm_cenm.compare_kubectl_client_and_server_version")
    def test_download_kubectl_client__fails_to_fetch_version(self, mock_compare_kubectl_client_and_server_version, _):
        mock_compare_kubectl_client_and_server_version.return_value = ""
        self.assertTrue(configure.download_kubectl_client(True))

    @patch("enmutils_int.lib.configure_wlvm_cenm.compare_kubectl_client_and_server_version")
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    def test_download_kubectl_client__fails_to_fetch_executable(self, mock_getstatusoutput, _):
        mock_getstatusoutput.side_effect = [(1, "error")]
        self.assertFalse(configure.download_kubectl_client(True))

    @patch("enmutils_int.lib.configure_wlvm_cenm.compare_kubectl_client_and_server_version")
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    def test_download_kubectl_client__will_not_fetch_version_if_already_provided(self, mock_getstatusoutput, _):
        mock_getstatusoutput.return_value = (0, "success")
        self.assertTrue(configure.download_kubectl_client(False, 'version'))

    @patch("enmutils_int.lib.configure_wlvm_cenm.compare_kubectl_client_and_server_version", return_value="")
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    def test_download_kubectl_client__if_proxy_not_required_and_version_is_empty(self, mock_getstatusoutput, _):
        mock_getstatusoutput.return_value = (0, "success")
        self.assertTrue(configure.download_kubectl_client(False))

    # install_kubectl_client test cases
    @patch("enmutils_int.lib.configure_wlvm_cenm.download_kubectl_client", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput", return_value=(0, ""))
    def test_install_kubectl_client__is_successful(self, mock_getstatusoutput, *_):
        self.assertTrue(configure.install_kubectl_client(True))
        mock_getstatusoutput.assert_called_with("chmod +x /usr/local/bin/kubectl")

    @patch("enmutils_int.lib.configure_wlvm_cenm.download_kubectl_client", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput", return_value=(0, ""))
    def test_install_kubectl_client__handles_download_failure(self, *_):
        self.assertFalse(configure.install_kubectl_client(True))

    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput", return_value=(1, "error"))
    @patch("enmutils_int.lib.configure_wlvm_cenm.download_kubectl_client", return_value=True)
    def test_install_kubectl_client__unable_to_set_permission(self, *_):
        self.assertFalse(configure.install_kubectl_client(True))

    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput")
    def test_check_kubectl_connection__successful(self, mock_getstatusoutput):
        output = ("Kubernetes master is running at https://XYZ:12345"
                  "KubeDNS is running at https://XYZ:12345/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy"
                  ""
                  "To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.")
        mock_getstatusoutput.return_value = (0, output)
        self.assertTrue(configure.check_kubectl_connection())
        mock_getstatusoutput.assert_called_with("/usr/local/bin/kubectl --kubeconfig /root/.kube/config cluster-info 2>/dev/null")

    @patch("enmutils_int.lib.configure_wlvm_cenm.commands.getstatusoutput", return_value=(1, "error"))
    @patch("enmutils_int.lib.configure_wlvm_cenm.log.logger")
    def test_check_kubectl_connection__unsuccessful(self, mock_logger, mock_getstatusoutput):
        self.assertFalse(configure.check_kubectl_connection())
        mock_getstatusoutput.assert_called_with("/usr/local/bin/kubectl --kubeconfig /root/.kube/config cluster-info 2>/dev/null")
        mock_logger.warn.assert_any_call("Failed to connect to cluster with kubectl client: error")

    @patch("enmutils_int.lib.configure_wlvm_cenm.update_bashrc_file_with_env_variable", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_parameter_value_from_sed_document", return_value="some_ip")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_sed_id", return_value="12345")
    def test_set_cenm_variables__is_successful(
            self, mock_get_sed_id, mock_get_parameter_value_from_sed_document,
            mock_update_bashrc_file_with_env_variable):
        self.assertTrue(configure.set_cenm_variables("deployment_name", "slogan"))
        mock_get_sed_id.assert_called_with("deployment_name")
        mock_get_parameter_value_from_sed_document.assert_called_with("12345", "httpd_fqdn")
        self.assertTrue(call("ENM_URL", "some_ip") in mock_update_bashrc_file_with_env_variable.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_cenm.update_bashrc_file_with_env_variable")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_parameter_value_from_sed_document")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_sed_id", return_value=None)
    def test_set_cenm_variables__handles_empty_sed_id(
            self, mock_get_sed_id, mock_get_parameter_value_from_sed_document,
            mock_update_bashrc_file_with_env_variable):
        self.assertFalse(configure.set_cenm_variables("deployment_name", "slogan"))
        mock_get_sed_id.assert_called_with("deployment_name")
        self.assertFalse(mock_get_parameter_value_from_sed_document.called)
        self.assertFalse(mock_update_bashrc_file_with_env_variable.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.update_bashrc_file_with_env_variable")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_parameter_value_from_sed_document", return_value=None)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_sed_id", return_value="12345")
    def test_set_cenm_variables__handles_empty_httpd_fqdn(
            self, mock_get_sed_id, mock_get_parameter_value_from_sed_document,
            mock_update_bashrc_file_with_env_variable):
        self.assertFalse(configure.set_cenm_variables("deployment_name", "slogan"))
        mock_get_sed_id.assert_called_with("deployment_name")
        mock_get_parameter_value_from_sed_document.assert_called_with("12345", "httpd_fqdn")
        self.assertFalse(mock_update_bashrc_file_with_env_variable.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.update_bashrc_file_with_env_variable", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_parameter_value_from_sed_document", return_value="some_ip")
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_sed_id", return_value="12345")
    def test_set_cenm_variables__handles_failure_to_update_bashrc_file(
            self, mock_get_sed_id, mock_get_parameter_value_from_sed_document,
            mock_update_bashrc_file_with_env_variable):
        self.assertFalse(configure.set_cenm_variables("deployment_name", "slogan"))
        mock_get_sed_id.assert_called_with("deployment_name")
        mock_get_parameter_value_from_sed_document.assert_called_with("12345", "httpd_fqdn")
        mock_update_bashrc_file_with_env_variable.assert_called_with("ENM_URL", "some_ip")

    @patch("enmutils_int.lib.configure_wlvm_cenm.install_kubectl_client", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_connection", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_kube_config_file", return_value=True)
    def test_setup_cluster_connection__is_successful(
            self, mock_create_kube_config_file, mock_check_kubectl_connection, _):
        dit_document_info_dict = Mock()
        self.assertTrue(configure.setup_cluster_connection("deployment_name", dit_document_info_dict, "slogan", True))
        mock_create_kube_config_file.assert_called_with(dit_document_info_dict, "deployment_name")
        self.assertTrue(mock_check_kubectl_connection.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.install_kubectl_client", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_connection", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_kube_config_file", return_value=True)
    def test_setup_cluster_connection__returns_false_if_connection_to_cluster_fails(
            self, mock_create_kube_config_file, mock_check_kubectl_connection, _):
        dit_document_info_dict = Mock()
        self.assertFalse(configure.setup_cluster_connection("deployment_name", dit_document_info_dict, "slogan", True))
        mock_create_kube_config_file.assert_called_with(dit_document_info_dict, "deployment_name")
        self.assertTrue(mock_check_kubectl_connection.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.add_secret_to_cluster", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.update_ssh_authorized_keys", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_ssh_keys", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_server_txt_file", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_deployment_namespace")
    def test_create_ddc_secret_on_cluster__successful(
            self, mock_get_deployment_namespace, mock_create_server_txt_file, mock_create_ssh_keys,
            mock_update_ssh_authorized_keys, mock_add_secret_to_cluster):
        dit_documents_info_dict = Mock()
        self.assertTrue(configure.create_ddc_secret_on_cluster("deployment_name", "slogan", dit_documents_info_dict))
        mock_get_deployment_namespace.assert_called_with("deployment_name", dit_documents_info_dict)
        self.assertTrue(mock_create_server_txt_file.called)
        self.assertTrue(mock_create_ssh_keys.called)
        self.assertTrue(mock_update_ssh_authorized_keys.called)
        mock_add_secret_to_cluster.assert_called_with(mock_get_deployment_namespace.return_value)

    @patch("enmutils_int.lib.configure_wlvm_cenm.add_secret_to_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.update_ssh_authorized_keys")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_ssh_keys")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_server_txt_file", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.get_deployment_namespace")
    def test_create_ddc_secret_on_cluster__unsuccessful(
            self, mock_get_deployment_namespace, mock_create_server_txt_file, mock_create_ssh_keys,
            mock_update_ssh_authorized_keys, mock_add_secret_to_cluster):
        dit_documents_info_dict = Mock()
        self.assertFalse(configure.create_ddc_secret_on_cluster("deployment_name", "slogan", dit_documents_info_dict))
        mock_get_deployment_namespace.assert_called_with("deployment_name", dit_documents_info_dict)
        self.assertTrue(mock_create_server_txt_file.called)
        self.assertFalse(mock_create_ssh_keys.called)
        self.assertFalse(mock_update_ssh_authorized_keys.called)
        self.assertFalse(mock_add_secret_to_cluster.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.socket.gethostname", return_value="some_host")
    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": True, "output": ""})
    def test_create_server_txt_file__successful(self, mock_execute_command, *_):
        self.assertTrue(configure.create_server_txt_file())
        mock_execute_command.assert_called_with("echo 'some_host.athtem.eei.ericsson.se=WORKLOAD\n' > "
                                                "/tmp/ddc_server.txt")

    @patch("enmutils_int.lib.configure_wlvm_cenm.verify_workload_entry_added_to_secret", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_secret_on_cluster", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.delete_secret_from_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_if_secret_exists", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_can_be_used", return_value=True)
    def test_add_secret_to_cluster__successful(
            self, mock_check_kubectl_can_be_used, mock_check_if_secret_exists, mock_delete_secret_from_cluster,
            mock_create_secret_on_cluster, mock_verify_workload_entry_added_to_secret):
        self.assertTrue(configure.add_secret_to_cluster("enm123"))
        self.assertTrue(mock_check_kubectl_can_be_used.called)
        mock_check_if_secret_exists.assert_called_with("enm123")
        self.assertFalse(mock_delete_secret_from_cluster.called)
        mock_create_secret_on_cluster.assert_called_with("enm123")
        mock_verify_workload_entry_added_to_secret.assert_called_with("enm123")

    @patch("enmutils_int.lib.configure_wlvm_cenm.verify_workload_entry_added_to_secret")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_secret_on_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.delete_secret_from_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_if_secret_exists")
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_can_be_used", return_value=False)
    def test_add_secret_to_cluster__unsuccessful_if_kubectl_cant_be_used(
            self, mock_check_kubectl_can_be_used, mock_check_if_secret_exists, mock_delete_secret_from_cluster,
            mock_create_secret_on_cluster, mock_verify_workload_entry_added_to_secret):
        self.assertFalse(configure.add_secret_to_cluster("enm123"))
        self.assertTrue(mock_check_kubectl_can_be_used.called)
        self.assertFalse(mock_check_if_secret_exists.called)
        self.assertFalse(mock_delete_secret_from_cluster.called)
        self.assertFalse(mock_create_secret_on_cluster.called)
        self.assertFalse(mock_verify_workload_entry_added_to_secret.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.verify_workload_entry_added_to_secret")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_secret_on_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.delete_secret_from_cluster", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_if_secret_exists", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_can_be_used", return_value=True)
    def test_add_secret_to_cluster__unsuccessful_if_cant_delete_secret(
            self, mock_check_kubectl_can_be_used, mock_check_if_secret_exists, mock_delete_secret_from_cluster,
            mock_create_secret_on_cluster, mock_verify_workload_entry_added_to_secret):
        self.assertFalse(configure.add_secret_to_cluster("enm123"))
        self.assertTrue(mock_check_kubectl_can_be_used.called)
        mock_check_if_secret_exists.assert_called_with("enm123")
        mock_delete_secret_from_cluster.assert_called_with("enm123")
        self.assertFalse(mock_create_secret_on_cluster.called)
        self.assertFalse(mock_verify_workload_entry_added_to_secret.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.verify_workload_entry_added_to_secret")
    @patch("enmutils_int.lib.configure_wlvm_cenm.create_secret_on_cluster", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.delete_secret_from_cluster")
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_if_secret_exists", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_can_be_used", return_value=True)
    def test_add_secret_to_cluster__unsuccessful_if_cant_create_secret(
            self, mock_check_kubectl_can_be_used, mock_check_if_secret_exists, mock_delete_secret_from_cluster,
            mock_create_secret_on_cluster, mock_verify_workload_entry_added_to_secret):
        self.assertFalse(configure.add_secret_to_cluster("enm123"))
        self.assertTrue(mock_check_kubectl_can_be_used.called)
        mock_check_if_secret_exists.assert_called_with("enm123")
        self.assertFalse(mock_delete_secret_from_cluster.called)
        mock_create_secret_on_cluster.assert_called_with("enm123")
        self.assertFalse(mock_verify_workload_entry_added_to_secret.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_connection", return_value=True)
    @patch("enmutils_int.lib.configure_wlvm_cenm.does_file_exist", return_value=True)
    def test_check_kubectl_can_be_used__successful(self, mock_does_file_exist, mock_check_kubectl_connection):
        self.assertTrue(configure.check_kubectl_can_be_used())
        self.assertTrue(mock_check_kubectl_connection.called)
        self.assertEqual([call("/usr/local/bin/kubectl"), call("/root/.kube/config")], mock_does_file_exist.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_cenm.check_kubectl_connection", return_value=False)
    @patch("enmutils_int.lib.configure_wlvm_cenm.does_file_exist", return_value=True)
    def test_check_kubectl_can_be_used__unsuccessful(self, mock_does_file_exist, mock_check_kubectl_connection):
        self.assertFalse(configure.check_kubectl_can_be_used())
        self.assertTrue(mock_check_kubectl_connection.called)
        self.assertEqual([call("/usr/local/bin/kubectl"), call("/root/.kube/config")], mock_does_file_exist.mock_calls)

    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": True, "output": ""})
    def test_check_if_secret_exists__successful(self, mock_execute_command, *_):
        self.assertTrue(configure.check_if_secret_exists("enm123"))
        mock_execute_command.assert_called_with(
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get secret remote-servers -n enm123 2>/dev/null")

    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": False, "output": Mock()})
    def test_check_if_secret_exists__unsuccessful(self, mock_execute_command, *_):
        self.assertFalse(configure.check_if_secret_exists("enm123"))
        mock_execute_command.assert_called_with(
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get secret remote-servers -n enm123 2>/dev/null")

    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": True, "output": Mock()})
    def test_delete_secret_from_cluster__successful(self, mock_execute_command):
        self.assertTrue(configure.delete_secret_from_cluster("enm123"))
        mock_execute_command.assert_called_with(
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config delete secret remote-servers -n enm123 2>/dev/null")

    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": True, "output": Mock()})
    def test_create_secret_on_cluster__successful(self, mock_execute_command, *_):
        self.assertTrue(configure.create_secret_on_cluster("enm123"))
        mock_execute_command.assert_called_with(
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config create secret generic remote-servers -n enm123 "
            "--from-file=server.txt=/tmp/ddc_server.txt --from-file=ssh-key=/root/.ssh/id_rsa 2>/dev/null")

    @patch("enmutils_int.lib.configure_wlvm_cenm.socket.gethostname", return_value="some_host")
    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": True, "output": Mock()})
    def test_verify_workload_entry_added_to_secret__successful(self, mock_execute_command, *_):
        self.assertTrue(configure.verify_workload_entry_added_to_secret("enm123"))
        mock_execute_command.assert_called_with(
            "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get secret remote-servers -n enm123 -o yaml 2>/dev/null | "
            "egrep server.txt | awk '{print $2}' | base64 --decode | egrep some_host.*WORKLOAD")

    @patch("enmutils_int.lib.configure_wlvm_cenm.socket.gethostname")
    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command", return_value={"result": False, "output": Mock()})
    def test_verify_workload_entry_added_to_secret__unsuccessful(self, mock_execute_command, *_):
        self.assertFalse(configure.verify_workload_entry_added_to_secret("enm123"))
        self.assertTrue(mock_execute_command.called)

    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command")
    def test_compare_kubectl_client_and_server_version__returns_server_version_if_it_is_not_same_as_client(self,
                                                                                                           mock_execute_command):
        output = 'client_version:  v1.20.5\nserver_version:  v1.19.3'
        mock_execute_command.return_value = {'result': True, 'output': output}
        result = configure.compare_kubectl_client_and_server_version("deployment_name", "slogan")
        self.assertEqual(result, 'v1.19.3')

    @patch("enmutils_int.lib.configure_wlvm_cenm.log")
    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command")
    def test_compare_kubectl_client_and_server_version__returns_nothing_if_client_version_same_as_server(self,
                                                                                                         mock_execute_command,
                                                                                                         mock_log):
        output = 'client_version:  v1.20.5\nserver_version:  v1.20.5'
        mock_execute_command.return_value = {'result': True, 'output': output}
        configure.compare_kubectl_client_and_server_version("deployment_name", "slogan")
        self.assertTrue(mock_execute_command.called)
        self.assertEqual(mock_log.logger.debug.call_count, 1)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.configure_wlvm_cenm.log")
    @patch("enmutils_int.lib.configure_wlvm_cenm.execute_command")
    def test_compare_kubectl_client_and_server_version__does_not_compare_versions(self, mock_execute_command, mock_log):
        output = 'sh: /usr/bin/kubectl: No such file or directory'
        mock_execute_command.return_value = {'result': False, 'output': output}
        configure.compare_kubectl_client_and_server_version("deployment_name", "slogan")
        self.assertTrue(mock_execute_command.called)
        self.assertEqual(mock_log.logger.info.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
