#!/usr/bin/env python
import unittest2
from mock import call, patch, MagicMock, Mock

from testslib import unit_test_utils
from parameterizedtestcase import ParameterizedTestCase
from enmutils.lib.exceptions import ShellCommandReturnedNonZero, ValidationError
from enmutils.lib.filesystem import delete_file, does_file_exist
from enmutils_int.lib.em import pull_config_files_tarball, configure_assigned_nodes, get_poids, _get_tarball_path, _is_corrupted, remove
from enmutils_int.lib.workload import em_01


class EmFlowExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.execute_flow")
    def test_em_01_profile_execute_flow__successful(self, mock_flow):
        em_01.EM_01().run()
        self.assertEqual(mock_flow.call_count, 1)


class EmUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()
        # unit_test_utils.mock_admin_session()
        self.tarball_path = '/tmp/enmutils/workload-profiles-1.0.1.tar.gz'
        if does_file_exist(self.tarball_path, verbose=False):
            delete_file(self.tarball_path)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.em._get_tarball_path')
    @patch('enmutils_int.lib.em.nexus.download_artifact_from_nexus')
    def test_attempt_is_made_to_pull_tarball_from_nexus_if_doesnt_exist(self, mock_nexus, mock_get_tarball_path):
        mock_nexus.return_value = self.tarball_path
        mock_get_tarball_path.return_value = self.tarball_path

        pull_config_files_tarball()

        self.assertTrue(mock_get_tarball_path.called_once)
        self.assertTrue(mock_nexus.called_once)
        self.assertTrue(mock_nexus.has_calls(call('workload-profiles', '1.0.1', 'tar.gz', '/tmp/enmutils')))

    @patch('enmutils_int.lib.em._is_corrupted')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    @patch('enmutils_int.lib.em.nexus.download_artifact_from_nexus')
    def test_new_tarball_gets_pulled_from_nexus_if_corrupted(self, mock_nexus, mock_get_tarball_path, mock_does_file_exist, mock_is_corrupted):
        mock_nexus.return_value = self.tarball_path
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        mock_is_corrupted.return_value = True

        pull_config_files_tarball()

        self.assertTrue(mock_get_tarball_path.called_once)
        self.assertTrue(mock_does_file_exist.called_once)
        self.assertTrue(mock_is_corrupted.called)
        self.assertTrue(mock_nexus.called_once)
        self.assertTrue(mock_nexus.has_calls(call('workload-profiles', '1.0.1', 'tar.gz', '/tmp/enmutils')))

    @patch('enmutils_int.lib.em.remove')
    def test_is_corrupted__remove_successful(self, mock_remove):
        _is_corrupted("/tmp/enmutils")
        mock_remove.assert_called_with("/tmp/enmutils")

    @patch('enmutils_int.lib.em.remove')
    @patch('enmutils_int.lib.em.shell.run_local_cmd')
    def test_is_corrupted__successful(self, mock_run_local_cmd, _):
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        self.assertFalse(_is_corrupted("/tmp/enmutils"))

    @patch('enmutils_int.lib.em.remove', side_effect=OSError)
    def test_is_corrupted__raises_os_error(self, _):
        _is_corrupted("/tmp/enmutils")
        self.assertRaises(OSError, remove, "/tmp/enmutils")

    @patch("enmutils_int.lib.em.path")
    def test_get_tarball_path__returns_as_expected(self, mock_path):
        _get_tarball_path("a", "b", "c")
        mock_path.join.assert_called_with('/tmp/enmutils', "a-b.c")

    @patch('enmutils_int.lib.em._is_corrupted')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    @patch('enmutils_int.lib.em.nexus.download_artifact_from_nexus')
    def test_no_tarball_gets_pulled_from_nexus_if_exists(self, mock_nexus, mock_get_tarball_path, mock_does_file_exist, mock_is_corrupted):
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        mock_is_corrupted.return_value = False
        mock_nexus.return_value = self.tarball_path

        pull_config_files_tarball()

        self.assertTrue(mock_get_tarball_path.called_once)
        self.assertTrue(mock_does_file_exist.called_once)
        self.assertTrue(mock_is_corrupted.called)
        self.assertFalse(mock_nexus.called)
        self.assertTrue(mock_nexus.call_count == 0)

    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    @patch('enmutils_int.lib.em.nexus.download_artifact_from_nexus')
    def test_exception_when_cant_pull_tarball_from_nexus(self, mock_nexus, mock_get_tarball_path, mock_does_file_exist):
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = False
        mock_nexus.return_value = False

        self.assertRaises(ValidationError, pull_config_files_tarball)
        self.assertTrue(mock_get_tarball_path.called_once)
        self.assertTrue(mock_does_file_exist.called_once)
        self.assertTrue(mock_nexus.called)

    @patch('enmutils_int.lib.em._setup_user_cmds_on_nodes')
    @patch('enmutils_int.lib.em.shell.run_remote_cmd')
    @patch('enmutils_int.lib.netsim_executor.deploy_script')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    def test_tarball_gets_uploaded_to_netsim(self, mock_get_tarball_path, mock_does_file_exist, mock_deploy_script, mock_run_remote_cmd, mock_setup_user_cmds_on_nodes):
        nodes = unit_test_utils.setup_test_node_objects(2)
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        response = MagicMock(rc=0)
        mock_run_remote_cmd.return_value = response

        configure_assigned_nodes(nodes, self.tarball_path)

        self.assertTrue(mock_deploy_script.call_count == 2)
        self.assertTrue(mock_run_remote_cmd.call_count == 2)
        self.assertTrue(mock_setup_user_cmds_on_nodes.called)

    @patch('enmutils_int.lib.em._setup_user_cmds_on_nodes')
    @patch('enmutils_int.lib.em.shell.run_remote_cmd')
    @patch('enmutils_int.lib.em.nets_exec.deploy_script')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    def test_exception_when_impassible_to_upload_to_netsim(self, mock_get_tarball_path, mock_does_file_exist, mock_deploy_script, mock_run_remote_cmd, mock_setup_user_cmds_on_nodes):
        nodes = unit_test_utils.setup_test_node_objects(2)
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        response = MagicMock(rc=1)
        mock_run_remote_cmd.return_value = response

        self.assertRaises(ShellCommandReturnedNonZero, configure_assigned_nodes, nodes, self.tarball_path)

        self.assertTrue(mock_deploy_script.call_count == 1)
        self.assertTrue(mock_run_remote_cmd.call_count == 1)
        self.assertFalse(mock_setup_user_cmds_on_nodes.called)

    @patch('enmutils_int.lib.em._push_tarball_to_netsim')
    @patch('enmutils_int.lib.em.nets_exec.run_cmd')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    def test_exception_when_impassible_to_configure_nodes(self, mock_get_tarball_path, mock_does_file_exist, mock_run_cmd, _):
        nodes = unit_test_utils.setup_test_node_objects(2)
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        response = MagicMock(rc=1)
        mock_run_cmd.return_value = response

        self.assertRaises(ShellCommandReturnedNonZero, configure_assigned_nodes, nodes, self.tarball_path)

    @patch('enmutils_int.lib.em._push_tarball_to_netsim')
    @patch('enmutils_int.lib.em.nets_exec.run_cmd')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    @patch('enmutils_int.lib.em._get_tarball_path')
    def test_configure_nodes_succes_no_errors(self, mock_get_tarball_path, mock_does_file_exist, mock_run_cmd, _):
        nodes = unit_test_utils.setup_test_node_objects(2)
        mock_get_tarball_path.return_value = self.tarball_path
        mock_does_file_exist.return_value = True
        response = MagicMock(rc=0)
        mock_run_cmd.return_value = response

        configure_assigned_nodes(nodes, self.tarball_path)

    @patch('enmutils_int.lib.em._push_tarball_to_netsim')
    @patch('enmutils_int.lib.em.nets_exec.run_cmd')
    @patch('enmutils_int.lib.em._get_tarball_path')
    @patch('enmutils_int.lib.em.fs.does_file_exist')
    def test_configure_nodes_unsuccesful(self, mock_does_file_exist, *_):
        nodes = unit_test_utils.setup_test_node_objects(2)
        mock_does_file_exist.return_value = False
        configure_assigned_nodes(nodes, self.tarball_path)

    def test_get_poids_is_successful(self):
        node1, node2, node3 = Mock(poid="123"), Mock(poid=""), Mock(poid="456")
        self.assertEqual((['123', '456'], [node1, node3]), get_poids([node1, node2, node3]))

if __name__ == "__main__":
    unittest2.main(verbosity=2)
