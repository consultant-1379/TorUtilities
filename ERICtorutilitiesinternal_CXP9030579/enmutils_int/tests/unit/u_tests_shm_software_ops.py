#!/usr/bin/env python
from datetime import datetime

import unittest2
from mock import Mock, patch, mock_open
from requests.exceptions import HTTPError

from enmutils.lib import filesystem
from enmutils.lib.enm_node import (ERBSNode as erbs, RadioNode as radionode, MiniLinkIndoorNode as mltn,
                                   MiniLink6352Node as mltn6352, Router6672Node)
from enmutils.lib.exceptions import (EnmApplicationError, ShellCommandReturnedNonZero)
from enmutils.lib.headers import SHM_LONG_HEADER
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.shm_utilities import SoftwarePackage
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from testslib import unit_test_utils


class SHMSoftwareOperationsUnitTests(unittest2.TestCase):

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    def setUp(self, _):  # pylint: disable=W0221
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [erbs(id='testNode', primary_type='ERBS', node_version='16A', mim_version='H.1.234')]
        self.radionodes = [radionode(id='testradioNode', primary_type='RadioNode', node_version='16A',
                                     model_identity='16B-R2ZV')]
        self.mltn6352_nodes = [mltn6352(node_id='testNode', primary_type='MINI-LINK-6352', platform="MINI_LINK_OUTDOOR")]
        self.router6672_nodes = [Router6672Node(node_id='testNode', primary_type="Router6672")]
        self.mltn669x_nodes = [mltn(node_id='testNode', primary_type='MINI-LINK-669x', platform="MINI_LINK_INDOOR")]
        self.package_name = get_internal_file_path_for_import('etc', 'data', 'CXP17A_H1234.zip')
        self.test_file = get_internal_file_path_for_import('etc', 'data', 'test.xml')
        self.test_package = get_internal_file_path_for_import('etc', 'data', 'test.zip')
        if not filesystem.does_file_exist(self.test_package):
            filesystem.touch_file(self.test_package)
        self.mltn6352_pkg = SoftwarePackage(nodes=self.mltn6352_nodes, user=self.user, identity='CXP9026371_3',
                                            existing_package='CXP9026371_3_R05210936_2-8', package=["package.xml"])
        self.radio_pkg = SoftwarePackage(nodes=self.radionodes, user=self.user,
                                         identity='CXP9024418/5', existing_package="CXP9024418_R2SM")
        self.router6672_pkg = SoftwarePackage(nodes=self.router6672_nodes, user=self.user)
        self.package = SoftwarePackage(nodes=self.nodes, user=self.user,
                                       mim_version="G1281", identity="CXPL16BCP1",
                                       existing_package="CXPL16BCP1_G1281")
        self.mltn_pkg = SoftwarePackage(nodes=self.mltn669x_nodes, user=self.user,
                                        identity='CXP9036600_1', existing_package="CXP9036600_1-R5N107")
        self.package_skip = SoftwarePackage(nodes=self.nodes, user=self.user, file_paths=[self.test_file],
                                            mim_version="G1281", identity="CXPL16BCP1")
        package = Mock()
        package.new_package = "CXPL16BCP1_G1281"
        package.new_dir = self.test_package.split('.zip')[0]
        self.software_operator = SoftwareOperations(user=self.user, package=package)

    def tearDown(self):
        unit_test_utils.tear_down()
        for _ in [self.package_name, self.test_file, self.test_package, "H1234.zip"]:
            if filesystem.does_file_exist(_):
                filesystem.delete_file(_)
        for _ in ["H1234", self.package_name.replace('.zip', '')]:
            if filesystem.does_dir_exist(_):
                filesystem.remove_dir(_)

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_file_exist', return_value=True)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", return_value=False)
    @patch("enmutils_int.lib.shm_software_ops.log.logger.debug")
    def test_import_package__raises_enm_application_error(self, *_):
        response = Mock(ok=True)
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, self.software_operator.import_package)

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_file_exist', return_value=True)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", side_effect=[False, True])
    @patch("enmutils_int.lib.shm_software_ops.log.logger.debug")
    def test_import_package__software_upgrade_success(self, mock_debug, *_):
        response = Mock()
        response.ok = True
        self.user.post.return_value = response
        self.software_operator.package_name = "ABC"
        self.software_operator.import_package()
        self.assertEqual(mock_debug.call_count, 5)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_file_exist', return_value=True)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", side_effect=[False, True])
    @patch("enmutils_int.lib.shm_software_ops.log.logger.debug")
    def test_nhc_import_package__software_upgrade_success(self, mock_debug, *_):
        response = Mock()
        response.ok = True
        self.user.post.return_value = response
        software_package = SoftwarePackage(self.radionodes, self.user, use_default=True, profile_name="NHC_04")
        nhc_software_operator = SoftwareOperations(user=self.user, package=software_package)
        nhc_software_operator.package_name = "CXP9024418_6_R2CXS2"
        nhc_software_operator.import_package()
        self.assertEqual(mock_debug.call_count, 5)

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", return_value=True)
    @patch("enmutils_int.lib.shm_software_ops.log.logger.debug")
    def test_import_package__package_already_uploaded(self, mock_debug, *_):
        self.software_operator.package_name = "CXP_1920"
        self.software_operator.import_package()
        mock_debug.assert_called_with("Software upgrade package CXP_1920 was already uploaded")

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_file_exist', return_value=False)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", return_value=False)
    def test_import_package__package_does_not_exist_in_shm_directory(self, *_):
        self.software_operator.package_name = "CXP_1920"
        self.assertRaises(EnvironmentError, self.software_operator.import_package)

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_file_exist', return_value=True)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", return_value=False)
    @patch("enmutils_int.lib.shm_software_ops.log.logger.debug")
    def test_import_package_package_raises_http_error(self, *_):
        response = Mock(ok=False, text="Error")
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.software_operator.import_package)

    @patch("enmutils_int.lib.shm_software_ops.sleep")
    @patch("time.sleep", return_value=0)
    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.package_exists", return_value=False)
    def test_import_package__raises_enm_application_error_due_to_connection_aborted(self, *_):
        self.user.post.side_effect = Exception("Connection aborted")
        self.assertRaises(EnmApplicationError, self.software_operator.import_package)

    def test_get_software_packages_success(self):
        content = {"totalCount": 1, "softwarePackages": [
            {"name": "Router6672CXP9027695_1_R5F27_118651116", "nodePlatform": "ECIM", "description": "",
             "importDate": "1463651901906", "importedBy": "administrator", "neType": "SGSN-MME", "type": "upgrade",
             "softwarePackageProductDetailsList": [
                 {"productName": "ECIM Upgrade package", "productNumber": "CXS101289", "productRevision": "R50L01",
                  "releaseDate": "1983-02-10", "productDescription": "SoftwarePackage", "type": "type1",
                  "technology": None}]},
            {"name": "CXP9027695_1_R5F27_11865111", "nodePlatform": "ECIM", "description": "",
             "importDate": "1463651901906", "importedBy": "administrator", "neType": "SGSN-MME", "type": "upgrade",
             "softwarePackageProductDetailsList": [
                 {"productName": "ECIM Upgrade package", "productNumber": "CXS101289", "productRevision": "R50L01",
                  "releaseDate": "1983-02-10", "productDescription": "SoftwarePackage", "type": "type1",
                  "technology": None}]}]}
        response = Mock(status_code=200, ok=True, content=content)
        self.user.post.return_value = response
        self.assertEqual(["Router6672CXP9027695_1_R5F27_118651116", "CXP9027695_1_R5F27_11865111"],
                         self.software_operator.get_all_software_packages(user=self.user,
                                                                          filter_text="CXP9027695_1_R5F27_11865111"))

    def test_get_software_packages_failure(self):
        response = Mock(status_code=400, ok=False, content="")
        self.user.post.return_value = response
        self.assertEqual("", self.software_operator.get_all_software_packages(user=self.user))

    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.get_all_software_packages")
    def test_package_exists_true(self, mock_package_list):
        mock_package_list.return_value = ["CXP9027695", "CXP9027695_1_R5F27_11865"]
        self.assertEqual(True, self.software_operator.package_exists(package_name="CXP9027695_1_R5F27_11865",
                                                                     user=self.user))

    @patch("enmutils_int.lib.shm_software_ops.SoftwareOperations.get_all_software_packages")
    def test_package_exists_false(self, mock_package_list):
        mock_package_list.return_value = ["CXP9027695_1_R5F27_11865111116", "Router6672CXP9027695_1_R5F27_1186511111"]
        self.assertEqual(False, self.software_operator.package_exists(package_name="CXP9027695_1_R5F27_11865",
                                                                      user=self.user))

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc',
           side_effect=[ShellCommandReturnedNonZero("Exception", response=Mock())])
    def test_edit_file_values_raises_shell_command_error(self, *_):
        package = SoftwarePackage(self.nodes, user=self.user, mim_version="G1281", profile_name="SHM_TEST_PROFILE",
                                  file_paths=[self.test_file])
        package.node_mim = 'H1234'
        self.assertRaises(ShellCommandReturnedNonZero, package.edit_file_values)

    def test_get_exact_identity_return_same_pkg(self):
        self.assertEqual("CXP2019", self.package.get_exact_identity("CXP2019"))

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_get_exact_identity_return_if_radio_pkg(self, _):
        self.assertEqual("CXP9024418_15", self.package.get_exact_identity("CXP9024418_15-R31A209"))

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    def test_edit_file_values(self, mock_run_cmd_and_evaluate_rc, _):
        package = SoftwarePackage(self.nodes, user=self.user, mim_version="G1281", identity="CXPL16BCP1",
                                  profile_name="SHM_06", existing_package="CXPL16BCP1_G1281",
                                  file_paths=[self.test_file])
        package.file_paths = [self.test_file]
        package.node_identity = "CXP17"
        package.node_mim = "H1234"
        package.edit_file_values()
        self.assertEqual(mock_run_cmd_and_evaluate_rc.call_count, 2)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.minidom')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    def test_edit_file_values__router_node_type(self, mock_run_cmd_and_evaluate_rc, *_):
        package = SoftwarePackage(self.nodes, user=self.user, mim_version="G1281", identity="CXPL16BCP1",
                                  profile_name="SHM_40", existing_package="CXP9060188_R7D44_20081991",
                                  file_paths=[self.test_file])
        package.file_paths = [self.test_file]
        package.node_identity = ""
        package.node_mim = ""
        package.edit_file_values(primary_type="Router6675")
        self.assertEqual(mock_run_cmd_and_evaluate_rc.call_count, 1)

    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_run_cmd_and_evaluate_rc_success(self, mock_cmd, *_):
        response = Mock()
        response.rc = 0
        mock_cmd.return_value = response
        self.package.run_cmd_and_evaluate_rc("pwd", "here")

    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_run_cmd_and_evaluate_rc_fail(self, mock_cmd, *_):
        response = Mock()
        response.rc = 1
        mock_cmd.return_value = response
        self.assertRaises(ShellCommandReturnedNonZero, self.package.run_cmd_and_evaluate_rc, "pwd", "here")

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.set_package_values')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_software_ops.filesystem.does_dir_exist', side_effect=[True, False])
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    @patch('enmutils_int.lib.shm_software_ops.filesystem.move_file_or_dir')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.edit_file_values')
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir')
    def test_update_file_details_and_create_archive(self, mock_remove_dir, mock_edit_file_values, *_):
        mock_remove_dir.return_value = True
        self.package.new_ucf = "ucf.xml"
        self.package.file_paths = ["ucf.xml"]
        self.package.LOCAL_PATH = "/home/enmutils/shm"
        self.package.update_file_details_and_create_archive()
        self.assertTrue(mock_remove_dir.called)
        self.assertTrue(mock_edit_file_values.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=False)
    def test_update_file_details_and_create_archive_environ_error(self, *_):
        self.package.LOCAL_PATH = "Error"
        self.assertRaises(EnvironmentError, self.package.update_file_details_and_create_archive)

    def test_set_file_paths__minilink_6352_success(self):
        test_res = self.mltn6352_pkg.set_file_paths("MINI-LINK-6352")
        self.assertEqual(test_res, self.mltn6352_pkg.package)

    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    def test_get_package_xml_files__success(self, mock_join):
        self.mltn6352_pkg.get_package_xml_files("MINI-LINK-6352")
        self.assertTrue(mock_join.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    def test_get_package_xml_files__failure_for_other_nodes(self, mock_join):
        self.mltn6352_pkg.get_package_xml_files("RadioNode")
        self.assertFalse(mock_join.called)

    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_mim_version")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_exact_identity")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version", return_value="R05210411")
    def test_set_package_values__on_minilink_6352_nodes(self, *_):
        self.mltn6352_pkg.set_package_values("MINI-LINK-6352")
        self.assertEqual("R05210936", self.mltn6352_pkg.revision_number)
        self.assertEqual("CXP9026371_3_R05210411_2-8", self.mltn6352_pkg.new_package)

    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.set_package_values")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc")
    def test_edit_file_values__on_minilink_6352_nodes(self, mock_run, *_):
        self.mltn6352_pkg.node_mim = "R05210411"
        self.mltn6352_pkg.file_paths = ["package.xml"]
        self.mltn6352_pkg.node_identity = "CXP9026371_3"
        self.mltn6352_pkg.edit_file_values(primary_type="MINI-LINK-6352")
        self.assertTrue(mock_run.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', side_effect=[True, False])
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.filesystem.move_file_or_dir')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.edit_file_values')
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_update_file_details_and_create_archive_radio_node(self, *_):
        self.package.new_ucf = "ucf.xml"
        self.package.file_paths = ["ucf.xml"]
        self.router6672_pkg.LOCAL_PATH = "/home/enmutils/shm"
        self.router6672_pkg.update_file_details_and_create_archive()

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', side_effect=[True, False])
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.filesystem.move_file_or_dir')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.edit_file_values')
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir')
    def test_update_file_details_and_create_archive_router_6672(self, mock_remove_dir, mock_edit_file_values, *_):
        mock_remove_dir.return_value = True
        self.package.new_ucf = "ucf.xml"
        self.package.file_paths = ["ucf.xml"]
        self.radio_pkg.LOCAL_PATH = "/home/enmutils/shm"
        self.radio_pkg.update_file_details_and_create_archive()
        self.assertTrue(mock_remove_dir.called)
        self.assertTrue(mock_edit_file_values.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', return_value=True)
    def test_update_file_details_and_create_archive_directory_exists(self, mock_does_dir_exists, *_):
        self.package.new_ucf = ['new ucf']
        self.package.file_paths = ['file path']
        self.package.LOCAL_PATH = "/home/enmutils/shm"
        self.package.run_cmd_and_evaluate_rc = Mock()
        self.package.update_file_details_and_create_archive()
        self.assertTrue(mock_does_dir_exists.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist')
    def test_update_file_details_and_create_archive_directory_exists_pkg_values(self, mock_does_dir_exists, *_):
        self.package.new_ucf = ['new ucf']
        self.package.existing_package = ""
        self.package.file_paths = ['file path']
        self.package.LOCAL_PATH = "/home/enmutils/shm"
        self.package.run_cmd_and_evaluate_rc = Mock()
        self.package.update_file_details_and_create_archive()
        mock_does_dir_exists.return_value = True
        self.assertTrue(mock_does_dir_exists.called)

    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.set_package_values')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', side_effect=[False, False])
    @patch('enmutils_int.lib.shm_utilities.filesystem.remove_dir', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    def test_update_file_details_and_create_archive_skip_existing_package(self, mock_get_revision, mock_identity,
                                                                          mock_cmd, *_):
        mock_get_revision.return_value = 'H1234'
        mock_identity.return_value = "CXP17A"
        self.package_skip.LOCAL_PATH = "/home/enmutils/shm"
        response = Mock()
        response.rc = 0
        mock_cmd.return_value = response
        self.package_skip.update_file_details_and_create_archive()

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.os.path.exists', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', side_effect=[False, False])
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc',
           side_effect=[ShellCommandReturnedNonZero("Exception", response=Mock())])
    def test_update_file_details_and_create_archive_raises_shell_command_error(self, *_):
        package = SoftwarePackage(self.nodes, user=self.user, mim_version="G1281", profile_name="SHM_06",
                                  existing_package="no_such_zip")
        package.LOCAL_PATH = "/home/enmutils/shm"
        self.assertRaises(ShellCommandReturnedNonZero, package.update_file_details_and_create_archive)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.update_node_identity_and_mim')
    def test_update_node_details__updates_with_correct_key(self, mock_update, *_):
        software = SoftwarePackage(self.nodes, user=self.user, mim_version="G1281", profile_name="SHM_06",
                                   existing_package="R35F105_1")
        software.new_package = "R35F105_1"
        software.update_node_details()
        mock_update.assert_called_with("MINI-LINK-Indoor")

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.update_node_identity_and_mim')
    def test_update_ML669x_node_details_updates_with_correct_key(self, mock_update, *_):
        software = SoftwarePackage(self.mltn669x_nodes, user=self.user, mim_version="G1281", profile_name="SHM_42",
                                   existing_package="R35F105_1")
        software.new_package = "CXP9036600_1_MINI-LINK_6600_6366_1.4_R5N107"
        software.update_node_details()
        mock_update.assert_called_with("MINI-LINK-669x_0")

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    def test_get_mim_version__router_nodes(self, _):
        router6672_pkg = SoftwarePackage(nodes=self.router6672_nodes, user=self.user,
                                         existing_package="CXP9060188_1-R7D44_9999_SF")
        self.assertEqual("R7D44_9999", router6672_pkg.get_mim_version(primary_type="Router6672"))

    def test_get_mim_version__radio_nodes(self):
        self.assertEqual("R2SM", self.radio_pkg.get_mim_version(primary_type="RadioNode"))

    def test_get_revision_from_ne_package_raises_exception(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.package.get_revision_from_ne_product_version)

    def test_get_ne_product_version_returns_response(self):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s)']
        self.user.enm_execute.return_value = response
        resp = self.package.get_ne_product_version()
        self.assertEqual(resp.get_output(), [u'1 instance(s)'])

    def test_get_ne_product_version_raises_exception(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response

        self.assertRaises(EnmApplicationError, self.package.get_ne_product_version)

    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_netype_describe', return_value=[u'0 instance(s)'])
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_node_model_identities')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.select_node_version_and_model_info', return_value=("1234", "18.Q4"))
    def test_get_identity_from_ne_describe_raises_exception(self, *_):
        self.package.nodes = [Mock()]
        self.assertRaises(EnmApplicationError, self.package.get_identity_from_ne_describe)

    def test_get_ne_type_describe_raises_exception(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertRaises(EnmApplicationError, self.package.get_netype_describe)

    def test_get_ne_type_describe_returns_content(self):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s)']
        self.user.enm_execute.return_value = response
        self.assertEqual([u'1 instance(s)'], self.package.get_netype_describe())

    @patch('datetime.datetime')
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version")
    def test_get_revision_from_ne_package_returns_increase_product_version(self, mock_get_ne_product_revision,
                                                                           mock_datetime):
        response = Mock()
        mock_datetime.now.return_value = datetime(2020, 4, 3, 16, 2, 0, 0)
        response.get_output.return_value = [u' FDN : NetworkElement=LTE01',
                                            u'neProductVersion : [{revision=H1234, identity=CXP9010021/3}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{revision=H1235, identity=CXP9010021/3}]',
                                            u'10 instance(s)']
        mock_get_ne_product_revision.return_value = response
        self.assertEqual('H12304031602', self.package.get_revision_from_ne_product_version())

    @patch('datetime.datetime')
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version")
    def test_get_revision_from_ne_package_returns_increase_product_version_nine(self, mock_get_ne_product_revision,
                                                                                mock_datetime):
        response = Mock()
        mock_datetime.now.return_value = datetime(2020, 4, 3, 16, 2, 0, 0)
        response.get_output.return_value = [u' FDN : NetworkElement=LTE01',
                                            u'neProductVersion : [{revision=H1234, identity=CXP9010021/3}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{revision=H1239, identity=CXP9010021/3}]',
                                            u'10 instance(s)']
        mock_get_ne_product_revision.return_value = response
        self.assertEqual('H12304031602', self.package.get_revision_from_ne_product_version())

    @patch('datetime.datetime')
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version")
    def test_get_revision_from_ne_package_returns_increase_product_version_alphanumeric(
            self, mock_get_ne_product_revision, mock_datetime):
        response = Mock()
        mock_datetime.now.return_value = datetime(2020, 4, 3, 16, 2, 0, 0)
        response.get_output.return_value = [u' FDN : NetworkElement=LTE01',
                                            u'neProductVersion : [{revision=J58126, identity=CXP9010021/3}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=J5811113}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=J882}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=R38A}]',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=J140}]',
                                            u'4 instance(s)']
        mock_get_ne_product_revision.return_value = response
        self.assertEqual('R38A04031602', self.package.get_revision_from_ne_product_version())

    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version")
    def test_get_revision_from_ne_package_raises_exception_if_no_revision(self, mock_get_ne_product_revision):
        response = Mock()
        response.get_output.return_value = [u' FDN : NetworkElement=LTE01',
                                            u' FDN : NetworkElement=LTE02',
                                            u'10 instance(s)']
        mock_get_ne_product_revision.return_value = response
        self.assertRaises(EnmApplicationError, self.package.get_revision_from_ne_product_version)

    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_ne_product_version")
    def test_get_revision_from_ne_product_version__is_node_variants_value_updated(self, mock_get_ne_product_revision):
        response = Mock()
        response.get_output.return_value = [u' FDN : NetworkElement=LTE01',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=J58126}]',
                                            u' FDN : NetworkElement=LTE02',
                                            u'neProductVersion : [{identity=CXP9010021/3, revision=J5811113}]'
                                            u'2 instance(s)']
        mock_get_ne_product_revision.return_value = response
        self.package.get_revision_from_ne_product_version()
        self.assertEqual(self.package.node_variants, ["CXP9010021/3"])

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_node_model_identities', return_value={})
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.select_node_version_and_model_info', return_value=("17A", "H.1.234"))
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_netype_describe")
    def test_get_identity_from_ne_describe_ERBS_package_returns_identity(self, mock_get_ne_product_revision, *_):

        mock_get_ne_product_revision.return_value = [
            u'ERBS\t17A\t-\tH1234\tERBS_NODE_MODEL\tH.1.234\t17A-H.1.234',
            u'ERBS\t16A\tCXPL17ACP1\t\tERBS_NODE_MODEL\tG1281\t16A-H.1.234']
        self.assertEqual(u'CXPL17ACP1', self.package.get_identity_from_ne_describe())

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_node_model_identities', return_value={})
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.select_node_version_and_model_info', return_value=("18A", "H.1.234"))
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_netype_describe")
    def test_get_identity_from_ne_describe_erbs_package_raises_enmapplicationerror(self, mock_get_ne_product_revision,
                                                                                   *_):
        mock_get_ne_product_revision.return_value = [
            u'ERBS\t17A\t-\t-\tERBS_NODE_MODEL\tH.1.234\t17A-H.1.234',
            u'ERBS\t16A\t-\t-\tERBS_NODE_MODEL\tG1281\t17A-H.1.234']
        self.assertRaises(EnmApplicationError, self.package.get_identity_from_ne_describe)

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_node_model_identities', return_value={})
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.select_node_version_and_model_info', return_value=("17A", "H.1.234"))
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_netype_describe")
    def test_get_identity_from_ne_describe_radionode_package_returns_identity(self, mock_get_ne_product_revision, *_):

        mock_get_ne_product_revision.return_value = [
            u'RadioNode\t17A\tCXP9024418/5\tH1234\tERBS_NODE_MODEL\tH.1.234\t17A-H.1.234',
            u'RadioNode\t16A\tCXP9024418/5\t\tLrat\t1.8010.0\t16B-R2ZV']
        self.assertEqual('CXP9024418/5', self.radio_pkg.get_identity_from_ne_describe())

    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.get_node_model_identities', return_value={})
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_netype_describe")
    def test_get_identity_from_ne_package_raises_exception_if_no_revision(self, mock_get_ne_product_revision, *_):
        mock_get_ne_product_revision.return_value = [u'ERBS\t17A\tCXPL17ACP/1\tH1160\tERBS_NODE_MODEL\tH.1.160\t17A',
                                                     u'ERBS\t16A\t-\t-\tERBS_NODE_MODEL\tH.1.234\t17A-H.1.234']
        self.assertRaises(EnmApplicationError, self.package.get_identity_from_ne_describe)

    def test_update_mim_version_raises_exception_on_no_digits_to_increment(self):
        self.assertRaises(EnvironmentError, self.package.update_mim_version, '')

    @patch('datetime.datetime')
    def test_update_mim_version_returns_correct_values(self, mock_datetime):
        # Example node revisions taken from
        # https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=1895179253
        mock_datetime.now.return_value = datetime(2020, 4, 3, 16, 2, 0, 0)
        self.assertEqual("R38A04031602", self.package.update_mim_version('R38A'))
        self.assertEqual('R2SM04031602', self.radio_pkg.update_mim_version('R2SM1124'))
        self.assertEqual('R5D03_04031602', self.router6672_pkg.update_mim_version('R5D03_111116'))
        self.assertEqual('R5N10704031602', self.mltn_pkg.update_mim_version("R5N107"))

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_referred_packages_on_nodes_success(self, _):
        fdn = "Upgrade,CXP1234"
        revision = "CXP"
        number = "1234"
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response
        self.assertIsNotNone(self.software_operator.get_referred_packages_on_nodes(self.nodes[0], self.user, fdn,
                                                                                   revision, number))

    @patch('time.sleep', return_value=lambda _: None)
    @patch("enmutils_int.lib.shm_software_ops.raise_for_status", side_effect=HTTPError)
    def test_get_referred_packages_on_nodes__raises_httperror(self, *_):
        response = Mock(status_code=500, ok=False)
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response
        fdn = "Upgrade,CXP1234"
        revision = "CXP"
        number = "1234"
        self.assertRaises(HTTPError, self.software_operator.get_referred_packages_on_nodes, self.nodes[0], self.user,
                          fdn, revision, number)

    @patch('time.sleep', return_value=lambda _: None)
    @patch("enmutils_int.lib.shm_software_ops.raise_for_status", side_effect=HTTPError)
    def test_get_referred_backups_on_nodes__raises_httperror(self, *_):
        response = Mock(status_code=500, ok=False)
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response
        fdn = "Upgrade,CXP1234"
        revision = "CXP"
        number = "1234"
        self.assertRaises(HTTPError, self.software_operator.get_referred_backups_on_nodes, self.nodes[0], self.user,
                          fdn, revision, number)

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_referred_backups_on_nodes_success(self, _):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response
        fdn = "Upgrade,CXP1234"
        revision = "CXP"
        number = "1234"
        self.assertIsNotNone(self.software_operator.get_referred_backups_on_nodes(self.nodes[0], self.user, fdn,
                                                                                  revision, number))

    @patch('time.sleep', return_value=lambda _: None)
    def test_get_packages_on_nodes__success(self, _):
        response = Mock(status_code=200, ok=True)
        nodes = [Mock(node_id="node1"), Mock(node_id="node2")]
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response

        self.assertIsNotNone(self.software_operator.get_packages_on_nodes(nodes, self.user))
        payload = {
            "fdns": ['NetworkElement=node1', 'NetworkElement=node2'],
            "offset": 1,
            "limit": 50,
            "sortBy": "nodeName",
            "ascending": True,
            "filterDetails": []
        }
        self.user.post.assert_called_with("/oss/shm/rest/inventory/v1/upgradepackage/list", json=payload,
                                          headers=SHM_LONG_HEADER)

    @patch('time.sleep', return_value=lambda _: None)
    @patch("enmutils_int.lib.shm_software_ops.raise_for_status", side_effect=HTTPError)
    def test_get_packages_on_nodes__raises_httperror(self, *_):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {u'upgradePackages': [], u'unsupportedNodes': {},
                                      u'responseMetadata': {u'totalCount': 0, u'clearOffset': True}}
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.software_operator.get_packages_on_nodes, self.nodes, self.user)

    def test_select_node_version_and_model_info__uses_enm_model_if_available(self):
        node = Mock(node_id="Node")
        model_ids = {"Node": "17.Q1-H.1.234", "Node1": "18.Q2-H.1.234"}
        self.assertEqual(("H.1.234", "17.Q1"), self.package.select_node_version_and_model_info(node, model_ids))

    def test_select_node_version_and_model_info__uses_default(self):
        node = Mock(node_id="Node", primary_type="ERBS", mim_version="G.1.380", node_version="16B")
        model_ids = {"Node1": "18.Q2-H.1.234"}
        self.assertEqual(("G.1.380", "16B"), self.package.select_node_version_and_model_info(node, model_ids))
        r_node = Mock(node_id="Node", primary_type="RadioNode", mim_version="", node_version="17.Q2",
                      model_identity="R1234")
        self.assertEqual(("R1234", "17.Q2"), self.package.select_node_version_and_model_info(r_node, model_ids))

    @patch('enmutils.lib.log.logger.debug')
    def test_select_node_version_and_model_info__logs_index_error(self, mock_debug):
        node = Mock(node_id="Node1")
        model_ids = {"Node1": [None]}
        self.package.select_node_version_and_model_info(node, model_ids)
        mock_debug.assert_any_call("Could not retrieve model information, error encountered 'list' object has no "
                                   "attribute 'split' for model_id [None]")

    def test_get_node_model_identities__zero_instances(self):
        self.package.user = Mock()
        self.package.user.enm_execute.return_value.get_output.return_value = ["0 instance(s)"]
        self.assertDictEqual({}, self.package.get_node_model_identities())

    def test_get_node_model_identities__instances(self):
        self.package.user = Mock()
        response = [u'NetworkElement', u'Node Name Model Id', u'Node\t17.Q2-H.1.234', u'Node1\t17.Q3-J.1.240', u'',
                    u'2 instance(s)']
        self.package.user.enm_execute.return_value.get_output.return_value = response
        self.assertDictEqual({"Node": "17.Q2-H.1.234", "Node1": "17.Q3-J.1.240"},
                             self.package.get_node_model_identities())

    def test_get_node_model_identities__index_error(self):
        self.package.user = Mock()
        response = [u'NetworkElement', u'Node Name Model Id', u'Node 17.Q2-H.1.234', u'',
                    u'2 instance(s)']
        self.package.user.enm_execute.return_value.get_output.return_value = response
        self.assertDictEqual({}, self.package.get_node_model_identities())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
