#!/usr/bin/env python
from datetime import datetime

import unittest2
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnmApplicationError, ScriptEngineResponseValidationError, EnvironError
from enmutils_int.lib.auto_provision import AutoProvision
from enmutils_int.lib.auto_provision_project import Project
from enmutils_int.lib.load_node import ERBSLoadNode
from enmutils_int.lib.profile_flows.ap_flows.ap_flow import (ApFlow, ApSetupFlow, Ap01Flow, Ap11Flow, Ap12Flow,
                                                             Ap13Flow, Ap14Flow, Ap15Flow, Ap16Flow, ApSetupRadioNode,
                                                             verify_nodes_on_enm)
from enmutils_int.lib.workload import ap_01, ap_11, ap_12, ap_13, ap_14, ap_15, ap_16, ap_setup
from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class ApFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_flow")
        unit_test_utils.setup()
        self.flow = ApFlow()
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34')]
        self.exception = Exception("Some Exception")
        self.auto = AutoProvision(user=self.user, project_name="Test", nodes=self.nodes_list)
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["admin"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.sleep')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_auto_provision_instances')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_profile_users')
    def test_execute_flow(self, *_):
        self.flow.execute_flow()

    def test_create_auto_provision_instances(self):
        self.flow.create_auto_provision_instances([Mock()])
        self.assertTrue(isinstance(self.flow.objects_list[0], AutoProvision))

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_download_artifact_logs_exceptions(self, enm_execute_mock, mock_add_exception):
        response = Mock()
        response.get_output.return_value = "ERROR"
        enm_execute_mock.return_value = response
        self.flow.download_artifact(self.auto)
        self.assertTrue(mock_add_exception.called)


class ApSetupFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_setup_flow")
        unit_test_utils.setup()
        self.ap_setup = ap_setup.AP_SETUP()
        self.flow = ApSetupFlow()
        self.flow.NUM_USERS, self.flow.USER_ROLES = 1, ["SomeRole"]
        self.flow.LOG_AFTER_COMPLETED = False

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.execute_flow')
    def test_run__in_ap_setup_is_successful(self, mock_execute_flow):
        self.ap_setup.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.delete_setup_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.import_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.create_project', side_effect=Exception("Exception"))
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_profile_users')
    def test_execute_flow__adds_exception(self, mock_create_users, mock_add_error_as_exception, *_):
        mock_create_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.time', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.import_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.create_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', return_value=False)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.delete_setup_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_profile_users')
    def test_execute_flow__success(self, mock_create_users, mock_scp, mock_delete, *_):
        mock_create_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertEqual(1, mock_scp.call_count)
        self.assertEqual(2, mock_delete.call_count)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', return_value=True)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApSetupFlow.delete_setup_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.create_profile_users')
    def test_execute_flow__project_exists(self, mock_create_users, mock_delete, *_):
        mock_create_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertEqual(0, mock_delete.call_count)

    def test_delete_setup_nodes__no_polling(self):
        user, auto, nodes = Mock(), Mock(), [Mock()]
        self.flow.delete_setup_nodes(user, auto, nodes, poll=False)
        self.assertEqual(0, auto.poll_until_enm_can_retrieve_network_element.call_count)
        self.assertEqual(1, auto.disable_supervision_and_delete_node.call_count)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.log.logger.debug')
    def test_delete_setup_nodes__logs_exception(self, mock_debug):
        user, auto, nodes = Mock(), Mock(), [Mock()]
        auto.poll_until_enm_can_retrieve_network_element.side_effect = Exception("Error")
        self.flow.delete_setup_nodes(user, auto, nodes)
        self.assertEqual(1, auto.poll_until_enm_can_retrieve_network_element.call_count)
        self.assertEqual(0, auto.disable_supervision_and_delete_node.call_count)
        mock_debug.assert_called_with("Issue encountered attempting to delete setup nodes: Error")


