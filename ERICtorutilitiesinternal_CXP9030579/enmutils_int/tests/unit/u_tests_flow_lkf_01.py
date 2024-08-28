import unittest2
from mock import Mock, patch, call

from enmutils.lib.exceptions import (EnvironError, EnvironWarning, NetsimError, ScriptEngineResponseValidationError)
from enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow import Lkf01Flow
from testslib import unit_test_utils


class LKF01UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.user.username = "TestLkfUser_u0"
        self.flow = Lkf01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["SomeRole"]
        node = Mock(primary_type='RadioNode', node_id='testNode')
        self.node = [node]
        self.flow.SAS_IP = None
        self.flow.CLEANUP = None
        self.flow.MAX_NODES = 2
        self.flow.NUM_NODES_PER_BATCH = 2

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.cleanup_imported_keys_on_shmserv')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.is_elis', return_value=True)
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.exchange_nodes")
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_nodes_list_by_attribute',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.execute_and_check_lkf_job')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_configuration_setup')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_prerequisites',
           return_value=([Mock()], [Mock()]))
    def test_execute_flow__success(self, mock_lkf_prerequisites, mock_lkf_setup, mock_lkf_job, mock_user,
                                   mock_nodes, *_):
        self.flow.CLEANUP = True
        mock_user.return_value = [self.user]
        self.flow.execute_flow()
        mock_lkf_prerequisites.assert_called_with(self.user, mock_nodes.return_value)
        mock_lkf_setup.assert_called_with(mock_lkf_prerequisites.return_value[1])
        mock_lkf_job.assert_called_with(self.user, mock_lkf_prerequisites.return_value[0])

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.cleanup_imported_keys_on_shmserv')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_nodes_list_by_attribute',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_prerequisites',
           return_value=([], [Mock()]))
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.is_elis')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.exchange_nodes")
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_configuration_setup')
    def test_execute_flow__adds_error_if_no_nodes(self, mock_setup, mock_error, *_):
        self.flow.execute_flow()
        self.assertIsInstance(mock_error.call_args[0][0], EnvironError)
        self.assertFalse(mock_setup.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.cleanup_imported_keys_on_shmserv')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_prerequisites',
           return_value=([Mock()], [Mock()]))
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_nodes_list_by_attribute',
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.exchange_nodes")
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.is_elis', side_effect=[EnvironError])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    def test_execute_flow__adds_exception_elis_not_configured(self, mock_error, *_):
        self.flow.execute_flow()
        self.assertIsInstance(mock_error.call_args[0][0], EnvironError)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.cleanup_imported_keys_on_shmserv')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_prerequisites')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.lkf_configuration_setup', side_effect=[True])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.create_profile_users')
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.exchange_nodes")
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_filtered_nodes_per_host',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_nodes_list_by_attribute',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    def test_execute_flow__adds_exception(self, mock_error, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_error.called)

    @patch('re.findall')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.get_enm_service_locations', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_filtered_nodes_per_host',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.set_administrator_state')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.get_pib_value_on_enm')
    def test_lkf_prerequisites__success(self, mock_pib_value, mock_admin_state, mock_filter_nodes, *_):
        mock_pib_value.return_value = 'url'
        self.flow.lkf_prerequisites(self.user, self.node)
        mock_filter_nodes.assert_called_with(self.node)
        mock_admin_state.assert_called_with(self.user, mock_filter_nodes.return_value)

    @patch('re.findall')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.get_pib_value_on_enm', return_value='[]')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.get_filtered_nodes_per_host',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.set_administrator_state')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.get_enm_service_locations')
    def test_lkf_prerequisites__raises_environ_error(self, mock_service, mock_admin_state, mock_filter_nodes, *_):
        self.assertRaises(EnvironError, self.flow.lkf_prerequisites, self.user, self.node)
        self.assertFalse(mock_service.called)
        mock_filter_nodes.assert_called_with(self.node)
        mock_admin_state.assert_called_with(self.user, mock_filter_nodes.return_value)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.arguments.split_list_into_chunks')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.EnmCli08Flow.get_mo')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.execute_command_on_enm_cli')
    def test_set_administrator_state__success(self, mock_execute, mock_get_mo, mock_chunks, *_):
        node1 = Mock(primary_type='RadioNode', node_id='testNode1')
        node2 = Mock(primary_type='RadioNode', node_id='testNode2')
        nodes = [node1, node2]
        mock_get_mo.side_effect = ['SubNetwork=testNode1,MeContext=testNode1,ManagedElement=testNode1,NodeSupport=1,'
                                   'LicenseSupport=1,InstantaneousLicensing=1',
                                   'SubNetwork=testNode2,MeContext=testNode2,ManagedElement=testNode2,NodeSupport=1,'
                                   'LicenseSupport=1,InstantaneousLicensing=1']
        mock_chunks.return_value = [['SubNetwork=testNode1,MeContext=testNode1,ManagedElement=testNode1,NodeSupport=1,'
                                     'LicenseSupport=1,InstantaneousLicensing=1',
                                     'SubNetwork=testNode2,MeContext=testNode2,ManagedElement=testNode2,NodeSupport=1,'
                                     'LicenseSupport=1,InstantaneousLicensing=1']]
        fdns = ";".join(mock_chunks.return_value[0])
        lock_cmd = "cmedit set {0} administrativeState=LOCKED".format(fdns)
        unlock_cmd = 'cmedit set {0} administrativeState=UNLOCKED'.format(fdns)
        mock_execute.side_effect = [Mock(), Mock()]
        self.flow.set_administrator_state(self.user, nodes)
        self.assertEqual(mock_execute.call_count, 2 * len(mock_chunks.return_value))
        self.assertTrue(mock_execute.mock_calls == [call(self.user, lock_cmd),
                                                    call(self.user, unlock_cmd)])

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.arguments.split_list_into_chunks')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.EnmCli08Flow.get_mo')
    def test_set_administrator_state__raises_environ_error(self, mock_get_mo, *_):
        mock_get_mo.side_effect = [Exception]
        self.assertRaises(EnvironError, self.flow.set_administrator_state, self.user, self.node)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.arguments.split_list_into_chunks')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.EnmCli08Flow.get_mo')
    def test_set_administrator_state__adds_exception_for_empty_fdn(self, mock_get_mo, *_):
        mock_get_mo.return_value = []
        self.assertRaises(EnvironError, self.flow.set_administrator_state, self.user, self.node)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.arguments.split_list_into_chunks')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.EnmCli08Flow.get_mo')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.execute_command_on_enm_cli')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    def test_set_administrator_state__adds_error_if_cmd_fails(self, mock_error, mock_execute, mock_get_mo,
                                                              mock_chunks, *_):
        mock_get_mo.return_value = ('SubNetwork=testNode,MeContext=testNode,ManagedElement=testNode,NodeSupport=1,'
                                    'LicenseSupport=1,InstantaneousLicensing=1')
        mock_chunks.return_value = [[mock_get_mo.return_value]]
        lock_cmd = "cmedit set {0} administrativeState=LOCKED".format(mock_chunks.return_value[0][0])
        unlock_cmd = 'cmedit set {0} administrativeState=UNLOCKED'.format(mock_chunks.return_value[0][0])
        mock_execute.side_effect = [Mock(), ScriptEngineResponseValidationError]
        self.flow.set_administrator_state(self.user, self.node)
        self.assertIsInstance(mock_error.call_args[0][0], EnvironWarning)
        self.assertEqual(mock_execute.call_count, 2 * len(mock_chunks.return_value))
        self.assertTrue(mock_execute.mock_calls == [call(self.user, lock_cmd),
                                                    call(self.user, unlock_cmd)])

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_remote_cmd')
    def test_is_elis__returns_true(self, mock_run, _):
        response = Mock()
        response.rc = 0
        response.stdout = "PID"
        mock_run.return_value = response
        self.flow.is_elis()

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_remote_cmd')
    def test_is_elis__raises_environ_error(self, mock_run, _):
        response = Mock()
        response.rc = 1
        response.stdout = ""
        mock_run.return_value = response
        self.assertRaises(EnvironError, self.flow.is_elis)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_generate_sftp_keys__success(self, mock_run, mock_file_exists, _):
        cmd_response = Mock()
        cmd_response.rc = 0
        mock_run.return_value = cmd_response
        mock_file_exists.return_value = True
        self.flow.generate_sftp_keys()

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_generate_sftp_keys__raises_environ_error_if_cmd_fails(self, mock_run, *_):
        cmd_response = Mock()
        cmd_response.rc = 1
        mock_run.return_value = cmd_response
        self.assertRaises(EnvironError, self.flow.generate_sftp_keys)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist', return_value=False)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_generate_sftp_keys__raises_environ_error_if_file_does_not_exist(self, mock_run, *_):
        cmd_response = Mock()
        cmd_response.rc = 0
        mock_run.return_value = cmd_response
        self.assertRaises(EnvironError, self.flow.generate_sftp_keys)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.generate_sftp_keys')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.copy_sftp_keys_to_sas')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.auth_between_enm_and_sas')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.import_sas_key_to_shmserv')
    def test_lkf_configuration_setup__success(self, mock_import, mock_auth, mock_copy, mock_keys):
        self.flow.lkf_configuration_setup([Mock()])
        self.assertTrue(mock_copy.called)
        self.assertTrue(mock_auth.called)
        self.assertTrue(mock_import.called)
        self.assertTrue(mock_keys.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_copy_sftp_keys_to_sas__success(self, mock_cmd_on_ms, mock_remote_cmd, _):
        response = Mock()
        response.rc = 0
        response.stdout = "key"
        mock_cmd_on_ms.return_value = response
        mock_remote_cmd.return_value = response
        self.flow.copy_sftp_keys_to_sas()

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_copy_sftp_keys_to_sas__raises_environ_error_if_ms_cmd_fails(self, mock_cmd_on_ms, *_):
        response = Mock()
        response.rc = 1
        response.stdout = "key"
        mock_cmd_on_ms.return_value = response
        self.assertRaises(EnvironError, self.flow.copy_sftp_keys_to_sas)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_ms')
    def test_copy_sftp_keys_to_sas__remote_cmd_raises_environ_error(self, mock_cmd_on_ms, mock_remote_cmd, _):
        response = Mock()
        response.rc = 0
        response.stdout = "key"
        response1 = Mock()
        response1.rc = 1
        mock_cmd_on_ms.return_value = response
        mock_remote_cmd.return_value = response1
        self.assertRaises(EnvironError, self.flow.copy_sftp_keys_to_sas)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.copy_pem_file_to_enm')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist')
    def test_auth_between_enm_and_sas__success_if_file_exists(self, mock_file_exists, mock_copy, _):
        mock_file_exists.return_value = True
        self.flow.auth_between_enm_and_sas()
        self.assertTrue(mock_copy.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.pexpect.spawn.expect')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.copy_pem_file_to_enm')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist')
    def test_auth_between_enm_and_sas__success_file_created(self, mock_file_exists, mock_copy, mock_expect,
                                                            mock_sendline, _):
        mock_file_exists.return_value = False
        self.flow.auth_between_enm_and_sas()
        self.assertTrue(mock_copy.called)
        self.assertEqual(mock_expect.call_count, 3)
        self.assertEqual(mock_sendline.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.pexpect.spawn.expect', side_effect=[True, True, Exception])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.copy_pem_file_to_enm')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.does_remote_file_exist')
    def test_auth_between_enm_and_sas__raises_environ_error(self, mock_file_exists, mock_copy, *_):
        mock_file_exists.return_value = False
        self.assertRaises(EnvironError, self.flow.auth_between_enm_and_sas)
        self.assertFalse(mock_copy.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.GenericFlow.switch_to_ms_or_emp')
    def test_copy_pem_file_to_enm__success(self, mock_ms_child, _):
        child = Mock()
        mock_ms_child.return_value = child
        self.flow.copy_pem_file_to_enm()
        self.assertTrue(mock_ms_child.called)
        self.assertEqual(child.expect.call_count, 2)
        self.assertEqual(child.sendline.call_count, 2)
        self.assertTrue(child.close.callde)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.GenericFlow.switch_to_ms_or_emp', side_effect=True)
    def test_copy_pem_file_to_enm__raises_environ_error(self, mock_ms_child, _):
        self.assertRaises(EnvironError, self.flow.copy_pem_file_to_enm)
        self.assertTrue(mock_ms_child.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_import_sas_key_to_shmserv__success(self, mock_cmd_on_vm, _):
        self.flow.CLEANUP = True
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 0
        mock_cmd_on_vm.return_value = response
        self.flow.import_sas_key_to_shmserv(shmserv_host)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_import_sas_key_to_shmserv__success_after_retry(self, mock_cmd_on_vm, *_):
        self.flow.CLEANUP = True
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 1
        response.stdout = ""
        response1 = Mock()
        response1.rc = 0
        response1.stdout = ""
        mock_cmd_on_vm.side_effect = [response, response1]
        self.flow.import_sas_key_to_shmserv(shmserv_host)
        self.assertEqual(mock_cmd_on_vm.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.cleanup_imported_keys_on_shmserv')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_import_sas_key_to_shmserv__success_after_cleanup_existing_key(self, mock_cmd_on_vm, mock_cleanup, *_):
        self.flow.CLEANUP = True
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 1
        response.stdout = "Certificate not imported, alias <cascert> already exists"
        response1 = Mock()
        response1.rc = 0
        response1.stdout = ""
        mock_cmd_on_vm.side_effect = [response, response1]
        self.flow.import_sas_key_to_shmserv(shmserv_host)
        self.assertTrue(mock_cleanup.called)
        self.assertEqual(mock_cmd_on_vm.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_import_sas_key_to_shmserv__raises_environ_error(self, mock_cmd_on_vm, *_):
        self.flow.CLEANUP = True
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 1
        response.stdout = ""
        mock_cmd_on_vm.return_value = response
        self.assertRaises(EnvironError, self.flow.import_sas_key_to_shmserv, shmserv_host)
        self.assertEqual(mock_cmd_on_vm.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.timestamp.get_current_time')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.update_pib_parameters')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.execute_il_netsim_cmd_on_nodes')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.check_lkf_job_status')
    def test_execute_and_check_lkf_job__success(self, mock_job_status, mock_netsim_cmd, mock_pib, *_):
        self.flow.execute_and_check_lkf_job(self.user, self.node)
        self.assertTrue(mock_job_status.called)
        self.assertTrue(mock_pib.called)
        self.assertTrue(mock_netsim_cmd.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.timestamp.get_current_time')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.update_pib_parameters')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.execute_il_netsim_cmd_on_nodes', side_effect=[NetsimError])
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.LkfJob.check_lkf_job_status')
    def test_execute_and_check_lkf_job__adds_error(self, mock_job_status, mock_netsim_cmd, mock_pib, mock_error, *_):
        self.flow.execute_and_check_lkf_job(self.user, self.node)
        self.assertTrue(mock_job_status.called)
        self.assertTrue(mock_pib.called)
        self.assertTrue(mock_netsim_cmd.called)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_cleanup_imported_keys_on_shmserv__success(self, mock_cmd_on_vm, _):
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 0
        mock_cmd_on_vm.return_value = response
        self.flow.cleanup_imported_keys_on_shmserv(shmserv_host)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_cleanup_imported_keys_on_shmserv__success_after_retry(self, mock_cmd_on_vm, *_):
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 1
        response.stdout = ""
        response1 = Mock()
        response1.rc = 0
        response1.stdout = ""
        mock_cmd_on_vm.side_effect = [response, response1]
        self.flow.cleanup_imported_keys_on_shmserv(shmserv_host)
        self.assertEqual(mock_cmd_on_vm.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.Lkf01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow.run_cmd_on_vm')
    def test_cleanup_imported_keys_on_shmserv__raises_environ_error(self, mock_cmd_on_vm, mock_error, *_):
        shmserv_host = [Mock()]
        response = Mock()
        response.rc = 1
        response.stdout = ""
        mock_cmd_on_vm.return_value = response
        self.flow.cleanup_imported_keys_on_shmserv(shmserv_host)
        self.assertIsInstance(mock_error.call_args[0][0], EnvironError)
        self.assertEqual(mock_cmd_on_vm.call_count, 2)


if __name__ == '__main__':
    unittest2.main()
