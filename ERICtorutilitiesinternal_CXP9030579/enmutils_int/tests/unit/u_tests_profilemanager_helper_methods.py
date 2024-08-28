#!/usr/bin/env python
from datetime import datetime
from mock import call, patch, Mock
from parameterizedtestcase import ParameterizedTestCase

import unittest2
from enmutils_int.lib.services import profilemanager_helper_methods
from testslib import unit_test_utils


class ProfileManagerHelperMethodsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    # diff_profiles test cases
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.IGNORE_PROFILES", ["TEST_02"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names", return_value=["TEST_01"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_installed_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_list_of_active_profiles_names")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.print_profiles_to_restart")
    def test_diff_profiles__is_successful_if_updated_list_needed(
            self, mock_print_profiles_to_restart, mock_get_list_of_active_profiles_names, mock_get_installed_version,
            *_):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profiles_names": ["PROFILE_01"], "priority": 1}
        active_profiles = ["PROFILE_01", "PROFILE_02"]
        mock_get_list_of_active_profiles_names.return_value = active_profiles
        mock_get_installed_version.return_value = "1.2.2"
        profilemanager_helper_methods.diff_profiles(**parameters)
        mock_print_profiles_to_restart.assert_called_with(active_profiles, True, "1.2.2")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.IGNORE_PROFILES", ["TEST_02"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names", return_value=["TEST_01"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_installed_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_list_of_active_profiles_names")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.print_profiles_diff")
    def test_diff_profiles__is_successful_if_updated_list_not_needed(
            self, mock_print_profiles_diff, mock_get_list_of_active_profiles_names, mock_get_installed_version, *_):
        parameters = {"list_format": True, "version": "1.2.3", "profile_names": ["PROFILE_01"], "priority": 1}
        active_profiles = ["PROFILE_01", "PROFILE_02"]
        mock_get_list_of_active_profiles_names.return_value = active_profiles
        mock_get_installed_version.return_value = "1.2.2"
        profilemanager_helper_methods.diff_profiles(**parameters)
        mock_print_profiles_diff.assert_called_with(["PROFILE_01"], ["TEST_01"], True, "1.2.3", 1, ["TEST_02"],
                                                    "1.2.2")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.IGNORE_PROFILES", ["TEST_02"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names", return_value=["TEST_01"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_installed_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_list_of_active_profiles_names")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.print_profiles_diff", side_effect=RuntimeError)
    def test_diff_profiles__raises_exception_if_no_profiles_to_list(
            self, mock_print_profiles_diff, mock_get_list_of_active_profiles_names, mock_get_installed_version, *_):
        parameters = {"list_format": True, "version": "1.2.3", "profile_names": ["PROFILE_01"], "priority": 1}
        active_profiles = ["PROFILE_01", "PROFILE_02"]
        mock_get_list_of_active_profiles_names.return_value = active_profiles
        mock_get_installed_version.return_value = "1.2.2"
        self.assertRaises(RuntimeError, profilemanager_helper_methods.diff_profiles, **parameters)
        mock_print_profiles_diff.assert_called_with(["PROFILE_01"], ["TEST_01"], True, "1.2.3", 1, ["TEST_02"],
                                                    "1.2.2")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.IGNORE_PROFILES", ["TEST_02"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names", return_value=["TEST_01"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_installed_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_list_of_active_profiles_names")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.print_profiles_to_restart")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_difference_nodes_between_wlvm_and_enm")
    def test_diff_profiles__is_successful_when_node_diff_is_true(self, mock_get_difference_nodes_between_wlvm_and_enm,
                                                                 *_):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profiles_names": ["PROFILE_01"], "priority": 1, "wl_enm_nodes_diff": True}
        profilemanager_helper_methods.diff_profiles(**parameters)
        self.assertEqual(mock_get_difference_nodes_between_wlvm_and_enm.call_count, 1)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.IGNORE_PROFILES", ["TEST_02"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names", return_value=["TEST_01"])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_installed_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_list_of_active_profiles_names")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.print_profiles_to_restart")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_wl_poids")
    def test_diff_profiles__is_successful_when_poid_diff_is_true(self, mock_get_wl_poids, *_):
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profiles_names": ["PROFILE_01"], "priority": 1, "wl_enm_poids_diff": True}
        profilemanager_helper_methods.diff_profiles(**parameters)
        self.assertEqual(mock_get_wl_poids.call_count, 1)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_persisted_profiles_by_name")
    def test_get_list_of_active_profiles_names__is_successful(self, mock_get_persisted_profiles_by_name):
        profiles = {"TEST_01": Mock(), "TEST_02": Mock()}
        mock_get_persisted_profiles_by_name.return_value = profiles
        self.assertEqual(["TEST_01", "TEST_02"], profilemanager_helper_methods.get_list_of_active_profiles_names())

    def test_get_data_for_profiles_to_restart__is_successful(self):
        self.mock_profile.version = '1.2.3'
        self.mock_profile.start_time = datetime(2019, 8, 7, 10, 10, 0)
        self.assertEqual(profilemanager_helper_methods.get_data_for_profiles_to_restart([self.mock_profile]),
                         [['\x1b[96mTEST_01\x1b[0m', '1.2.3', '07-08-2019', '\x1b[92mYES\x1b[0m']])

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    def test_print_profiles_to_restart__no_active_profiles(self, mock_log):
        active_profiles = []
        profilemanager_helper_methods.print_profiles_to_restart(active_profiles, False, "")
        mock_log.assert_called_with("\x1b[92mNo profiles to be restarted. No active profiles found.\x1b[0m")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_updated_active_profiles")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    def test_print_profiles_to_restart__list_format(self, mock_log, mock_get_updated):
        active_profiles = ['TEST_01']
        mock_get_updated.return_value = [self.mock_profile]
        profilemanager_helper_methods.print_profiles_to_restart(active_profiles, True, "")
        mock_log.assert_called_with("TEST_01")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.tabulate")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_data_for_profiles_to_restart")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    def test_print_profiles_to_restart__is_successful(self, mock_log, mock_get_data, mock_tab):
        installed_version = '1.2.3'
        active_profiles = ['TEST_01']
        mock_get_data.return_value = ['TEST_01', 'YES', '-']
        profilemanager_helper_methods.print_profiles_to_restart(active_profiles, False, installed_version)
        self.assertEqual(mock_log.call_count, 2)
        self.assertTrue(mock_tab.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.tabulate")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_data_for_profiles_to_restart")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    def test_print_profiles_to_restart__no_tabulate_data(self, mock_log, mock_get_data, mock_tab):
        installed_version = '1.2.3'
        active_profiles = ['TEST_01']
        mock_get_data.return_value = []
        profilemanager_helper_methods.print_profiles_to_restart(active_profiles, False, installed_version)
        self.assertEqual(mock_log.call_count, 2)
        self.assertFalse(mock_tab.called)

    # print_profiles_diff test cases
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_running_not_running_profiles")
    def test_print_profiles_diff__is_successful_if_list_format_required(self, mock_running_not_running, mock_info):
        profile_names = ['TEST_01']
        mock_running_not_running.return_value = [self.mock_profile], []
        profilemanager_helper_methods.print_profiles_diff(profile_names=profile_names, supported_profiles=[],
                                                          list_format=True, version="", priority=1, ignore=[],
                                                          installed_version="")
        mock_info.assert_called_with("TEST_01")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.update_message")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.is_valid_version_number", return_value=True)
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.tabulate")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_profiles_info_for_specific_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.check_nexus_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_running_not_running_profiles")
    def test_print_profiles_diff__if_version_and_no_artifact_profiles(
            self, mock_running_not_running, mock_check_nexus, mock_info, mock_set_tab, mock_tabulate, *_):
        profile_names = ['TEST_01']
        mock_running_not_running.return_value = [self.mock_profile], []
        mock_check_nexus.return_value = '1.2.4'
        mock_info.return_value = {"TEST_00": {'SUPPORTED': True, 'PHYSICAL_SUPPORTED': True, 'NOTE': '-',
                                              'PROJECT': '-', 'CLOUD_SUPPORTED': True, 'PRIORITY': '1'},
                                  "TEST_01": {'SUPPORTED': True, 'PHYSICAL_SUPPORTED': True, 'NOTE': '-',
                                              'PROJECT': '-', 'CLOUD_SUPPORTED': True, 'PRIORITY': '1'}}, {}
        tabulate_data = ['TEST_01', 'YES', 'YES', 'NO', 'YES', '-']
        mock_set_tab.return_value = tabulate_data
        profilemanager_helper_methods.print_profiles_diff(profile_names=profile_names, supported_profiles=[],
                                                          list_format=False, version="1.2.3", priority=1, ignore=[],
                                                          installed_version="1.2.4")
        self.assertTrue(mock_tabulate.called)
        self.assertTrue(mock_set_tab.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info",
           return_value=['TEST_01', 'YES', '-'])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.is_valid_version_number", return_value=True)
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.update_message")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.tabulate")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_profiles_info_for_specific_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.check_nexus_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_running_not_running_profiles")
    def test_print_profiles_diff__if_successful_if_version_not_specified_and_no_artifact_profiles(
            self, mock_running_not_running, mock_check_nexus, mock_get_profiles_info_for_specific_version,
            mock_tabulate, *_):
        profile_names = ['TEST_01']
        mock_running_not_running.return_value = [self.mock_profile], []
        mock_get_profiles_info_for_specific_version.return_value = {}, {}
        profilemanager_helper_methods.print_profiles_diff(profile_names=profile_names, supported_profiles=[],
                                                          list_format=False, version="", priority=1, ignore=[],
                                                          installed_version="1.2.4")
        self.assertTrue(mock_tabulate.called)
        self.assertFalse(mock_check_nexus.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.config.set_prop")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.check_nexus_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.is_valid_version_number")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info", return_value=[])
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_profiles_info_for_specific_version")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_running_not_running_profiles")
    def test_print_profiles_diff__raises_runtime_error(
            self, mock_running_not_running, mock_info, _, mock_is_valid, mock_check_nexus, mock_set):
        profile_names = ['TEST_01']
        mock_running_not_running.return_value = [self.mock_profile], []
        mock_info.return_value = {}, {}
        mock_is_valid.return_value = False
        with self.assertRaises(RuntimeError):
            profilemanager_helper_methods.print_profiles_diff(profile_names=profile_names, supported_profiles=[],
                                                              list_format=False, version="1.2", priority=1, ignore=[],
                                                              installed_version="1.2.4")
        self.assertFalse(mock_check_nexus.called)
        self.assertEqual(1, mock_set.call_count)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_profiles_info_for_specified_priority")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_active_profiles")
    def test_get_running_not_running_profiles__if_priority(self, mock_load_mgr, mock_info):
        mock_load_mgr.get_all_active_profiles.return_value = {'TEST_01': self.mock_profile}
        mock_load_mgr.get_profile.return_value = []
        mock_info.return_value = [], []
        profilemanager_helper_methods.get_running_not_running_profiles([], 1, [], "")
        self.assertTrue(mock_info.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_profiles_info_for_specified_priority")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_active_profiles")
    def test_get_running_not_running_profiles__if_not_priority(self, mock_load_mgr, mock_info):
        mock_load_mgr.get_all_active_profiles.return_value = {'TEST_01': self.mock_profile}
        mock_load_mgr.get_profile.return_value = []
        mock_info.return_value = [], []
        profilemanager_helper_methods.get_running_not_running_profiles([], 0, [], "")
        self.assertFalse(mock_info.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.return_dict_from_json_artifact")
    def test_get_profiles_info_for_specified_priority__is_successful(self, mock_json_dict):
        mock_json_dict.return_value = {
            "basic": {
                'test': {
                    'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1},
                    'TEST_02': {'SUPPORTED': True, 'PRIORITY': 2},
                    'TEST_03': {'SUPPORTED': True, 'PRIORITY': 1},
                }
            }
        }
        mock_profile_2 = Mock()
        mock_profile_2.NAME = 'TEST_02'
        mock_profile_3 = Mock()
        mock_profile_3.NAME = 'TEST_03'
        mock_profile_4 = Mock()
        mock_profile_4.NAME = 'TEST_04'
        mock_profile_5 = Mock()
        mock_profile_5.NAME = 'EXAMPLE_01'
        expected = [self.mock_profile], []
        self.assertEqual(expected,
                         profilemanager_helper_methods.get_profiles_info_for_specified_priority(
                             running=[self.mock_profile, mock_profile_2, mock_profile_3, mock_profile_4,
                                      mock_profile_5],
                             not_running=[mock_profile_2], priority=1, ignore=['TEST_03'], installed_version=""))

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.return_dict_from_json_artifact")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_networks")
    def test_get_profiles_info_for_specific_version__is_successful(
            self, mock_get_all_networks, mock_return_dict):
        basic_network = {"basic": {'test': {
            'TEST_01': {'SUPPORTED': True, 'PHYSICAL': True, 'PRIORITY': 1},
            'TEST_02': {'SUPPORTED': True, 'PHYSICAL': True, 'PRIORITY': 2}}}}
        mock_get_all_networks.return_value = {'basic': basic_network}
        mock_return_dict.return_value = basic_network
        profiles_supported_artifact, profiles_supported_local = (
            {'TEST_01': {'NOTE': None, 'PRIORITY': 1, 'SUPPORTED': True, 'PHYSICAL_SUPPORTED': None,
                         'CLOUD_SUPPORTED': None, 'CLOUD_NATIVE_SUPPORTED': None},
             'TEST_02': {'NOTE': None, 'PRIORITY': 2, 'SUPPORTED': True, 'PHYSICAL_SUPPORTED': None,
                         'CLOUD_SUPPORTED': None, 'CLOUD_NATIVE_SUPPORTED': None}},
            {'test': {'NOTE': None, 'PRIORITY': None, 'SUPPORTED': None, 'PHYSICAL_SUPPORTED': None,
                      'CLOUD_SUPPORTED': None, 'CLOUD_NATIVE_SUPPORTED': None}})
        self.assertEqual(
            profilemanager_helper_methods.get_profiles_info_for_specific_version("1.2.3", []),
            (profiles_supported_artifact, profiles_supported_local))

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_all_networks")
    def test_get_profiles_info_for_specific_version__if_version_none(self, mock_get_all_networks):
        basic_network = {"basic": {'test': {
            'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1},
            'TEST_02': {'SUPPORTED': True, 'PRIORITY': 2}}}}
        mock_get_all_networks.return_value = {'basic': basic_network}
        profilemanager_helper_methods.get_profiles_info_for_specific_version("", [])

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.green_text")
    def test_diff_op___set_supported_value_text_and_get_profile_values_for_artifact_profile(self, mock_log):
        artifact_profiles = {'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1}}
        profilemanager_helper_methods.set_supported_value_text_and_get_profile_values_for_artifact_profile(
            artifact_profiles, self.mock_profile)
        mock_log.assert_called_with("YES")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.debug")
    def test_set_supported_value_text_and_get_profile_values_for_artifact_profile__for_artifact_profile_no_profile(
            self, mock_log):
        artifact_profiles = {'TEST_03': {'SUPPORTED': True, 'PRIORITY': 1}}
        profilemanager_helper_methods.set_supported_value_text_and_get_profile_values_for_artifact_profile(
            artifact_profiles, self.mock_profile)
        mock_log.assert_called_with("Error getting profile from nexus version of TEST_01. "
                                    "May have been deprecated or name changed.")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_text_of_supported_value")
    def test_set_tabulated_info_for_local_version_supported(self, mock_set_text_of_supported_value):
        profile_value = {'SUPPORTED': False, 'PRIORITY': 1}
        profilemanager_helper_methods.set_tabulated_info_for_local_version_supported(profile_value)
        self.assertTrue(mock_set_text_of_supported_value.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_text_of_supported_value")
    def test_set_tabulated_info_for_local_version_supported__no_profile_value(self, mock_set):
        profilemanager_helper_methods.set_tabulated_info_for_local_version_supported({})
        self.assertFalse(mock_set.called)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.green_text")
    def test_set_text_of_supported_value__supported_is_true(self, mock_log):
        profilemanager_helper_methods.set_text_of_supported_value({'SUPPORTED': True, 'PRIORITY': 1})
        mock_log.assert_called_with("YES")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.yellow_text")
    def test_set_text_of_supported_value__supported_not_boolean(self, mock_log):
        profilemanager_helper_methods.set_text_of_supported_value({'SUPPORTED': 'INTRUSIVE', 'PRIORITY': 1})
        mock_log.assert_called_with("INTRUSIVE")

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.red_text")
    def test_set_text_of_supported_value__supported_is_false(self, mock_log):
        profilemanager_helper_methods.set_text_of_supported_value({'SUPPORTED': False, 'PRIORITY': 1})
        mock_log.assert_called_with("NO")

    @ParameterizedTestCase.parameterize(
        "profile_value', 'expected_text",
        [
            ({'CLOUD_SUPPORTED': False}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': True}, '\x1b[92mYES\x1b[0m'),
            ({'SUPPORTED': 'INTRUSIVE'}, '\x1b[33mINTRUSIVE\x1b[0m')
        ]
    )
    def test_get_text_value_for_cloud_supported__is_successful(self, profile_value, expected_text):
        self.assertEqual(profilemanager_helper_methods.get_text_value_for_cloud_supported(profile_value),
                         expected_text)

    @ParameterizedTestCase.parameterize(
        "profile_value', 'expected_text",
        [
            ({'SUPPORTED': True, 'CLOUD_NATIVE_SUPPORTED': True}, '\x1b[92mYES\x1b[0m'),
            ({'SUPPORTED': True, 'CLOUD_NATIVE_SUPPORTED': False}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': True}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': False}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': 'INTRUSIVE'}, '\x1b[33mINTRUSIVE\x1b[0m')
        ]
    )
    def test_get_text_value_for_cloud_native_supported__is_successful(self, profile_value, expected_text):
        self.assertEqual(profilemanager_helper_methods.get_text_value_for_cloud_native_supported(profile_value),
                         expected_text)

    @ParameterizedTestCase.parameterize(
        "profile_value', 'expected_text",
        [
            ({'SUPPORTED': True, 'PHYSICAL_SUPPORTED': True}, '\x1b[92mYES\x1b[0m'),
            ({'SUPPORTED': True, 'PHYSICAL_SUPPORTED': False}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': True}, '\x1b[92mYES\x1b[0m'),
            ({'SUPPORTED': False}, '\x1b[91mNO\x1b[0m'),
            ({'SUPPORTED': 'INTRUSIVE', 'PHYSICAL_SUPPORTED': 'INTRUSIVE'}, '\x1b[33mINTRUSIVE\x1b[0m'),
            ({'SUPPORTED': 'INTRUSIVE'}, '\x1b[33mINTRUSIVE\x1b[0m')
        ]
    )
    def test_get_text_value_for_physical_supported__is_successful(self, profile_value, expected_text):
        self.assertEqual(profilemanager_helper_methods.get_text_value_for_physical_supported(profile_value),
                         expected_text)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_profile_values")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_for_local_version_supported")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods."
           "set_supported_value_text_and_get_profile_values_for_artifact_profile")
    def test_set_tabulated_info__is_successful_with_artifact_profiles(
            self, mock_artifact, mock_set_local, mock_set_tabulated_info_profile_values):
        profile_values_local = {'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1}}
        mock_profile_test_02 = Mock(NAME="TEST_02")
        mock_artifact.return_value = '1.2.4', mock_profile_test_02
        mock_set_local.return_value = '1.2.3'
        profilemanager_helper_methods.set_tabulated_info(
            tabulate_data=[], profiles=[self.mock_profile],
            profile_values_local=profile_values_local, ignore=[], artifact_profiles={'TEST_02': mock_profile_test_02},
            running=False)
        self.assertTrue(call(self.mock_profile, False, '1.2.3', '1.2.4',
                             {'SUPPORTED': True, 'PRIORITY': 1}, mock_profile_test_02) in
                        mock_set_tabulated_info_profile_values.mock_calls)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_profile_values")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_for_local_version_supported")
    def test_set_tabulated_info__is_successful_with_no_artifact_profiles(
            self, mock_set_local, mock_set_tabulated_info_profile_values):
        profile_values_local = {'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1}}
        mock_set_local.return_value = '1.2.3'
        mock_ignore_profile = Mock()
        mock_ignore_profile.NAME = 'APP_01'
        profilemanager_helper_methods.set_tabulated_info(
            tabulate_data=[], profiles=[self.mock_profile, mock_ignore_profile],
            profile_values_local=profile_values_local, ignore=["APP_01"], artifact_profiles={})
        self.assertTrue(call(self.mock_profile, True, '1.2.3', None, {'SUPPORTED': True, 'PRIORITY': 1}, None) in
                        mock_set_tabulated_info_profile_values.mock_calls)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.debug")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_profile_values")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.set_tabulated_info_for_local_version_supported")
    def test_diff_op__set_tabulated_info_profile_value_none(
            self, mock_set_local, mock_set_tabulated_info_profile_values, mock_debug):
        profile_value = {'TEST_03': {'SUPPORTED': True, 'PRIORITY': 1}}
        mock_set_local.return_value = '1.2.3'
        profilemanager_helper_methods.set_tabulated_info(
            [], [self.mock_profile], profile_value, [], {})
        self.assertFalse(mock_set_tabulated_info_profile_values.called)
        self.assertTrue(mock_debug.call_count, 2)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.yellow_text", return_value="priority")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.red_text", return_value="not_running")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.green_text", return_value="running")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.cyan_text", return_value="profile_name")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_physical_supported",
           return_value="PHYSICAL_SUPPORTED")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_cloud_supported",
           return_value="CLOUD_SUPPORTED")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_cloud_native_supported",
           return_value="CLOUD_NATIVE_SUPPORTED")
    def test_set_tabulated_info_profile_values__is_successful_with_no_artifact_profile(self, *_):
        profile = Mock(NAME="TEST_PROFILE")
        artifact_profile = None
        running = True
        local_version_supported = "1.2.3"
        nexus_version_supported = "1.2.4"
        profile_value = {'SUPPORTED': True, 'PRIORITY': 1}
        profile_info = profilemanager_helper_methods.set_tabulated_info_profile_values(
            profile, running, local_version_supported, nexus_version_supported, profile_value, artifact_profile)
        self.assertEqual(profile_info,
                         ['profile_name', 'running', 'priority', '1.2.3', '1.2.4', 'PHYSICAL_SUPPORTED',
                          'CLOUD_SUPPORTED', 'CLOUD_NATIVE_SUPPORTED', '-'])

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.yellow_text", return_value="priority")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.red_text", return_value="not_running")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.green_text", return_value="running")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.cyan_text", return_value="profile_name")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_physical_supported",
           return_value="PHYSICAL_SUPPORTED")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_cloud_supported",
           return_value="CLOUD_SUPPORTED")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.get_text_value_for_cloud_native_supported",
           return_value="CLOUD_NATIVE_SUPPORTED")
    def test_set_tabulated_info_profile_values__is_successful_with_artifact_profile(self, *_):
        profile = Mock(NAME="TEST_PROFILE1", PRIORITY=1, NOTE="NOTE1")
        artifact_profile = {"PRIORITY": 2, "NOTE": "NOTE2"}
        running = False
        local_version_supported = "1.2.3"
        nexus_version_supported = ""
        profile_value = {'SUPPORTED': True, 'PRIORITY': 1}
        profile_info = profilemanager_helper_methods.set_tabulated_info_profile_values(
            profile, running, local_version_supported, nexus_version_supported, profile_value, artifact_profile)
        self.assertEqual(profile_info,
                         ['profile_name', 'not_running', 'priority', '1.2.3', 'PHYSICAL_SUPPORTED',
                          'CLOUD_SUPPORTED', 'CLOUD_NATIVE_SUPPORTED', 'NOTE2'])

    def test_get_values_for_profile_from_python_dict__is_successful(self):
        profile_names = ['TEST_01']
        basic_network = {"basic": {'test': {
            'TEST_01': {'SUPPORTED': True, 'PHYSICAL': True, 'PRIORITY': 1},
            'TEST_02': {'SUPPORTED': True, 'PHYSICAL': True, 'PRIORITY': 2}}}}
        self.assertEqual({'TEST_01': {'NOTE': None, 'PRIORITY': 1, 'SUPPORTED': True, 'PHYSICAL_SUPPORTED': None,
                                      'CLOUD_SUPPORTED': None, 'CLOUD_NATIVE_SUPPORTED': None}},
                         profilemanager_helper_methods.get_values_for_profile_from_python_dict(
                             basic_network, 'basic', profile_names))

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.config.set_prop")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    def test_get_values_for_profile_from_python_dict__unknown_network(self, mock_error, mock_set):
        basic_network = {"basic": {'test': {
            'TEST_01': {'SUPPORTED': True, 'PRIORITY': 1},
            'TEST_02': {'SUPPORTED': True, 'PRIORITY': 2}}}}
        profilemanager_helper_methods.get_values_for_profile_from_python_dict(basic_network, 'unknown', [])
        mock_error.assert_called_with("\x1b[91mERROR: Invalid network: None.\n\x1b[0m")
        self.assertEqual(1, mock_set.call_count)

    def test_get_values_for_profile_from_python_dict__no_network(self, ):
        self.assertEqual({}, profilemanager_helper_methods.get_values_for_profile_from_python_dict({}, '', []))

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.get_prop',
           side_effect=["Bad version\n", "Bad Network\n"])
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.set_prop')
    def test_update_message__updates_message(self, mock_set, *_):
        expected = "Bad version\nBad Network\nMessage"
        result = profilemanager_helper_methods.update_message("Message")
        self.assertEqual(expected, result)
        self.assertEqual(2, mock_set.call_count)

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.set_prop')
    def test_update_message__no_update(self, mock_set, *_):
        expected = "Message"
        result = profilemanager_helper_methods.update_message("Message")
        self.assertEqual(expected, result)
        self.assertEqual(2, mock_set.call_count)

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.get_all_profile_names')
    def test_get_categories(self, mock_all_profiles):
        some_categories = ["cli_mon", "amos"]
        some_profiles = ["cli_mon_01", "amos_01"]
        mock_all_profiles.return_value = some_profiles
        test_categories = profilemanager_helper_methods.get_categories()
        for cat in some_categories:
            self.assertIn(cat, test_categories)

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.config.get_prop', return_value=False)
    def test_get_all_profile_names(self, *_):
        some_profiles = ["cmimport_10", "top_01"]
        all_profile_names = profilemanager_helper_methods.get_all_profile_names()
        for profile in some_profiles:
            self.assertIn(profile, all_profile_names)

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.CmManagement.get_status')
    def test_get_synced_count__returns_correct_number_of_cm_synchronised_nodes(self, mock_get_status, *_):
        mock_get_status.return_value = {
            "Node": "UNSYN", "Node1": "UNSYN", "Node2": "UNSYN", "Node3": "SYN", "Node4": "SYN", "Node5": "SYN"
        }
        self.assertEqual(tuple, type(profilemanager_helper_methods.get_synced_count()))
        self.assertEqual((3, 6), profilemanager_helper_methods.get_synced_count())

    @patch('enmutils_int.lib.services.profilemanager_helper_methods.get_synced_count',
           side_effect=[(40, 100), (41, 100)])
    @patch('enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info')
    def test_report_syncronised_level(self, mock_info, _):
        profilemanager_helper_methods.report_syncronised_level()
        self.assertEqual(mock_info.call_count, 0)
        profilemanager_helper_methods.report_syncronised_level()
        self.assertEqual(mock_info.call_count, 1)

    # get_difference_nodes_between_wlvm_and_enm test cases
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.enm_user_2.get_admin_user")
    def test_get_difference_nodes_between_wlvm_and_enm__is_successful(self, mock_get_admin_user, mock_get_pool,
                                                                      mock_log_info):
        mock_get_admin_user.return_value = Mock()
        data = [{"id": "22848847", "poId": "22848847", "moType": "NetworkElement", "mibRootName": "CORE02EPGSSR-13",
                 "parentRDN": "NetworkRestorationPool=1", "moName": "1", "fullMoType": "NetworkElement",
                 "attributes": {}, "radioAccessTechnology": None, "managementState": None},
                {"id": "22854092", "poId": "22854092", "moType": "NetworkElement", "mibRootName": "CORE02EPGSSR-06",
                 "parentRDN": "NetworkRestorationPool=1", "moName": "1", "fullMoType": "NetworkElement",
                 "attributes": {}, "radioAccessTechnology": None, "managementState": None}]
        response = Mock(ok=True)
        response.json.return_value = data
        mock_get_admin_user.return_value.get.return_value = response
        mock_get_pool.return_value = Mock(wl_nodes=[Mock(node_id="123"), Mock(node_id="124"),
                                                    Mock(node_id="CORE02EPGSSR-13")])
        profilemanager_helper_methods.get_difference_nodes_between_wlvm_and_enm()
        self.assertEqual(mock_log_info.call_count, 4)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.enm_user_2.get_admin_user")
    def test_get_difference_nodes_between_wlvm_and_enm__if_got_error_while_getting_enm_nodes_data(self,
                                                                                                  mock_get_admin_user,
                                                                                                  mock_get_pool,
                                                                                                  mock_log_info):
        mock_get_admin_user.return_value = Mock()
        response = Mock(ok=False, text="error")
        mock_get_admin_user.return_value.get.return_value = response
        mock_get_pool.return_value = Mock(wl_nodes=[Mock(node_id="123"), Mock(node_id="124")])
        profilemanager_helper_methods.get_difference_nodes_between_wlvm_and_enm()
        self.assertEqual(mock_log_info.call_count, 4)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.log.logger.info")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.enm_user_2.get_admin_user")
    def test_get_difference_nodes_between_wlvm_and_enm__if_nodes_not_available_in_wlpool(self, mock_get_admin_user,
                                                                                         mock_get_pool,
                                                                                         mock_log_info):
        mock_get_admin_user.return_value = Mock()
        data = [{"id": "22848847", "poId": "22848847", "moType": "NetworkElement", "mibRootName": "CORE02EPGSSR-13",
                 "parentRDN": "NetworkRestorationPool=1", "moName": "1", "fullMoType": "NetworkElement",
                 "attributes": {}, "radioAccessTechnology": None, "managementState": None},
                {"id": "22854092", "poId": "22854092", "moType": "NetworkElement", "mibRootName": "CORE02EPGSSR-06",
                 "parentRDN": "NetworkRestorationPool=1", "moName": "1", "fullMoType": "NetworkElement",
                 "attributes": {}, "radioAccessTechnology": None, "managementState": None}]
        response = Mock(ok=True)
        response.json.return_value = data
        mock_get_admin_user.return_value.get.return_value = response
        mock_get_pool.return_value = Mock(wl_nodes=[])
        profilemanager_helper_methods.get_difference_nodes_between_wlvm_and_enm()
        self.assertEqual(mock_log_info.call_count, 4)

    @patch("enmutils_int.lib.services.profilemanager_helper_methods.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.services.profilemanager_helper_methods.deployment_info_helper_methods.build_poid_dict_from_enm_data")
    def test_get_wl_poids__is_success(self, mock_enm, mock_get_pool):
        mock_enm.return_value = {'node4': 123, 'node1': 34}
        mock_get_pool.return_value = Mock(wl_nodes=[Mock(node_id="node1", poid=123), Mock(node_id="node2", poid=143),
                                                    Mock(node_id="node3", poid=1234)])

        profilemanager_helper_methods.get_wl_poids()

    @patch("enmutils_int.lib.workload_ops.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.workload_ops.deployment_info_helper_methods.build_poid_dict_from_enm_data")
    def test_get_wl_poids__no_differences(self, mock_enm, mock_get_pool):
        mock_enm.return_value = {}
        mock_get_pool.return_value = Mock(wl_nodes=[])

        profilemanager_helper_methods.get_wl_poids()

    @patch("enmutils_int.lib.workload_ops.log.red_text")
    @patch("enmutils_int.lib.workload_ops.log.logger.info")
    @patch("enmutils_int.lib.workload_ops.node_pool_mgr.get_pool")
    @patch("enmutils_int.lib.workload_ops.deployment_info_helper_methods.build_poid_dict_from_enm_data")
    def test_get_wl_poids__exception(self, mock_enm, mock_get_pool, mock_log, mock_red):
        mock_enm.side_effect = Exception
        mock_get_pool.return_value = Mock(wl_nodes=[])

        profilemanager_helper_methods.get_wl_poids()


if __name__ == '__main__':
    unittest2.main(verbosity=2)
