#!/usr/bin/env python

import datetime
import unittest2

from enmutils.lib import persistence
from enmutils.lib.timestamp import convert_datetime_to_str_format
from enmutils_int.lib.services import profilemanager_adaptor
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class ProfileManagerAcceptanceTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)
        persistence.get_db(index=0).remove('TEST_00-status')

    def setUp(self):
        func_test_utils.setup(self)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("ProfileManager Service", "Check if profiles list is successful.")
    def test_01_profiles_list(self):
        profilemanager_adaptor.get_all_profiles_list()

    @func_dec("ProfileManager Service", "Check if category list is successful.")
    def test_02_category_list(self):
        profilemanager_adaptor.get_categories_list()

    @func_dec("ProfileManager Service", "Check if clean pid is successful.")
    def test_03_clear_pid_files(self):
        profilemanager_adaptor.clear_profile_pid_files(["TEST_00"])

    @func_dec("ProfileManager Service", "Check if describe is successful.")
    def test_04_describe_profile(self):
        profilemanager_adaptor.describe_profiles(["AP_11"])

    @func_dec("ProfileManager Service", "Check if export is successful.")
    def test_05_export_profiles(self):
        profilemanager_adaptor.export_profiles(["AP_11"], "/var/log/enmutils/")

    @func_dec("ProfileManager Service", "Check if status can be set successfully.")
    def test_06_set_status(self):
        argument_dict = {"name": "TEST_00", "state": "RUNNING",
                         "start_time": convert_datetime_to_str_format(datetime.datetime.now()), "pid": 1234,
                         "num_nodes": 10,
                         "schedule": "Runs at the following times: 05:00 on MONDAY (last run: 06-Mar 10:17:30, next "
                                     "run: [NOW])", "priority": 1, "last_run": "[NEVER]", "user_count": 10}
        profilemanager_adaptor.set_status(argument_dict)
        result = persistence.get_db(index=0).get('TEST_00-status').NAME
        self.assertEqual("TEST_00", result)

    @func_dec("ProfileManager Service", "Get the status object previously set.")
    def test_07_get_status(self):
        self.assertEqual("TEST_00", profilemanager_adaptor.get_status({'profiles': ["TEST_00"]})[0].NAME)

    @func_dec("ProfileManager Service", "Add warning to persistence.")
    def test_08_add_profile_warning(self):
        argument_dict = {"profile_key": "TEST_00-warnings",
                         "profile_values": "[{'DUPLICATES': ['2020/03/06 10:36:26'], 'TIMESTAMP': '2020/03/06 10:36:26'"
                                           ", 'REASON': \"[EnvironWarning] NotAllNodeTypesAvailable: 'No nodes of type"
                                           " Router6672 found for SHM_37'\"}]"}
        profilemanager_adaptor.add_profile_exception(argument_dict)
        self.assertIsNotNone(persistence.get_db(index=0).get('TEST_00-warnings'))

    @func_dec("ProfileManager Service", "Add error to persistence.")
    def test_09_add_profile_error(self):
        argument_dict = {"profile_key": "TEST_00-errors",
                         "profile_values": "[{'DUPLICATES': [], 'TIMESTAMP': '2020/03/06 09:15:19', 'REASON': \""
                                           "[EnvironError] UnsupportedNeTypeException: 'Unable to locate ne type: None"
                                           " in mediation dictionary.'\"}]"}
        profilemanager_adaptor.add_profile_exception(argument_dict)
        self.assertIsNotNone(persistence.get_db(index=0).get('TEST_00-errors'))

    @func_dec("ProfileManager Service", "Clear profile errors.")
    def test_10_clear_profile_error(self):
        profilemanager_adaptor.clear_profile_exceptions(["TEST_00", "TEST_01"])
        self.assertIsNone(persistence.get_db(index=0).get('TEST_00-errors'))
        self.assertIsNone(persistence.get_db(index=0).get('TEST_00-warnings'))

    @func_dec("ProfileManager Service", "Check if diff is successful.")
    def test_11_diff(self):
        argument_dict = {}
        profilemanager_adaptor.diff_profiles(**argument_dict)

    @func_dec("ProfileManager Service", "Check if diff is successful.")
    def test_11_diff__updated(self):
        argument_dict = {"updated": True, 'priority': 1, 'profile_names': ["SECUI_03", "SECUI_04"]}
        profilemanager_adaptor.diff_profiles(**argument_dict)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