class Ap01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_01_flow")
        unit_test_utils.setup()
        self.ap_01 = ap_01.AP_01()
        self.flow = Ap01Flow()
        self.flow.PROJECT_NAME = "NothingToSeeHere"
        node, node1, rnode = Mock(), Mock(), Mock()
        node.id, node1.id, rnode.id = "LTE01", "LTE02", "LTE03"
        node.primary_type, node1.primary_type, rnode.primary_type = "RadioNode", "RadioNode", "RadioNode"
        node.model_identity, node1.model_identity, rnode.model_identity = "1-2-33", "1-2-34", "1-2-33"
        node.node_id, node1.node_id = "LTE01", "LTE02"
        node.node_ip, node1.node_ip = [generate_configurable_ip(), generate_configurable_ip(ipversion=6)]
        node.node_name, node1.node_name = "LTE45dg2ERBS00069", "LTE45dg2ERBS00070"
        self.nodes_list = [node, node1]
        self.flow.NUM_USERS, self.flow.USER_ROLES = 1, ["SomeRole"]
        self.now = datetime.now()
        self.flow.SCHEDULED_TIMES = [datetime(self.now.year, self.now.month, self.now.day, 10, 0, 0),
                                     datetime(self.now.year, self.now.month, self.now.day, 15, 0, 0)]
        self.exception = Exception("Some Exception")
        self.flow.auto = AutoProvision(user=self.user, project_name="Test", nodes=self.nodes_list)
        self.project = Project(name="Test", nodes=self.nodes_list, user=self.user)
        self.radio_project = Project(name="Test", nodes=[rnode], user=self.user)
        self.no_nodes_project = Project(name="no_nodes", nodes=[], user=self.user)
        self.flow.MAX_NODES = 1
        self.flow.NUM_ITERATIONS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.execute_flow')
    def test_run__in_ap_01_is_successful(self, mock_execute_flow):
        self.ap_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages',
           side_effect=["PKGA", "PKGB", "PKGC", "PKGD"])
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    def test_create_project_end_to_end_raises_invalid_project_no_condition(self, mock_project, mock_nodes, *_):
        mock_project.return_value = self.no_nodes_project
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(None, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project._install_software_packages')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_project_end_to_end_success(self, mock_user, mock_project, mock_nodes, mock_package, *_):
        package = Mock()
        package.name = "PKGA"
        mock_package.return_value = package
        mock_project.return_value = self.radio_project
        response = Mock()
        response.get_output.return_value = [u'test_output']
        mock_user.return_value = response
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(self.nodes_list, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages',
           side_effect=["CXP9024418_15-R69C29", "PKGB", "PKGC", "PKGD"])
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_project_end_to_end_skips_software_install(self, mock_user, mock_project, mock_nodes, mock_package,
                                                              *_):
        package = Mock()
        package.name = "PKGE"
        mock_package.return_value = package
        mock_project.return_value = self.radio_project
        response = Mock()
        response.get_output.return_value = [u'test_output']
        mock_user.return_value = response
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(self.nodes_list, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages',
           side_effect=["PKGA", "PKGB", "PKGC", "PKGD"])
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_project_end_to_end_responses_already_imported(self, mock_user, mock_project,
                                                                  mock_nodes, mock_package, *_):
        package = Mock()
        package.name = "PKGE"
        mock_package.return_value = package
        mock_project.return_value = self.radio_project
        response = Mock()
        response.get_output.return_value = [u'already imported package']
        mock_user.return_value = response
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(self.nodes_list, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages',
           side_effect=["PKGA", "PKGB", "PKGC", "PKGD"])
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_project_end_to_end_handles_scriptengine_validation_error(self, mock_user, mock_project, mock_nodes,
                                                                             mock_package, *_):
        package = Mock()
        package.name = "PKGE"
        mock_package.return_value = package
        mock_project.return_value = self.radio_project
        response = Mock()
        response.get_output.return_value = [u'ERROR in importing package']
        mock_user.return_value = response
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(self.nodes_list, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.Project.import_node_up')
    @patch('enmutils_int.lib.auto_provision_project.Project._create_archive')
    @patch('enmutils_int.lib.auto_provision_project.Project.delete_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.SoftwareOperations.get_all_software_packages',
           side_effect=["PKGA", "PKGB", "PKGC", "PKGD"])
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch('enmutils_int.lib.auto_provision_project.SoftwarePackage')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    def test_create_project_end_to_end_continues_for_unmatches_response(self, mock_user, mock_project, mock_nodes,
                                                                        mock_package, *_):
        package = Mock()
        package.name = "PKGE"
        mock_package.return_value = package
        mock_project.return_value = self.radio_project
        response = Mock()
        response.get_output.return_value = [u'no response']
        mock_user.return_value = response
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.create_project(self.nodes_list, self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.auto_provision_project.Project._create_directory_structure')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_project_info_xml_file')
    @patch('enmutils_int.lib.auto_provision_project.Project._prepare_node_xml_files')
    @patch('enmutils_int.lib.auto_provision_project.get_internal_file_path_for_import', return_value=Mock())
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.add_error_as_exception')
    def test_create_project_end_to_end_handles_IndexError(self, mock_error, mock_project, mock_nodes, *_):
        mock_project.return_value = self.no_nodes_project
        response = Mock()
        response.get_output.return_value = [u'test_output']
        mock_nodes.side_effect = []
        self.flow.create_project([], self.user)
        self.assertTrue(mock_error.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.create_project')
    def test_create_project_logs_exceptions(self, mock_project, mock_add_exception, *_):
        mock_project.side_effect = [self.exception, 'Something']
        self.flow.create_project(0, user=self.user)
        self.assertTrue(mock_add_exception.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.create_project')
    def test_create_project_handles_empty_iterator(self, mock_project, mock_add_exception, *_):
        mock_project.side_effect = [self.exception, 'Something']
        self.flow.create_project(1, user=self.user)
        self.assertTrue(mock_add_exception.called)

    @patch('time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.delete_nodes_from_enm')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils.lib.log.logger.debug')
    def test_delete_project_nodes_logs_exceptions(self, mock_debug, mock_add_exception, mock_delete_nodes, *_):
        mock_delete_nodes.side_effect = [self.exception, None]
        self.flow.delete_project_nodes(self.nodes_list, user=self.user)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.delete_project')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_delete_project_continues_with_exceptions(self, mock_add_exception, mock_delete_project, *_):
        mock_delete_project.side_effect = [self.exception, None, self.exception, None]
        self.flow.delete_project(self.flow.auto)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', side_effect=[True, False, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.delete_project')
    def test_delete_project__project_does_not_exist(self, mock_delete_project, _):
        mock_delete_project.return_value = None
        self.flow.delete_project(self.flow.auto)
        self.assertEqual(2, mock_delete_project.call_count)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.delete_project', return_value=None)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.persist')
    def test_delete_project__removes_from_teardown_list(self, mock_persist, *_):
        self.flow.teardown_list.append(self.flow.auto)
        self.flow.delete_project(self.flow.auto)
        self.assertEqual(0, len(self.flow.teardown_list))
        self.assertEqual(1, mock_persist.call_count)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists', side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.delete_project', return_value=None)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.persist')
    def test_delete_project__project_not_in_teardown(self, mock_persist, *_):
        self.flow.delete_project(self.flow.auto)
        self.assertEqual(0, mock_persist.call_count)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists',
           side_effect=[True, False, True])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.import_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    def test_import_auto_provision_project_continues_with_errors(self, mock_delete_project, mock_import_project,
                                                                 mock_add_error, *_):
        mock_import_project.side_effect = [self.exception, None]
        self.flow.import_auto_provision_project(self.flow.auto)
        self.assertTrue(mock_delete_project.call_count is 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists',
           side_effect=[False, True])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    def test_import_auto_provision_project_skips(self, mock_delete_project, *_):
        self.flow.import_auto_provision_project(self.flow.auto)
        self.assertFalse(mock_delete_project.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists',
           side_effect=[False for _ in xrange(0, 16)])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.import_project')
    def test_import_auto_provision_project_continues_with_retries(self, *_):
        self.assertRaises(EnmApplicationError, self.flow.import_auto_provision_project, self.flow.auto)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.persist')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_model_id')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_node_secure_username_and_password', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_auto_provisioning_project')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_users')
    def test_execute_flow__success(self, mock_user, mock_nodes, mock_create, mock_ldap, *_):
        mock_user.return_value = [self.user]
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list,
                                  self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list, self.nodes_list]
        self.flow.execute_flow()
        self.assertTrue(mock_ldap.called)
        mock_create.assert_called_with(self.nodes_list)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_auto_provisioning_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.get_nodes_list_by_attribute")
    def test_execute_flow__ldap_adds_error_on_exception(self, mock_nodes, mock_add_error_as_exception,
                                                        mock_ldap, *_):
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list]
        mock_ldap.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_auto_provisioning_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_model_id')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.get_nodes_list_by_attribute")
    def test_execute_flow__get_model_id_adds_error_on_exception(self, mock_nodes, mock_model_id,
                                                                mock_add_error_as_exception, *_):
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list]
        mock_model_id.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_auto_provisioning_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_model_id')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_node_secure_username_and_password')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.get_nodes_list_by_attribute")
    def test_execute_flow__get_node_secure_username_and_password_adds_error_on_exception(self, mock_nodes,
                                                                                         mock_get_node_creds,
                                                                                         mock_add_error_as_exception,
                                                                                         *_):
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list]
        mock_get_node_creds.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.scp_upgrade_packages')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_model_id')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project.get_node_secure_username_and_password',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_auto_provisioning_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.ap_flows.ap_flow.ApFlow.get_nodes_list_by_attribute")
    def test_execute_flow__create_project_adds_error_on_exception(self, mock_nodes, mock_add_error_as_exception,
                                                                  mock_create, *_):
        mock_nodes.side_effect = [self.nodes_list, self.nodes_list]
        mock_create.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.call_count, 1)

    @patch('time.sleep')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.handle_node_integration_failure')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.auto_provisioning_project_setup')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.node_up_task')
    def test_create_auto_provisioning_project__executes_correct_number_of_iterations(
            self, mock_node_up_task, mock_update_nodes_with_poid_info, mock_status, *_):
        self.flow.NUM_ITERATIONS = 10
        mock_status.inprogress = [u'Project Name\tNode Quantity\tIn '
                                  u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                  u'ap_01_workload\t2\t2\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                                  u'LTE45dg2ERBS00069\tIn Progress\tIntegration Completed', u'', u'', u'']
        mock_status.successfull = [u'Project Name\tNode Quantity\tIn '
                                   u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                   u'ap_01_workload\t2\t0\t0\t2\t0\t0', u'Node Name\tStatus\tState',
                                   u'LTE45dg2ERBS00069\tIn Progress\tIntegration Completed', u'', u'', u'']
        mock_status.side_effect = [mock_status.inprogress, mock_status.successfull] * self.flow.NUM_ITERATIONS
        self.flow.create_auto_provisioning_project(self.nodes_list)
        self.assertEqual(mock_node_up_task.call_count, len(self.nodes_list) * self.flow.NUM_ITERATIONS)
        self.assertEqual(mock_update_nodes_with_poid_info.call_count, self.flow.NUM_ITERATIONS)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.handle_node_integration_failure')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.auto_provisioning_project_setup')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.node_up_task')
    def test_create_auto_provisioning_project__success(
            self, mock_node_up_task, mock_setup, mock_delete, mock_update_nodes_with_poid_info, mock_status, *_):
        flow = Ap01Flow()
        nodes = [Mock()]
        auto = Mock(nodes=nodes)
        flow.NUM_ITERATIONS = 1
        flow.auto = auto
        auto.status.side_effect = [[u'Project Name\tNode Quantity\tIn '
                                    u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                    u'ap_01_workload\t2\t2\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                                    u'LTE45dg2ERBS00069\tIn Progress\tIntegration Started', u'', u'', u''],
                                   [u'Project Name\tNode Quantity\tIn '
                                    u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                    u'ap_01_workload\t2\t0\t0\t2\t0\t0', u'Node Name\tStatus\tState',
                                    u'LTE45dg2ERBS00069\tIn Progress\tIntegration Completed', u'', u'', u'']]
        flow.create_auto_provisioning_project(self.nodes_list)
        mock_setup.assert_called_with(self.nodes_list)
        self.assertTrue(mock_node_up_task.mock_calls == [call(nodes[0])])
        mock_setup.assert_called_with(self.nodes_list)
        mock_delete.assert_called_with(auto)
        self.assertEqual(mock_update_nodes_with_poid_info.call_count, 1)

    @patch('time.sleep')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.handle_node_integration_failure')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.node_up_task')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.auto_provisioning_project_setup')
    def test_create_auto_provisioning_project__adds_error_on_exception(
            self, mock_setup, mock_add_error_as_exception, mock_update_nodes_with_poid_info, *_):
        mock_setup.side_effect = Exception
        self.flow.create_auto_provisioning_project(self.nodes_list)
        self.assertTrue(mock_add_error_as_exception.call_count, 1)
        self.assertFalse(mock_update_nodes_with_poid_info.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.node_up_task', side_effect=EnmApplicationError)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.update_nodes_with_poid_info')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.auto_provisioning_project_setup')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.handle_node_integration_failure')
    def test_create_auto_provisioning_project__node_up_task_adds_error_on_exception(
            self, mock_node_integration, mock_setup, mock_add_error_as_exception, mock_update_nodes_with_poid_info, mock_status, *_):
        mock_status.return_value = [[u'Project Name\tNode Quantity\tIn '
                                     u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                     u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                                     u'LTE45dg2ERBS00069\tIn Progress\tIntegration Started', u'', u'', u'']]
        mock_node_integration.return_value = None
        self.flow.create_auto_provisioning_project(self.nodes_list)
        self.assertTrue(mock_setup.called)
        self.assertTrue(mock_add_error_as_exception.call_count, 1)
        self.assertTrue(mock_update_nodes_with_poid_info.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.get_workload_admin_user')
    def test_verify_nodes_on_enm__success(self, mock_get_user):
        mock_user = Mock()
        mock_user.enm_execute.return_value.get_output.return_value = [
            u'', u'FDN : NetworkElement=LTE45dg2ERBS00069', u'', u'1 instance(s)']
        mock_get_user.return_value = mock_user
        node = Mock()
        node.node_id = "LTE45dg2ERBS00069"
        found_nodes = verify_nodes_on_enm([node])
        self.assertEqual(found_nodes[0], "LTE45dg2ERBS00069")
        self.assertEqual(1, len(found_nodes))

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.get_workload_admin_user')
    def test_verify_nodes_on_enm__raises_enm_applicaton_error(self, mock_user):
        mock_user.return_value.enm_execute.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, verify_nodes_on_enm, self.nodes_list)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes',
           return_value=['LTE45dg2ERBS00069', 'LTE45dg2ERBS00062'])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.verify_nodes_on_enm')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.create_and_supervise_node')
    def test_handle_node_integration_failure__success(self, mock_create_node, mock_verify_nodes, *_):
        status_response = [u'Project Name\tNode Quantity\tIn Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                           u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                           u'LTE45dg2ERBS00070\tIn Progress\tIntegration Started',
                           u'LTE45dg2ERBS00069\tIn Progress\tIntegration Completed', u'', u'']
        mock_verify_nodes.return_value = ["LTE45dg2ERBS00070"]
        self.flow.user = Mock()
        self.flow.handle_node_integration_failure(status_response, self.nodes_list)
        self.assertEqual(mock_create_node.call_count, 1)
        self.assertEqual(mock_verify_nodes.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes',
           return_value=['LTE45dg2ERBS00069', 'LTE45dg2ERBS00062'])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.verify_nodes_on_enm')
    @patch('enmutils_int.lib.auto_provision.AutoProvision.create_and_supervise_node')
    def test_handle_node_integration_failure__raises_environ_error(self, mock_create_node, mock_verify_nodes, *_):
        status_response = [u'Project Name\tNode Quantity\tIn Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                           u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                           u'LTE45dg2ERBS00069\tIn Progress\tIntegration Started',
                           u'LTE45dg2ERBS00070\tIn Progress\tIntegration Completed', u'', u'']
        self.flow.user = Mock()
        mock_verify_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.handle_node_integration_failure, status_response, self.nodes_list)
        self.assertEqual(mock_verify_nodes.call_count, 1)

    @patch('enmutils_int.lib.auto_provision.AutoProvision.create_and_supervise_node')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.check_ldap_is_configured_on_radio_nodes')
    def test_handle_node_integration_failure__raises_enm_application_error(self, *_):
        status_response = [u'Project Name\tNode Quantity\tIn Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                           u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                           u'LTE45dg2ERBS00069\tIn Progress\tIntegration Started',
                           u'LTE45dg2ERBS00070\tIn Progress\tIntegration Completed', u'', u'']
        self.assertRaises(EnmApplicationError, self.flow.handle_node_integration_failure, status_response,
                          self.nodes_list)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.import_auto_provision_project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.prepare_auto_provision_project')
    def test_auto_provisioning_project_setup__success(self, mock_prepare_project, mock_enm_execute, mock_import_project,
                                                      mock_status, *_):
        mock_prepare_project.side_effect = [self.flow.auto]
        response = Mock()
        response.get_output.return_value = [u'Ne Type Ne Release      Product Identity        Revision (R-State)',
                                            u'Functional MIM Name     Functional MIM Version  Model ID',
                                            u'RadioNode       19.Q2   -       -       GNBCUCP 6.0.0   1-2-33',
                                            u'RadioNode       19.Q2   -       -       GNBCUUP 2.0.0   19.Q2-R37A02',
                                            u'RadioNode       19.Q2   -       -       GNBDU   11.0.0  19.Q2-R37A02']
        mock_enm_execute.return_value = response
        mock_status.return_value = [u'Project Name\tNode Quantity\tIn '
                                    u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                    u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                                    u'LTE50dg2ERBS00052\tIn Progress\tOrder Completed', u'', u'', u'']
        self.flow.auto_provisioning_project_setup(self.nodes_list)
        mock_import_project.assert_called_with(self.flow.auto)
        mock_prepare_project.assert_called_with(self.nodes_list)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.import_auto_provision_project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.prepare_auto_provision_project')
    def test_auto_provisioning_project_setup__oredering_not_completed(self, mock_prepare_project, mock_enm_execute, mock_import_project,
                                                                      mock_status, *_):
        mock_prepare_project.side_effect = [self.flow.auto]
        response = Mock()
        response.get_output.return_value = [u'Ne Type Ne Release      Product Identity        Revision (R-State)',
                                            u'Functional MIM Name     Functional MIM Version  Model ID',
                                            u'RadioNode       19.Q2   -       -       GNBCUCP 6.0.0   1-2-33',
                                            u'RadioNode       19.Q2   -       -       GNBCUUP 2.0.0   19.Q2-R37A02',
                                            u'RadioNode       19.Q2   -       -       GNBDU   11.0.0  19.Q2-R37A02']
        mock_enm_execute.return_value = response
        mock_status.return_value = [u'Project Name\tNode Quantity\tIn '
                                    u'Progress\tSuspended\tSuccessful\tFailed\tCancelled',
                                    u'ap_01_workload\t1\t1\t0\t0\t0\t0', u'Node Name\tStatus\tState',
                                    u'LTE50dg2ERBS00066\tIn Progress\tOrder Started', u'', u'', u'']
        self.flow.auto_provisioning_project_setup(self.nodes_list)
        mock_import_project.assert_called_with(self.flow.auto)
        mock_prepare_project.assert_called_with(self.nodes_list)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.import_auto_provision_project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.prepare_auto_provision_project')
    def test_auto_provisioning_project_setup__raises_enmapplication_error(self, mock_prepare_project,
                                                                          mock_add_error_as_exception, *_):
        mock_prepare_project.side_effect = Exception("Import project failed after multiple retries..")
        self.assertRaises(EnmApplicationError, self.flow.auto_provisioning_project_setup, self.nodes_list)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.import_auto_provision_project')
    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.prepare_auto_provision_project')
    def test_auto_provisioning_project_setup__adds_error_on_exception(self, mock_prepare_project,
                                                                      mock_add_error_as_exception, *_):
        mock_prepare_project.side_effect = Exception
        self.flow.auto_provisioning_project_setup(self.nodes_list)
        self.assertTrue(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.exists',
           side_effect=[True, True])
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.import_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project')
    def test_import_auto_provision_project_deletes_existing(self, mock_delete_project, mock_import_project, *_):
        self.flow.import_auto_provision_project(self.flow.auto)
        self.assertTrue(mock_delete_project.call_count is 1)
        self.assertFalse(mock_import_project.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_node_up_task(self, mock_auto, mock_add_error_as_exception):
        mock_auto.return_value = [u'failed', u'0 project(s) found', u'']
        self.flow.node_up_task(Mock())
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact', side_effect=Exception(""))
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.integrate_node')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_node_up_task_integrates_if_download_fails(self, mock_auto, mock_integrate_node, *_):
        mock_auto.return_value = [u'', u'0 project(s) found', u'']
        self.flow.node_up_task(Mock())
        self.assertTrue(mock_integrate_node.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.integrate_node', side_effect=Exception(""))
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_node_up_task__adds_error_on_integrate_failure(self, mock_auto, mock_add_error_as_exception, *_):
        mock_auto.return_value = [u'', u'0 project(s) found', u'']
        self.flow.node_up_task(Mock())
        self.assertTrue(mock_add_error_as_exception.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.download_artifact')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.integrate_node')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_node_up_task__raises_enmapplication_error(self, mock_auto, mock_log, *_):
        mock_auto.side_effect = ScriptEngineResponseValidationError("License permission check failed", Mock())
        self.assertRaises(EnmApplicationError, self.flow.node_up_task, Mock())
        self.assertTrue(mock_log.call_count, 2)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    def test_prepare_auto_provision_project__retries_if_project_fails_to_create(self, mock_add_error, mock_project, *_):
        mock_project.side_effect = [None, self.project]
        self.flow.user = Mock()
        self.flow.prepare_auto_provision_project(self.nodes_list)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_project')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.add_error_as_exception')
    def test_prepare_auto_provision_project__retries_if_exception_occurs(self, mock_add_error, mock_project,
                                                                         mock_delete_nodes, *_):
        mock_project.side_effect = [Exception("Error"), self.project]
        self.flow.user = Mock()
        self.flow.prepare_auto_provision_project(self.nodes_list)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_delete_nodes.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_project')
    def test_prepare_auto_provision_project__updates_teardown(self, *_):
        self.flow.user = Mock()
        self.assertFalse(self.flow.AUTO_TEARDOWN_CHECK)
        self.flow.prepare_auto_provision_project([Mock()])
        self.assertTrue(self.flow.AUTO_TEARDOWN_CHECK)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.delete_project_nodes')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap01Flow.create_project')
    def test_prepare_auto_provision_project__does_not_update_teardown(self, *_):
        # If made true during earlier iteration
        self.flow.AUTO_TEARDOWN_CHECK = True
        self.flow.user = Mock()
        length_before_execute = len(self.flow.teardown_list)
        self.flow.prepare_auto_provision_project([Mock()])
        self.assertEqual(len(self.flow.teardown_list), length_before_execute)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    def test_create_project__updates_teardown(self, _):
        self.assertFalse(self.flow.PROJECT_TEARDOWN_CHECK)
        self.flow.create_project([Mock()], Mock())
        self.assertTrue(self.flow.PROJECT_TEARDOWN_CHECK)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Project')
    def test_create_project__does_not_update_teardown(self, _):
        # If made true during earlier iteration
        self.flow.PROJECT_TEARDOWN_CHECK = True
        length_before_execute = len(self.flow.teardown_list)
        self.flow.create_project([Mock()], Mock())
        self.assertEqual(len(self.flow.teardown_list), length_before_execute)


