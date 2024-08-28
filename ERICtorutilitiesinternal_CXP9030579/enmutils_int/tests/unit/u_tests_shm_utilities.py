#!/usr/bin/env python
import unittest2
from mock import Mock, PropertyMock, mock_open, patch
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import BSCNode
from enmutils.lib.enm_node import ERBSNode as erbs
from enmutils.lib.enm_node import MiniLink6352Node as mltn6352
from enmutils.lib.enm_node import MiniLinkIndoorNode as mltn
from enmutils.lib.enm_node import RadioNode as radionode
from enmutils.lib.enm_node import Router6672Node
from enmutils.lib.exceptions import (EnmApplicationError,
                                     FailedNetsimOperation, NetsimError,
                                     ScriptEngineResponseValidationError,
                                     ShellCommandReturnedNonZero, EnvironError)
from enmutils_int.lib.load_node import ERBSLoadNode as load_node
from enmutils_int.lib.shm_utilities import (SHMLicense, SHMUtils,
                                            SoftwarePackage)
from testslib import unit_test_utils


class SHMUtilsUnitTests(ParameterizedTestCase):

    PIB_VALUES = {"SOFTWARE_PACKAGE_LOCK_EXPIRY_IN_DAYS": "1"}

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    def setUp(self, _):  # pylint: disable=W0221
        unit_test_utils.setup()
        self.user = Mock()
        self.shm_util = SHMUtils()
        self.empty_nodes = ''
        self.nodes = [erbs(id='testNode', primary_type='ERBS', node_version='16A', mim_version='H.1.234')]
        self.radio_nodes = [radionode(node_id='testNode', primary_type='RadioNode', platform="ECIM")]

        self.mltn_nodes = [mltn(node_id='testNode', primary_type='MLTN', platform="ECIM")]
        self.mltn6352_nodes = [mltn6352(node_id='tstNode', primary_type='MINI-LINK-6352', platform="MINI_LINK_OUTDOOR")]
        self.mltn669x_nodes = [mltn(node_id='testNode', primary_type='MINI-LINK-669x', platform="MINI_LINK_INDOOR")]
        self.router6672_nodes = [Router6672Node(node_id='testNode', primary_type="Router6672")]
        self.router6675_nodes = [erbs(node_id='testNode', primary_type='Router6675')]
        self.bsc_nodes = [BSCNode(node_id='testNode', primary_type="BSC")]
        self.erbs_package = SoftwarePackage(self.nodes, self.user, profile_name="SHM_06", use_default=False, pib_values=self.PIB_VALUES)
        self.radio_package = SoftwarePackage(self.radio_nodes, self.user, use_default=True, additional=True, pib_values=self.PIB_VALUES)
        self.pkg = SoftwarePackage(self.radio_nodes, self.user, profile_name="ASU_01", use_default=False, pib_values=self.PIB_VALUES)
        self.asu_package = SoftwarePackage(self.radio_nodes, self.user, profile_name="ASU_01", use_default=True, pib_values=self.PIB_VALUES)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_tolerance_check(self):
        self.assertTrue(self.shm_util.retry_when_below_skipped_tolerance(tolerance=10, skipped=12, total=100))
        self.assertFalse(self.shm_util.retry_when_below_skipped_tolerance(tolerance=10, skipped=9, total=100))
        self.assertTrue(self.shm_util.retry_when_below_skipped_tolerance(tolerance=0, skipped=0, total=0))

    @patch('enmutils_int.lib.shm_utilities.annotate_fdn_poid_return_node_objects')
    def test_enm_annotate_method(self, mock_annotate):
        self.shm_util.enm_annotate_method(user=self.user, nodes=[])
        self.assertTrue(mock_annotate.iscalled)

    @patch('enmutils_int.lib.shm_utilities.netsim_operations.NetsimOperation.execute_command_string')
    def test_execute_restart_delay(self, mock_execute_command_string):
        self.shm_util.execute_restart_delay(nodes=self.nodes)
        self.assertTrue(mock_execute_command_string.iscalled)

    @patch('enmutils_int.lib.shm_utilities.netsim_operations.NetsimOperation.execute_command_string', side_effect=NetsimError)
    def test_execute_restart_delay_error_netsim(self, *_):
        self.assertRaises(NetsimError, self.shm_util.execute_restart_delay, nodes=self.nodes)

    def test_execute_restart_delay_no_nodes(self):
        self.shm_util.execute_restart_delay(nodes=[])

    def test_determine_highest_model_identity_count_nodes_success(self):
        response = Mock()
        response.get_output.return_value = [
            u'RadioNode\t17A\t-\tH1234\tNODE_MODEL\tG.1.124\t17A-H.10',
            u'RadioNode\t17A\tABC\tH1234\tNODE_MODEL\tG.1.124\t17A-H.12',
            u'RadioNode\t16A\tCXPL17ACP1\t\tNODE_MODEL\tG.1.123\t17A-H.1.5']
        response_omi_nmi = Mock()
        response_omi_nmi.get_output.return_value = [u'NetworkElement',
                                                    u'NodeId    nodeModelIdentity   ossModelIdentity',
                                                    u'LTE104dg2ERBS00053    17.Q3-R25D04    17.Q3-R25D04',
                                                    u'LTE100dg2ERBS00028    17.Q4-R32B07    17.Q4-R32B07',
                                                    u'LTE91dg2ERBS00045 18.Q4-R57A02    18.Q4-R58A04',
                                                    u'27 instance(s)']
        self.user.enm_execute.side_effect = [response] + [response_omi_nmi] + [response] + [response_omi_nmi]
        nodes = ([load_node(model_identity='17A-H.12', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00053', primary_type="mock")] * 5 +
                 [load_node(model_identity='17A-H.19', profiles=['Test2'],
                            node_id='LTE100dg2ERBS00028', primary_type="mock")] * 1 +
                 [load_node(model_identity='17A-H.1.5', profiles=['Test2'],
                            node_id='LTE91dg2ERBS00045', primary_type="mock")] * 4)
        profile_object = Mock()
        profile_object.deallocate_unused_nodes_and_update_profile_persistence.return_value = Mock()
        self.assertEqual(
            len(self.shm_util.determine_highest_model_identity_count_nodes(profile_object, nodes, self.user)), 5)
        nodes = ([load_node(model_identity='17A-H.12', profiles=['Test1'],
                            node_id='LTE104dg2ERBS00053', primary_type="mock")] * 3 +
                 [load_node(model_identity='17A-H.1.5', profiles=['Test2'],
                            node_id='LTE91dg2ERBS00045', primary_type="mock")] * 4)
        self.assertEqual(
            len(self.shm_util.determine_highest_model_identity_count_nodes(profile_object, nodes, self.user)), 3)

    def test_get_nodes_same_omi_nmi_raises_enm_application_error(self):
        response = Mock()
        response.get_output.return_value = ["Error", "0 instance(s)"]
        self.user.enm_execute.return_value = response
        nodes = ([load_node(model_identity='17A-H.12', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00053', primary_type="mock")] * 5 +
                 [load_node(model_identity='17A-H.19', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00028', primary_type="mock")] * 1 +
                 [load_node(model_identity='17A-H.1.5', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00045', primary_type="mock")] * 4)
        self.assertRaises(EnmApplicationError, self.shm_util.get_nodes_same_omi_nmi, self.user, nodes)

    def test_determine_highest_model_identity_count_nodes_get_nodes_same_omi_nmi_raises_enmapplicationerror(self):
        response = Mock()
        response.get_output.return_value = [
            u'RadioNode\t17A\t-\tH1234\tNODE_MODEL\tG.1.124\t17A-H.10',
            u'RadioNode\t17A\tABC\tH1234\tNODE_MODEL\tG.1.124\t17A-H.12',
            u'RadioNode\t16A\tCXPL17ACP1\t\tNODE_MODEL\tG.1.123\t17A-H.1.5']
        response_omi_nmi = Mock()
        response_omi_nmi.get_output.return_value = [u'NetworkElement', u'NodeId\tnodeModelIdentity\tossModelIdentity',
                                                    u'LTE103dg2ERBS00028\t17.Q3-R25D04\t17.Q3-R25D04',
                                                    u'LTE45dg2ERBS00045\t18.Q4-R57A02\t18.Q4-R57A02',
                                                    u'LTE75dg2ERBS00062\t17.Q3-R25D04\t17.Q3-R25D04',
                                                    u'Error 1049 : The scope is incorrect or not associated ',
                                                    u'27 instance(s)']
        self.user.enm_execute.side_effect = [response] + [response_omi_nmi] + [response] + [response_omi_nmi]
        nodes = ([load_node(model_identity='17A-H.12', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00053', primary_type="mock")] * 5 +
                 [load_node(model_identity='17A-H.19', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00028', primary_type="mock")] * 1 +
                 [load_node(model_identity='17A-H.1.5', profiles=['Test2'],
                            node_id='LTE104dg2ERBS00045', primary_type="mock")] * 4)
        profile_object = Mock()
        profile_object.deallocate_unused_nodes_and_update_profile_persistence.return_value = Mock()
        self.assertRaises(EnmApplicationError, self.shm_util.determine_highest_model_identity_count_nodes,
                          profile_object, nodes, self.user)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.check_availability_of_identity_revision', return_value=[])
    def test_determine_highest_model_identity_count_nodes_raises_EnmApplicationError(self, *_):
        nodes = ([load_node(model_identity='G.1.124', profiles=['Test2'], simulation='LTE', primary_type="mock")] * 5 +
                 [load_node(model_identity='G.1.123', profiles=['Test2'], simulation='LTE', primary_type="mock")] * 4)
        profile_object = Mock()
        profile_object.deallocate_unused_nodes_and_update_profile_persistence.return_value = Mock()
        self.assertRaises(EnmApplicationError,
                          self.shm_util.determine_highest_model_identity_count_nodes, profile_object, nodes, self.user)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.get_model_list', return_value=[])
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.get_nodes_same_omi_nmi', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.check_availability_of_identity_revision', return_value=[Mock(), Mock()])
    def test_determine_highest_model_identity_count_nodes_raises_second_EnmApplicationError(self, *_):
        nodes = ([load_node(model_identity='G.1.124', profiles=['Test2'], simulation='LTE', primary_type="mock")] * 5 +
                 [load_node(model_identity='G.1.123', profiles=['Test2'], simulation='LTE', primary_type="mock")] * 4)
        profile_object = Mock()
        profile_object.deallocate_unused_nodes_and_update_profile_persistence.return_value = Mock()
        self.assertRaises(EnmApplicationError,
                          self.shm_util.determine_highest_model_identity_count_nodes, profile_object, nodes, self.user)

    def test_check_availability_of_identity_revision(self):
        self.user.enm_execute.return_value.get_output.return_value = "0 instance(s)"
        self.assertRaises(EnmApplicationError, self.shm_util.check_availability_of_identity_revision, user=self.user,
                          node_type="ERBS")

    @patch('enmutils_int.lib.shm_utilities.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.deallocate_unused_nodes')
    def test_determine_highest_mim_count(self, mock_deallocate_unused_nodes, *_):
        profile = Mock()

        node1 = Mock(mim_version='G.1.124', profiles=['Test2'], simulation='LTE')
        node2 = Mock(mim_version='G.1.124', profiles=['Test2'], simulation='LTE')
        node3 = Mock(mim_version='G.1.124', profiles=['Test2'], simulation='LTE')

        node4 = Mock(mim_version='G.1.123', profiles=['Test2'], simulation='LTE')
        node5 = Mock(mim_version='G.1.123', profiles=['Test2'], simulation='LTE')

        nodes = ([node1, node2, node3, node4, node5])
        self.assertEqual(len(self.shm_util.determine_highest_mim_count_nodes(nodes, profile)), 3)
        self.assertTrue(mock_deallocate_unused_nodes.called)

    @patch("enmutils_int.lib.shm_utilities.run_local_cmd")
    @patch("enmutils_int.lib.shm_utilities.log.logger.debug")
    @patch("enmutils_int.lib.shm_utilities.SHMUtils.verify_unzip")
    @ParameterizedTestCase.parameterize(
        ('verify_value', 'expected_result'),
        [
            (True, True),
            (False, False),
        ]
    )
    def test_install_unzip__calls_logger_as_expected(self, verify_value, expected_result,
                                                     mock_verify, mock_log, mock_run_cmd):
        mock_verify.return_value = verify_value
        mock_run_cmd.return_value.rc = None
        self.shm_util.install_unzip()
        self.assertEqual(mock_log.called, expected_result)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.cmd_exists")
    def test_verify_unzip__calls_cmd_exists_as_expected(self, mock_cmd_exists):
        self.shm_util.verify_unzip()
        self.assertTrue(mock_cmd_exists.called)

    @patch.dict("enmutils_int.lib.shm_utilities.os.environ", {"PATH": "/usr/bin:/bin"})
    @patch("enmutils_int.lib.shm_utilities.os.path.isfile")
    @patch("enmutils_int.lib.shm_utilities.os.access")
    @ParameterizedTestCase.parameterize(
        ('access_value', 'is_file_value', 'expected_result'),
        [
            (True, True, True),
            (False, True, False),
            (True, False, False),
            (False, False, False),
        ]
    )
    def test_cmd_exists__returns_as_expected(self, access_value, is_file_value,
                                             expected_result, mock_access, mock_is_file, *_):
        mock_access.return_value = access_value
        mock_is_file.return_value = is_file_value
        self.assertEqual(self.shm_util.cmd_exists("zip"), expected_result)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.verify_unzip", return_value=False)
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_install_unzip_raises_environ_error(self, mock_run_local_cmd, _):
        response = Mock()
        response.rc = 1
        mock_run_local_cmd.return_value = response
        self.assertRaises(ShellCommandReturnedNonZero, self.shm_util.install_unzip)

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.verify_unzip", return_value=False)
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_install_unzip_raises_success(self, mock_run_local_cmd, _):
        mock_run_local_cmd.return_value.rc = 0
        self.shm_util.install_unzip()

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    def test_backup_setup_erbs_backup_call(self, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.nodes, file_name="qrstpq")
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    def test_backup_setup_radionode_backup_call(self, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.radio_nodes, file_name="qrstpq")
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_mltn_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.mltn_nodes, file_name="qrstpq")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_mltn6352_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.mltn6352_nodes, file_name="qrstpq")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_mltn669x_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.mltn669x_nodes, file_name="qrstpq")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_Router6672_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.router6672_nodes, file_name="qrstpq")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_Router6675_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.router6675_nodes, file_name="qrstpq")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.ShmJob.create')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_backup_setup_BSC_backup_call(self, mock_log, mock_create):
        self.shm_util.backup_setup(user=self.user, nodes=self.bsc_nodes, file_name="bsc_backup")
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    def test_backup_setup_raise_exception(self, _):
        self.assertRaises(EnmApplicationError, self.shm_util.backup_setup, user=self.user, nodes=self.nodes,
                          file_name="qrstpq")

    def test_upgrade_setup_raises_environ_error_no_nodes(self):
        self.assertRaises(EnvironError, self.shm_util.upgrade_setup, user=Mock(), nodes=None)

    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    def test_upgrade_setup__shm_27_profile(self, mock_upgrade, mock_create, *_):
        nodes = [erbs(id='siu', primary_type='SIU02'), erbs(id='tcu', primary_type='TCU02')]
        self.shm_util.upgrade_setup(user=Mock(), nodes=nodes, use_default=False,
                                    profile_name="SHM_27", log_only=False, pib_values=self.PIB_VALUES)
        self.assertTrue(mock_upgrade.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.upgrade_trigger')
    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    def test_upgrade_setup__shm_27_profile_tcu(self, mock_upgrade, *_):
        nodes = [erbs(id='tcu', primary_type='TCU02')]
        self.shm_util.upgrade_setup(user=Mock(), nodes=nodes, use_default=False,
                                    profile_name="SHM_27", log_only=False, pib_values=self.PIB_VALUES)
        self.assertTrue(mock_upgrade.called)

    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.__init__', return_value=None)
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.upgrade_trigger')
    @patch('enmutils_int.lib.shm_utilities.MultiUpgrade.create')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    def test_upgrade_setup__shm_27_profile_siu(self, mock_upgrade, *_):
        nodes = [erbs(id='siu', primary_type='SIU02')]
        self.shm_util.upgrade_setup(user=Mock(), nodes=nodes, use_default=False,
                                    profile_name="SHM_27", log_only=False, pib_values=self.PIB_VALUES)
        self.assertTrue(mock_upgrade.called)

    @patch('enmutils_int.lib.shm_utilities.UpgradeJob')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.upgrade_trigger')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    def test_upgrade_setup_log_only__success(self, mock_upgrade, *_):
        self.shm_util.upgrade_setup(user=Mock(), nodes=self.nodes, use_default=False, log_only=True,
                                    profile_name="SHM_TEST_PROFILE", pib_values=self.PIB_VALUES)
        self.assertTrue(mock_upgrade.called)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    @patch('enmutils_int.lib.shm_utilities.UpgradeJob.create')
    def test_upgrade_setup_raises_on_create_failure(self, mock_create, _):
        mock_create.side_effect = Exception("Some Exception")
        self.assertRaises(Exception, self.shm_util.upgrade_setup, user=Mock(), nodes=self.nodes, use_default=True,
                          log_only=False, pib_values=self.PIB_VALUES)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.create_and_import_software_package')
    @patch('enmutils_int.lib.shm_utilities.UpgradeJob.create')
    def test_upgrade_setup_on_create_failure_logs_only(self, mock_create, *_):
        mock_create.side_effect = Exception("Some Exception")
        self.shm_util.upgrade_setup(user=Mock(), nodes=self.nodes, use_default=True, log_only=True, pib_values=self.PIB_VALUES)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.get_node_list')
    def test_get_nodes_for_shm_27__returns_as_expected(self, mock_get_node):
        mock_get_node.side_effect = [["SIU02_01", "SIU02_02"], ["TCU02_01", "TCU02_02"]]
        nodes = ["SIU02_01", "SIU02_02", "TCU02_01", "TCU02_02"]
        expected = (["SIU02_01", "SIU02_02"], ["TCU02_01", "TCU02_02"], nodes, 2)
        self.assertEqual(self.shm_util.get_nodes_for_shm_27(nodes), expected)

    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.update_file_details_and_create_archive')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file')
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage')
    @patch('enmutils_int.lib.shm_utilities.SoftwareOperations.import_package')
    def test_create_and_import_software_package__raises_enm_application_error(self, mock_import, mock_package,
                                                                              mock_file_exists, mock_del_file, *_):
        mock_import.side_effect = Exception
        package = Mock()
        package.name = "CXP_1920"
        package.new_dir = "/home/enmutils/shm/CXP_1920"
        mock_package.return_value = package
        node = Mock()
        node.primary_type = "ERBS"
        self.assertRaises(EnmApplicationError, self.shm_util.create_and_import_software_package, user=Mock(),
                          nodes=[node], use_default=False, pib_values=self.PIB_VALUES)
        self.assertFalse(mock_file_exists.called)
        self.assertFalse(mock_del_file.called)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.update_file_details_and_create_archive')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage')
    @patch('enmutils_int.lib.shm_utilities.SoftwareOperations.import_package')
    def test_create_and_import_software_package__returns_software_package(self, mock_import, mock_package,
                                                                          mock_del_file, *_):
        mock_import.return_value = None
        package = Mock()
        package.name = "CXP_1920"
        package.new_dir = "/home/enmutils/shm/CXP_1920"
        mock_package.return_value = package
        node = Mock()
        node.primary_type = "ERBS"
        upgrade_package = self.shm_util.create_and_import_software_package(user=Mock(), nodes=[node], use_default=False,
                                                                           profile=self, pib_values=self.PIB_VALUES)
        self.assertEqual("CXP_1920", upgrade_package.get("software_package").name)
        self.assertTrue(mock_del_file.called)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_dir_exist', return_value=False)
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.set_package_values')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.edit_file_values_for_asu')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.install_unzip')
    @patch('enmutils_int.lib.shm_utilities.SoftwareOperations.import_package')
    @patch('enmutils_int.lib.shm_utilities.os')
    def test_update_file_details_and_create_archive__returns_asu_package(self, mock_os, *_):
        self.pkg.file_paths = ["nmsinfo.xml", "ucf.xml"]
        mock_os.path.exists.return_value = True
        self.pkg.update_file_details_and_create_archive()

    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.parse_values_in_xml_file')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    def test_edit_file_values_for_asu__success(self, mock_run, *_):
        self.pkg.node_identity = "CXP9024418/15"
        self.pkg.existing_package = "CXP9024418/15-R31A209"
        self.pkg.identity = "CXP9024418_12"
        self.pkg.node_mim = "R31A209"
        self.pkg.smo_info = 'nmsinfo.xml'
        self.pkg.file_paths = {'nmsinfo.xml': 'smoinfo', 'ucf': 'ucf.xml'}
        self.pkg.edit_file_values_for_asu()
        self.assertEqual(mock_run.call_count, 5)

    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.parse_values_in_xml_file')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.run_cmd_and_evaluate_rc')
    def test_edit_file_values_for_asu__not_success(self, mock_run, *_):
        self.pkg.identity = "CXP9024418_12"
        self.pkg.smo_info = 'nmsinfo.xml'
        self.pkg.file_paths = {'nmsinfo.xml': 'smoinfo', 'ucf': 'ucf.xml'}
        self.pkg.edit_file_values_for_asu()
        self.assertEqual(mock_run.call_count, 1)

    @patch('enmutils_int.lib.shm_utilities.minidom.parse')
    @patch('enmutils_int.lib.shm_utilities.minidom.Element.getElementsByTagName')
    def test_parse_values_in_xml_file__success(self, *_):
        self.pkg.parse_values_in_xml_file('nmsinfo.xml', 'UpgradePackage', 'name')

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage.update_file_details_and_create_archive')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage')
    @patch('enmutils_int.lib.shm_utilities.SoftwareOperations.import_package')
    def test_create_and_import_software_package__file_does_not_exist_for_remove(self, mock_import, mock_package, *_):
        mock_import.return_value = None
        package = Mock()
        package.name = "CXP_1920"
        package.new_dir = "/home/enmutils/shm/CXP_1920"
        mock_package.return_value = package
        node = Mock()
        node.primary_type = "BSC"
        upgrade_package = self.shm_util.create_and_import_software_package(user=Mock(), nodes=[node], use_default=False,
                                                                           profile=self, pib_values=self.PIB_VALUES)
        self.assertEqual("CXP_1920", upgrade_package.get("software_package").name)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file', return_value=True)
    @patch('enmutils_int.lib.shm_utilities.SoftwareOperations.import_package')
    @patch('enmutils_int.lib.shm_utilities.SoftwarePackage')
    def test_create_and_import_software_package_moves_non_default(self, mock_package, *_):
        node = Mock()
        node.primary_type = "MLTN"
        package = Mock()
        package.name = "CXP_1920"
        mock_package.new_dir.return_value = None
        mock_package.return_value = package
        upgrade_package = self.shm_util.create_and_import_software_package(user=Mock(), nodes=[node], use_default=False,
                                                                           pib_values=self.PIB_VALUES)
        self.assertEqual("CXP_1920", upgrade_package.get("software_package").name)

    def test_package_upgrade_list_radio_node(self):
        self.shm_util.package_upgrade_list(self.radio_nodes, self.radio_package, node_type="RadioNode")

    def test_package_upgrade_list_other_nodes(self):
        self.shm_util.package_upgrade_list(self.radio_nodes, self.radio_package, node_type="ErbsNode")

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    def test_upgrade_delete_radio_node_success(self, *_):
        response_1 = Mock()
        response_2 = Mock()
        response_1.status_code = 200
        response_1.ok = True
        response_2.json.return_value = {"totalCount": 2, 'result': [
            {"jobId": "281474984037012", "jobTemplateId": "123132",
             "jobName": "ABC_RadioNode_pnV2", "jobType": "BACKUP", "createdBy": "user_2",
             "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED",
             "result": "SUCCESS", "startDate": "12", "endDate": "13",
             "creationTime": "", "periodic": False, "totalNoOfNEs": "1",
             "jobTemplateIdAsLong": 123123, "jobIdAsLong": 123123, "comment": []}]}
        response_2.ok = True
        response_2.status_code = 200
        self.user.post.side_effect = [response_1, response_2, response_2]
        self.shm_util.upgrade_delete(self.user, self.radio_nodes, self.radio_package, job_name="ABC_RadioNode_pnV2")

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    @patch('enmutils_int.lib.shm_job.sleep', return_value=0)
    def test_upgrade_delete_erbs_node_success(self, *_):
        response_1 = Mock()
        response_2 = Mock()
        response_1.status_code = 200
        response_1.ok = True
        response_2.json.return_value = {"totalCount": 2, 'result': [
            {"jobId": "281474984037012", "jobTemplateId": "123132",
             "jobName": "ABC_ERBS_pnV2", "jobType": "BACKUP", "createdBy": "user_2",
             "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED",
             "result": "SUCCESS", "startDate": "12", "endDate": "13",
             "creationTime": "", "periodic": False, "totalNoOfNEs": "1",
             "jobTemplateIdAsLong": 123123, "jobIdAsLong": 123123, "comment": []}]}
        response_2.ok = True
        response_2.status_code = 200
        self.user.post.side_effect = [response_1, response_2, response_2]
        self.shm_util.upgrade_delete(self.user, self.nodes, self.radio_package, job_name="ABC_ERBS_pnV2")

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_upgrade_delete_mltn_node_success(self, mock_log, *_):
        self.shm_util.upgrade_delete(self.user, self.mltn_nodes, self.radio_package, job_name="ABC_ERBS_pnV2")
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    @patch('time.sleep', side_effect=lambda _: None)
    def test_upgrade_delete_node_raises_exception(self, *_):
        response_1 = Mock()
        response_1.status_code = 403
        self.user.post.return_value = response_1
        self.assertRaises(Exception, self.shm_util.upgrade_delete, self.user, self.radio_nodes, self.radio_package,
                          job_name="ABC_ERBS_pnV2")

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    @patch('time.sleep', side_effect=lambda _: None)
    def test_upgrade_delete_node_dont_raise_exception(self, *_):
        response_1 = Mock()
        response_1.status_code = 403
        self.user.post.return_value = response_1
        self.shm_util.upgrade_delete(self.user, self.radio_nodes, self.radio_package, job_name="ABC_ERBS_pnV2",
                                     log_only=True)

    @patch('enmutils_int.lib.shm_utilities.SHMUtils.package_upgrade_list')
    def test_upgrade_delete_without_nodes(self, *_):
        self.assertRaises(EnvironmentError, self.shm_util.upgrade_delete, self.user, self.empty_nodes, self.radio_package)

    @patch("enmutils_int.lib.shm_utilities.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch('enmutils_int.lib.shm_utilities.node_pool_mgr.remove_profile_from_nodes')
    def test_deallocate_unused_nodes__is_successful_if_service_cannot_be_used(self, mock_remove_profile_from_nodes, *_):
        profile = Mock(NAME="SHM_01")
        nodes = [Mock()]
        self.shm_util.deallocate_unused_nodes(nodes, profile, allocate=True)
        mock_remove_profile_from_nodes.assert_called_with(nodes, "SHM_01")

    @patch("enmutils_int.lib.shm_utilities.nodemanager_adaptor.can_service_be_used", return_value=True)
    @patch('enmutils_int.lib.shm_utilities.nodemanager_adaptor.deallocate_nodes')
    def test_deallocate_unused_nodes__is_successful_if_service_can_be_used(self, mock_deallocate_nodes, *_):
        profile = Mock(NAME="SHM_01")
        nodes = [Mock()]
        self.shm_util.deallocate_unused_nodes(nodes, profile)
        mock_deallocate_nodes.assert_called_with(profile, unused_nodes=nodes)

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_deallocate_unused_nodes__does_nothing_if_no_nodes_to_be_deallocated(
            self, mock_debug):
        profile = Mock(NAME="SHM_01")
        nodes = []
        self.shm_util.deallocate_unused_nodes(nodes, profile)
        mock_debug.assert_called_with("No unused nodes to be deallocated")

    @patch('enmutils_int.lib.shm_utilities.nodemanager_adaptor.can_service_be_used', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.shm_utilities.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.load_node.ERBSLoadNode._persist')
    def test_deallocate_unused_nodes__if_allocated(self, mock_persist, *_):
        profile = Mock(NAME="SHM_01")
        nodes = [load_node(node_id="ERBS01", _is_exclusive=True, profiles=[])]
        self.shm_util.deallocate_unused_nodes(nodes, profile)
        self.assertEqual(mock_persist.call_count, 0)

    @patch('enmutils_int.lib.shm_utilities.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.load_node.ERBSLoadNode._persist')
    def test_deallocate_unused_nodes_does_not_if_no_nodes(self, mock_persist, *_):
        profile = Mock(NAME="SHM_01")
        self.shm_util.deallocate_unused_nodes([], profile)
        self.assertEqual(mock_persist.call_count, 0)

    @patch('enmutils_int.lib.shm_utilities.DeleteInactiveSoftwarePackageOnNodeJob.create')
    def test_upgrade_delete_inactive_radio_node_success(self, mock_create, *_):
        response_1 = Mock()
        response_2 = Mock()
        response_1.status_code = 200
        response_1.ok = True
        response_2.json.return_value = {"totalCount": 2, 'result': [
            {"jobId": "281474984037012", "jobTemplateId": "123132",
             "jobName": "ABC_RadioNode_pnV2", "jobType": "BACKUP", "createdBy": "user_2",
             "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED",
             "result": "SUCCESS", "startDate": "12", "endDate": "13",
             "creationTime": "", "periodic": False, "totalNoOfNEs": "1",
             "jobTemplateIdAsLong": 123123, "jobIdAsLong": 123123, "comment": []}]}
        response_2.ok = True
        self.user.post.side_effect = [response_1, response_2, response_2]
        self.shm_util.upgrade_delete_inactive(self.user, self.radio_nodes, job_name="ABC_RadioNode_pnV2")
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.shm_utilities.DeleteInactiveSoftwarePackageOnNodeJob.create')
    def test_upgrade_delete_inactive_erbs_node_success(self, mock_create, *_):
        response_1 = Mock()
        response_2 = Mock()
        response_1.status_code = 200
        response_1.ok = True
        response_2.json.return_value = {"totalCount": 2, 'result': [
            {"jobId": "281474984037012", "jobTemplateId": "123132",
             "jobName": "ABC_ERBS_pnV2", "jobType": "BACKUP", "createdBy": "user_2",
             "noOfMEs": 0, "progress": 100.0, "status": "COMPLETED",
             "result": "SUCCESS", "startDate": "12", "endDate": "13",
             "creationTime": "", "periodic": False, "totalNoOfNEs": "1",
             "jobTemplateIdAsLong": 123123, "jobIdAsLong": 123123, "comment": []}]}
        response_2.ok = True
        self.user.post.side_effect = [response_1, response_2, response_2]
        self.shm_util.upgrade_delete_inactive(self.user, self.nodes, job_name="ABC_ERBS_pnV2")
        self.assertTrue(mock_create.called)

    @patch('time.sleep', side_effect=lambda _: None)
    def test_upgrade_delete_inactive_node_raises_exception(self, *_):
        response_1 = Mock()
        response_1.status_code = 403
        self.user.post.return_value = response_1
        self.assertRaises(Exception, self.shm_util.upgrade_delete_inactive,
                          self.user, self.radio_nodes, job_name="ABC_ERBS_pnV2")

    @patch('time.sleep', side_effect=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_upgrade_delete_inactive_node_log_only_true(self, mock_debug, *_):
        response_1 = Mock()
        response_1.status_code = 403
        self.user.post.return_value = response_1
        self.shm_util.upgrade_delete_inactive(self.user, self.radio_nodes,
                                              job_name="ABC_ERBS_pnV2", log_only=True)
        self.assertTrue(mock_debug.called)

    def test_upgrade_delete_inactive_without_nodes(self):
        self.assertRaises(EnvironmentError, self.shm_util.upgrade_delete_inactive, self.user, self.empty_nodes, self.radio_package)

    @patch('enmutils_int.lib.shm_utilities.netsim_operations.NetsimOperation.execute_command_string')
    def test_set_netsim_values__no_nodes(self, mock_execute_command_string):
        self.assertRaises(FailedNetsimOperation, self.shm_util.set_netsim_values([], ["Param"]))
        self.assertFalse(mock_execute_command_string.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.shm_utilities.netsim_operations.NetsimOperation')
    def test_set_netsim_values__success(self, mock_netsim_operation, _):
        mock_nodes = [Mock()]
        mock_netsim_operation.return_value.execute_command_string.side_effect = [FailedNetsimOperation('error'), mock_nodes]
        self.shm_util.set_netsim_values(mock_nodes, ["Param"])
        mock_netsim_operation.assert_called_with(mock_nodes)
        mock_netsim_operation.return_value.execute_command_string.assert_called_with("Param")

    def test_validate_omi_equals_nmi__returns_as_expected(self):
        data = [
            u'NetworkElement', u'NodeId\tnodeModelIdentity\tossModelIdentity',
            u'MSC25BSC50\tBSC-G19.Q2-R1Y-APG43L-3.6.0-R7D\tBSC-G19.Q2-R1Y-APG43L-3.6.0-R7D',
            u'', u'1 instance(s)'
        ]
        self.assertEqual(self.shm_util.validate_omi_equals_nmi(data), [u'MSC25BSC50'])

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_mim_version")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_exact_identity")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version", return_value="R05210411")
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_set_package_values(self, *_):
        scunode = Mock()
        scunode.node_id = 'testNode'
        scunode.primary_type = 'SCU'
        scunode.platform = 'ECIM'
        scunode.mim_version = 'L.1.120'
        software_package = SoftwarePackage([scunode], self.user, profile_name="SHM_44", use_default=False,
                                           identity='CXP9017878_3', package=["package.xml"],
                                           existing_package='CXP9017878_3_P24A', pib_values=self.PIB_VALUES)
        software_package.set_package_values(primary_type='SCU')

    @patch("enmutils_int.lib.shm_utilities.SHMUtils.check_and_update_pib_values_for_packages")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_mim_version")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_exact_identity")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_identity_from_ne_describe")
    @patch("enmutils_int.lib.shm_utilities.SoftwarePackage.get_revision_from_ne_product_version",
           return_value="R05210411")
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_set_package_values__for_asu_profile(self, *_):
        self.pkg.set_package_values(primary_type='RadioNode')

    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.shm_utilities.log.logger")
    def test_check_and_update_pib_values_for_packages__does_not_call_pib_for_other_deployments(self, mock_log, mock_dep_config, mock_get_pib, _):
        mock_dep_config.return_value = "forty_network"
        SHMUtils.check_and_update_pib_values_for_packages(self.PIB_VALUES)
        self.assertTrue(mock_log.debug.called)
        self.assertFalse(mock_get_pib.called)

    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.shm_utilities.log.logger")
    def test_check_and_update_pib_values_for_packages__calls_error_log_when_exception_is_raised(self, mock_log, mock_dep_config, mock_get_pib, _):
        mock_get_pib.side_effect = Exception
        mock_dep_config.return_value = "extra_small_network"
        SHMUtils.check_and_update_pib_values_for_packages(self.PIB_VALUES)
        self.assertTrue(mock_log.error.called)

    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.shm_utilities.log.logger")
    def test_check_and_update_pib_values_for_packages__has_calls_as_expected_for_radionode(self, mock_log, mock_dep_config, mock_get_pib, _):
        mock_get_pib.side_effect = ["1", "5"]
        mock_dep_config.return_value = "extra_small_network"
        pib_values = {"SOFTWARE_PACKAGE_LOCK_EXPIRY_IN_DAYS": "1", "NUMBER_OF_SOFTWARE_PACKAGES_TO_RETAIN_FOR_RADIONODE": "5"}
        SHMUtils.check_and_update_pib_values_for_packages(pib_values=pib_values)
        self.assertTrue(mock_get_pib.call_count == 2)
        self.assertTrue(mock_log.debug.call_count == 3)

    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.shm_utilities.log.logger")
    def test_check_and_update_pib_values_for_packages__has_calls_as_expected_for_other_nodes(self, mock_log, mock_dep_config, mock_get_pib, _):
        mock_get_pib.side_effect = "1"
        mock_dep_config.return_value = "extra_small_network"
        SHMUtils.check_and_update_pib_values_for_packages(self.PIB_VALUES)
        self.assertTrue(mock_get_pib.call_count == 1)
        self.assertTrue(mock_log.debug.call_count == 2)

    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.shm_utilities.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.shm_utilities.log.logger")
    def test_check_and_update_pib_values_for_packages__calls_update_when_needed(self, mock_log, mock_dep_config, mock_get_pib, mock_update_pib):
        mock_get_pib.side_effect = ["10", "40"]
        mock_dep_config.return_value = "extra_small_network"
        pib_values = {"SOFTWARE_PACKAGE_LOCK_EXPIRY_IN_DAYS": "1", "NUMBER_OF_SOFTWARE_PACKAGES_TO_RETAIN_FOR_RADIONODE": "5"}
        SHMUtils.check_and_update_pib_values_for_packages(pib_values)
        self.assertTrue(mock_get_pib.call_count == 2)
        self.assertTrue(mock_update_pib.call_count == 2)
        self.assertTrue(mock_log.debug.call_count == 3)


class SHMLicenseUnitTests(unittest2.TestCase):
    def setUp(self):

        unit_test_utils.setup()
        self.user = Mock()
        node = Mock()
        node.node_id = "testnode"
        self.nodes = [node, node]
        self.shm_license = SHMLicense(user=self.user, node=self.nodes[0])

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.raise_for_status')
    def test_delete_license_success(self, mock_log, *_):
        response = Mock()
        self.shm_license.fingerprint_id = "ABCD"
        response.json.return_value = {"status": "success"}
        self.user.post.return_value = response
        self.shm_license.delete()
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.raise_for_status')
    def test_delete_license_success_with_delete_on_enm_true(self, mock_log, *_):
        response = Mock()
        self.shm_license.fingerprint_id = "ABCD"
        response.json.return_value = {"status": "success"}
        self.user.post.return_value = response
        self.shm_license.delete(delete_on_enm_only=True)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file')
    @patch('enmutils_int.lib.shm_utilities.raise_for_status')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_teardown_delete_license_success(self, mock_log, *_):
        response = Mock()
        self.shm_license.path_to_license_key = "/tmp/license.sh"
        self.shm_license.fingerprint_id = "ABCD"
        response.json.return_value = {"status": "success"}
        self.user.post.return_value = response
        self.shm_license._teardown()
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense._get_fingerprint')
    def test_delete_license_raises_http_error_in_raise_for_status(self, *_):
        response = Mock()
        response.json.return_value = {"status": "failure"}
        response.status_code = 599
        self.user.post.return_value = response
        self.shm_license.path_to_license_key = "/tmp/license.sh"
        self.assertRaises(EnmApplicationError, self.shm_license.delete)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense._get_fingerprint')
    def test_delete_license_raises_http_error_with_failure(self, *_):
        response = Mock()
        response.json.return_value = {"status": "failure"}
        response.status_code = 100
        self.user.post.return_value = response
        self.shm_license.path_to_license_key = "/tmp/license.sh"
        self.assertRaises(EnmApplicationError, self.shm_license.delete)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense._get_fingerprint')
    def test_delete_license_raises_http_error(self, *_):
        response = Mock()
        response.json.return_value = {"status": "failure"}
        response.status_code = 601
        self.user.post.return_value = response
        self.shm_license.path_to_license_key = "/tmp/license.sh"
        self.assertRaises(EnmApplicationError, self.shm_license.delete)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.filesystem.delete_file', side_effect=RuntimeError)
    def test_delete_license_raises_runtime_error(self, *_):
        self.shm_license.path_to_license_key = "/tmp/license.sh"
        self.assertRaises(EnmApplicationError, self.shm_license.delete)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.SHMLicense._get_fingerprint', side_effect=AttributeError)
    def test_delete_license_raises_attribute_error(self, *_):
        self.assertRaises(Exception, self.shm_license.delete, delete_on_enm_only=True)

    @patch('enmutils.lib.enm_user_2.User.enm_execute')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_get_fingerprint_success(self, mock_log, _):
        node_id = self.nodes[0].node_id
        response = Mock()
        response.get_output.return_value = [u'fingerprint : {0}_fp ,1 instance(s)'.format(node_id)]
        self.user.enm_execute.return_value = response
        self.shm_license._get_fingerprint()
        self.assertEqual(self.shm_license.fingerprint_id, "%s%s" % (node_id, "_fp"))
        self.assertTrue(mock_log.called)

    def test_get_fingerprint_raises_scriptenginevalidationerror_error(self):
        node_id = self.nodes[0].node_id
        response = Mock()
        response.get_output.return_value = [u' : {0}_fp ,1 instance(s)'.format(node_id)]
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.shm_license._get_fingerprint)

    @patch('enmutils_int.lib.shm_utilities.re.search', side_effect=AttributeError("Error"))
    def test_get_fingerprint_raises_attribute_error(self, *_):
        node_id = self.nodes[0].node_id
        response = Mock()
        response.get_output.return_value = [u'fingerprint : {0}_fp ,1 instance(s)'.format(node_id)]
        self.user.enm_execute.return_value = response
        self.assertRaises(AttributeError, self.shm_license._get_fingerprint)

    @patch('enmutils_int.lib.shm_utilities.filesystem')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_generate_license_success(self, mock_log, mock_local_cmd, *_):
        self.shm_license.fingerprint_id = "ABCD"
        response = mock_local_cmd.return_value
        response.stdout = ["has been created under your home folder"]
        self.shm_license.generate()
        self.assertTrue(mock_log.called)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch('enmutils_int.lib.shm_utilities.filesystem')
    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    def test_install_license_script_dependencies_success1(self, mock_unzip,
                                                          mock_local_cmd,
                                                          mock_log, mock_join, *_):
        mock_join.return_value = "/root/path"
        self.shm_license.install_license_script_dependencies()
        self.assertTrue(mock_unzip.return_value.install_unzip.called)
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    def test_install_license_script_dependencies_success2(self, mock_unzip,
                                                          mock_local_cmd, mock_log, mock_join,
                                                          mock_filesystem):
        mock_join.return_value = "/root/path"
        mock_filesystem.return_value = False
        self.shm_license.install_license_script_dependencies()
        self.assertTrue(mock_unzip.return_value.install_unzip.called)
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils')
    def test_install_license_script_dependencies_success3(self, mock_unzip,
                                                          mock_local_cmd, mock_log, mock_join,
                                                          mock_filesystem):
        mock_join.return_value = "/root/path"
        mock_filesystem.side_effect = [False, True]
        self.shm_license.install_license_script_dependencies()
        self.assertTrue(mock_unzip.return_value.install_unzip.called)
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch('enmutils_int.lib.shm_utilities.filesystem.does_file_exist')
    @patch('enmutils_int.lib.shm_utilities.os.path.join')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    @patch('enmutils_int.lib.shm_utilities.SHMUtils.install_unzip')
    def test_install_license_script_dependencies_success4(self, mock_unzip,
                                                          mock_local_cmd, mock_log, mock_join, mock_filesystem):
        mock_join.return_value = "/root/path"
        response = Mock()
        response.return_value = 0
        mock_filesystem.side_effect = [False, True]
        self.shm_license.install_license_script_dependencies()
        self.assertTrue(mock_unzip.called)
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.SHMLicense.get_imported_keys')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense.delete')
    @patch('enmutils_int.lib.shm_utilities.raise_for_status')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_import_keys_success1(self, mock_log, mock_raise, mock_delete, mock_importkey, *_):
        user = Mock()
        shm_license = SHMLicense(user=user, node=self.nodes[0])
        user.post.return_value = ["There is no available license key."]
        shm_license.fingerprint_id = "ABC"
        mock_importkey.return_value = ["ABC", "DEF"]
        shm_license.path_to_license_key = "There is no available license key."
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            shm_license.import_keys()
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_raise.called)
        self.assertTrue(mock_log.called)

    @patch('time.sleep', return_value=lambda _: None)
    def test_import_keys_environ_error(self, *_):
        self.assertRaises(EnvironmentError, self.shm_license.import_keys)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.SHMLicense.get_imported_keys')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense.delete')
    def test_import_keys_raise_http_error(self, mock_delete, mock_importkey, *_):
        self.shm_license.path_to_license_key = "There is no available license key."
        self.shm_license.fingerprint_id = "ABC"
        mock_importkey.return_value = ["ABC", "DEF"]
        mock_delete.side_effect = HTTPError
        self.assertRaises(HTTPError, self.shm_license.import_keys)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.SHMLicense.get_imported_keys')
    @patch('enmutils_int.lib.shm_utilities.raise_for_status')
    @patch('enmutils_int.lib.shm_utilities.log.logger.debug')
    def test_import_keys_success2(self, mock_log, mock_raise, mock_importkey, *_):
        user = Mock()
        shm_license = SHMLicense(user=user, node=self.nodes[0])
        user.post.return_value = ["There is no available license key."]
        shm_license.fingerprint_id = "ABCDEF"
        mock_importkey.return_value = ["ABC", "DEF"]
        shm_license.path_to_license_key = "There is no available license key."
        mock_open_file = mock_open()
        with patch('__builtin__.open', mock_open_file):
            shm_license.import_keys()
        self.assertTrue(mock_raise.called)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.shm_utilities.filesystem')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_generate_license_raises_runtime_error(self, mock_local_cmd, *_):
        self.shm_license.fingerprint_id = "ABCD"
        response = mock_local_cmd.return_value
        response.stdout = ["wrong response"]
        self.assertRaises(RuntimeError, self.shm_license.generate)

    @patch('enmutils_int.lib.shm_utilities.filesystem')
    @patch('enmutils_int.lib.shm_utilities.SHMLicense._get_fingerprint')
    @patch('enmutils_int.lib.shm_utilities.run_local_cmd')
    def test_generate_get_finger_print_called(self, mock_local_cmd, mock_finger_print, *_):
        response = mock_local_cmd.return_value
        response.stdout = ["has been created under your home folder"]
        self.shm_license.generate()
        self.assertTrue(mock_finger_print.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.shm_utilities.raise_for_status', side_effect=[HTTPError, 201])
    def test_get_license_success(self, *_):
        response = Mock()
        response.json.return_value = {"result": [{'fingerprint': 'test'}]}
        self.user.post.return_value = response
        self.shm_license.get_imported_keys(self.user)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
