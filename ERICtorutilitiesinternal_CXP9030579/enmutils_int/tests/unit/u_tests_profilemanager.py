#!/usr/bin/env python
from datetime import datetime

import unittest2
from flask import Flask
from mock import patch, Mock, mock_open

from enmutils_int.lib.services import profilemanager
from enmutils_int.lib.services.profilemanager import (get_status, get_profiles_by_category, status, get_profile_status,
                                                      get_multiple_status, set_status, set_error_or_warning,
                                                      StatusProfile, clear_errors, delete_pid_files, clear_pids,
                                                      profiles_list, categories_list, describe,
                                                      build_describe_message_for_profiles, print_basic_network_values,
                                                      print_profile_description, export_all, print_export_path,
                                                      get_profiles_and_file_names, write_to_file, generate_export_file,
                                                      export, diff, at_startup, verify_profiles,
                                                      check_for_consistently_dead_or_inactive_profiles)
from testslib import unit_test_utils

app = Flask(__name__)


class ProfileManagerServiceUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        profilemanager.EXPORT_PROP_FILE_NAME = "_test.py"
        self.svc_running = [0, "svc running"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.profilemanager.timestamp.convert_datetime_to_str_format', return_value="Datetime")
    @patch('enmutils_int.lib.services.profilemanager.get_status')
    def test_status__returns_all_status_objects(self, mock_get_status, _):
        mock_get_status.return_value = [StatusProfile(**{"name": "TEST_00", "state": "OK",
                                                         "start_time": "2020-01-32 10:30", "pid": "1234",
                                                         "num_nodes": 0, "schedule": "Every hour", "priority": "1",
                                                         "last_run": "NEVER", "user_count": 0}),
                                        StatusProfile(**{"name": "TEST_00", "state": "OK",
                                                         "start_time": datetime.now(), "pid": "1234",
                                                         "num_nodes": 0, "schedule": "Every hour", "priority": "1",
                                                         "last_run": datetime.now(), "user_count": 0})]
        categories = [u"CM", u"FM", u"PM"]
        with app.test_request_context('profile/status', json=dict(profile_name="None", category=categories,
                                                                  profiles="None")):
            status()
            self.assertEqual(1, mock_get_status.call_count)
            mock_get_status.assert_called_with(profile_name=None, categories=[u'CM', u'FM', u'PM'], profile_list=None)

    @patch('enmutils_int.lib.services.profilemanager.timestamp.convert_datetime_to_str_format', return_value="Datetime")
    @patch('enmutils_int.lib.services.profilemanager.get_status')
    def test_status__returns_all_status_objects_if_no_parameters_passed(self, mock_get_status, _):
        mock_get_status.return_value = [StatusProfile(**{"name": "TEST_00", "state": "OK",
                                                         "start_time": "2020-01-32 10:30", "pid": "1234",
                                                         "num_nodes": 0, "schedule": "Every hour", "priority": "1",
                                                         "last_run": "NEVER", "user_count": 0}),
                                        StatusProfile(**{"name": "TEST_00", "state": "OK",
                                                         "start_time": datetime.now(), "pid": "1234",
                                                         "num_nodes": 0, "schedule": "Every hour", "priority": "1",
                                                         "last_run": datetime.now(), "user_count": 0})]

        with app.test_request_context('profile/status', json=None):
            status()
            self.assertEqual(1, mock_get_status.call_count)
            mock_get_status.assert_called_with(profile_name=None, categories=None, profile_list=None)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.get_status')
    def test_status__calls_abort_with_message_if_no_status_found(self, mock_get_status, mock_abort, mock_logger):
        error = Exception("Error")
        mock_get_status.side_effect = error
        profiles = [u'AP_11', u'SECUI_03']
        with app.test_request_context('profile/status', json=dict(profile_name="None", category="None",
                                                                  profiles=profiles)):
            status()
            self.assertEqual(1, mock_get_status.call_count)
            mock_get_status.assert_called_with(profile_name=None, categories=None,
                                               profile_list=[u'AP_11', u'SECUI_03'])
            mock_abort.assert_called_with("Failed to retrieve Status values.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.timestamp.convert_str_to_datetime_object')
    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.persistence.set')
    def test_set_status__success(self, mock_set, mock_get_json, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        with app.test_request_context('profile/status/set', json=request_data):
            set_status()
            self.assertEqual(1, mock_set.call_count)
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils_int.lib.services.profilemanager.timestamp.convert_datetime_to_str_format')
    @patch('enmutils_int.lib.services.profilemanager.get_status')
    def test_status__skips_none_type(self, mock_get_status, mock_convert):
        mock_get_status.return_value = [None]
        with app.test_request_context('profile/status', json=dict(category="None", profiles=["TEST_00"])):
            status()
            self.assertEqual(1, mock_get_status.call_count)
            self.assertEqual(0, mock_convert.call_count)
            mock_get_status.assert_called_with(profile_name=u"TEST_00", categories=None, profile_list=None)

    @patch('enmutils_int.lib.services.profilemanager.timestamp.convert_str_to_datetime_object')
    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.persistence.set')
    def test_set_status__calls_abort_with_message(self, mock_set, mock_abort, mock_logger, _):
        error = Exception("Error")
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        with app.test_request_context('profile/status/set', json=request_data):
            mock_set.side_effect = error
            set_status()
            mock_abort.assert_called_with("Failed to set Profile Status.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.persistence.set')
    def test_set_error_or_warning__success(self, mock_set, mock_get_json):
        request_data = {"profile_key": "TEST_00-errors",
                        "profile_values": {'DUPLICATES': ['2020/02/02 06:00:05', '2020/02/02 12:00:04',
                                                          '2020/02/03 06:00:04', '2020/02/03 12:00:01',
                                                          '2020/02/04 06:00:03'], 'TIMESTAMP': '2020/02/04 12:00:05',
                                           'REASON': "[EnvironError] EnvironError: 'Errors for 7/7 thread(s).'"}}
        with app.test_request_context('profile/exceptions', json=request_data):
            set_error_or_warning()
            self.assertEqual(1, mock_set.call_count)
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.persistence.set')
    def test_set_error_or_warning__calls_abort_with_message(self, mock_set, mock_abort, mock_logger):
        error = Exception("Error")
        request_data = {"profile_key": "TEST_00-errors",
                        "profile_values": {'DUPLICATES': ['2020/02/02 06:00:05', '2020/02/02 12:00:04',
                                                          '2020/02/03 06:00:04', '2020/02/03 12:00:01',
                                                          '2020/02/04 06:00:03'], 'TIMESTAMP': '2020/02/04 12:00:05',
                                           'REASON': "[EnvironError] EnvironError: 'Errors for 7/7 thread(s).'"}}
        with app.test_request_context('profile/exceptions', json=request_data):
            mock_set.side_effect = error
            set_error_or_warning()
            mock_abort.assert_called_with("Failed to add Profile Exception.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.get_categories', return_value=["ap", "amos"])
    def test_categories_list__success(self, mock_get_profiles, mock_get_json):
        with app.test_request_context('categories'):
            categories_list()
            self.assertEqual(1, mock_get_profiles.call_count)
            mock_get_json.assert_called_with(message="\x1b[92mCategories:\nap, amos\x1b[0m")
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.get_categories')
    def test_categories_list__calls_abort_with_message(self, mock_get_profiles, mock_abort, mock_logger):
        error = Exception("Error")
        with app.test_request_context('categories'):
            mock_get_profiles.side_effect = error
            categories_list()
            mock_abort.assert_called_with("Failed to retrieve categories list.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.clear_profile_errors')
    def test_clear_errors__success(self, mock_clear_profile_errors, mock_get_json):
        request_data = {"profile_names": [u'CELLMGT_13', u'CELLMGT_14']}
        with app.test_request_context('clear/errors', json=request_data):
            clear_errors()
            self.assertEqual(1, mock_clear_profile_errors.call_count)
            mock_get_json.assert_called_with(message="\nSuccessfuly removed errors and warnings for profile(s):: "
                                                     "[CELLMGT_13, CELLMGT_14]")

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.clear_profile_errors')
    def test_clear_errors__calls_abort_with_message(self, mock_clear_profile_errors, mock_abort, mock_logger):
        error = Exception("Error")
        request_data = {"profile_names": "None"}
        with app.test_request_context('clear/errors', json=request_data):
            mock_clear_profile_errors.side_effect = error
            clear_errors()
            mock_abort.assert_called_with("Failed to remove profile errors from persistence.", mock_logger,
                                          'profilemanager', "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.delete_pid_files')
    def test_clear_pids__success(self, mock_clear_profile_errors, mock_get_json):
        request_data = {"profile_names": [u'CELLMGT_13', u'CELLMGT_14']}
        with app.test_request_context('clear/pids', json=request_data):
            clear_pids()
            self.assertEqual(1, mock_clear_profile_errors.call_count)
            mock_get_json.assert_called_with(message=mock_clear_profile_errors())
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.delete_pid_files')
    def test_clear_pids__calls_abort_with_message(self, mock_clear_profile_errors, mock_abort, mock_logger):
        error = Exception("Error")
        request_data = {"profile_names": [u'CELLMGT_13', u'CELLMGT_14']}
        with app.test_request_context('clear/pids', json=request_data):
            mock_clear_profile_errors.side_effect = error
            clear_pids()
            mock_abort.assert_called_with("Failed to remove profile pid files.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.get_all_profile_names', return_value=["CELLMGT_13", "CELLMGT_14"])
    def test_profiles_list__success(self, mock_get_profiles, mock_get_json):
        with app.test_request_context('profiles'):
            profiles_list()
            self.assertEqual(1, mock_get_profiles.call_count)
            mock_get_json.assert_called_with(message="\x1b[96mExisting Profiles:\x1b[0m\x1b[92m\nCELLMGT_13, "
                                                     "CELLMGT_14\x1b[0m")
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.get_all_profile_names')
    def test_profiles_list__calls_abort_with_message(self, mock_get_profiles, mock_abort, mock_logger):
        error = Exception("Error")
        with app.test_request_context('profiles'):
            mock_get_profiles.side_effect = error
            profiles_list()
            mock_abort.assert_called_with("Failed to retrieve profiles list.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.build_describe_message_for_profiles',
           return_value=["DESC1", "DESC2"])
    def test_describe__success(self, mock_build, mock_get_json):
        with app.test_request_context('describe', json={'profile_names': [u'CELLMGT_13', u'CELLMGT_14']}):
            describe()
            self.assertEqual(1, mock_build.call_count)
            mock_build.assert_called_with([u'CELLMGT_13', u'CELLMGT_14'])
            mock_get_json.assert_called_with(message="DESC1\nDESC2")
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.build_describe_message_for_profiles',
           return_value=["DESC1", "DESC2"])
    def test_describe__calls_abort_with_message(self, mock_build, mock_abort, mock_logger):
        error = Exception("Error")
        with app.test_request_context('describe', json={'profile_names': [u'CELLMGT_13', u'CELLMGT_14']}):
            mock_build.side_effect = error
            describe()
            mock_abort.assert_called_with("Unable to retrieve describe information.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.generate_export_file', return_value="Export Message")
    @patch('enmutils_int.lib.services.profilemanager.persistence.get_keys')
    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    def test_export__success(self, mock_get_json, *_):
        json_data = {"profiles_to_export": {}, "export_file_path": 'path',
                     "categories_to_export": {"TEST": {"NAME": "TEST_00"}}, "all_profiles": 'None',
                     "all_categories": 'None'}
        with app.test_request_context('export', json=json_data):
            export()
            mock_get_json.assert_called_with(message="Export Message")

    @patch('enmutils_int.lib.services.profilemanager.persistence.get_keys')
    @patch('enmutils.lib.log.logger')
    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.generate_export_file')
    def test_export__calls_abort_with_message(self, mock_gen, mock_abort, mock_logger, _):
        json_data = {"profiles_to_export": ["TEST_00"], "export_file_path": 'path',
                     "categories_to_export": 'None', "all_profiles": True, "all_categories": 'None'}
        error = Exception("Error")
        with app.test_request_context('export', json=json_data):
            mock_gen.side_effect = error
            export()
            mock_abort.assert_called_with("Failed to export profile(s) attributes.", mock_logger, 'profilemanager',
                                          "/home/enmutils/services", error)

    @patch('enmutils_int.lib.services.profilemanager.get_profile_status')
    def test_get_status__returns_single_profile(self, mock_get_profile_status):
        get_status(profile_name="TEST_00")
        self.assertEqual(1, mock_get_profile_status.call_count)
        mock_get_profile_status.assert_called_with("TEST_00")

    @patch('enmutils_int.lib.services.profilemanager.get_multiple_status')
    def test_get_status__returns_list_of_profiles(self, mock_get_multiple_status):
        get_status(profile_list=["TEST_00", "TEST_01"])
        self.assertEqual(1, mock_get_multiple_status.call_count)
        mock_get_multiple_status.assert_called_with(["TEST_00", "TEST_01"])

    @patch('enmutils_int.lib.services.profilemanager.get_profiles_by_category')
    def test_get_status__returns_profiles_by_category(self, mock_category_status):
        get_status(categories=["TEST", "TESTER"])
        self.assertEqual(1, mock_category_status.call_count)
        mock_category_status.assert_called_with(["TEST", "TESTER"])

    @patch('enmutils_int.lib.services.profilemanager.persistence.get_all_default_keys',
           return_value=["LTE01", "TEST_01-status", "TEST_00", "TEST_00-status"])
    @patch('enmutils_int.lib.services.profilemanager.persistence.get_key_values_from_default_db')
    def test_get_status__returns_all_profile_status(self, mock_get_keys, mock_get_all):
        get_status()
        self.assertEqual(1, mock_get_all.call_count)
        mock_get_keys.assert_called_with(["TEST_01-status", "TEST_00-status"])

    @patch('enmutils_int.lib.services.profilemanager.persistence.get')
    def test_get_profile_status__success(self, mock_get):
        get_profile_status("TEST_00")
        mock_get.assert_called_with("TEST_00-status")

    @patch('enmutils_int.lib.services.profilemanager.persistence.get_key_values_from_default_db')
    def test_get_multiple_status__success(self, mock_get_keys):
        get_multiple_status(["TEST_00", "TEST_01"])
        mock_get_keys.assert_called_with(["TEST_00-status", "TEST_01-status"])

    @patch('enmutils_int.lib.services.profilemanager.persistence.get_all_default_keys',
           return_value=["TEST_01-status", "TESTER_00-status", "NOT_00"])
    @patch('enmutils_int.lib.services.profilemanager.persistence.get_key_values_from_default_db')
    def test_get_profiles_by_category__success(self, mock_get_keys, mock_get_all):
        get_profiles_by_category(["TEST", "TESTER"])
        self.assertEqual(1, mock_get_all.call_count)
        mock_get_keys.assert_called_with(["TEST_01-status", "TESTER_00-status"])

    @patch('enmutils_int.lib.services.profilemanager.os')
    def test_delete_pid_files__only_removes_present_files(self, mock_os):
        mock_os.path.exists.side_effect = [True, False]
        mock_os.remove.return_value = True
        delete_pid_files([u'TEST_01', u'TEST_02'])
        self.assertEqual(1, mock_os.remove.call_count)

    @patch('enmutils_int.lib.services.profilemanager.log.green_text')
    @patch('enmutils_int.lib.services.profilemanager.os')
    def test_delete_pid_files__logs_missing_file(self, mock_os, mock_info):
        mock_os.path.exists.return_value = False
        mock_os.remove.return_value = True
        delete_pid_files([u'TEST_01'])
        self.assertEqual(0, mock_os.remove.call_count)
        mock_info.assert_called_with('No pid file found for TEST_01, nothing to delete.\n')

    @patch('enmutils_int.lib.services.profilemanager.print_basic_network_values')
    @patch('enmutils_int.lib.services.profilemanager.print_profile_description')
    def test_build_describe_message_for_profiles__returns_multiple_profile_describes(self, mock_print_desc,
                                                                                     mock_print_values):
        mock_print_desc.side_effect = ["DESC1 ", "DESC2 "]
        mock_print_values.side_effect = ["Values1", "Values2"]
        self.assertListEqual(["DESC1 Values1", "DESC2 Values2"], build_describe_message_for_profiles(
            ["TEST_00", "TEST_01"]))

    @patch('enmutils_int.lib.services.profilemanager.log.logger.info')
    @patch('enmutils_int.lib.services.profilemanager.log.cyan_text')
    def test_print_profile_description__success(self, mock_cyan, mock_info):
        print_profile_description("test_00")
        mock_cyan.assert_called_with("\n Description of the profile: TEST_00: \n")
        mock_info.assert_called_with('\n Please refer to the latest ENM TERE at: \n '
                                     'https://eteamspace.internal.ericsson.com'
                                     '/pages/viewpage.action?pageId=1982554551 \n ')

    @patch('enmutils_int.lib.services.profilemanager.log.logger.info')
    @patch('enmutils_int.lib.services.profilemanager.log.cyan_text')
    @patch('enmutils_int.lib.services.profilemanager.get_all_networks')
    def test_print_basic_network_values__success(self, mock_all_networks, mock_cyan, mock_info):
        mock_all_networks.return_value = {"basic": {"test": {"TEST_SETUP": {"NUM_NODES": {"ERBS": -1}}}}}
        print_basic_network_values("test_setup")
        mock_cyan.assert_called_with("\n Basic network values for TEST_SETUP: \n")
        mock_info.assert_called_with("{\'NUM_NODES\': {\'ERBS\': -1}}\n")

    @patch('enmutils_int.lib.services.profilemanager.export_all')
    def test_generate_export_file__all_categories(self, mock_export_all):
        profiles = {"TEST_00": Mock()}
        categories = {"TEST_00": Mock()}
        generate_export_file(profiles, "path", categories_to_export=categories, all_categories=True)
        mock_export_all.assert_called_with(categories, "path", all_profiles=False)

    @patch('enmutils_int.lib.services.profilemanager.get_profiles_and_file_names',
           return_value={"path/1": [Mock(NAME="TEST_00")]})
    @patch('enmutils_int.lib.services.profilemanager.print_export_path')
    @patch('enmutils_int.lib.services.profilemanager.write_to_file')
    def test_generate_export_file__specific_profiles(self, mock_write, mock_print, mock_get_profiles):
        profiles = {"TEST_00": Mock(), "OTHER_01": Mock()}
        generate_export_file(profiles, "path", categories_to_export=None)
        self.assertEqual(1, mock_write.call_count)
        self.assertEqual(1, mock_print.call_count)
        self.assertEqual(1, mock_get_profiles.call_count)

    @patch('enmutils_int.lib.services.profilemanager.get_profiles_and_file_names')
    @patch('enmutils_int.lib.services.profilemanager.print_export_path')
    @patch('enmutils_int.lib.services.profilemanager.write_to_file')
    def test_generate_export_file__category(self, mock_write, mock_print, mock_get_profiles):
        profiles = {"TEST_00": Mock(), "OTHER_01": Mock()}
        categories = {"TEST": [Mock(), Mock()]}
        generate_export_file(profiles, "path", categories_to_export=categories)
        self.assertEqual(1, mock_write.call_count)
        self.assertEqual(1, mock_print.call_count)
        self.assertEqual(0, mock_get_profiles.call_count)

    @patch('enmutils_int.lib.services.profilemanager.os.path.join', return_value="/path/file_name")
    def test_write_to_file__success(self, _):
        mock_open_file = mock_open()
        profile, profile1 = Mock(), Mock()
        profile.EXPORTABLE = False
        profile1.EXPORTABLE = True
        profile1.SCHEDULED_TIMES = [datetime.now()]
        profile1.SUPPORTED = "MANUAL"
        profiles = [profile, profile1]
        with patch('__builtin__.open', mock_open_file):
            write_to_file(profiles, "file_name", "path")
        self.assertEqual(1, mock_open_file.call_count)

    def test_get_profiles_and_file_names__sorts_profiles_by_app(self):
        profiles_to_export = {"TEST_00": Mock(), "TEST_01": Mock(), "OTHER_00": Mock()}
        result = get_profiles_and_file_names(profiles_to_export)
        self.assertListEqual(result.keys(), ["test_test.py", "other_00_test.py"])
        self.assertEqual(2, len(result.get("test_test.py")))

    def test_print_export_path__outputs_file_details_correctly(self):
        file_list = ["/path/to/file", "/path/file/file1"]
        file_paths = print_export_path(file_list, [0, 1], "profile", "path")
        self.assertEqual("0 profile properties exported to /path/to/file\n1 profile properties exported to /path/file"
                         "/file1", file_paths)

    @patch('enmutils_int.lib.services.profilemanager.write_to_file')
    def test_export_all__all_profiles(self, _):
        message = export_all({}, export_file_path="path", all_profiles=True)
        self.assertEqual(message, "All profiles properties exported to 'all_profiles_test.py' in path directory.")

    @patch('enmutils_int.lib.services.profilemanager.write_to_file')
    def test_export_all__all_categories(self, _):
        message = export_all({}, export_file_path="path")
        self.assertEqual(message, "All profiles properties from all categories exported to 'all_categories_test.py' "
                                  "in path directory.")

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.diff_profiles',
           return_value=["message1", "message2"])
    def test_diff__is_successful(self, mock_diff_profiles, mock_get_json):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": ["TEST_01", "TEST_02"], "priority": 1}
        with app.test_request_context('diff', json={'diff_parameters': parameters}):
            diff()
            self.assertEqual(1, mock_diff_profiles.call_count)
            mock_diff_profiles.assert_called_with(updated=True, list_format=True, version="1.2.3",
                                                  profile_names=["TEST_01", "TEST_02"], priority=1)
            mock_get_json.assert_called_with(message="message1\nmessage2")
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.diff_profiles',
           side_effect=RuntimeError("No 'diff' information to display for the profiles provided"))
    def test_diff__is_successful_if_no_diff_info(self, mock_diff_profiles, mock_get_json):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": ["TEST_01", "TEST_02"], "priority": 1}
        with app.test_request_context('diff', json={'diff_parameters': parameters}):
            diff()
            self.assertEqual(1, mock_diff_profiles.call_count)
            mock_diff_profiles.assert_called_with(updated=True, list_format=True, version="1.2.3",
                                                  profile_names=["TEST_01", "TEST_02"], priority=1)
            mock_get_json.assert_called_with(message="No 'diff' information to display for the profiles provided",
                                             rc=599)
            self.assertEqual(1, mock_get_json.call_count)

    @patch('enmutils_int.lib.services.profilemanager.config.set_prop')
    @patch('enmutils_int.lib.services.profilemanager.get_json_response')
    @patch('enmutils_int.lib.services.profilemanager.diff_profiles',
           return_value=["message1", "message2"])
    def test_diff__disables_log_colour(self, mock_diff_profiles, mock_get_json, mock_set):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": ["TEST_01", "TEST_02"], "priority": 1, "no_ansi": True}
        with app.test_request_context('diff', json={'diff_parameters': parameters}):
            diff()
            self.assertEqual(1, mock_diff_profiles.call_count)
            mock_diff_profiles.assert_called_with(updated=True, list_format=True, version="1.2.3",
                                                  profile_names=["TEST_01", "TEST_02"], priority=1, no_ansi=True)
            mock_get_json.assert_called_with(message="message1\nmessage2")
            self.assertEqual(1, mock_get_json.call_count)
            self.assertEqual(2, mock_set.call_count)

    @patch('enmutils_int.lib.services.profilemanager.abort_with_message')
    @patch('enmutils_int.lib.services.profilemanager.diff_profiles',
           side_effect=Exception)
    def test_diff__is_unsuccessful(self, mock_diff_profiles, mock_abort_with_message):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": ["TEST_01", "TEST_02"], "priority": 1}
        with app.test_request_context('diff', json={'diff_parameters': parameters}):
            diff()
            self.assertEqual(1, mock_diff_profiles.call_count)
            mock_diff_profiles.assert_called_with(updated=True, list_format=True, version="1.2.3",
                                                  profile_names=["TEST_01", "TEST_02"], priority=1)
            self.assertEqual(1, mock_abort_with_message.call_count)

    @patch('enmutils_int.lib.services.profilemanager.create_and_start_once_off_background_scheduled_job')
    @patch('enmutils_int.lib.services.profilemanager.create_and_start_background_scheduled_job')
    def test_at_startup__starts_background_jobs(self, mock_start_background_job, mock_start_once_off_job):
        at_startup()
        self.assertEqual(1, mock_start_background_job.call_count)
        self.assertEqual(1, mock_start_once_off_job.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager.get_persisted_profiles_by_name', return_value={})
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state')
    def test_verify_profiles__no_profiles_to_check(self, mock_verify, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        verify_profiles()
        self.assertEqual(0, mock_verify.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager.get_persisted_profiles_by_name',
           return_value={"TEST_00", Mock(NAME="TEST_00")})
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state')
    def test_verify_profiles__skips_consistently_dead(self, mock_verify, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = ["TEST_00"]
        verify_profiles()
        self.assertEqual(0, mock_verify.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager.get_persisted_profiles_by_name',
           return_value={"TEST_00": Mock(NAME="TEST_00", state="DEAD", start_time="NOW")})
    @patch('enmutils_int.lib.services.profilemanager.check_for_consistently_dead_or_inactive_profiles')
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state', return_value=[])
    def test_verify_profiles__no_profiles_returned(self, mock_verify, mock_check, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        verify_profiles()
        self.assertEqual(1, mock_verify.call_count)
        self.assertEqual(0, mock_check.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager.get_persisted_profiles_by_name',
           return_value={"TEST_00": Mock(NAME="TEST_01", state="DEAD", start_time="NOW")})
    @patch('enmutils_int.lib.services.profilemanager.check_for_consistently_dead_or_inactive_profiles')
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state', return_value=["TEST_01"])
    def test_verify_profiles__checks_return_profile_inactive_count(self, mock_verify, mock_check, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        verify_profiles()
        self.assertEqual(1, mock_verify.call_count)
        self.assertEqual(1, mock_check.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager.get_persisted_profiles_by_name',
           return_value={"TEST_00": Mock(NAME="TEST_00", state="DEAD", start_time="NOW")})
    @patch('enmutils_int.lib.services.profilemanager.check_for_consistently_dead_or_inactive_profiles',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.profilemanager.log.logger.debug')
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state', return_value=["TEST_01"])
    def test_verify_profiles__logs_exception(self, mock_verify, mock_debug, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        verify_profiles()
        self.assertEqual(1, mock_verify.call_count)
        self.assertEqual(2, mock_debug.call_count)

    @patch('enmutils_int.lib.services.profilemanager.threading')
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key', return_value=True)
    @patch('enmutils_int.lib.services.profilemanager.log.logger.debug')
    @patch('enmutils_int.lib.services.profilemanager.verify_profile_state', return_value=["TEST_01"])
    def test_verify_profiles__check_is_disabled(self, mock_verify, mock_debug, *_):
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        verify_profiles()
        self.assertEqual(0, mock_verify.call_count)
        mock_debug.assert_called_with("Verification currently disabled, no checks will be performed.")

    @patch('enmutils_int.lib.services.profilemanager.reset_recently_restarted_profiles_dead_count')
    def test_check_for_consistently_dead_or_inactive_profiles__updates_consistently_dead(self, _):
        profile_name = "TEST_00"
        profilemanager.DEAD_PROFILES[profile_name] = 3
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        check_for_consistently_dead_or_inactive_profiles([profile_name], {})
        self.assertListEqual([profile_name], profilemanager.CONSISTENTLY_DEAD_PROFILES)

    @patch('enmutils_int.lib.services.profilemanager.reset_recently_restarted_profiles_dead_count')
    def test_check_for_consistently_dead_or_inactive_profiles__increments_dead(self, _):
        profile_name = "TEST_00"
        profilemanager.DEAD_PROFILES[profile_name] = 1
        profilemanager.CONSISTENTLY_DEAD_PROFILES = []
        check_for_consistently_dead_or_inactive_profiles([profile_name], {})
        self.assertDictEqual({profile_name: 2}, profilemanager.DEAD_PROFILES)
        self.assertListEqual([], profilemanager.CONSISTENTLY_DEAD_PROFILES)

    @patch('enmutils_int.lib.services.profilemanager.reset_recently_restarted_profiles_dead_count')
    def test_check_for_consistently_dead_or_inactive_profiles__adds_dead(self, _):
        profile_name = "TEST_00"
        profilemanager.DEAD_PROFILES = {}
        check_for_consistently_dead_or_inactive_profiles([profile_name], {})
        self.assertDictEqual({profile_name: 1}, profilemanager.DEAD_PROFILES)

    @patch('enmutils_int.lib.services.profilemanager.reset_recently_restarted_profiles_dead_count')
    def test_check_for_consistently_dead_or_inactive_profiles__resets_profile_if_node_inactive_or_dead_check(self, _):
        profile_name = "TEST_00"
        profilemanager.DEAD_PROFILES = {"TEST_01": 1}
        check_for_consistently_dead_or_inactive_profiles([profile_name], {})
        self.assertDictEqual({profile_name: 1}, profilemanager.DEAD_PROFILES)

    @patch('enmutils_int.lib.services.profilemanager.datetime.datetime')
    def test_reset_recently_restarted_profiles_dead_count__resets_profile(self, mock_datetime):
        mock_datetime.now.return_value = datetime(year=2020, month=8, day=04, hour=12, minute=00, second=00)
        profilemanager.DEAD_PROFILES["TEST_00"] = 1
        profilemanager.reset_recently_restarted_profiles_dead_count(
            ["TEST_00"], {"TEST_00": datetime(year=1900, month=8, day=04, hour=10, minute=00, second=00)})
        self.assertEqual(0, profilemanager.DEAD_PROFILES.get('TEST_00'))

    @patch('enmutils_int.lib.services.profilemanager.datetime.datetime')
    def test_reset_recently_restarted_profiles_dead_count__no_reset_required(self, mock_datetime):
        mock_datetime.now.return_value = datetime(year=2020, month=8, day=04, hour=14, minute=00, second=01)
        profilemanager.DEAD_PROFILES["TEST_00"] = 2
        profilemanager.reset_recently_restarted_profiles_dead_count(
            ["TEST_00"], {"TEST_00": datetime(year=1900, month=8, day=04, hour=10, minute=00, second=00)})
        self.assertEqual(2, profilemanager.DEAD_PROFILES.get('TEST_00'))

    @patch('enmutils_int.lib.services.profilemanager.datetime.datetime')
    @patch('enmutils_int.lib.services.profilemanager.log.logger.debug')
    def test_reset_recently_restarted_profiles_dead_count__invalid_start_time(self, mock_debug, mock_datetime):
        mock_datetime.now.return_value = None
        profilemanager.DEAD_PROFILES["TEST_00"] = 2
        profilemanager.reset_recently_restarted_profiles_dead_count(["TEST_00"], {"TEST_00": None})
        mock_debug.assert_called_with("Start time is not in correct format to verify.")

    @patch('enmutils_int.lib.services.profilemanager.log.logger.debug')
    @patch('enmutils_int.lib.services.profilemanager.verify_profiles', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.profilemanager.persisted_verify_key')
    def test_once_off_function_holder(self, mock_persisted, mock_verify, mock_debug):
        profilemanager.once_off_function_holder()
        self.assertEqual(1, mock_persisted.call_count)
        self.assertEqual(1, mock_verify.call_count)
        mock_debug.assert_called_with("Error")

    @patch('enmutils_int.lib.services.profilemanager.persistence.get')
    @patch('enmutils_int.lib.services.profilemanager.persistence.remove')
    def test_persisted_verify_key__returns_key(self, mock_remove, mock_get):
        profilemanager.persisted_verify_key(remove_key=False)
        self.assertEqual(0, mock_remove.call_count)
        self.assertEqual(1, mock_get.call_count)

    @patch('enmutils_int.lib.services.profilemanager.persistence.get')
    @patch('enmutils_int.lib.services.profilemanager.persistence.remove')
    def test_persisted_verify_key__removes_key(self, mock_remove, _):
        profilemanager.persisted_verify_key()
        self.assertEqual(1, mock_remove.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