class Ap11FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_11_flow")
        unit_test_utils.setup()
        self.ap_11 = ap_11.AP_11()
        self.exception = Exception("Some Exception")
        self.flow = Ap11Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap11Flow.execute_flow')
    def test_run__in_ap_11_is_successful(self, mock_execute_flow):
        self.ap_11.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap11Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_view):
        mock_view.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class Ap12FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_12_flow")
        unit_test_utils.setup()
        self.ap_12 = ap_12.AP_12()
        self.exception = Exception("Some Exception")
        self.flow = Ap12Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap12Flow.execute_flow')
    def test_run__in_ap_12_is_successful(self, mock_execute_flow):
        self.ap_12.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap12Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_download_artifacts):
        mock_download_artifacts.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class Ap13FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_13_flow")
        unit_test_utils.setup()
        self.ap_13 = ap_13.AP_13()
        self.exception = Exception("Some Exception")
        self.flow = Ap13Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap13Flow.execute_flow')
    def test_run__in_ap_13_is_successful(self, mock_execute_flow):
        self.ap_13.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.view')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap13Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_download_artifacts):
        mock_download_artifacts.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class Ap14FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_14_flow")
        unit_test_utils.setup()
        self.ap_14 = ap_14.AP_14()
        self.exception = Exception("Some Exception")
        self.flow = Ap14Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap14Flow.execute_flow')
    def test_run__in_ap_14_is_successful(self, mock_execute_flow):
        self.ap_14.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap14Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_download_artifacts):
        mock_download_artifacts.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class Ap15FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_15_flow")
        unit_test_utils.setup()
        self.ap_15 = ap_15.AP_15()
        self.exception = Exception("Some Exception")
        self.flow = Ap15Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap15Flow.execute_flow')
    def test_run__in_ap_15_is_successful(self, mock_execute_flow):
        self.ap_15.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap15Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_download_artifacts):
        mock_download_artifacts.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class Ap16FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = User(username="ap_16_flow")
        unit_test_utils.setup()
        self.ap_16 = ap_16.AP_16()
        self.exception = Exception("Some Exception")
        self.flow = Ap16Flow()
        self.auto = AutoProvision(user=self.user, project_name="Test")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap16Flow.execute_flow')
    def test_run__in_ap_16_is_successful(self, mock_execute_flow):
        self.ap_16.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    def test_task_set(self, *_):
        self.flow.task_set(self.auto, self.flow)

    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.AutoProvision.status')
    @patch('enmutils_int.lib.profile_flows.ap_flows.ap_flow.Ap16Flow.add_error_as_exception')
    def test_task_set_adds_exception(self, mock_add_errors_as_exception, mock_download_artifacts):
        mock_download_artifacts.side_effect = self.exception
        self.flow.task_set(self.auto, self.flow)
        self.assertTrue(mock_add_errors_as_exception.called)


class ApSetupErbsNodeUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_ap_setup_node__overrides_node_name(self):
        node = ApSetupRadioNode(node_id="AP_SETUP")
        self.assertEqual("AP_SETUP", node.node_name)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
