#!/usr/bin/env python

import unittest2

from mock import patch, Mock

from enmutils.lib import config
from enmutils_int.lib.profile_properties_manager import ProfilePropertiesManager
from testslib import unit_test_utils


class ProfilePropertiesManagerUnitTest(unittest2.TestCase):

    class MockConfig(object):
        def __init__(self):
            self.TOP_01 = None

    test_config = MockConfig()

    test_config.TOP_01 = {
        'NAME': 'TOP_01_config',
    }

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.services.deployment_info_helper_methods.get_total_cell_count")
    def test_get_profile_objects_returns_correct_profile_objects(self, mock_cell_count):
        mock_cell_count.return_value = 40000
        profiles = ["TOP_01", "CMSYNC_01", "NETEX_01"]
        properies_mgr = ProfilePropertiesManager(profiles)
        profile_objs = properies_mgr.get_profile_objects()
        for profile in profile_objs:
            self.assertIn(profile.NAME, profiles)
        self.assertEqual(len(profile_objs), len(profiles))

    @patch('enmutils_int.lib.profile_properties_manager.ProfilePropertiesManager.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_properties_manager.datetime', return_value="test_day")
    def test_current_day__successful(self, mock_date, _):
        mock_date.now().strftime().upper.return_value = "test_day"
        prop_mgr = ProfilePropertiesManager(['profile_1', 'profile_2'])
        self.assertEqual("test_day", prop_mgr.current_day)

    @patch('enmutils_int.lib.profile_properties_manager.ProfilePropertiesManager.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_properties_manager.log.logger.error')
    @patch('enmutils_int.lib.profile_properties_manager.imp.load_source')
    def test_load_config_file__raises_exception(self, mock_imp, mock_log, *_):
        profiles = ["TOP_01", "CMSYNC_01", "NETEX_01"]
        mock_imp.side_effect = Exception
        properties_mgr = ProfilePropertiesManager(profiles)
        self.assertRaises(Exception, properties_mgr._load_config_file, "config")
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils_int.lib.profile_properties_manager.config')
    @patch('enmutils_int.lib.profile_properties_manager.get_days_of_the_week', return_value=['MONDAY'])
    @patch('enmutils_int.lib.profile_properties_manager.imp')
    @patch('enmutils_int.lib.profile_properties_manager.InputData')
    @patch('enmutils_int.lib.profile_properties_manager.load_mgr.get_profile_objects_from_profile_names')
    def test_get_profile_objects_returns_only_profiles_in_config_file(self, mock_get_profile_objects, mock_input_data, mock_imp, *_):
        profile_1 = Mock()
        profile_1.NAME = 'TOP_01'
        profile_2 = Mock()
        profile_2.NAME = 'Mock_01'
        mock_get_profile_objects.return_value = [profile_1, profile_2]
        config_data = mock_input_data.return_value
        config_data.pool = {'ERBS': 20}
        config_data.get_profiles_values.return_value = {'TOTAL_NODES': 100}
        mock_imp.load_source.return_value = self.test_config
        prop_mgr = ProfilePropertiesManager(['profile_1', 'profile_2'], config_file='mock_config.py')
        self.assertEqual(len(prop_mgr.get_profile_objects()), 1)

    @patch('enmutils_int.lib.profile_properties_manager.config')
    @patch('enmutils_int.lib.profile_properties_manager.InputData')
    @patch('enmutils_int.lib.profile_properties_manager.load_mgr.get_profile_objects_from_profile_names')
    def test_get_profile_objects_returns_profile_objs_if_no_pool_available(self, mock_get_profile_objects, mock_input_data, _):
        profile_1 = Mock()
        profile_1.NAME = 'TOP_01'
        profile_2 = Mock()
        profile_2.NAME = 'Mock_01'
        mock_get_profile_objects.return_value = [profile_1, profile_2]
        config_data = mock_input_data.return_value
        config_data.pool = {}
        prop_mgr = ProfilePropertiesManager(['profile_1', 'profile_2'])
        self.assertFalse(mock_input_data.get_profiles_values.called)
        self.assertEqual(prop_mgr.get_profile_objects(), [profile_1, profile_2])

    @patch('enmutils_int.lib.profile_properties_manager.config')
    @patch('enmutils_int.lib.profile_properties_manager.InputData')
    @patch('enmutils_int.lib.profile_properties_manager.load_mgr.get_profile_objects_from_profile_names')
    def test_get_profile_objects_returns_profile_objs_if_workload_item_is_none(self, mock_get_profile_objects, mock_input_data, _):
        profile_1 = Mock()
        profile_1.NAME = 'TOP_01'
        profile_2 = Mock()
        profile_2.NAME = 'Mock_01'
        mock_get_profile_objects.return_value = [profile_1, profile_2]
        config_data = mock_input_data.return_value
        config_data.pool = {'ERBS': 20}
        config_data.get_profiles_values.return_value = None
        prop_mgr = ProfilePropertiesManager(['profile_1', 'profile_2'])
        self.assertEqual(prop_mgr.get_profile_objects(), [profile_1, profile_2])

    @patch('enmutils_int.lib.profile_properties_manager.InputData.get_profiles_values')
    @patch('enmutils_int.lib.profile_properties_manager.load_mgr.get_profile_objects_from_profile_names')
    def test_update_scheduled_days_with_new_profiles_flag(self, mock_get_profile_objects_from_profile_names,
                                                          mock_get_profiles_values):
        class PseudoProfile(object):
            def __init__(self):
                self.NAME = "TEST_01"

        profiles = [PseudoProfile()]
        mock_get_profile_objects_from_profile_names.return_value = profiles
        mock_get_profiles_values.return_value = {'SCHEDULED_DAYS': []}
        config.set_prop('SOAK', True)
        properties_mgr = ProfilePropertiesManager(profiles)
        profiles = properties_mgr.get_profile_objects()
        self.assertIs(7, len(profiles[0].SCHEDULED_DAYS))

    @patch('enmutils_int.lib.profile_properties_manager.InputData.get_profiles_values')
    @patch('enmutils_int.lib.profile_properties_manager.load_mgr.get_profile_objects_from_profile_names')
    def test_update_scheduled_days_has_no_impact_without_new_profiles_flag(self,
                                                                           mock_get_profile_objects_from_profile_names,
                                                                           mock_get_profiles_values):
        class PseudoProfile(object):
            def __init__(self):
                self.NAME = "TEST_01"

        profiles = [PseudoProfile()]
        mock_get_profile_objects_from_profile_names.return_value = profiles
        mock_get_profiles_values.return_value = {'SCHEDULED_DAYS': []}
        properties_mgr = ProfilePropertiesManager(profiles)
        profiles = properties_mgr.get_profile_objects()
        self.assertIs(0, len(profiles[0].SCHEDULED_DAYS))

    @patch('enmutils_int.lib.profile_properties_manager.ProfilePropertiesManager.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_properties_manager.log.logger.debug')
    @patch('enmutils_int.lib.profile_properties_manager.imp')
    def test_inject_values_from_user_supplied_config_file__has_attribute(self, mock_imp, *_):
        profiles = ["TOP_01", "CMSYNC_01", "NETEX_01"]
        mock_config = Mock()
        mock_config.TOP_01 = {"ENM": 123, "Test": 456}
        mock_imp.load_source.return_value = mock_config
        properties_mgr = ProfilePropertiesManager(profiles, "config")
        properties_mgr.config_file = mock_config
        mock_profile_obj = Mock(spec=["NAME", "ENM"])
        mock_profile_obj.NAME = "TOP_01"
        properties_mgr._inject_values_from_user_supplied_config_file(mock_profile_obj)
        self.assertTrue(hasattr(mock_profile_obj, "ENM"))
        self.assertEqual(getattr(mock_profile_obj, "Test"), 456)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
