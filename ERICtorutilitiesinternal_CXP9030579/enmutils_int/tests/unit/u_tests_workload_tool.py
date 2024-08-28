#!/usr/bin/env python

import unittest2
from mock import patch, Mock
from enmutils_int.bin.workload import (log_workload_message, perform_cli_pre_checks, cli, SessionNotEstablishedException,
                                       _validate_profiles, _update_config, _get_existing_profiles_in_categories,
                                       _do_profiles_validation_against_existing_profiles, _validate_categories,
                                       _ignoring_profiles, _remove_duplicates, display_workload_operation_info_message)
from testslib import unit_test_utils


class WorkloadToolUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.argument_dict = {"--category": False, "--conf": None, "--csv": False, "--error-type": None,
                              "--errored-nodes": False, "--errors": False, "--force": False, "--force-stop": False,
                              "--help": False, "--ignore": None, "--include": None,
                              "--initial-install-teardown": False, "--jenkins": False, "--json": False,
                              "--lastrun": False, "--list-format": False, "--message": None,
                              "--network-check": False, "--network-config": None, "--network-size": None,
                              "--network-values": False, "--new-only": False, "--no-ansi": False,
                              "--no-exclusive": False, "--no-network-size-check": False, "--no-sleep": False,
                              "--priority": None, "--profiles": None, "--release-exclusive-nodes": False,
                              "--robustness": False, "--rpm-version": None, "--schedule": None, "--skip": False,
                              "--soak": False, "--supported": False, "--test-only": False, "--total": None,
                              "--updated": False, "--validate": False, "--verbose": False, "--version": None,
                              "--warnings": False, "IDENTIFIER": None, "PROFILES": "PM_26", "RANGE": None,
                              "add": False, "category": False, "clean-pid": False, "clear-errors": False,
                              "describe": False, "diff": False, "export": False, "list": False, "profiles": False,
                              "remove": False, "reset": False, "restart": False, "start": False, "status": True,
                              "stop": False}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.bin.workload.log.get_workload_ops_logger')
    def test_log_workload_message__start_message(self, mock_logger):
        log_workload_message({'start': True, 'stop': False, 'PROFILES': "TEST_00,TEST_01", '--category': False,
                              '--message': "Why are you reading this?!"})
        mock_logger.return_value.info.assert_called_with("Starting profiles::\t[TEST_00,TEST_01].\tMessage supplied "
                                                         "with operation::\t[Why are you reading this?!]")

    @patch('enmutils_int.bin.workload.log.get_workload_ops_logger')
    def test_log_workload_message__stop_message(self, mock_logger):
        log_workload_message({'start': False, 'stop': True, 'PROFILES': "ap,ha", '--category': True,
                              '--message': "Still reading the test messages, are you?"})
        mock_logger.return_value.info.assert_called_with("Stopping categories::\t[ap,ha].\tMessage supplied with "
                                                         "operation::\t[Still reading the test messages, are you?]")

    @patch('enmutils_int.bin.workload.log.get_workload_ops_logger')
    def test_log_workload_message__restart_no_message(self, mock_logger):
        log_workload_message({'start': False, 'stop': False, 'PROFILES': "all", '--category': False,
                              '--message': False})
        mock_logger.return_value.info.assert_called_with("Restarting profiles::\t[all].\tMessage supplied with "
                                                         "operation::\t[No message provided.]")

    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__logs_message(self, mock_log):
        argument_dict = {'start': False, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': True,
                         '--errored-nodes': False, '--message': False, 'restart': True, '--ignore': False,
                         '--initial-install-teardown': False, '--no-ansi': False, '--priority': False,
                         '--test-only': False, '--robustness': False}
        perform_cli_pre_checks(argument_dict)
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils_int.bin.workload.config.set_prop")
    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__robustness_flag_used(self, mock_log, _):
        argument_dict = {'start': True, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': True,
                         '--errored-nodes': False, '--message': False, 'restart': False, '--ignore': False,
                         '--initial-install-teardown': False, '--no-ansi': False, '--priority': False,
                         '--test-only': False, '--robustness': True}
        perform_cli_pre_checks(argument_dict)
        self.assertEqual(1, mock_log.call_count)

    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__errored_nodes(self, mock_log, mock_init):
        argument_dict = {'start': False, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': True,
                         '--errored-nodes': True, '--message': False, 'restart': False, '--ignore': False,
                         '--initial-install-teardown': False, '--no-ansi': False, '--priority': False,
                         '--test-only': False, 'list': True}
        perform_cli_pre_checks(argument_dict)
        self.assertEqual(0, mock_log.call_count)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__invalid_priority(self, mock_log, mock_init):
        argument_dict = {'start': False, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': True,
                         '--errored-nodes': False, '--message': False, 'restart': False, '--ignore': False,
                         '--initial-install-teardown': False, '--no-ansi': False, '--priority': 3,
                         '--test-only': False, 'list': True}
        perform_cli_pre_checks(argument_dict)
        self.assertEqual(0, mock_log.call_count)
        mock_init.assert_called_with(0)

    @patch('__builtin__.raw_input', return_value="No")
    @patch('enmutils_int.bin.workload.config.set_prop')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__initial_install_failure(self, mock_log, mock_init, *_):
        argument_dict = {'start': False, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': False,
                         '--errored-nodes': False, '--message': False, 'restart': False, '--ignore': False,
                         '--initial-install-teardown': True, '--no-ansi': True, '--priority': False,
                         '--test-only': False, 'list': True}
        perform_cli_pre_checks(argument_dict)
        self.assertEqual(0, mock_log.call_count)
        mock_init.assert_called_with(0)

    @patch('__builtin__.raw_input', return_value="Yes")
    @patch('enmutils_int.bin.workload.config.set_prop')
    @patch('enmutils_int.bin.workload._ignoring_profiles', return_value=["TEST_00", "TEST_01"])
    @patch('enmutils_int.bin.workload.log_workload_message')
    def test_perform_cli_pre_checks__ignore_profiles(self, mock_log, *_):
        argument_dict = {'start': False, 'stop': False, 'PROFILES': "all", '--category': False, '--skip': False,
                         '--errored-nodes': False, '--message': False, 'restart': False, '--ignore': True,
                         '--initial-install-teardown': True, '--no-ansi': True, '--priority': False,
                         '--test-only': True, 'list': True}
        ignoring, operation = perform_cli_pre_checks(argument_dict)
        self.assertEqual(0, mock_log.call_count)
        self.assertListEqual(ignoring, ["TEST_00", "TEST_01"])
        self.assertEqual("list", operation)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.docopt')
    def test_cli__call_to_help(self, mock_docopt, *_):
        mock_docopt.side_effect = SystemExit()
        self.assertRaises(SystemExit, cli)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload.docopt')
    def test_cli__invalid_argument_calls_handle_exception(self, mock_docopt, mock_handle, *_):
        mock_docopt.side_effect = SystemExit("Invalid argument")
        # Have the handler raise an exception as normally init.exit(2) would be called if the func wasn't patched.
        mock_handle.side_effect = Exception("error")
        self.assertRaises(Exception, cli)
        self.assertEqual(1, mock_handle.call_count)

    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload._validate_profiles', side_effect=RuntimeError("Error"))
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__validation_failure(self, mock_perform_cli_pre_checks, mock_process, mock_init, *_):
        mock_perform_cli_pre_checks.return_value = ["TEST_00"], "add"
        cli()
        self.assertEqual(1, mock_process.call_count)
        mock_init.assert_called_with(1)

    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload._validate_profiles')
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.workload_ops_node_operations.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__workload_node_op_called(self, mock_perform_cli_pre_checks, mock_init, mock_get_op, *_):
        mock_perform_cli_pre_checks.return_value = ["TEST_00"], "add"
        cli()
        self.assertEqual(1, mock_get_op.return_value.execute.call_count)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload._validate_profiles')
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__fails_if_session_not_established_error(self, mock_perform_cli_pre_checks, mock_init, mock_get_op, *_):
        mock_perform_cli_pre_checks.return_value = ["TEST_00"], "start"
        mock_get_op.return_value.execute.side_effect = SessionNotEstablishedException()
        cli()
        mock_init.assert_called_with(1)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload._validate_profiles', return_value=["PM_26"])
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__when_getting_profile_status_in_json_format(self, mock_perform_cli_pre_checks, mock_init,
                                                             mock_get_op, mock_docopt, mock_print_wl_message, *_):
        self.argument_dict['--json'] = True
        mock_docopt.return_value = self.argument_dict
        mock_perform_cli_pre_checks.return_value = None, "status"
        mock_get_op.return_value.execute.return_value = Mock()
        cli()
        self.assertEqual(mock_print_wl_message.call_count, 1)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload._validate_profiles', return_value=["PM_26"])
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__when_getting_all_profiles_status_in_json_format(self, mock_perform_cli_pre_checks, mock_init,
                                                                  mock_get_op, mock_docopt, mock_print_wl_message, *_):
        self.argument_dict['--json'] = True
        self.argument_dict['PROFILES'] = None
        mock_docopt.return_value = self.argument_dict
        mock_perform_cli_pre_checks.return_value = None, "status"
        mock_get_op.return_value.execute.return_value = Mock()
        cli()
        self.assertEqual(mock_print_wl_message.call_count, 1)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload._validate_profiles', return_value=["PM_26"])
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__when_getting_all_profiles_status_based_on_priority_in_json_format(self, mock_perform_cli_pre_checks,
                                                                                    mock_init, mock_get_op,
                                                                                    mock_docopt,
                                                                                    mock_print_wl_message, *_):
        self.argument_dict['--json'] = True
        self.argument_dict['PROFILES'] = None
        self.argument_dict['--priority'] = 1
        mock_docopt.return_value = self.argument_dict
        mock_perform_cli_pre_checks.return_value = None, "status"
        mock_get_op.return_value.execute.return_value = Mock()
        cli()
        self.assertEqual(mock_print_wl_message.call_count, 1)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.exception.handle_invalid_argument')
    @patch('enmutils_int.bin.workload._validate_profiles', return_value=["PM_26"])
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__when_getting_all_profiles_status(self, mock_perform_cli_pre_checks, mock_init,
                                                   mock_get_op, mock_docopt, mock_print_wl_message, *_):
        self.argument_dict['--json'] = False
        self.argument_dict['PROFILES'] = None
        mock_docopt.return_value = self.argument_dict
        mock_perform_cli_pre_checks.return_value = None, "status"
        mock_get_op.return_value.execute.return_value = Mock()
        cli()
        self.assertEqual(mock_print_wl_message.call_count, 1)
        mock_init.assert_called_with(0)

    @patch('enmutils_int.bin.workload.display_workload_operation_info_message')
    @patch('enmutils_int.bin.workload.signal.signal')
    @patch('enmutils_int.bin.workload.init.global_init')
    @patch('enmutils_int.bin.workload.docopt')
    @patch('enmutils_int.bin.workload._validate_profiles')
    @patch('enmutils_int.bin.workload._update_config')
    @patch('enmutils_int.bin.workload.exception.process_exception')
    @patch('enmutils_int.bin.workload.log.logger.error')
    @patch('enmutils_int.bin.workload.workload_ops.get_workload_operations')
    @patch('enmutils_int.bin.workload.init.exit')
    @patch('enmutils_int.bin.workload.perform_cli_pre_checks')
    def test_cli__fails_if_any_exception_with_clean_output(
            self, mock_perform_cli_pre_checks, mock_init, mock_get_op, mock_error, mock_process_exception, *_):
        mock_perform_cli_pre_checks.return_value = ["TEST_00"], "start"
        mock_get_op.return_value.execute.side_effect = Exception('Some problem occured')
        cli()
        mock_init.assert_called_with(1)
        self.assertEqual(mock_error.call_count, 0)
        mock_process_exception.assert_called_once_with('Some problem occured', print_msg_to_console=True)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._do_profiles_validation_against_existing_profiles")
    def test_validate_profiles__status_of_all_profiles(self, mock_do_profiles_validation_against_existing_profiles, _):
        mock_argument_dict = {"status": 1, "PROFILES": None, "--new-only": None, "start": None, "--updated": None, "--category": None}
        _validate_profiles(mock_argument_dict)
        self.assertFalse(mock_do_profiles_validation_against_existing_profiles.called)

    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    @patch("enmutils_int.lib.load_mgr.get_new_profiles")
    def test_validate_profiles__new_only(self, mock_get_new_profiles, _):
        mock_argument_dict = {"status": True, "PROFILES": True, "--new-only": True, "start": True, "--updated": True,
                              "--category": True, "--version": True}
        _validate_profiles(mock_argument_dict)
        self.assertTrue(mock_get_new_profiles.called)

    @patch("enmutils_int.lib.load_mgr.get_updated_profiles")
    def test_validate_profiles__start_updated_profiles(self, mock_get_updated_profiles):
        mock_argument_dict = {"status": 1, "PROFILES": 1, "--new-only": None, "start": 1, "--updated": 1,
                              "--category": 1, "--version": 1}
        _validate_profiles(mock_argument_dict)
        self.assertTrue(mock_get_updated_profiles.called)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._validate_categories", return_value=[{"cmsync, cmimport"}, {}])
    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    def test_validate_profiles__valid_profiles_given(self, mock_get_existing_profiles_in_categories, *_):
        mock_argument_dict = {"status": None, "PROFILES": "cmsync, cmimport", "--new-only": None, "start": None, "--updated": None,
                              "--category": 1, "--version": 1}
        _validate_profiles(mock_argument_dict)
        self.assertTrue(mock_get_existing_profiles_in_categories.called)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._validate_categories", return_value=[{"cmsync, cmimport"}, {}])
    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    def test_validate_profiles__profiles_flag_not_used(self, mock_get_existing_profiles_in_categories, *_):
        mock_argument_dict = {"status": False, "PROFILES": False, "--new-only": False, "start": False,
                              "--updated": False,
                              "--category": True, "--version": True}
        _validate_profiles(mock_argument_dict)
        self.assertFalse(mock_get_existing_profiles_in_categories.called)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._validate_categories", return_value=[{}, {"cmsync"}])
    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    def test_validate_profiles__no_valid_categories_given(self, mock_get_existing_profiles_in_categories, *_):
        mock_argument_dict = {"status": None, "PROFILES": "Made_up_profile", "--new-only": None, "start": None,
                              "--updated": None,
                              "--category": 1, "--version": 1}
        with self.assertRaisesRegexp(RuntimeError, ""):
            _validate_profiles(mock_argument_dict)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._validate_categories", return_value=[{}, {"Made_up_profile"}])
    @patch("enmutils_int.bin.workload._do_profiles_validation_against_existing_profiles", return_value=[{}, {}])
    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    def test_validate_profiles__no_valid_profiles_given(self, mock_get_existing_profiles_in_categories, *_):
        mock_argument_dict = {"status": False, "PROFILES": "Test", "--new-only": False, "start": False,
                              "--updated": False,
                              "--category": False, "--version": 1}
        with self.assertRaisesRegexp(RuntimeError, ""):
            _validate_profiles(mock_argument_dict)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload._validate_categories", return_value=[{}, {}])
    @patch("enmutils_int.bin.workload._do_profiles_validation_against_existing_profiles", return_value=[{"Test"}, {}])
    @patch("enmutils_int.bin.workload._get_existing_profiles_in_categories")
    def test_validate_profiles__profiles_matches_againsts_existing_profiles(self, mock_get_existing_profiles_in_categories, *_):
        mock_argument_dict = {"status": False, "PROFILES": "Test", "--new-only": False, "start": False,
                              "--updated": False,
                              "--category": False, "--version": 1}
        self.assertEqual(_validate_profiles(mock_argument_dict), ["Test"])

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__select_new_profiles_only(self, mock_set_prop):
        mock_argument_dict = {'--new-only': True, '--no-sleep': False, '--soak': False,
                              '--network-config': '40K'}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 3)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__profile_started_without_no_sleep(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': True, '--soak': False,
                              '--network-config': '40K'}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 3)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__valid_network_configuration_used(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': False, '--soak': False,
                              '--network-config': '40K'}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 2)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__no_network_config_given(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': False, '--soak': False,
                              '--network-config': False}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 1)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__non_default_network_configuration_used(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': False, '--soak': False,
                              '--network-config': 'EXTRA-SMALL'}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 3)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__no_network_config_used(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': False, '--soak': False,
                              '--network-config': False}
        mock_profile_names = ["cmimport_03"]
        _update_config(mock_argument_dict, mock_profile_names)
        self.assertEqual(mock_set_prop.call_count, 1)

    @patch("enmutils_int.bin.workload.config.set_prop")
    def test_update_config__invalid_config_used(self, mock_set_prop):
        mock_argument_dict = {'--new-only': False, '--no-sleep': False, '--soak': False,
                              '--network-config': "INVALID_NETWORK"}
        mock_profile_names = ["cmimport_03"]
        with self.assertRaisesRegexp(RuntimeError, ""):
            _update_config(mock_argument_dict, mock_profile_names)

    @patch("enmutils_int.bin.workload.get_categories", return_value={})
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_validate_categories__not_valid_category(self, mock_log, *_):
        mock_categories = {"Test"}
        _validate_categories(mock_categories)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.bin.workload.get_categories", return_value={"Test"})
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_validate_categories__valid_category(self, mock_log, *_):
        mock_categories = {"Test"}
        _validate_categories(mock_categories)
        self.assertFalse(mock_log.called)

    @patch("enmutils_int.bin.workload._remove_duplicates")
    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value={"cmimport"})
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_ignoring_profiles__invalid_profiles(self, mock_log, *_):
        mock_profiles_to_ignore = "Test, Test2"
        _ignoring_profiles(mock_profiles_to_ignore)
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.bin.workload._remove_duplicates", return_value={"Test"})
    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value={"Test"})
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_ignoring_profiles__valid_profiles_ignored(self, mock_log, *_):
        mock_profiles_to_ignore = "Test"
        self.assertEqual(_ignoring_profiles(mock_profiles_to_ignore), {"TEST"})

    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value={"cmimport"})
    def test_get_existing_profiles_in_categories__correct_categorie_given(self, _):
        mock_categories = {"cmimport", "cmsync", "cmexport"}
        self.assertEqual(_get_existing_profiles_in_categories(mock_categories), ["cmimport"])

    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value={"cmimport"})
    def test_get_existing_profiles_in_categories__no_categorie_given(self, _):
        mock_categories = {}
        self.assertEqual(_get_existing_profiles_in_categories(mock_categories), [])

    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value=["cmimport", "cmexport"])
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_do_profiles_validation_against_existing_profiles__profiles_exists(self, mock_log, *_):
        mock_profiles = {"cmimport"}
        _do_profiles_validation_against_existing_profiles(mock_profiles)
        self.assertFalse(mock_log.called)

    @patch("enmutils_int.bin.workload.get_all_profile_names", return_value=["cmimport", "cmexport"])
    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_do_profiles_validation_against_existing_profiles__not_an_existing_profile(self, mock_log, *_):
        mock_profiles = {"cmmadeup"}
        _do_profiles_validation_against_existing_profiles(mock_profiles)
        self.assertTrue(mock_log.called)

    def test_remove_duplicates_successfull(self):
        mock_list_of_values = ["Test", "Test"]
        self.assertEqual(_remove_duplicates(mock_list_of_values), {"test"})

    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_display_workload_operation_info_message__when_json_is_true_and_opr_type_is_status(
            self, mock_log_info):
        display_workload_operation_info_message(operation_type="status", argument_dict={"--json": True})
        self.assertEqual(mock_log_info.call_count, 0)

    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_display_workload_operation_info_message__when_json_is_false_and_opr_type_is_status(
            self, mock_log_info):
        display_workload_operation_info_message(operation_type="status", argument_dict={"--json": False})
        self.assertEqual(mock_log_info.call_count, 1)

    @patch("enmutils_int.bin.workload.log.logger.info")
    def test_display_workload_operation_info_message__when_json_is_false_and_opr_type_is_start(
            self, mock_log_info):
        display_workload_operation_info_message(operation_type="start", argument_dict={"--json": False})
        self.assertEqual(mock_log_info.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
