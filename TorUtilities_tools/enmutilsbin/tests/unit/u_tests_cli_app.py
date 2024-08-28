#!/usr/bin/env python
import sys

import unittest2
from mock import patch, Mock, mock_open, call
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import persistence
from enmutilsbin import cli_app
from testslib import unit_test_utils

URL = 'http://test.com'
CMD = 'cmedit get * NetworkElement'
CMD1 = 'cmedit get * CmFunction'
TOOL = "./cli_app.py"


class CliAppUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.create_as = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutilsbin.cli_app.init.exit")
    @patch('enmutilsbin.cli_app.log.logger.error')
    def test_handle_invalid_argument__is_None_sucess(self, mock_log, _):
        cli_app.handle_invalid_argument(None)
        self.assertTrue(mock_log.called)

    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch("enmutilsbin.cli_app.init.exit")
    def test_handle_invalid_argument__not_None_sucess(self, mock_exit, _):
        cli_app.handle_invalid_argument("test")
        self.assertTrue(mock_exit.called)

    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.time.sleep', return_value=0)
    @patch('enmutilsbin.cli_app.getpass.getpass', return_value="pass")
    @patch('__builtin__.raw_input', return_value="user")
    def test_prompt_for_credentials__success(self, *_):
        self.assertEqual(cli_app.prompt_for_credentials(), ('user', 'pass'))

    @patch('enmutilsbin.cli_app.base64.b64decode')
    @patch('enmutilsbin.cli_app.persistence.get')
    def test_get_persisted_admin_user_details__decodes_wl_admin(self, mock_get, mock_decode):
        wl_user = Mock(password="pass")
        wl_user.username = "workload_admin"
        mock_decode.return_value = wl_user.password
        mock_get.return_value = wl_user
        self.assertEqual(cli_app.get_persisted_admin_user_details(), (wl_user.username, wl_user.password))
        self.assertEqual(1, mock_decode.call_count)

    @patch('enmutilsbin.cli_app.base64.b64decode')
    @patch('enmutilsbin.cli_app.persistence.get')
    def test_get_persisted_admin_user_details__uses_admin(self, mock_get, mock_decode):
        admin_user = Mock(password="pass")
        admin_user.username = "administrator"
        mock_get.side_effect = [None, admin_user]
        self.assertEqual(cli_app.get_persisted_admin_user_details(), (admin_user.username, admin_user.password))
        self.assertEqual(0, mock_decode.call_count)

    @patch('enmutilsbin.cli_app.persistence.get')
    def test_get_persisted_admin_user_details__no_persisted_creds(self, mock_get):
        mock_get.return_value = None
        self.assertEqual(cli_app.get_persisted_admin_user_details(), (None, None))

    @patch('enmutilsbin.cli_app.get_persisted_admin_user_details', return_value=('user', 'pass'))
    @patch('enmutilsbin.cli_app.os.path')
    def test_get_credentials__uses_persisted(self, mock_path, _):
        self.assertEqual(cli_app.get_credentials(), ('user', 'pass'))
        self.assertEqual(0, mock_path.return_value.isdir.call_count)

    @patch('enmutilsbin.cli_app.get_persisted_admin_user_details', return_value=('user', None))
    @patch('enmutilsbin.cli_app.prompt_for_credentials', return_value=('user', 'pass'))
    @patch('enmutilsbin.cli_app.os.path')
    def test_get_credentials__prompts_if_no_cred_file(self, mock_path, mock_prompt, _):
        mock_path.isfile.return_value = False
        self.assertEqual(cli_app.get_credentials(), ('user', 'pass'))
        self.assertEqual(1, mock_prompt.call_count)

    @patch('enmutilsbin.cli_app.get_persisted_admin_user_details', return_value=('user', None))
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutilsbin.cli_app.os.path')
    def test_get_credentials__reads_cred_file(self, mock_path, mock_read, _):
        mock_path.isfile.return_value = True
        mock_read.return_value.readlines.return_value = ["user\n", "pass\n"]
        self.assertEqual(cli_app.get_credentials(), ('user', 'pass'))

    @patch('enmutilsbin.cli_app.get_persisted_admin_user_details', return_value=('user', None))
    @patch('enmutilsbin.cli_app.prompt_for_credentials', return_value=('user', 'pass'))
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutilsbin.cli_app.os.path')
    def test_get_credentials__prompts_if_reads_cred_file_fails(self, mock_path, mock_read, mock_prompt, _):
        mock_path.isdir.return_value = False
        mock_path.isfile.return_value = True
        mock_read.return_value.readlines.return_value = ["user\n"]
        self.assertEqual(cli_app.get_credentials(), ('user', 'pass'))
        self.assertEqual(1, mock_prompt.call_count)

    @patch('enmutilsbin.cli_app.cache.get_apache_url', return_value=URL)
    @patch('enmutilsbin.cli_app.get_credentials', return_value=("user", "pass"))
    @patch('enmutilsbin.cli_app.enmscripting.open', return_value="session")
    def test_open_enm_scripting_session__success(self, mock_session, mock_creds, _):
        self.assertEqual(("session", URL, "user", "pass"), cli_app.open_enm_scripting_session())
        self.assertEqual(1, mock_creds.call_count)
        self.assertEqual(1, mock_session.call_count)

    @patch('enmutilsbin.cli_app.cache.get_apache_url', return_value=URL)
    @patch('enmutilsbin.cli_app.get_credentials')
    @patch('enmutilsbin.cli_app.enmscripting.open', return_value="session")
    def test_open_enm_scripting_session__creds_supplied(self, mock_session, mock_creds, _):
        self.assertEqual(("session", URL, "user", "pass"), cli_app.open_enm_scripting_session(username="user",
                                                                                              password="pass"))
        self.assertEqual(0, mock_creds.call_count)
        self.assertEqual(1, mock_session.call_count)

    @patch('enmutilsbin.cli_app.enmscripting.close')
    def test_close_file_and_close_session__closes_file_and_session(self, mock_close):
        file_obj, session = Mock(), Mock()
        cli_app.close_file_and_close_session(file_obj, "user", session)
        self.assertEqual(1, file_obj.close.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutilsbin.cli_app.enmscripting.close')
    def test_close_file_and_close_session__no_closes(self, mock_close):
        cli_app.close_file_and_close_session(None, "user", None)
        self.assertEqual(0, mock_close.call_count)

    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.enm_execute')
    def test_execute_cli_command__success(self, mock_execute, mock_info):
        response = Mock()
        response.get_output.return_value = [u'', u'FDN', u'1 instance(s)']
        mock_execute.return_value = response
        cli_app._execute_cli_command("", "")
        self.assertEqual(2, mock_info.call_count)
        mock_info.assert_any_call("FDN")
        mock_info.assert_called_with("1 instance(s)")

    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.enm_execute')
    def test_execute_cli_command__no_response(self, mock_execute, mock_info, mock_error):
        response = Mock()
        response.get_output.return_value = []
        mock_execute.return_value = response
        cli_app._execute_cli_command("", "")
        self.assertEqual(0, mock_info.call_count)
        mock_error.assert_called_with("ERROR: No result was returned from ENM script-engine service, response:\t[]")

    @patch('enmutilsbin.cli_app.os.path.isfile', return_value=True)
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutilsbin.cli_app.open_enm_scripting_session', return_value=("", "", "", ""))
    @patch('enmutilsbin.cli_app.close_file_and_close_session')
    @patch('enmutilsbin.cli_app.execute_cmd')
    def test_enm_execute__success(self, mock_execute, mock_close, *_):
        response = Mock()
        response.command = ""
        response.is_command_result_available.return_value = True
        mock_execute.return_value = response
        cli_app.enm_execute("cmd", file_in="file")
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutilsbin.cli_app.open_enm_scripting_session', return_value=("", "", "", ""))
    @patch('enmutilsbin.cli_app.close_file_and_close_session')
    @patch('enmutilsbin.cli_app.execute_cmd')
    def test_enm_execute__no_ouput_from_script_engine_response_error(self, mock_execute, mock_close, *_):
        response = Mock()
        response.command = ""
        response.is_command_result_available.return_value = False
        mock_execute.return_value = response
        self.assertRaises(cli_app.NoOuputFromScriptEngineResponseError, cli_app.enm_execute, "cmd")
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutilsbin.cli_app.os.path.isfile', return_value=False)
    def test_enm_execute__raises_os_error(self, _):
        self.assertRaises(OSError, cli_app.enm_execute, "cmd", file_in="file")

    @patch('enmutilsbin.cli_app.re.sub', return_value="cmd")
    @patch('enmutilsbin.cli_app.open_enm_scripting_session', return_value=("", "", "", ""))
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.close_file_and_close_session')
    @patch('enmutilsbin.cli_app.execute_cmd')
    def test_enm_execute__file_download(self, mock_execute, mock_close, mock_info, *_):
        response, enm_file = Mock(), Mock()
        response.command = ""
        response.has_files.return_value = True
        response.files.return_value = [enm_file]
        response.is_command_result_available.return_value = True
        mock_execute.return_value = response
        cli_app.enm_execute("password cmd", outfile="file")
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)
        mock_info.assert_called_with("Downloaded file: file")

    @patch('enmutilsbin.cli_app.open_enm_scripting_session', return_value=("", "", "", ""))
    @patch('enmutilsbin.cli_app.close_file_and_close_session')
    @patch('enmutilsbin.cli_app.execute_cmd')
    def test_enm_execute__raises_enm_application_error(self, mock_execute, mock_close, _):
        response, enm_file = Mock(), Mock()
        response.command = ""
        enm_file.download.side_effect = OSError("Error")
        response.has_files.return_value = True
        response.files.return_value = [enm_file]
        response.is_command_result_available.return_value = True
        mock_execute.return_value = response
        self.assertRaises(Exception, cli_app.enm_execute, "cmd", outfile="file")
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)

    def test_execute_cmd__success(self):
        session = Mock()
        session.terminal.return_value.execute.return_value = "Resp"
        self.assertEqual("Resp", cli_app.execute_cmd(session, "", "", "", ""))

    def test_execute_cmd__raises_exception(self):
        session = Mock()
        session.terminal.return_value.execute.side_effect = Exception("Error")
        self.assertRaises(Exception, cli_app.execute_cmd, session, "", "", "", "")

    @patch('enmutilsbin.cli_app.time.sleep', return_value=lambda _: None)
    @patch('enmutilsbin.cli_app.open_enm_scripting_session')
    def test_execute_cmd__session_timeout(self, mock_session, _):
        session = Mock()
        session.terminal.return_value.execute.side_effect = [cli_app.SessionTimeoutException("Timeout"), ""]
        self.assertEqual("", cli_app.execute_cmd(session, "", "", "", ""))
        self.assertEqual(1, mock_session.call_count)

    @patch('enmutilsbin.cli_app.time.sleep', return_value=lambda _: None)
    @patch('enmutilsbin.cli_app.open_enm_scripting_session')
    def test_execute_cmd__pool_closed(self, mock_session, _):
        session = Mock()
        session.terminal.return_value.execute.side_effect = [Exception("Pool is closed"), ""]
        self.assertEqual("", cli_app.execute_cmd(session, "", "", "", ""))
        self.assertEqual(1, mock_session.call_count)

    def test_get_saved_search_cmd_returns_saved_search(self):
        persistence.set(cli_app.SAVE_PERSISTENCE_KEY, {'command1': CMD}, 10)
        self.assertEqual(cli_app._get_saved_search_cmd('command1'), CMD)

    def test_get_saved_search_cmd_returns_None_cmd_if_not_in_saved_searches(self):
        self.assertEqual(cli_app._get_saved_search_cmd({'COMMAND': CMD}), None)

    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.persistence.get')
    def test_cli_save_cmd_to_persistence_when_no_similar_identitifer_exists(self, mock_persistence_get,
                                                                            mock_persistence_set, *_):
        argument_dict = {'--list': False, '--save': 'new_cmd', '-s': None, 'COMMAND': 'cmedit get * MeContext',
                         'FILE': None}
        mock_persistence_get.return_value = {'cmd_name': CMD1, 'cmd_name4': CMD, 'cmd_name3': CMD1,
                                             'cmd_name2': 'cmedit describe NetworkElement8',
                                             'cmd_name1': 'cmedit describe Blah'}
        cli_app._save_search_cmd(argument_dict)
        self.assertTrue(mock_persistence_set.called)

    @patch('__builtin__.raw_input')
    @patch('enmutilsbin.cli_app.log.logger.warn')
    def test_read_keyboard_input__is_successful(self, mock_warn_log, mock_raw_input):
        mock_raw_input.return_value = "yes"
        cli_app._read_keyboard_input()
        self.assertTrue(mock_raw_input.called)
        self.assertTrue(mock_warn_log.called)

    # cli test cases
    @patch('enmutilsbin.cli_app.signal')
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch("enmutilsbin.cli_app._read_keyboard_input")
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.persistence.get')
    @ParameterizedTestCase.parameterize(
        ("keyboard_input_values", "expected_call_count", "persistence_set_return"),
        [
            (['YES'], 1, True),
            (['yes'], 1, True),
            (['NO'], 1, False),
            (['no'], 1, False),
            (['a', 'b', 'yES', 'z'], 3, True),
            (['a', 'b', 'e', 'nO'], 4, False)

        ]
    )
    def test_cli_save_cmd_to_persistence_when_similar_identitifer_exists(
            self, keyboard_input_values, expected_call_count, persistence_set_return, mock_persistence_get,
            mock_persistence_set, mock_read_keyboard_input, *_):
        sys.argv = [TOOL, "command", "--save", 'cmd_name']
        mock_persistence_get.return_value = {'cmd_name': CMD1, 'cmd_name4': CMD, 'cmd_name3': CMD1,
                                             'cmd_name2': 'cmedit describe NetworkElement8',
                                             'cmd_name1': 'cmedit describe Blah'}
        mock_read_keyboard_input.side_effect = keyboard_input_values
        cli_app.cli()
        self.assertEqual(mock_persistence_set.called, persistence_set_return)
        self.assertEqual(mock_read_keyboard_input.call_count, expected_call_count)

    @patch('enmutilsbin.cli_app.signal')
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch('enmutilsbin.cli_app.persistence.set')
    def test_cli_save_saves_to_persistence(self, mock_persistence_set, *_):
        sys.argv = [TOOL, "command", "--save", 'cmd']
        cli_app.cli()
        self.assertTrue(mock_persistence_set.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch('enmutilsbin.cli_app.log.logger.info')
    def test_cli_list_calls_logger_info(self, mock_logger_info, *_):
        sys.argv = [TOOL, "--list"]
        cli_app.cli()
        self.assertTrue(mock_logger_info.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch("enmutilsbin.cli_app.init.exit")
    def test_cli_saved_search_returns_with_2_if_not_found(self, mock_exit, *_):
        sys.argv = [TOOL, "-s", "missing"]
        cli_app.cli()
        self.assertTrue(mock_exit.called_with(2))

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app._execute_cli_command")
    @patch("enmutilsbin.cli_app.initialize_logger")
    def test_cli__calls_initialize_logger_when_debug_is_selected(self, mock_initialize_logger, *_):
        sys.argv = [TOOL, "cmd", "--debug"]
        cli_app.cli()
        self.assertTrue(mock_initialize_logger.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.traceback.format_exc")
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch("enmutilsbin.cli_app._execute_cli_command")
    def test_cli__calls_error_logger_when_exception_is_detected(self, mock_execute_cli_command, mock_log,
                                                                mock_traceback, mock_exit, *_):
        sys.argv = [TOOL, "cmd"]
        mock_execute_cli_command.side_effect = cli_app.NoOuputFromScriptEngineResponseError
        cli_app.cli()
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_traceback.called)
        self.assertTrue(mock_exit.called_with(5))

    @patch("enmutilsbin.cli_app.init.global_init")
    @patch("enmutilsbin.cli_app.handle_invalid_argument")
    @ParameterizedTestCase.parameterize(
        "command_arguments",
        [
            ([TOOL, "more", "than", "five", "user", "cli", "arguments"], ),
            ([TOOL, "only", "three", "arguments"],),
            ([TOOL, "--file"],),  # invalid
            ([TOOL, "command", "--save"],),  # save identifier missing
            ([TOOL, "-s"],),  # Identifier missing
            ([TOOL, "-s", "1", "2", '3'],),  # Multiple identifiers

        ]
    )
    def test_exception_handle_invalid_argument_is_called_when_incorrect_amount_of_arguments_passed_into_tool(
            self, command_arguments, mock_handle_invalid_argument, _):
        sys.argv = command_arguments
        mock_handle_invalid_argument.side_effect = SystemExit("Exit message")
        with self.assertRaises(SystemExit):
            cli_app.cli()
        self.assertTrue(mock_handle_invalid_argument.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.persistence.get')
    @patch("enmutilsbin.cli_app.docopt")
    def test_cli__if_docopt_raises_system_exit_error(self, mock_doctopt, *_):
        sys.argv = [TOOL, "command", "--save", 'cmd']
        mock_doctopt.side_effect = SystemExit()
        self.assertRaises(SystemExit, cli_app.cli)
        self.assertTrue(mock_doctopt.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch("enmutilsbin.cli_app.init.exit")
    @patch("enmutilsbin.cli_app.init.global_init")
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch("enmutilsbin.cli_app.docopt")
    @patch('enmutilsbin.cli_app.persistence.get')
    def test_cli__if_list_argument_is_true(self, mock_persistence_get, mock_docopt, *_):
        sys.argv = [TOOL, "command", "--save", 'cmd']
        mock_persistence_get.return_value = {'cmd_name': CMD1, 'cmd_name4': CMD, 'cmd_name3': CMD1,
                                             'cmd_name2': 'cmedit describe NetworkElement8',
                                             'cmd_name1': 'cmedit describe Blah'}
        mock_docopt.return_value = {'--debug': False, '--list': True, '--outfile': None, '--save': 'cmd', '-s': None,
                                    'COMMAND': 'command', 'FILE': None}
        cli_app.cli()
        self.assertTrue(mock_persistence_get.called)
        self.assertTrue(mock_docopt.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch("enmutilsbin.cli_app._execute_cli_command")
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.init.exit')
    @patch('enmutilsbin.cli_app.init.global_init')
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app._get_saved_search_cmd')
    @patch("enmutilsbin.cli_app.docopt")
    @patch('enmutilsbin.cli_app.persistence.get')
    def test_cli__if_s_argument_is_true(self, mock_persistence_get, mock_docopt, mock_get_saved_search_cmd, *_):
        sys.argv = [TOOL, "command", 'cmd']
        mock_persistence_get.return_value = {'cmd_name': CMD1, 'cmd_name4': CMD, 'cmd_name3': CMD1,
                                             'cmd_name2': 'cmedit describe NetworkElement',
                                             'cmd_name1': 'cmedit describe Blah'}
        mock_get_saved_search_cmd.return_value = "cmedit describe NetworkElement"
        mock_docopt.return_value = {'--debug': False, '--list': False, '--outfile': None, '--save': None, '-s': True,
                                    'COMMAND': "cmd_name", 'FILE': None}
        cli_app.cli()
        self.assertTrue(mock_docopt.called)
        self.assertTrue(mock_get_saved_search_cmd.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app._execute_cli_command')
    @patch('enmutilsbin.cli_app.mutexer.mutex')
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.init.exit')
    @patch('enmutilsbin.cli_app.init.global_init')
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.does_file_exist', return_value=False)
    @patch('enmutilsbin.cli_app.persistence.get')
    @patch('enmutilsbin.cli_app._get_saved_search_cmd')
    @patch("enmutilsbin.cli_app.docopt")
    def test_cli__if_FILE_is_true(self, mock_docopt, *_):
        sys.argv = [TOOL, "command", 'cmd']
        mock_docopt.return_value = {'--debug': False, '--list': False, '--outfile': None, '--save': None, '-s': False,
                                    'COMMAND': "cmd_name", 'FILE': True}
        cli_app.cli()
        self.assertTrue(mock_docopt.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app._execute_cli_command')
    @patch('enmutilsbin.cli_app.mutexer.mutex')
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.init.exit')
    @patch('enmutilsbin.cli_app.init.global_init')
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.does_file_exist', return_value=True)
    @patch('enmutilsbin.cli_app.persistence.get')
    @patch('enmutilsbin.cli_app._get_saved_search_cmd')
    @patch("enmutilsbin.cli_app.docopt")
    def test_cli__if_FILE_is_true_and_file_existed(self, mock_docopt, *_):
        sys.argv = [TOOL, "command", 'cmd']
        mock_docopt.return_value = {'--debug': False, '--list': False, '--outfile': None, '--save': None, '-s': False,
                                    'COMMAND': "cmd_name", 'FILE': True}
        cli_app.cli()
        self.assertTrue(mock_docopt.called)

    @patch('enmutilsbin.cli_app.signal')
    @patch('enmutilsbin.cli_app.persistence.get')
    @patch('enmutilsbin.cli_app._execute_cli_command')
    @patch('enmutilsbin.cli_app.mutexer.mutex')
    @patch('enmutilsbin.cli_app.log.logger.error')
    @patch('enmutilsbin.cli_app.log.logger.info')
    @patch('enmutilsbin.cli_app.init.exit')
    @patch('enmutilsbin.cli_app.init.global_init')
    @patch('enmutilsbin.cli_app.persistence.set')
    @patch('enmutilsbin.cli_app.does_file_exist', return_value=False)
    @patch('enmutilsbin.cli_app._get_saved_search_cmd')
    @patch("enmutilsbin.cli_app.docopt")
    def test_cli__if_FILE_is_false(self, mock_docopt, *_):
        sys.argv = [TOOL, "command", 'cmd']
        mock_docopt.return_value = {'--debug': False, '--list': False, '--outfile': None, '--save': None, '-s': False,
                                    'COMMAND': "cmd_name", 'FILE': False}
        cli_app.cli()
        self.assertTrue(mock_docopt.called)

    @patch('enmutilsbin.cli_app.logging.Formatter')
    @patch('enmutilsbin.cli_app.log.logging')
    @patch('enmutilsbin.cli_app.logging.StreamHandler')
    @patch('enmutilsbin.cli_app.logging.FileHandler')
    @patch('enmutilsbin.cli_app.logging.getLogger')
    @patch('enmutilsbin.cli_app.check_log_dir')
    def test_initialize_logger(self, mock_check_log_dir, mock_logger, mock_filehandler, mock_streamhandler, *_):
        cli_app.TOOL_NAME = "test_tool"
        cli_app.initialize_logger()
        self.assertTrue(mock_check_log_dir.called)
        self.assertTrue(call(mock_streamhandler.return_value) in mock_logger.return_value.addHandler.mock_calls)
        self.assertTrue(call(mock_filehandler.return_value) in mock_logger.return_value.addHandler.mock_calls)
        mock_filehandler.assert_called_with("/var/log/enmutils/test_tool.log")

    @patch("enmutilsbin.cli_app.os")
    def test_mock_check_log_dir__successful_if_log_dir_exists(self, mock_os):
        mock_os.path.exists.return_value = True
        cli_app.check_log_dir()
        self.assertTrue(mock_os.path.exists.called)
        self.assertFalse(mock_os.mkdir.called)

    @patch("enmutilsbin.cli_app.os")
    def test_mock_check_log_dir__successful_if_log_dir_does_not_exist(self, mock_os):
        mock_os.path.exists.return_value = False
        cli_app.check_log_dir()
        mock_os.path.exists.assert_called_with("/var/log/enmutils")
        mock_os.mkdir.assert_called_with("/var/log/enmutils")

    @patch('enmutilsbin.cli_app.os')
    def test_mock_check_log_dir__unsuccessful_if_cannot_create_dir(self, mock_os):
        mock_os.path.exists.return_value = False
        mock_os.mkdir.side_effect = Exception("some error")

        with self.assertRaises(SystemExit) as e:
            cli_app.check_log_dir()
        self.assertEqual(e.exception.message, "Problem accessing log dir (/var/log/enmutils): some error")
        mock_os.path.exists.assert_called_with("/var/log/enmutils")
        mock_os.mkdir.assert_called_with("/var/log/enmutils")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
