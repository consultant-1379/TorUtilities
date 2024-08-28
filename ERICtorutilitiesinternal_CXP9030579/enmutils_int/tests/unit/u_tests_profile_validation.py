#!/usr/bin/env python
import unittest2
from mock import patch

from testslib import unit_test_utils
from enmutils_int.lib import profile_validation
from enmutils_int.lib.workload_network_manager import InputData
from enmutils_int.lib.services.profilemanager_helper_methods import get_all_profile_names


class ProfileValidationTests(unittest2.TestCase):

    def setUp(self):
        self.rpm = '4.6.2'

    def tearDown(self):
        unit_test_utils.tear_down()

    @classmethod
    def setUpClass(cls):
        unit_test_utils.setup()
        cls.profiles_in_workload_dir = list(set(get_all_profile_names()))

    @patch('enmutils_int.lib.profile_validation.get_active_profile_names')
    @patch('enmutils_int.lib.profile_validation._fetch_dict_from_json')
    def test_active_versus_artifact__returns_correct_list(self, mock_json, mock_active_profiles):
        mock_active_profiles.return_value = {'profile', 'TOP'}
        mock_json.return_value = {"network": {"app": {"profile": "profile"}}}
        self.assertEqual(set(['TOP']), profile_validation._artifact_versus_active_profiles(self.rpm))

    @patch('enmutils_int.lib.profile_validation.get_active_profile_names')
    @patch('enmutils_int.lib.profile_validation._fetch_dict_from_json')
    def test_active_versus_artifact__returns_no_value(self, mock_json, mock_active_profiles):
        mock_active_profiles.return_value = {'profile'}
        mock_json.return_value = {"abc": {"bcd": ""}}
        self.assertEqual(set(['profile']), profile_validation._artifact_versus_active_profiles(self.rpm))

    @patch('enmutils_int.lib.profile_validation.ProfileManager.stop')
    @patch('enmutils_int.lib.profile_validation.get_profile_objects_from_profile_names')
    def test_stop_missing_profiles__has_missing_profiles(self, mock_profiles, _):
        missing_profiles_list = ["cmsync_01", "cmsync_02"]
        mock_profiles.return_value = missing_profiles_list
        profile_validation._stop_missing_profiles(missing_profiles_list)

    @patch('enmutils_int.lib.profile_validation.log.logger.info')
    @patch('enmutils_int.lib.profile_validation.get_profile_objects_from_profile_names')
    def test_stop_missing_profiles__no_profiles_objects(self, mock_profiles, mock_log):
        missing_profiles_list = ["cmsync_01", "cmsync_02"]
        mock_profiles.return_value = []
        profile_validation._stop_missing_profiles(missing_profiles_list)
        self.assertFalse(mock_log.called)

    @patch('enmutils_int.lib.profile_validation.download_artifact_from_nexus', return_value=None)
    def test_fetch_dict_from_json__raises_exception(self, _):
        self.assertRaises(profile_validation.RpmMisMatch, profile_validation._fetch_dict_from_json, self.rpm)

    @patch('enmutils_int.lib.profile_validation.convert_from_json_to_dict', return_value={"ENM": 123})
    @patch('enmutils_int.lib.profile_validation.get_json_from_a_file')
    @patch('enmutils_int.lib.profile_validation.download_artifact_from_nexus', return_value=["abc"])
    def test_fetch_dict_from_json_return_artifact__successful(self, *_):
        self.assertEqual({"ENM": 123}, profile_validation._fetch_dict_from_json("123"))

    @patch('enmutils_int.lib.profile_validation._fetch_dict_from_json')
    @patch('enmutils_int.lib.profile_validation._stop_missing_profiles')
    @patch('enmutils_int.lib.profile_validation._artifact_versus_active_profiles')
    def test_stop_deleted_or_renamed_profiles(self, mock_artifact, *_):
        profile_validation.stop_deleted_or_renamed_profiles(self.rpm, auto_stop=True)
        self.assertTrue(mock_artifact.called)
        mock_artifact.return_value = ['DUMMY']
        self.assertRaises(profile_validation.RpmMisMatch, profile_validation.stop_deleted_or_renamed_profiles, self.rpm)

    @patch('enmutils_int.lib.profile_validation._stop_missing_profiles')
    @patch('enmutils_int.lib.profile_validation.log.logger.info')
    @patch('enmutils_int.lib.profile_validation._artifact_versus_active_profiles', return_value=["abc"])
    def test_stop_deleted_or_renamed_profiles__auto_stop_flag_is_raised_to_stop_profile(self, mock_artifact, mock_info, _):
        profile_validation.stop_deleted_or_renamed_profiles(self.rpm, auto_stop=True)
        self.assertTrue(mock_artifact.called)
        self.assertEqual(mock_info.call_count, 1)

    @staticmethod
    def _retrieve_key(key):
        input_data = InputData()
        profiles, missing, key_values = [], [], []
        basic = 'basic'
        for app_key in input_data.networks.get(basic).iterkeys():
            for profile_key in input_data.networks.get(basic).get(app_key):
                if input_data.networks.get(basic).get(app_key).get(profile_key).get(key) is not None:
                    profiles.append(profile_key.lower())
                    key_values.append(input_data.networks.get(basic).get(app_key).get(profile_key).get(key))
                else:
                    missing.append(profile_key.lower())
        return profiles, missing, key_values

    def test_profile_contains_priority_rating(self):
        profiles, _, key_values = self._retrieve_key('PRIORITY')
        self.assertEqual(len(self.profiles_in_workload_dir), len(profiles))
        self.assertEqual(set(self.profiles_in_workload_dir), set(profiles))

        for _ in key_values:
            self.assertIn(_, [1, 2, 'M', 'KTT'])

    def test_profile_contains_supported_flag(self):
        profiles, _, key_values = self._retrieve_key('SUPPORTED')
        self.assertEqual(len(self.profiles_in_workload_dir), len(profiles))
        self.assertEqual(set(self.profiles_in_workload_dir), set(profiles))

        for _ in key_values:
            self.assertIn(_, [True, False, 'INTRUSIVE'])

    def test_profile_contains_note_field(self):
        profiles, _, key_values = self._retrieve_key('NOTE')
        self.assertEqual(len(self.profiles_in_workload_dir), len(profiles))
        self.assertEqual(set(self.profiles_in_workload_dir), set(profiles))

        for _ in key_values:
            self.assertTrue(isinstance(_, str))

    def test_profile_contains_update_version(self):
        profiles, _, key_values = self._retrieve_key('UPDATE_VERSION')
        self.assertEqual(len(self.profiles_in_workload_dir), len(profiles))
        self.assertEqual(set(self.profiles_in_workload_dir), set(profiles))

        for _ in key_values:
            self.assertTrue(isinstance(_, int))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
