#!/usr/bin/env python
import unittest2
from mock import Mock, PropertyMock, patch
from testslib import unit_test_utils

from enmutils.lib.exceptions import EnmApplicationError, SessionNotEstablishedException

from enmutils_int.lib.workload.amos_01 import AMOS_01
from enmutils_int.lib.workload.amos_02 import AMOS_02
from enmutils_int.lib.workload.amos_03 import AMOS_03
from enmutils_int.lib.workload.amos_04 import AMOS_04
from enmutils_int.lib.workload.amos_05 import AMOS_05
from enmutils_int.lib.workload.amos_08 import AMOS_08


class AmosProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock()] * 2
        self.radionodes = [Mock(1, primary_type="RadioNode", host_name="host")]
        self.roles = ['ADMINISTRATOR', 'Amos_Administrator', 'BscApplicationAdministrator',
                      'Bts_Application_Administrator', 'ENodeB_Application_Administrator',
                      'ENodeB_Application_SecurityAdministrator', 'ENodeB_Application_User', 'EricssonSupport',
                      'NodeB_Application_Administrator', 'NodeB_Application_User', 'RBS_Application_Operator',
                      'Support_Application_Administrator', 'SystemAdministrator', 'SystemReadOnly',
                      'SystemSecurityAdministrator', 'Amos_Operator']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_01.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_01.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.create_users')
    @patch('enmutils_int.lib.workload.amos_01.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_01.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.keep_running')
    def test_001_run_amos_01__is_successfull(self, mock_keep_running, mock_debug, mock_set_max_sessions,
                                             mock_create_users, mock_perform_prerequisites, *_):
        profile = AMOS_01()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "get lp"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.COMMANDS_PER_ITERATION = 10
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertEqual(mock_perform_prerequisites.call_count, 1)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_02.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_02.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.create_users')
    @patch('enmutils_int.lib.workload.amos_02.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_02.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.keep_running')
    def test_002_run_amos_02__is_successfull(self, mock_keep_running, mock_debug, mock_set_max_sessions,
                                             mock_create_users, mock_perform_prerequisites, *_):
        profile = AMOS_02()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform_prerequisites.call_count, 1)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_timestamp_str')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_03.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_03.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.create_users')
    @patch('enmutils_int.lib.workload.amos_03.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_03.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.keep_running')
    def test_003_run_amos_03__is_successfull(self, mock_keep_running, mock_debug, mock_set_max_sessions,
                                             mock_create_users, mock_perform_prerequisites, *_):
        profile = AMOS_03()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform_prerequisites.call_count, 1)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile.Profile.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile.Profile.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_04.ThreadQueue')
    @patch('enmutils_int.lib.profile.Profile.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_04.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.perform_amos_prerequisites')
    @patch('enmutils_int.lib.profile.Profile.create_users')
    @patch('enmutils_int.lib.workload.amos_04.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_04.log.logger.debug')
    @patch('enmutils_int.lib.profile.Profile.keep_running')
    def test_004_run_amos_04__is_successfull(self, mock_keep_running, mock_debug, mock_set_max_sessions,
                                             mock_create_users, mock_perform_prerequisites, *_):
        profile = AMOS_04()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "st cell"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform_prerequisites.call_count, 1)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_05.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.nodes')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_05.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.workload.amos_05.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_05.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_05.MoBatchCmd')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.create_users')
    def test_005_run_amos_05__is_successfull(self, mock_create_users, mock_nodes, mock_mo_batch,
                                             mock_perform_prerequisites, mock_delete_sessions, *_):
        profile = AMOS_05()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.BATCH_COMMANDS = ["lt all", "al"] * 2
        profile.NUM_PARALLEL = 1
        profile.COMMANDS_PER_ITERATION = 10
        profile.TIMEOUT = 10
        profile.SCHEDULE_SLEEP = 60 * 10
        profile.TOTAL_NODES = 1
        profile.BATCH_CMD_CHECK = True
        profile.USER_NODES = [(Mock(), Mock())]
        mock_create_users.return_value = [self.user]
        mock_nodes.return_value = [Mock()]
        profile.taskset(mock_mo_batch, _)
        profile.run()
        self.assertEqual(mock_perform_prerequisites.call_count, 1)
        mock_perform_prerequisites.assert_called_with(mock_create_users.return_value, mock_nodes.return_value)
        self.assertTrue(mock_delete_sessions.called)

    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_05.MoBatchCmd')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_05.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_05.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_05.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.create_users')
    @patch('enmutils_int.lib.workload.amos_05.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.keep_running')
    def test_006_run_amos_05__delete_session_raises_exception(self, mock_keep_running, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_05()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.BATCH_COMMANDS = ["lt all", "al"] * 2
        profile.NUM_PARALLEL = 1
        profile.COMMANDS_PER_ITERATION = 10
        profile.TIMEOUT = 10
        profile.SCHEDULE_SLEEP = 60 * 10
        profile.BATCH_CMD_CHECK = False
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.workload.amos_08.random.sample')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.download_tls_certs')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.amos_executor.get_radio_erbs_nodes')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_08.taskset')
    @patch('enmutils_int.lib.workload.amos_08.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_08.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.create_users')
    @patch('enmutils_int.lib.workload.amos_08.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_08.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.keep_running')
    def test_007_run_amos_08__is_successfull(self, mock_keep_running, mock_debug, mock_set_max_sessions,
                                             mock_create_users, mock_configure_ldap, *_):

        profile = AMOS_08()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "dcgkf"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.SCHEDULED_TIMES_STRINGS = ["05:00:00", "11:00:00"]
        mock_configure_ldap.return_value = self.radionodes
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_08.random.sample')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.download_tls_certs')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.amos_executor.get_radio_erbs_nodes')
    @patch('enmutils_int.lib.workload.amos_08.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_08.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.create_users')
    @patch('enmutils_int.lib.workload.amos_08.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_08.taskset')
    @patch('enmutils_int.lib.workload.amos_08.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.keep_running')
    def test_008_run_amos_08__taskset_raises_exception(self, mock_keep_running, mock_debug, mock_taskset,
                                                       mock_set_max_sessions, mock_create_users, *_):
        profile = AMOS_08()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "dcgkf"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.SCHEDULED_TIMES_STRINGS = ["05:00:00", "11:00:00"]
        mock_taskset.side_effect = Exception
        mock_keep_running.side_effect = [True, False]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_08.random.sample')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.download_tls_certs')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.amos_executor.get_radio_erbs_nodes')
    @patch('enmutils_int.lib.workload.amos_08.taskset')
    @patch('enmutils_int.lib.workload.amos_08.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.create_users')
    @patch('enmutils_int.lib.workload.amos_08.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_08.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.workload.amos_08.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.keep_running')
    def test_009_run_amos_08__configure_ldap_raises_exception(self, mock_keep_running, mock_debug, mock_configure_ldap,
                                                              mock_set_max_sessions, mock_create_users, *_):
        profile = AMOS_08()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "dcgkf"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.SCHEDULED_TIMES_STRINGS = ["05:00:00", "11:00:00"]
        mock_configure_ldap.side_effect = Exception
        mock_keep_running.side_effect = [None, False]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_05.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_05.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_05.MoBatchCmd')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_05.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.create_users')
    @patch('enmutils_int.lib.workload.amos_05.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.keep_running')
    def test_010_run_amos_05__raises_enm_application_error_due_to_scriptor(self, mock_keep_running,
                                                                           mock_get_iterator, mock_create_users, *_):
        profile = AMOS_05()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.BATCH_COMMANDS = ["lt all", "al"] * 2
        profile.NUM_PARALLEL = 1
        profile.TIMEOUT = 10
        profile.SCHEDULE_SLEEP = 60 * 10
        mock_keep_running.side_effect = [True, False]
        mock_get_iterator.side_effect = RuntimeError
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_01.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_01.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.create_users')
    @patch('enmutils_int.lib.workload.amos_01.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_01.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.keep_running')
    def test_011_run_amos_01__delete_session_raises_exception(self, mock_keep_running, mock_debug, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_01()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "get lp"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.COMMANDS_PER_ITERATION = 10
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_02.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_02.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.create_users')
    @patch('enmutils_int.lib.workload.amos_02.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_02.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.keep_running')
    def test_012_run_amos_02__delete_session_raises_exception(self, mock_keep_running, mock_debug, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_02()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_timestamp_str')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_03.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_03.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.create_users')
    @patch('enmutils_int.lib.workload.amos_03.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_03.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.keep_running')
    def test_013_run_amos_03__delete_session_raises_exception(self, mock_keep_running, mock_debug, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_03()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_04.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_04.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.create_users')
    @patch('enmutils_int.lib.workload.amos_04.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_04.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.keep_running')
    def test_014_run_amos_04__delete_session_raises_exception(self, mock_keep_running, mock_debug, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_04()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "st cell"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_08.random.sample')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.download_tls_certs')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_08.get_radio_erbs_nodes', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.workload.amos_08.taskset')
    @patch('enmutils_int.lib.workload.amos_08.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.workload.amos_08.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.create_users')
    @patch('enmutils_int.lib.workload.amos_08.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_08.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.keep_running')
    def test_015_run_amos_08__delete_session_raises_exception(self, mock_keep_running, mock_debug, mock_delete_session,
                                                              mock_create_users, mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_08()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "dcgkf"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.SCHEDULED_TIMES_STRINGS = ["05:00:00", "11:00:00"]
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = [EnmApplicationError, None]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_04.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_04.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.create_users')
    @patch('enmutils_int.lib.workload.amos_04.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_04.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_04.AMOS_04.keep_running')
    def test_016_run_amos_04__raises_exception_for_delete_user_sessions(self, mock_keep_running, mock_debug,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_04()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "st cell"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_05.MoBatchCmd')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_05.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_05.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.workload.amos_05.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.create_users')
    @patch('enmutils_int.lib.workload.amos_05.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.keep_running')
    def test_017_run_amos_05__raises_exception_for_delete_user_sessions(self, mock_keep_running,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_05()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.BATCH_COMMANDS = ["lt all", "al"] * 2
        profile.NUM_PARALLEL = 1
        profile.COMMANDS_PER_ITERATION = 10
        profile.TIMEOUT = 10
        profile.SCHEDULE_SLEEP = 60 * 10
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.workload.amos_08.random.sample')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.download_tls_certs')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_08.taskset')
    @patch('enmutils_int.lib.workload.amos_08.check_ldap_is_configured_on_radio_nodes')
    @patch('enmutils_int.lib.workload.amos_08.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.create_users')
    @patch('enmutils_int.lib.workload.amos_08.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_08.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_08.AMOS_08.keep_running')
    def test_018_run_amos_08__raises_exception_for_delete_user_sessions(self, mock_keep_running, mock_debug,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_08()
        profile.NUM_USERS = 1
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "dcgkf"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.SCHEDULED_TIMES_STRINGS = ["05:00:00", "11:00:00"]
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_timestamp_str')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_03.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_03.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.create_users')
    @patch('enmutils_int.lib.workload.amos_03.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_03.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_03.AMOS_03.keep_running')
    def test_019_run_amos_03__raises_exception_for_delete_user_sessions(self, mock_keep_running, mock_debug,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_03()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_02.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_02.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.create_users')
    @patch('enmutils_int.lib.workload.amos_02.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_02.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_02.AMOS_02.keep_running')
    def test_020_run_amos_02__raises_exception_for_delete_user_sessions(self, mock_keep_running, mock_debug,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_02()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS_PER_ITERATION = 10
        profile.COMMANDS = ["lt all", "confb"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_01.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_01.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.create_users')
    @patch('enmutils_int.lib.workload.amos_01.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_01.log.logger.debug')
    @patch('enmutils_int.lib.workload.amos_01.AMOS_01.keep_running')
    def test_021_run_amos_01__raises_exception_for_delete_user_sessions(self, mock_keep_running, mock_debug,
                                                                        mock_delete_session, mock_create_users,
                                                                        mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_01()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.COMMANDS = ["lt all", "get lp"] * 3
        profile.VERIFY_TIMEOUT = 10 * 60
        profile.COMMANDS_PER_ITERATION = 10
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        mock_delete_session.side_effect = SessionNotEstablishedException
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)

    @patch('time.sleep')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.workload.amos_05.MoBatchCmd')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.add_error_as_exception')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.sleep_until_time')
    @patch('enmutils_int.lib.workload.amos_05.ThreadQueue')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.process_thread_queue_errors')
    @patch('enmutils_int.lib.workload.amos_05.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.perform_amos_prerequisites')
    @patch('enmutils_int.lib.workload.amos_05.set_max_amos_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.create_users')
    @patch('enmutils_int.lib.workload.amos_05.delete_user_sessions')
    @patch('enmutils_int.lib.workload.amos_05.AMOS_05.keep_running')
    def test_022_run_amos_05__mo_batch_cmd_returns_empty_list_raises_environ_error(self, mock_keep_running, mock_debug,
                                                                                   mock_delete_session,
                                                                                   mock_create_users,
                                                                                   mock_set_max_sessions, *_):
        self.user.username = "user1"
        profile = AMOS_05()
        profile.NUM_USERS = 5
        profile.USER_ROLES = self.roles
        profile.MAX_AMOS_SESSIONS = 150
        profile.BATCH_COMMANDS = ["lt all", "al"] * 2
        profile.NUM_PARALLEL = 1
        profile.COMMANDS_PER_ITERATION = 10
        profile.TIMEOUT = 10
        profile.SCHEDULE_SLEEP = 60 * 10
        profile.BATCH_CMD_CHECK = False
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, True, False]
        profile.run()
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_set_max_sessions.called)
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
