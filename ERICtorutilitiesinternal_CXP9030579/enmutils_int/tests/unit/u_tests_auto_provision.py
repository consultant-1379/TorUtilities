#!/usr/bin/env python
import commands
import os
import pkgutil

import unipath
import unittest2
from mock import Mock, mock_open, patch, call

from enmutils.lib import filesystem
from enmutils.lib.exceptions import (EnmApplicationError, EnvironError, ScriptEngineResponseValidationError,
                                     ShellCommandReturnedNonZero)
from enmutils_int.lib.auto_provision import (AutoProvision, CREATE_NE_CMD, CREATE_CONNECTIVITY_CMD, CREATE_SECURITY_CMD,
                                             CREATE_SNMP_CMD, DELETE_NE_CMD, DELETE_NRM_DATA_CMD)
from enmutils_int.lib.auto_provision_project import (Project, create_ap_pkg_directory, scp_upgrade_packages,
                                                     raise_invalid_project, InvalidProjectException)
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class AutoProvisionUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser", password="T3stP4ssw0rd")
        self.name = "AutoProvisionUnitTest"
        self.node = Mock()
        self.node.ip = generate_configurable_ip()
        self.node_id = "unitNode"
        self.node.primary_type = "RadioNode"
        self.project = Project(user=self.user, name=self.name, nodes=[self.node])
        self.auto = AutoProvision(user=self.user, nodes=[self.node], project_name=self.name)
        self.file_name = "/tmp/no_such_file"

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_import_project_raises_import_error(self):
        self.auto.project_name = None
        self.assertRaises(EnvironError, self.auto.import_project, file_name=self.file_name)

    @patch('enmutils_int.lib.auto_provision_project.os.makedirs', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.os.path.exists', return_value=False)
    def test_create_ap_pkg_directory(self, *_):
        create_ap_pkg_directory()

    @patch('enmutils_int.lib.auto_provision_project.os.path.exists', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.os.makedirs', side_effect=Exception)
    def test_create_ap_pkg_directory_exception(self, *_):
        self.assertRaises(Exception, create_ap_pkg_directory)

    @patch('enmutils_int.lib.auto_provision_project.os.path.exists', return_value=True)
    def test_create_ap_pkg_directory_path_exists(self, *_):
        create_ap_pkg_directory()

    @patch("enmutils_int.lib.auto_provision_project.filesystem.does_file_exist", return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch('enmutils_int.lib.auto_provision_project.download')
    def test_scp_upgrade_packages(self, mock_download, *_):
        scp_upgrade_packages()
        self.assertTrue(mock_download.called)

    @patch("enmutils_int.lib.auto_provision_project.filesystem.does_file_exist", return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory')
    def test_scp_upgrade_packages_file_exists(self, *_):
        scp_upgrade_packages()

    @patch("enmutils_int.lib.auto_provision_project.filesystem.does_file_exist", return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch('enmutils_int.lib.auto_provision_project.download', side_effect=Exception)
    def test_scp_upgrade_packages_exception(self, *_):
        self.assertRaises(Exception, scp_upgrade_packages)

    @patch('enmutils_int.lib.auto_provision.common_utils.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    def test_import_project_raises_script_engine_error(self, execute_safe_command, mock_check_response, _):
        self.auto.import_project(file_name=self.file_name)
        self.assertTrue(mock_check_response.called)
        self.assertTrue(execute_safe_command.called)

    def test_delete_project_raises_value_error(self):
        self.auto.project_name = None
        self.assertRaises(EnvironError, self.auto.delete_project)

    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    def test_delete_project(self, mock_check_response, *_):
        self.auto.delete_project()
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_delete_project_retain_nes_alters_command(self, mock_check_response, *_):
        self.auto.delete_project(retain_ne=True)
        self.assertTrue(mock_check_response.called)

    def test_download_artifacts_raises_value_error(self):
        self.assertRaises(ValueError, self.auto.download_artifacts)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_download_artifacts_no_node(self, mock_check_response, *_):
        self.auto.download_artifacts(artifact="ERBS")
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_download_artifacts(self, mock_check_response, *_):
        self.auto.download_artifacts(node=self.node)
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_view_all(self, mock_check_response, *_):
        self.auto.view(view_all=True)
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_view(self, mock_check_response, *_):
        self.auto.view()
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_status_all(self, mock_check_response, *_):
        self.auto.status(status_all=True)
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_status(self, mock_check_response, *_):
        self.auto.status()
        self.assertTrue(mock_check_response.called)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.execute_safe_command')
    @patch('enmutils_int.lib.auto_provision.AutoProvision._check_response')
    def test_order(self, mock_check_response, *_):
        self.auto.order()
        self.assertTrue(mock_check_response.called)

    def test_execute_safe_command_raises_enm_application_error(self):
        self.user.enm_execute.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, self.auto.execute_safe_command, "command")

    def test_execute_safe_command(self, *_):
        self.auto.execute_safe_command("command")

    def test_exist_returns_false_when_no_project(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertFalse(self.auto.exists())

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    def test_exist_handles_exceptions(self, mock_debug):
        self.user.enm_execute.side_effect = Exception("Error")
        self.assertFalse(self.auto.exists())
        self.assertTrue(mock_debug.called)

    def test_exist_returns_true_even_if_multiple_project_on_system(self):
        response = Mock()
        response.get_output.return_value = [u'Project Name\tNode Quantity\tCreator\tCreation Date\tDescription',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'AutoProvisionUnitTest\t2\tEricsson\t'
                                            u'2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'project1\t2\tEricsson\t2018-02-08 15:31:21\tA sample project',
                                            u'', u'10 project(s) found', u'']
        self.user.enm_execute.return_value = response
        self.assertTrue(self.auto.exists())

    @patch("enmutils_int.lib.auto_provision.log.logger.info")
    def test_validate_response__success(self, mock_log_info):
        self.auto.validate_response(Mock(stdout="success"))
        self.assertFalse(mock_log_info.called)

    @patch("enmutils_int.lib.auto_provision.log.logger.info")
    def test_validate_response__success_known_error(self, mock_log_info):
        node_response = " Error creating SnmpIpv6Address : Invalid String arg\n"
        self.auto.validate_response(Mock(stdout=node_response))
        mock_log_info.assert_called_with("Error creating SnmpIpv6Address : Invalid String arg. \n The above statement"
                                         " is result of third party tool which gives this string as a response for ipv6"
                                         " nodes used by design. This error can be ignored")

    def test_validate_response__raises_environ_error(self):
        node_error = " ERROR: NodeSecurityUup failed with the following :sum []: null\n"
        message = "Failed to send Node up notification, Response was {0}".format(node_error)
        with self.assertRaises(EnvironError) as error:
            self.auto.validate_response(Mock(stdout=node_error))
        self.assertEqual(error.exception.message, message)

    def test_validate_response__raises_environ_error__with_failed(self):
        node_error = "SNMP inform request failed or timed out for retry"
        message = "Failed to send Node up notification, Response was {0}".format(node_error)
        with self.assertRaises(EnvironError) as error:
            self.auto.validate_response(Mock(stdout=node_error))
        self.assertEqual(error.exception.message, message)

    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_emp_or_ms')
    @patch('enmutils_int.lib.auto_provision.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.auto_provision.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision.AutoProvision.validate_response')
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch("enmutils_int.lib.auto_provision.get_values_from_global_properties")
    def test_send_node_up__runs_only_on_supported_node(self, mock_get_values_from_global_properties, mock_log, *_):
        self.auto._send_node_up(node=Mock(primary_type="RBS"))
        self.assertEqual(mock_log.call_count, 1)
        self.assertFalse(mock_get_values_from_global_properties.called)

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.auto_provision.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision.AutoProvision.validate_response')
    @patch("enmutils_int.lib.auto_provision.get_values_from_global_properties", return_value=[])
    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_emp_or_ms')
    def test_send_node_up__raises_environ_error_if_ip_no_found(self, mock_run_cmd_on_emp_or_ms, mock_global_properties,
                                                               *_):
        node = Mock(primary_type="RadioNode")
        mock_run_cmd_on_emp_or_ms.return_value = Mock(stdout="No key match")
        self.assertRaises(EnvironError, self.auto._send_node_up, node)
        mock_global_properties.assert_called_with("svc_CM_vip_ipaddress")

    @patch('enmutils_int.lib.auto_provision.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.auto_provision.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.auto_provision.get_values_from_global_properties", return_value=["naming_service_ip"])
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.validate_response')
    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_emp_or_ms')
    def test_send_node_up__success_for_physical_cloud(self, mock_run_cmd_on_emp_or_ms, mock_validate, mock_log,
                                                      mock_global_properties, *_):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(stdout="Success")
        self.auto._send_node_up(node=Mock(primary_type="RadioNode"))
        self.assertEqual(mock_log.call_count, 2)
        mock_validate.assert_called_with(mock_run_cmd_on_emp_or_ms.return_value)
        mock_global_properties.assert_called_with("svc_CM_vip_ipaddress")

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.auto_provision.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.auto_provision.get_values_from_global_properties", return_value=["naming_service_ip"])
    @patch('enmutils_int.lib.auto_provision.AutoProvision.validate_response')
    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_emp_or_ms')
    def test_send_node_up__raises_environ_error_if_error(self, mock_run_cmd_on_emp_or_ms, mock_validate,
                                                         mock_global_properties, *_):
        node = Mock(primary_type="RadioNode")
        node_error = " ERROR: NodeSecurityUup failed with the following :sum []: null\n"
        mock_run_cmd_on_emp_or_ms.return_value = Mock(stdout=node_error)
        mock_validate.side_effect = EnvironError
        self.assertRaises(EnvironError, self.auto._send_node_up, node=node)
        mock_global_properties.assert_called_with("svc_CM_vip_ipaddress")

    @patch('enmutils_int.lib.auto_provision.deployment_info_helper_methods.get_cloud_native_service_vip')
    @patch('enmutils_int.lib.auto_provision.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.auto_provision.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.validate_response')
    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_cloud_native_pod')
    def test_node_up__success_for_cloud_native(self, mock_run_cmd_on_cn, mock_validate, mock_log, *_):
        response = mock_run_cmd_on_cn.return_value = Mock(stdout="Success")
        self.auto._send_node_up(node=Mock(primary_type="RadioNode"))
        self.assertEqual(mock_log.call_count, 2)
        mock_validate.assert_called_with(response)

    def test_check_response(self):
        class Temp(object):
            def __init__(self, msg_a=False):
                """
                Init method
                :param msg_a: Switch between defined results
                :type msg_a: bool
                """
                self.msg_a = msg_a

            def get_output(self):
                """
                Callable list

                :return: List to be assessed
                :rtype: list
                """
                if not self.msg_a:
                    return [u"10 instance(s)"]
                return [u'', u'Error 16002 : Node does not exist', u'Suggested Solution : Provide a valid node name']

        self.auto._check_response("error", Temp(), "error found")
        self.assertRaises(ScriptEngineResponseValidationError, self.auto._check_response, "error", Temp(msg_a=True),
                          "error found")

    @patch('enmutils_int.lib.auto_provision.AutoProvision._send_node_up')
    def test_integrate_node(self, mock_send_node_up):
        self.auto.integrate_node()
        self.auto.integrate_node(node=Mock())
        self.assertTrue(mock_send_node_up.called)

    @patch('enmutils_int.lib.auto_provision.shell.run_local_cmd')
    @patch('enmutils_int.lib.auto_provision.common_utils')
    @patch('enmutils_int.lib.auto_provision.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.delete_project')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.populate_nodes_on_enm')
    def test_teardown_success(self, mock_populate, mock_delete_pro, mock_ldap_is_configured, *_):
        self.auto._teardown()
        self.assertTrue(mock_populate.call_count, 1)
        self.assertTrue(mock_delete_pro.call_count, 1)
        self.assertTrue(mock_ldap_is_configured.call_count, 1)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.delete_project')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.populate_nodes_on_enm')
    @patch('enmutils_int.lib.auto_provision.check_ldap_is_configured_on_radio_nodes', side_effect=Exception)
    def test_teardown_raises_exception_when_error_encountered_with_ldap_configuration(self, *_):
        with self.assertRaises(EnmApplicationError):
            self.auto._teardown()

    @patch('enmutils_int.lib.auto_provision.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.populate_nodes_on_enm')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.delete_project', side_effect=Exception)
    @patch('enmutils_int.lib.auto_provision.shell.run_local_cmd', side_effect=Exception)
    def test_teardown_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, self.auto._teardown)

    @patch('enmutils_int.lib.auto_provision.time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision.AutoProvision._unmanage_delete_node')
    def test_delete_nodes_from_enm__deletes_by_node_name(self, mock_unmanage, _):
        user, response, response1 = Mock(), Mock(), Mock()
        response1.get_output.return_value = [u"1 instance(s)"]
        response.get_output.return_value = [u"0 instance(s)"]
        user.enm_execute.side_effect = [response, response1]
        self.auto.delete_nodes_from_enm(user, self.auto.nodes)
        self.assertEqual(1, mock_unmanage.call_count)

    @patch('enmutils_int.lib.auto_provision.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.auto_provision.AutoProvision._unmanage_delete_node')
    def test_delete_nodes_from_enm__retries_on_exception(self, mock_unmanage, _):
        user, response, response1 = Mock(), Mock(), Mock()
        response1.get_output.return_value = [u"1 instance(s)"]
        response.get_output.return_value = [u"0 instance(s)"]
        user.enm_execute.side_effect = [EnmApplicationError, response1, response]
        self.auto.delete_nodes_from_enm(user, self.auto.nodes)
        self.assertEqual(1, mock_unmanage.call_count)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.disable_supervision_and_delete_node')
    def test_unmanage_delete_node__success(self, mock_disable):
        self.auto._unmanage_delete_node(self.auto.nodes[0], Mock())
        self.assertEqual(1, mock_disable.call_count)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.disable_supervision_and_delete_node')
    def test_unmanage_delete_node__raises_enm_application_error(self, mock_disable):
        mock_disable.side_effect = Exception("error")
        self.assertRaises(EnmApplicationError, self.auto._unmanage_delete_node, self.auto.nodes[0], Mock())

    @patch('enmutils_int.lib.auto_provision.AutoProvision.create_and_supervise_node')
    def test_populate_nodes_on_enm__success(self, mock_create):
        self.auto.populate_nodes_on_enm()
        self.assertEqual(1, mock_create.call_count)

    @patch('enmutils_int.lib.auto_provision.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.create_and_supervise_node')
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    def test_populate_nodes_on_enm__logs_exception(self, mock_debug, mock_create, *_):
        mock_create.side_effect = Exception("error")
        self.auto.populate_nodes_on_enm()
        mock_debug.assert_called_with("Encountered exception with populate operation: error")

    @patch('enmutils_int.lib.auto_provision.AutoProvision.toggle_supervision')
    def test_disable_supervision_and_delete_node__calls_correct_commands(self, mock_disable):
        user = Mock()
        user.enm_execute.return_value.get_output.return_value = ["Success"]
        node = Mock(node_name="Node")
        self.auto.disable_supervision_and_delete_node(user, node)
        user.enm_execute.assert_any_call(DELETE_NRM_DATA_CMD.format(node_name=node.node_name))
        user.enm_execute.assert_called_with(DELETE_NE_CMD.format(node_name=node.node_name))
        self.assertEqual(2, user.enm_execute.call_count)
        self.assertEqual(1, mock_disable.call_count)

    @patch('enmutils_int.lib.auto_provision.ShmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.PmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.FmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.CmManagement.get_management_obj')
    def test_disable_supervision__disables_supervision_on_node(self, mock_cm, mock_fm, mock_pm, mock_shm):
        node, user = Mock(), Mock()
        self.auto.toggle_supervision(node, user, operation="unsupervise")
        self.assertEqual(1, mock_cm.return_value.unsupervise.call_count)
        self.assertEqual(1, mock_fm.return_value.unsupervise.call_count)
        self.assertEqual(1, mock_pm.return_value.unsupervise.call_count)
        self.assertEqual(1, mock_shm.return_value.unsupervise.call_count)

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.ShmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.PmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.FmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.CmManagement.get_management_obj')
    def test_disable_supervision__logs_failures(self, mock_cm, mock_fm, mock_pm, mock_shm, mock_debug):
        node, user, response = Mock(), Mock(), Mock()
        mock_cm.return_value.unsupervise.side_effect = ScriptEngineResponseValidationError("Cm Error",
                                                                                           response=response)
        mock_fm.return_value.unsupervise.side_effect = ScriptEngineResponseValidationError("Fm Error",
                                                                                           response=response)
        mock_pm.return_value.unsupervise.side_effect = ScriptEngineResponseValidationError("Pm Error",
                                                                                           response=response)
        mock_shm.return_value.unsupervise.side_effect = ScriptEngineResponseValidationError("Shm Error",
                                                                                            response=response)
        self.auto.toggle_supervision(node, user, operation="unsupervise")
        mock_debug.assert_any_call('Cm Error')
        mock_debug.assert_any_call('Pm Error')
        mock_debug.assert_any_call('Shm Error')
        mock_debug.assert_called_with('Fm Error')

    @patch('enmutils_int.lib.auto_provision.AutoProvision.toggle_supervision')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.poll_until_enm_can_retrieve_network_element')
    def test_create_and_supervise_node__calls_correct_commands(self, mock_supervise, *_):
        node = Mock(node_name="Node", node_id="Node1", node_ip="ip", primary_type="ERBS", secure_user="PmLdapEnabled",
                    secure_password="PmLdapEnabled01!")
        self.auto.create_and_supervise_node(node)
        self.auto.user.enm_execute.assert_any_call(CREATE_NE_CMD.format(node_name=node.node_name, node_id=node.node_id,
                                                                        primary_type=node.primary_type,
                                                                        oss_prefix=node.oss_prefix))
        self.auto.user.enm_execute.assert_any_call(CREATE_CONNECTIVITY_CMD.format(node_name=node.node_name,
                                                                                  node_ip=node.node_ip))
        self.auto.user.enm_execute.assert_any_call(CREATE_SECURITY_CMD.format(node_name=node.node_name,
                                                                              secure_user=node.secure_user,
                                                                              secure_password=node.secure_password))
        self.auto.user.enm_execute.assert_any_call(CREATE_SNMP_CMD.format(node_name=node.node_name))
        self.assertEqual(4, self.auto.user.enm_execute.call_count)
        self.assertEqual(1, mock_supervise.call_count)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.toggle_supervision')
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.poll_until_enm_can_retrieve_network_element',
           side_effect=EnmApplicationError("Error"))
    def test_create_and_supervise_node__logs_poll_exception(self, mock_supervise, mock_debug, *_):
        node = Mock(node_name="Node", node_id="Node1", node_ip="ip", primary_type="ERBS")
        self.auto.create_and_supervise_node(node)
        self.auto.user.enm_execute.assert_any_call(CREATE_NE_CMD.format(node_name=node.node_name, node_id=node.node_id,
                                                                        primary_type=node.primary_type,
                                                                        oss_prefix=node.oss_prefix))
        self.auto.user.enm_execute.assert_any_call(CREATE_CONNECTIVITY_CMD.format(node_name=node.node_name,
                                                                                  node_ip=node.node_ip))
        self.auto.user.enm_execute.assert_any_call(CREATE_SECURITY_CMD.format(node_name=node.node_name,
                                                                              secure_user=node.secure_user,
                                                                              secure_password=node.secure_password))
        self.auto.user.enm_execute.assert_any_call(CREATE_SNMP_CMD.format(node_name=node.node_name))
        self.assertEqual(4, self.auto.user.enm_execute.call_count)
        self.assertEqual(1, mock_supervise.call_count)
        mock_debug.assert_called_with("Failed to query ENM for NetworkElement value, error encountered: [Error]")

    @patch('enmutils_int.lib.auto_provision.ShmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.PmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.FmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.CmManagement.get_management_obj')
    def test_supervise__supervises_node(self, mock_cm, mock_fm, mock_pm, mock_shm):
        node = Mock()
        self.auto.toggle_supervision(node, self.auto.user)
        self.assertEqual(1, mock_cm.return_value.supervise.call_count)
        self.assertEqual(1, mock_fm.return_value.supervise.call_count)
        self.assertEqual(1, mock_pm.return_value.supervise.call_count)
        self.assertEqual(0, mock_shm.return_value.supervise.call_count)

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.PmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.FmManagement.get_management_obj')
    @patch('enmutils_int.lib.auto_provision.CmManagement.get_management_obj')
    def test_supervise__logs_failures(self, mock_cm, mock_fm, mock_pm, mock_debug):
        node, response = Mock(), Mock()
        mock_cm.return_value.supervise.side_effect = ScriptEngineResponseValidationError("Cm Error", response=response)
        mock_fm.return_value.supervise.side_effect = ScriptEngineResponseValidationError("Fm Error", response=response)
        mock_pm.return_value.supervise.side_effect = ScriptEngineResponseValidationError("Pm Error", response=response)
        self.auto.toggle_supervision(node, self.auto.user)
        mock_debug.assert_any_call('Cm Error')
        mock_debug.assert_any_call('Pm Error')
        mock_debug.assert_called_with('Fm Error')

    @patch('enmutils_int.lib.auto_provision.time.sleep', return_value=lambda _: None)
    def test_poll_until_enm_can_retrieve_network_element__retrys_if_failure(self, _):
        node, response = Mock(), Mock()
        node.node_id = "1234"
        response.get_output.side_effect = [Exception("Error"), "0 instance(s)", "1 instance(s)"]
        self.auto.user.enm_execute.return_value = response
        self.auto.poll_until_enm_can_retrieve_network_element(node)
        self.assertEqual(3, self.auto.user.enm_execute.call_count)


class AutoProvisionProjectUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="auto_test_user")
        self.name = "AutoProvisionUnitTestProject"
        self.node = Mock()
        self.node.node_id = "unitNode"
        self.node.mim_version = "17A"
        self.node.primary_type = "RadioNode"
        self.node.ip = generate_configurable_ip()
        self.node_fake_pico = Mock()
        self.node_fake_pico.node_id = "unitNode"
        self.node_fake_pico.mim_version = "17A"
        self.node_fake_pico.primary_type = "RadioNode"
        self.node_fake_pico.ip = generate_configurable_ip()
        self.project = Project(name=self.name, user=self.user, nodes=[self.node, self.node_fake_pico])
        internal_data = pkgutil.get_loader('enmutils_int')
        file_path = unipath.Path(internal_data.filename)
        self.path_to_project = "/tmp/{0}".format(self.name)
        self.path = os.path.join(file_path, "etc", "data", "{0}.zip".format(self.name))
        self.path_to_node_up = "/tmp/node-discovery-test-client"
        self.path_to_licence = "/tmp/LicenseKeyFiles/{0}_fp-9000.zip".format(self.node.node_name)
        self.node_files = ['radio_nodeInfo.xml', 'radio_siteInstallation.xml', 'radio_siteBasic.xml',
                           'radio_siteEquipment.xml', 'Optional-feature-file.xml', 'Unlock-cells-file.xml']
        if not filesystem.does_dir_exist('/tmp/LicenseKeyFiles'):
            _, _ = commands.getstatusoutput('mkdir /tmp/LicenseKeyFiles')

    def tearDown(self):
        unit_test_utils.tear_down()
        if filesystem.does_dir_exist(self.path_to_project):
            self.project.delete_directory_structure()
        if filesystem.does_dir_exist(self.path_to_node_up):
            _, _ = commands.getstatusoutput('rm -rf {0}'.format(self.path_to_node_up))
        if filesystem.does_file_exist(self.path):
            _, _ = commands.getstatusoutput('rm -rf {0}'.format(self.path))

    @patch("enmutils_int.lib.auto_provision_project.shell")
    @patch("enmutils_int.lib.auto_provision_project.raise_invalid_project")
    @patch("enmutils_int.lib.auto_provision_project.filesystem")
    def test_teardown__calls_raise_invalid_project_when_archive_exists(self, mock_filesystem, mock_raise, _):
        mock_filesystem.does_file_exist.return_value = True
        self.project._teardown()
        self.assertTrue(mock_raise.called)

    @patch("enmutils_int.lib.auto_provision_project.shell")
    @patch("enmutils_int.lib.auto_provision_project.raise_invalid_project")
    @patch("enmutils_int.lib.auto_provision_project.filesystem")
    def test_teardown__does_not_call_raise_invalid_project_when_archive_does_not_exist(self, mock_filesystem,
                                                                                       mock_raise, _):
        mock_filesystem.does_file_exist.return_value = False
        self.project._teardown()
        self.assertFalse(mock_raise.called)

    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    def test_prepare_project_info_xml_file(self, mock_builtin_open, *_):
        self.project._prepare_project_info_xml_file()
        self.assertTrue(mock_builtin_open.called)

    def test_update_subnetwork_name__when_split_length_more_than_one(self):
        subnetwork = "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW"
        self.project.nodes = [Mock(subnetwork=subnetwork, primary_type="MSRBS_V1")]
        test_res = self.project.update_subnetwork_name(self.project.nodes[0])
        self.assertEqual(test_res, "Europe,SubNetwork=Ireland,SubNetwork=NETSimW")

    def test_update_subnetwork_name__when_split_length_less_than_two(self):
        subnetwork = "SubnNetwork=1"
        self.project.nodes = [Mock(subnetwork=subnetwork, primary_type="RadioNode")]
        test_res = self.project.update_subnetwork_name(self.project.nodes[0])
        self.assertEqual(test_res, "SubnNetwork=1")

    @patch('enmutils_int.lib.auto_provision_project.arguments.get_random_string')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.auto_provision_project.Project.update_subnetwork_name')
    @patch('enmutils_int.lib.auto_provision_project.Project.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_provision_project.Project.get_model_id')
    def test_prepare_node_xml_files__success_for_radionode(self, mock_get_model_id, *_):
        mock_get_model_id.return_value = '111-222-333'
        self.project._prepare_node_xml_files()

    @patch('enmutils_int.lib.auto_provision_project.arguments.get_random_string')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.auto_provision_project.Project.update_template_with_node_details')
    @patch('enmutils_int.lib.auto_provision_project.Project.update_subnetwork_name')
    @patch('enmutils_int.lib.auto_provision_project.Project.__init__', return_value=None)
    @patch('enmutils_int.lib.auto_provision_project.Project.get_model_id')
    def test_prepare_node_xml_files__success_for_msrbs(self, mock_get_model_id, *_):
        mock_get_model_id.return_value = '111-222-333'
        self.project._prepare_node_xml_files()

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_dir_exist', side_effect=[False, True])
    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    def test_create_directory_structure(self, mock_delete_directory_structure, *_):
        self.project._create_directory_structure()
        self.assertFalse(mock_delete_directory_structure.called)
        self.project._create_directory_structure()
        self.assertTrue(mock_delete_directory_structure.called)

    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd', return_value=True)
    def test_delete_directory_structure_is_success(self, *_):
        self.project.delete_directory_structure()

    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.auto_provision_project.shutil.make_archive')
    @patch('enmutils_int.lib.auto_provision_project.raise_invalid_project')
    def test_create_archive_is_success(self, mock_raise_invalid_project, *_):
        self.project._create_archive()
        self.assertTrue(mock_raise_invalid_project.called)

    def test_raise_invalid_project(self):
        self.assertRaises(InvalidProjectException, raise_invalid_project, False, "ProjectValidationFailed")

    def test_get_node_secure_username_and_password(self):
        response = Mock()
        response.get_output.return_value = [u'Node\tUser Name\tUser Password',
                                            u'unitNode\tsecureUserName:netsim\tsecureUserPassword:netsim',
                                            u'unitNode\tnodeCliUserName:Not Configured\tnodeCliUserPassword:Not Configured',
                                            u'Command Executed Successfully']
        self.user.enm_execute.return_value = response
        self.assertEqual(self.project.get_node_secure_username_and_password(self.node), ("netsim", "netsim"))

    def test_get_node_secure_username_and_password__not__found(self):
        response = Mock()
        response.get_output.return_value = [u'Node\tUser Name\tUser Password',
                                            u'unitNode\tnodeCliUserName:Not Configured\tnodeCliUserPassword:Not Configured',
                                            u'Command Executed Successfully']
        self.user.enm_execute.return_value = response
        self.assertEqual(self.project.get_node_secure_username_and_password(self.node), None)

    def test_get_node_secure_username_and_password_raises_exception(self):
        response = Mock()
        response.get_output.return_value = [u'Node\tUser Name\tUser Password',
                                            u'Error']
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.project.get_node_secure_username_and_password, self.node)

    def test_get_model_identity(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.300\t18.Q2-J.1.300']
        self.user.enm_execute.return_value = response
        self.node.mim_version = "J.1.300"
        self.assertEqual(self.project.get_model_id(self.node), "18.Q2-J.1.300")

    def test_get_model_identity_default(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.300\t18.Q2-J.1.300']
        self.user.enm_execute.return_value = response
        self.node.mim_version = "J.1.400"
        self.assertEqual(self.project.get_model_id(self.node), "18.Q2-J.1.300")

    def test_get_model_identity_raises_exception(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200',
                                            u'ERBS\t18.Q1\t-\tERBS_NODE_MODEL\tJ.1.300\t18.Q2-J.1.300']
        self.user.enm_execute.return_value = response
        self.node.mim_version = "J.1.400"
        self.assertRaises(EnmApplicationError, self.project.get_model_id, self.node)

    def test_get_model_identity_raises_enm_application_error(self):
        response = Mock()
        response.get_output.return_value = u'Error '
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.project.get_model_id, self.node)

    def test_get_model_identity_returns_first_model_id_if_no_match(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200']
        self.user.enm_execute.return_value = response
        self.assertEqual(self.project.get_model_id(self.node), '18.Q1-J.1.200')

    def test_update_credentials_on_node(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200']
        self.user.enm_execute.return_value = response
        self.assertEqual(self.project.get_model_id(self.node), '18.Q1-J.1.200')

    def test_get_model_identity_returns_first_model_id_if_no_node_mim_version(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18.Q1\t-\t-\tERBS_NODE_MODEL\tJ.1.200\t18.Q1-J.1.200']
        self.user.enm_execute.return_value = response
        self.node.mim_version = ""
        self.assertEqual(self.project.get_model_id(self.node), '18.Q1-J.1.200')

    def test_get_model_identity_matches_mim_version(self):
        response = Mock()
        response.get_output.return_value = [u'Ne Type\tNe Release\tProduct Identity\tRevision (R-State)\tFunctional '
                                            u'MIM Name\tFunctional MIM Version\tModel ID',
                                            u'ERBS\t18A\t-\t-\tERBS_NODE_MODEL\tJ.1.200\t17.Q1-J.1.200']
        self.user.enm_execute.return_value = response
        self.assertEqual(self.project.get_model_id(self.node), '17.Q1-J.1.200')

    @patch('enmutils_int.lib.auto_provision_project.Project.run_command_and_check_response')
    def test_make_dir_executable__if_ecim(self, mock_run_command):
        test_client_files = ['ecim', 'node-up', 'test1', 'test2']
        self.project.make_dir_executable(test_client_files)
        self.assertTrue(mock_run_command.called)

    @patch('enmutils_int.lib.auto_provision_project.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.shell.copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native')
    def test_copy_test_client_files_to_pod__success(self, mock_get_pod, mock_copy, mock_log):
        mock_copy.return_value = Mock(rc=0)
        mock_get_pod.return_value = [unit_test_utils.generate_configurable_ip(),
                                     unit_test_utils.generate_configurable_ip()]
        self.project.copy_test_client_files_to_pod('node-test-client')
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.auto_provision_project.shell.copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native')
    def test_copy_test_client_files_to_pod__raises_error(self, mock_get_pod, mock_copy):
        mock_copy.return_value = Mock(rc=1)
        mock_get_pod.return_value = [unit_test_utils.generate_configurable_ip(),
                                     unit_test_utils.generate_configurable_ip()]
        self.assertRaises(EnvironError, self.project.copy_test_client_files_to_pod, 'node-test-client')

    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.auto_provision_project.Project.run_command_and_check_response')
    @patch('enmutils_int.lib.auto_provision_project.Project.make_dir_executable')
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.log.logger.debug')
    def test_unzip_test_client_files__success(self, *_):
        ap_dir = '/tmp'
        client = ['/tmp/node-discovery-test-client', 'node-up.zip', '/tmp/node-discovery-test-client/bin/sh/unsecure/',
                  'nodeup-unsecure.sh']
        self.project.unzip_test_client_files(ap_dir, client)

    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native', return_value=['abc', 'bca'])
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up_for_cloud_native')
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    def test_import_node_up__success_for_cn_if_files_exists(self, mock_install_unzip, *_):
        self.project.import_node_up()
        self.assertEqual(mock_install_unzip.call_count, 1)

    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native', return_value=['abc', 'bca'])
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up_for_cloud_native')
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    def test_import_node_up__success_for_cn_if_files_doesnot_exists(self, mock_install_unzip, *_):
        self.project.import_node_up()
        self.assertEqual(mock_install_unzip.call_count, 1)

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=False)
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.copy_test_client_files_to_pod')
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.is_host_physical_deployment', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.is_emp', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd')
    def test_node_up_import__physical(self, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.side_effect = [response for _ in range(8)]
        self.project.import_node_up()

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=False)
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.is_host_physical_deployment', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.is_emp', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd')
    def test_node_up_import__emp(self, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.side_effect = [response for _ in range(8)]
        self.project.import_node_up()

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    def test_node_up_does_not_run_if_file_exists_for_physical_and_emp(self, mock_install_unzip, *_):
        self.project.import_node_up()
        self.assertEqual(mock_install_unzip.call_count, 1)

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils.install_unzip')
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.is_host_physical_deployment', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    @patch('enmutils_int.lib.auto_provision_project.is_emp', return_value=False)
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd')
    def test_node_up_import__else(self, mock_run_local_cmd, mock_log, *_):
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.side_effect = [response for _ in range(6)]
        self.project.import_node_up()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    @patch('enmutils_int.lib.auto_provision_project.is_host_physical_deployment', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.is_emp', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.shell.run_local_cmd')
    def test_node_up_import__raises_environ_error(self, mock_run_local_cmd, *_):
        response = Mock()
        response.rc = 1
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, self.project.import_node_up)

    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.SHMUtils')
    def test_import_node_up__shmutils_raises_exception(self, mock_unzip, *_):
        mock_unzip.return_value.install_unzip.side_effect = [ShellCommandReturnedNonZero]
        self.project.import_node_up()

    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native', return_value=['abc', 'bca'])
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.copy_test_client_files_to_pod')
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exists_on_cloud_native_pod',
           return_value=False)
    def test_import_node_up_cloud_native__success_if_files_does_not_exists(self, *_):
        ap_dir = '/tmp'
        clients = {
            'cpp': ['{}/node-discovery-test-client'.format(ap_dir), 'node-up.zip',
                    '{}/node-discovery-test-client/bin/sh/unsecure/'.format(ap_dir), 'nodeup-unsecure.sh'],

            'ecim': ['{}/node-discovery-ecim-test-client'.format(ap_dir), 'ecim-node-up.zip',
                     '{}/node-discovery-ecim-test-client/bin/sh/'.format(ap_dir), 'ecim-node-up.sh']
        }
        self.project.import_node_up_for_cloud_native(ap_dir=ap_dir, clients=clients)

    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native', return_value=['abc', 'bca'])
    @patch('enmutils_int.lib.auto_provision_project.Project.unzip_test_client_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.copy_test_client_files_to_pod')
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exists_on_cloud_native_pod', return_value=True)
    def test_import_node_up_cloud_native__success_if_files_exists(self, *_):
        ap_dir = '/tmp'
        clients = {
            'cpp': ['{}/node-discovery-test-client'.format(ap_dir), 'node-up.zip',
                    '{}/node-discovery-test-client/bin/sh/unsecure/'.format(ap_dir), 'nodeup-unsecure.sh'],

            'ecim': ['{}/node-discovery-ecim-test-client'.format(ap_dir), 'ecim-node-up.zip',
                     '{}/node-discovery-ecim-test-client/bin/sh/'.format(ap_dir), 'ecim-node-up.sh']
        }
        self.project.import_node_up_for_cloud_native(ap_dir=ap_dir, clients=clients)

    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages",
           return_value=[None, None, None])
    @patch("enmutils_int.lib.auto_provision_project.log.logger.debug")
    def test_install_software_packages_success(self, mock_log, mock_get, *_):
        response = Mock()
        response.get_output.return_value = "already imported"
        self.user.enm_execute.return_value = response
        self.project._install_software_packages()
        mock_get.assert_called_with(filter_text='R69C29', user=self.user)
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.get_all_software_packages",
           return_value=[None, None, None])
    @patch("enmutils_int.lib.auto_provision_project.log.logger.debug")
    def test_install_software_packages_raises_validation_error(self, *_):
        response = Mock()
        response.get_output.return_value = "ERROR"
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.project._install_software_packages)

    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch("enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages",
           return_value=[None, None, None])
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.auto_provision_project.log.logger.debug")
    def test_install_software_packages__raises_validation_error_for_invalid_file(self, *_):
        response = Mock()
        response.get_output.return_value = "Please Import a file"
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.project._install_software_packages)

    @patch('enmutils_int.lib.auto_provision_project.create_ap_pkg_directory', return_value="/home/enmutils/ap")
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.get_all_software_packages",
           return_value=[None, None, None])
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.auto_provision_project.log.logger.debug")
    def test_install_software_packages_no_response(self, mock_log, *_):
        response = Mock()
        response.get_output.return_value = ""
        self.user.enm_execute.return_value = response
        self.project._install_software_packages()
        self.assertEqual(mock_log.call_count, 2)

    def test_install_software_packages_raises_index_error(self):
        self.project.nodes = []
        self.assertRaises(IndexError, self.project._install_software_packages)

    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.get_all_software_packages",
           return_value=['CXP9024418_15-R69C29'])
    @patch("enmutils_int.lib.auto_provision_project.log.logger.debug")
    def test_install_software_packages_no_package(self, mock_log, mock_get, *_):
        self.project._install_software_packages()
        self.assertEqual(mock_log.call_count, 2)
        mock_get.assert_called_with(filter_text='R69C29', user=self.user)

    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project._install_software_packages')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    def test_create_project(self, *_):
        self.project.create_project()

    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision.shell.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exists_on_cloud_native_pod',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.auto_provision_project.get_pod_hostnames_in_cloud_native')
    def test_delete_copied_scripts_from_pod__success(self, mock_hostnames, mock_does_file_exists, mock_run, mock_log):
        pod_name = 'apserv'
        response1 = Mock()
        response1.rc = 1
        response = Mock()
        response.rc = 0
        mock_hostnames.return_value = ["apserv1", "apserv2", "apserv3"]
        mock_run.side_effect = [response, response1]
        file_path = "/tmp/"
        file_name = "ecim_node_up.sh"
        cmd = "rm /tmp/ecim_node_up.sh"
        self.project.delete_copied_scripts_from_pod(cmd, file_path, file_name)
        self.assertEqual(mock_does_file_exists.call_count, len(mock_hostnames.return_value))
        self.assertTrue(mock_run.mock_calls == [call(pod_name, mock_hostnames.return_value[0], cmd),
                                                call(pod_name, mock_hostnames.return_value[1], cmd)])
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', side_effect=[True, True])
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.shell.run_cmd_on_emp_or_ms')
    def test_delete_scripts_copied_remote_host__success(self, mock_run_cmd, mock_log, *_):
        response1 = Mock()
        response1.rc = 1
        response = Mock()
        response.rc = 0
        mock_run_cmd.side_effect = [response, response1]
        self.project.delete_scripts_copied_remote_host()
        self.assertEqual(mock_log.call_count, 3)

    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', side_effect=[True, False])
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.shell.run_cmd_on_emp_or_ms')
    def test_delete_scripts_copied_remote_host__file_does_not_exist(self, mock_run_cmd, mock_log, *_):
        response = Mock()
        response.rc = 0
        mock_run_cmd.side_effect = [response]
        self.project.delete_scripts_copied_remote_host()
        self.assertEqual(mock_log.call_count, 2)

    @patch('enmutils_int.lib.auto_provision_project.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.auto_provision_project.filesystem.does_file_exist_on_ms', side_effect=[True, True])
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_copied_scripts_from_pod')
    @patch('enmutils_int.lib.auto_provision.log.logger.debug')
    @patch('enmutils_int.lib.auto_provision_project.shell.run_cmd_on_emp_or_ms')
    def test_delete_scripts_copied_remote_host__if_cloud_native(self, mock_run_cmd, mock_log, mock_delete, *_):
        self.project.delete_scripts_copied_remote_host()
        self.assertFalse(mock_run_cmd.called)
        self.assertTrue(mock_delete.called)
        self.assertEqual(mock_log.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
