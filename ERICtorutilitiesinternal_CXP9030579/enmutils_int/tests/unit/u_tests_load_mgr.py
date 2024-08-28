#!/usr/bin/env python
import datetime
from itertools import cycle

import unittest2
from mock import Mock, PropertyMock, patch, call
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import filesystem, persistence
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib import common_utils, load_mgr, node_pool_mgr
from enmutils_int.lib.nrm_default_configurations import basic_network, profile_values
from enmutils_int.lib.profile import ExclusiveProfile
from enmutils_int.lib.profile import Profile
from testslib import unit_test_utils


class LoadManagerUnitTests(ParameterizedTestCase):
    Profile.NAME = "TEST"

    def setUp(self):
        unit_test_utils.setup()
        self.tmp_dir = "/tmp/enmutils/"
        self.jsons = ["ERICtorutilitiesinternal_CXP9030579-4.1.1.json",
                      "ERICtorutilitiesinternal_CXP9030579-4.1.2.json"]
        self.msg = ("Status of {0} profile is '{1}'. Expected status: '{2}'. Current profile will start only if {0} "
                    "is {3} with {2} status. Please refer {0} profile logs for more")
        for _ in self.jsons:
            if not filesystem.does_file_exist(_):
                if not filesystem.does_dir_exist(self.tmp_dir):
                    filesystem.create_dir(self.tmp_dir)
                filesystem.copy(common_utils.get_internal_file_path_for_import('etc', 'data', _), self.tmp_dir)

    def tearDown(self):
        for _ in self.jsons:
            if filesystem.does_file_exist(self.tmp_dir + _):
                filesystem.delete_file(self.tmp_dir + _)
        unit_test_utils.tear_down()

    def _get_profiles(self, num_profiles, num_nodes, exclusive=None):
        profiles = {}
        priorities = cycle([1, 2])
        for i in range(num_profiles):

            profile = Profile()
            # If exclusive = None, alternate whether exclusivity is True or False
            if exclusive is None:
                if i % 2 == 0:
                    profile.EXCLUSIVE = True
            else:
                profile.EXCLUSIVE = exclusive
            profile.NAME = "TEST_0{}".format(i)
            profile.NUM_NODES = {"ERBS": num_nodes}
            profile.PRIORITY = next(priorities)
            profiles[profile.NAME] = profile
        return profiles

    def test_get_profile_objects_from_profile_names(self):
        profiles = ["FM_01", "NETEX_02"]
        valid_profiles = load_mgr.get_profile_objects_from_profile_names(profiles)
        self.assertTrue(len(profiles) == len(valid_profiles))

    def test_get_profiles_by_name_from_persistence(self):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profile_names = [profile.NAME for profile in profiles.values()]
        for profile in profiles.keys()[:-1]:
            persistence.set(profiles[profile].NAME, profiles[profile], -1)
        profiles_dict = load_mgr.get_persisted_profiles_by_name(profile_names)
        for profile in profiles.keys()[:-1]:
            self.assertIn(profile, profiles_dict)

    def test_get_active_profile_names(self):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profile_names = [profile.NAME for profile in profiles.values()]
        persistence.set("active_workload_profiles", profile_names, -1)
        active_profile_names = load_mgr.get_active_profile_names()
        for profile in profile_names:
            self.assertIn(profile, active_profile_names)

    def test_get_persisted_profiles_by_name(self):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profile_names = [profile.NAME for profile in profiles.values()]
        for profile in profiles:
            persistence.set(profiles[profile].NAME, profiles[profile], -1)
        persisted_profiles = load_mgr.get_persisted_profiles_by_name(profile_names)
        for profile in profile_names:
            self.assertIn(profile, persisted_profiles)

    @patch('enmutils_int.lib.load_mgr.get_existing_diff_objects')
    @patch('enmutils_int.lib.load_mgr.log.logger.debug')
    def test_get_persisted_profiles_by_name__gets_diff_objects(self, mock_debug, mock_diff_objects):
        profile_names = ['CA_01', 'LOGVIEWER_01']
        diff_profile = Mock(NAME='CA_01')
        full_profile = Mock(NAME='LOGVIEWER_01')
        mock_diff_objects.return_value = [diff_profile, full_profile]
        persisted_profiles = load_mgr.get_persisted_profiles_by_name(profile_names, True)
        expected = {'LOGVIEWER_01': full_profile, 'CA_01': diff_profile}
        self.assertEqual(expected, persisted_profiles)
        mock_debug.assert_called_with('Number of Active profile objects: 2')

    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    @patch('enmutils_int.lib.load_mgr.log.logger.debug')
    def test_get_existing_diff_objects__returns_diff_objects_and_profile_objects(self, mock_debug, mock_get_keys):
        diff_profile = Mock(NAME='CA_01')
        full_profile = Mock(NAME='LOGVIEWER_01')
        mock_get_keys.side_effect = [[diff_profile], [full_profile]]
        profile_names = ['CA_01', 'LOGVIEWER_01']
        expected = [diff_profile, full_profile]
        self.assertEqual(expected, load_mgr.get_existing_diff_objects(profile_names))
        mock_debug.assert_called_with('Number of diff objects: [1] Number of normal profile objects: [1]')

    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    def test_get_existing_diff_objects__returns_only_diff_objects(self, mock_get_keys):
        diff_profile = Mock(NAME='CA_01')
        diff_profile2 = Mock(NAME='LOGVIEWER_01')
        mock_get_keys.side_effect = [[diff_profile, diff_profile2], []]
        profile_names = ['CA_01']
        expected = [diff_profile, diff_profile2]
        self.assertEqual(expected, load_mgr.get_existing_diff_objects(profile_names))

    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    def test_get_existing_diff_objects__add_no_diff_objects(self, mock_get_keys):
        full_profile = Mock(NAME='CA_01')
        mock_get_keys.side_effect = [[], [full_profile]]
        profile_names = ['CA_01', 'LOGVIEWER_01']
        expected = [full_profile]
        self.assertEqual(expected, load_mgr.get_existing_diff_objects(profile_names))

    @patch('enmutils_int.lib.load_mgr.process.get_profile_daemon_pid', return_value=["123", "456"])
    @patch('enmutils_int.lib.load_mgr.process.kill_process_id')
    def test_kill_profile_daemon_process__process_running(self, mock_kill_process_id, *_):
        load_mgr.kill_profile_daemon_process('TEST_01')
        self.assertEqual([call(123), call(456)], mock_kill_process_id.mock_calls)

    def test_get_active_foundation_profiles(self):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profile_names = [profile.NAME for profile in profiles.values()]
        profiles["TEST_01"].FOUNDATION = True
        for profile in profiles:
            persistence.set(profiles[profile].NAME, profiles[profile], -1)
        persistence.set("active_workload_profiles", profile_names, -1)
        active_foundation_profiles = load_mgr.get_active_foundation_profiles()
        self.assertEqual(len(active_foundation_profiles), 1)

    @patch("enmutils_int.lib.load_mgr.get_all_active_profiles",
           return_value={"TEST_PROFILE_01": Mock(), "TEST_PROFILE_02": Mock()})
    @patch("enmutils_int.lib.load_mgr.get_active_profile_names",
           return_value=set(["TEST_PROFILE_01", "TEST_PROFILE_02"]))
    @patch("enmutils_int.lib.load_mgr.get_all_profile_names_from_persistence",
           return_value=["TEST_PROFILE_01", "TEST_PROFILE_02"])
    @patch('enmutils_int.lib.load_mgr.get_profiles_with_priority')
    @patch('enmutils_int.lib.load_mgr.mutexer.mutex')
    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    @patch('enmutils_int.lib.load_mgr.persistence.set')
    def test_get_persisted_profiles_status_by_name__is_successful_for_all_profiles(self, mock_set, mock_get_keys, *_):
        load_mgr.get_persisted_profiles_status_by_name(priority="")
        self.assertFalse(mock_set.called)
        mock_get_keys.assert_called_with(["TEST_PROFILE_01-status", "TEST_PROFILE_02-status"])

    @patch("enmutils_int.lib.load_mgr.get_all_active_profiles",
           return_value={"TEST_PROFILE_01": Mock(), "TEST_PROFILE_02": Mock()})
    @patch("enmutils_int.lib.load_mgr.get_active_profile_names",
           return_value=set(["TEST_PROFILE_01", "TEST_PROFILE_02"]))
    @patch("enmutils_int.lib.load_mgr.get_all_profile_names_from_persistence",
           return_value=["TEST_PROFILE_01", "TEST_PROFILE_02"])
    @patch('enmutils_int.lib.load_mgr.get_profiles_with_priority')
    @patch('enmutils_int.lib.load_mgr.mutexer.mutex')
    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    @patch('enmutils_int.lib.load_mgr.persistence.set')
    def test_get_persisted_profiles_status_by_name__is_successful_for_specified_profiles(
            self, mock_set, mock_get_keys, *_):
        load_mgr.get_persisted_profiles_status_by_name(priority="", profile_names=["TEST_PROFILE_01"])
        self.assertFalse(mock_set.called)
        mock_get_keys.assert_called_with(["TEST_PROFILE_01-status"])

    @patch("enmutils_int.lib.load_mgr.get_all_active_profiles",
           return_value={"TEST_PROFILE_01": Mock(), "TEST_PROFILE_02": Mock()})
    @patch("enmutils_int.lib.load_mgr.get_active_profile_names",
           return_value=set(["TEST_PROFILE_01"]))
    @patch("enmutils_int.lib.load_mgr.get_all_profile_names_from_persistence",
           return_value=["TEST_PROFILE_01", "TEST_PROFILE_02"])
    @patch('enmutils_int.lib.load_mgr.mutexer.mutex')
    @patch('enmutils_int.lib.load_mgr.get_profiles_with_priority',
           return_value=["TEST_PROFILE_02"])
    @patch('enmutils_int.lib.load_mgr.persistence.get_keys')
    @patch('enmutils_int.lib.load_mgr.persistence.set')
    def test_get_persisted_profiles_status_by_name__is_successful_for_specified_profiles_if_redis_mismatch_exists(
            self, mock_set, mock_get_keys, mock_get_profiles_with_priority, *_):
        load_mgr.get_persisted_profiles_status_by_name(priority="2", profile_names=["TEST_PROFILE_02"])
        mock_set.assert_called_with("active_workload_profiles", set(["TEST_PROFILE_01", "TEST_PROFILE_02"]), -1)
        mock_get_keys.assert_called_with(["TEST_PROFILE_02-status"])
        mock_get_profiles_with_priority.assert_called_with("2", ["TEST_PROFILE_02"])

    @patch('enmutils_int.lib.load_mgr.persistence.get_all_keys',
           return_value=["TEST_PROFILE_01", "TEST_PROFILE_02", "TEST_PROFILE_01-status", "TEST_PROFILE_02-status",
                         "OTHER_KEY1", "TEST_PROFILE_03-status", "TEST_PROFILE_04"])
    def test_get_all_profile_names_from_persistence__is_successful(self, _):
        self.assertEqual(["TEST_PROFILE_01", "TEST_PROFILE_02"], load_mgr.get_all_profile_names_from_persistence())

    @patch('enmutils.lib.log.logger.debug')
    def test_get_dependant_profiles(self, mock_logger):
        self.assertEqual(set(["NHM_03", "NHM_04", "NHM_05", "NHM_06", "NHM_07", "NHM_08", "NHM_09", "NHM_10", "NHM_11",
                              "NHM_12", "NHM_13", "NHM_14"]), load_mgr.get_dependent_profiles(["SHM_01", "NHM_SETUP"]))
        self.assertTrue(mock_logger.called)

    def test_get_profiles_with_priority__raises_priority_not_digit_error(self):
        self.assertRaises(RuntimeError, load_mgr.get_profiles_with_priority, "two", ["TEST_PROFILE_02"])

    def test_get_profiles_with_specified_priority(self):
        basic = 'basic'
        profiles = []
        for key in profile_values.networks.get(basic).iterkeys():
            for profile in profile_values.networks.get(basic).get(key):

                if profile_values.networks.get(basic).get(key).get(profile).get(basic_network.PRIORITY) is not None:
                    if profile_values.networks.get(basic).get(key).get(profile).get(basic_network.PRIORITY) == 1:
                        profiles.append(profile)
        priority = '1'
        profiles_with_priority = load_mgr.get_profiles_with_priority(priority, profiles)
        self.assertEqual(len(profiles_with_priority), len(profiles))
        for _ in profiles_with_priority:
            self.assertIn(_, profiles)

    def test_get_profiles_with_specified_priority_returns_no_profiles_given_invalid_priority(self):
        profiles = self._get_profiles(num_profiles=10, num_nodes=0)
        priority = '3'
        profiles_with_priority = load_mgr.get_profiles_with_priority(priority, profiles)
        self.assertFalse(profiles_with_priority)

    @patch('enmutils_int.lib.load_mgr.profile_values.networks')
    def test_get_profiles_with_priority__profile_priority_returns_none(self, _):
        basic = 'basic'
        profiles = []
        priority = '1'
        profile_values.networks = {basic: {'key': {'profile': {'PRIORITY': None}}}}
        profiles_with_priority = load_mgr.get_profiles_with_priority(priority, profiles)
        self.assertEqual(len(profiles_with_priority), len(profiles))

    @patch('enmutils_int.lib.load_mgr.log.logger')
    @patch('enmutils_int.lib.load_mgr.log.persistence.get')
    @patch('enmutils_int.lib.load_mgr.log.persistence.has_key')
    def test_get_start_time_of_profile__returns_none_if_profile_is_not_running(self, mock_has_key, *_):
        mock_has_key.side_effect = [False]

        self.assertEqual(None, load_mgr.get_start_time_of_profile("some_profile_name"))

    @patch('enmutils_int.lib.load_mgr.log.logger')
    @patch('enmutils_int.lib.load_mgr.log.persistence.get')
    @patch('enmutils_int.lib.load_mgr.log.persistence.has_key')
    def test_get_start_time_of_profile__returns_none_if_profile_is_running(self, mock_has_key, mock_get, _):
        mock_has_key.side_effect = [True]

        time_now = datetime.datetime.now()
        profile = Profile()
        profile.start_time = time_now
        mock_get.return_value = profile
        self.assertEqual(time_now, load_mgr.get_start_time_of_profile("some_profile_name"))

    # wait_for_setup_profile test cases
    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.time.sleep")
    def test_wait_for_setup_profile_blocks_until_profile_is_not_starting(self, mock_sleep, mock_verify_profile_status):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = "STARTING"
        with patch("enmutils_int.lib.profile.Profile.status", new_callable=PropertyMock) as mock_status:
            mock_status.side_effect = ["OK", "OK", "DEAD"]
            load_mgr.wait_for_setup_profile("TEST_SETUP")
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertEqual(mock_verify_profile_status.call_count, 1)

    @patch("enmutils_int.lib.load_mgr.profile.Profile.status", new_callable=PropertyMock, return_value="ERROR")
    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    def test_wait_for_setup_profile_raises_error_when_status_not_ok(self, mock_verify_profile_status, _):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = "COMPLETED"
        mock_verify_profile_status.side_effect = EnvironError
        self.assertRaises(EnvironError, load_mgr.wait_for_setup_profile, "TEST_SETUP", state_to_wait_for="COMPLETED",
                          status="OK")
        self.assertEqual(mock_verify_profile_status.call_count, 1)

    @patch("enmutils_int.lib.load_mgr.profile.Profile.status", new_callable=PropertyMock, return_value="OK")
    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    def test_wait_for_setup_profile_returns_when_status_ok(self, mock_verify_profile_status, _):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = "COMPLETED"
        load_mgr.wait_for_setup_profile("TEST_SETUP", state_to_wait_for="COMPLETED", status="OK")
        self.assertEqual(mock_verify_profile_status.call_count, 1)

    @patch("enmutils_int.lib.load_mgr.time.sleep")
    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.log.logger.debug")
    @patch("enmutils_int.lib.load_mgr.datetime.timedelta")
    def test_wait_for_setup_profile_eventually_times_out(self, mock_datetime_timedelta, mock_logger,
                                                         mock_verify_profile_status, _):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.state = "STARTING"
        mock_datetime_timedelta.return_value = datetime.timedelta(minutes=20)
        with patch("enmutils_int.lib.profile.Profile.state", new_callable=PropertyMock) as mock_state:
            mock_state.return_value = "STARTING"
            load_mgr.wait_for_setup_profile("TEST")
        self.assertTrue(mock_logger.called)
        self.assertEqual(mock_verify_profile_status.call_count, 0)

    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.time.sleep")
    @patch("enmutils_int.lib.load_mgr.log.logger.debug")
    @patch("enmutils_int.lib.load_mgr.datetime.datetime")
    @patch("enmutils_int.lib.load_mgr.datetime.timedelta")
    @patch('enmutils_int.lib.load_mgr.persistence.has_key')
    def test_wait_for_setup_profile_profile_has_no_key_in_later_iterations(self, mock_has_key, mock_time_delta,
                                                                           mock_date_time, mock_log_debug, *_):
        mock_has_key.side_effect = [True, False]
        mock_date_time.now.side_effect = [0, 0]
        mock_time_delta.return_value = 10
        load_mgr.wait_for_setup_profile("TEST")
        self.assertTrue(mock_log_debug.called)

    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.time.sleep")
    @patch("enmutils_int.lib.load_mgr.log.logger.debug")
    @patch("enmutils_int.lib.load_mgr.datetime.datetime")
    @patch("enmutils_int.lib.load_mgr.datetime.timedelta")
    @patch('enmutils_int.lib.load_mgr.persistence.has_key')
    def test_wait_for_setup_profile_profile_times_out_on_first_iteration(self, mock_has_key, mock_time_delta,
                                                                         mock_date_time, mock_log_debug, *_):
        mock_has_key.side_effect = [True, False]
        mock_date_time.now.side_effect = [0, 0]
        mock_time_delta.return_value = -1
        load_mgr.wait_for_setup_profile("TEST")
        self.assertTrue(mock_log_debug.called)

    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.time.sleep")
    @patch("enmutils_int.lib.load_mgr.log.logger")
    @patch("enmutils_int.lib.load_mgr.datetime.datetime")
    @patch("enmutils_int.lib.load_mgr.datetime.timedelta")
    @patch('enmutils_int.lib.load_mgr.persistence')
    def test_wait_for_setup_profile_executes_with_flag(self, mock_persistence, mock_time_delta, mock_date_time,
                                                       mock_log, mock_sleep, *_):
        mock_persistence.has_key.side_effect = [True, True]
        mock_profile = Mock()
        mock_profile.FLAG = 'COMPLETED'
        mock_persistence.get.return_value = mock_profile
        mock_date_time.now.side_effect = [0, 0]
        mock_time_delta.return_value = 10
        load_mgr.wait_for_setup_profile("TEST", wait_for_flag=True, flag='COMPLETED')
        self.assertFalse(mock_log.debug.called)
        self.assertFalse(mock_log.info.called)
        self.assertFalse(mock_sleep.called)

    @patch("enmutils_int.lib.load_mgr.verify_profile_status")
    @patch("enmutils_int.lib.load_mgr.time.sleep")
    @patch("enmutils_int.lib.load_mgr.log.logger")
    @patch("enmutils_int.lib.load_mgr.datetime.datetime")
    @patch("enmutils_int.lib.load_mgr.datetime.timedelta")
    @patch('enmutils_int.lib.load_mgr.persistence')
    def test_wait_for_setup_profile_executes_with_incorrect_flag(self, mock_persistence, mock_time_delta,
                                                                 mock_date_time, mock_log, mock_sleep, *_):
        mock_persistence.has_key.side_effect = [True, True]
        mock_profile = Mock()
        mock_profile.FLAG = 'COMPLETED'
        mock_persistence.get.return_value = mock_profile
        mock_date_time.now.side_effect = [0, 0, 20]
        mock_time_delta.side_effect = [10]
        load_mgr.wait_for_setup_profile("TEST", wait_for_flag=True, flag='Some Flag')
        self.assertTrue(mock_log.debug.called)
        self.assertTrue(mock_sleep.called)

    # verify_profile_status test cases
    def test_verify_profile_status__is_successful(self):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = None
        load_mgr.verify_profile_status(profile, profile.NAME, profile.state, "RUNNING", self.msg)

    def test_verify_profile_status__when_state_is_dead(self):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = "DEAD"
        load_mgr.verify_profile_status(profile, profile.NAME, profile.state, "RUNNING", self.msg)

    def test_verify_profile_status__raises_env_error(self):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.NAME = "TEST_SETUP"
        profile.SETUP = True
        profile.state = "ERROR"
        self.assertRaises(EnvironError, load_mgr.verify_profile_status, profile, profile.NAME, profile.state,
                          "SLEEPING", self.msg)

    @patch("enmutils_int.lib.load_mgr.log.logger.info")
    @patch("enmutils_int.lib.load_mgr.persistence.remove")
    def test_profile_errors_clears(self, mock_remove_persistance, mock_log):
        some_profiles = ["cmimport_02", "cli_mon_01"]
        load_mgr.clear_profile_errors(some_profiles)
        self.assertTrue(mock_remove_persistance.call_count is 4)
        self.assertTrue(mock_log.called)

    def test_get_stopping_profiles(self):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profiles["TEST_01"].FOUNDATION = True
        for profile in profiles.keys()[::2]:
            persistence.set(profiles[profile].NAME, profiles[profile], -1)
        stopping_profiles = load_mgr._get_stopping_profiles(profiles)
        self.assertEqual(len(stopping_profiles), len(profiles) / 2)

    @patch('enmutils_int.lib.load_mgr.get_active_foundation_profiles')
    @patch('enmutils_int.lib.load_mgr.get_persisted_profiles_by_name', return_value={'TEST_04': "test_info",
                                                                                     'TEST_00': "test_info",
                                                                                     'TEST_02': "test_info"})
    def test_get_stopping_profiles__force_stop_set_to_True(self, mock_get_persist_profiles, _):
        profiles = self._get_profiles(num_profiles=6, num_nodes=10)
        profiles["TEST_01"].FOUNDATION = True
        for profile in profiles.keys()[::2]:
            persistence.set(profiles[profile].NAME, profiles[profile], -1)
        stopping_profiles = load_mgr._get_stopping_profiles(profiles, True)
        self.assertEqual(len(stopping_profiles), len(profiles) / 2)
        self.assertEqual(1, mock_get_persist_profiles.call_count)

    @patch("enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles", return_value=[Mock()])
    @patch("enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached", return_value=True)
    @patch("enmutils_int.lib.load_mgr.log.logger.warn")
    def test_allocate_exclusive_nodes__returns_true_when_nothing_to_allocate(
            self, mock_warn, mock_check_if_required_allocated_node_count_reached, _):
        self.assertTrue(load_mgr.allocate_exclusive_nodes())
        self.assertTrue(mock_warn.called)
        self.assertEqual(mock_check_if_required_allocated_node_count_reached.call_count, 2)

    @patch("enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles")
    @patch("enmutils_int.lib.load_mgr.nodemanager_adaptor")
    @patch("enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached", side_effect=[False, True])
    @patch("enmutils_int.lib.load_mgr.log.logger.warn")
    def test_allocate_exclusive_nodes__returns_true_if_allocate_required_using_service(
            self, mock_warn, mock_check_if_required_allocated_node_count_reached, mock_nodemanager_adaptor,
            mock_retrieve_all_exclusive_profiles):
        profile = Mock()
        mock_retrieve_all_exclusive_profiles.return_value = [profile]
        self.assertTrue(load_mgr.allocate_exclusive_nodes(service_to_be_used=True))
        self.assertTrue(mock_warn.called)
        self.assertEqual(mock_check_if_required_allocated_node_count_reached.call_count, 2)
        mock_nodemanager_adaptor.allocate_nodes.assert_called_with(profile)

    @patch("enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles")
    @patch("enmutils_int.lib.load_mgr.node_pool_mgr")
    @patch("enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached", side_effect=[False, True])
    @patch("enmutils_int.lib.load_mgr.log.logger.warn")
    def test_allocate_exclusive_nodes__returns_true_if_allocate_required_not_using_service(
            self, mock_warn, mock_check_if_required_allocated_node_count_reached, mock_node_pool_mgr,
            mock_retrieve_all_exclusive_profiles):
        profile = Mock()
        mock_retrieve_all_exclusive_profiles.return_value = [profile]
        self.assertTrue(load_mgr.allocate_exclusive_nodes())
        self.assertTrue(mock_warn.called)
        self.assertEqual(mock_check_if_required_allocated_node_count_reached.call_count, 2)
        mock_node_pool_mgr.get_pool.return_value.allocate_nodes.assert_called_with(profile)

    @patch("enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles")
    @patch("enmutils_int.lib.load_mgr.node_pool_mgr")
    @patch("enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached", side_effect=[False, True])
    @patch("enmutils_int.lib.load_mgr.log.logger.debug")
    @patch("enmutils_int.lib.load_mgr.log.logger.warn")
    def test_allocate_exclusive_nodes__returns_false_if_allocate_required_but_allocate_fails(
            self, mock_warn, mock_debug, mock_check_if_required_allocated_node_count_reached, mock_node_pool_mgr,
            mock_retrieve_all_exclusive_profiles):
        profile = Mock()
        mock_retrieve_all_exclusive_profiles.return_value = [profile]
        mock_node_pool_mgr.get_pool.return_value.allocate_nodes.side_effect = Exception("some error")
        self.assertTrue(load_mgr.allocate_exclusive_nodes())
        self.assertTrue(mock_warn.called)
        self.assertEqual(mock_check_if_required_allocated_node_count_reached.call_count, 2)
        mock_node_pool_mgr.get_pool.return_value.allocate_nodes.assert_called_with(profile)
        self.assertTrue(call("Failed to correctly allocate nodes, response: some error") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles", return_value=[])
    @patch("enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached")
    @patch("enmutils_int.lib.load_mgr.log.logger.warn")
    def test_allocate_exclusive_nodes__returns_false_when_no_exclusive_profiles_found(
            self, mock_log, mock_check_if_required_allocated_node_count_reached, _):
        self.assertFalse(load_mgr.allocate_exclusive_nodes())
        self.assertFalse(mock_log.called)
        self.assertFalse(mock_check_if_required_allocated_node_count_reached.called)

    def test_check_if_required_allocated_node_count_reached__returns_true_for_profile_with_num_nodes(self):
        node = Mock(profiles=["TEST_PROFILE_1"])
        profile = Mock(NAME="TEST_PROFILE_1", NUM_NODES={"ERBS": 1})
        delattr(profile, "TOTAL_NODES")
        node_pool_mgr.cached_nodes_list = [node]
        self.assertTrue(load_mgr.check_if_required_allocated_node_count_reached([profile]))

    def test_check_if_required_allocated_node_count_reached__returns_true_for_profile_with_total_nodes(self):
        node = Mock(profiles=["TEST_PROFILE_1"])
        profile = Mock(NAME="TEST_PROFILE_1", TOTAL_NODES=1)
        delattr(profile, "NUM_NODES")
        node_pool_mgr.cached_nodes_list = [node]
        self.assertTrue(load_mgr.check_if_required_allocated_node_count_reached([profile]))

    @patch("enmutils_int.lib.load_mgr.node_pool_mgr")
    def test_check_if_required_allocated_node_count_reached__returns_true_for_profile_no_total_nodes_no_num_nodes(
            self, _):
        profile1 = Mock()
        profile2 = Mock()
        delattr(profile1, "TOTAL_NODES")
        delattr(profile2, "TOTAL_NODES")
        delattr(profile1, "NUM_NODES")
        delattr(profile2, "NUM_NODES")
        self.assertTrue(load_mgr.check_if_required_allocated_node_count_reached([profile1, profile2]))

    def test_is_profile_in_state(self):
        profile = self._get_profiles(num_profiles=1, num_nodes=10).values()[0]
        profile.state = "STARTING"
        persistence.set(profile.NAME, profile, -1)
        self.assertTrue(load_mgr.is_profile_in_state(profile.NAME, state="STARTING"))
        profile.state = "STOPPING"
        persistence.set(profile.NAME, profile, -1)
        self.assertFalse(load_mgr.is_profile_in_state(profile.NAME, state="STARTING"))

    @patch('enmutils_int.lib.load_mgr.ProfilePool.allocated_nodes', return_value=[1])
    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    @patch('enmutils_int.lib.load_mgr.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_deallocate_all_exclusive_nodes__is_successful_if_service_not_used(self, mock_retrieve, mock_deallocate,
                                                                               mock_info, *_):
        profile = ExclusiveProfile(name="Test_01")
        profile.NUM_NODES = {"ERBS": 1}
        mock_retrieve.return_value = [profile]
        load_mgr.deallocate_all_exclusive_nodes([])
        self.assertTrue(mock_deallocate.called)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.load_mgr.ProfilePool.allocated_nodes', return_value=[1])
    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    @patch('enmutils_int.lib.load_mgr.nodemanager_adaptor.deallocate_nodes')
    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_deallocate_all_exclusive_nodes__is_successful_if_service_is_used(self, mock_retrieve, mock_deallocate,
                                                                              mock_info, *_):
        profile = ExclusiveProfile(name="Test_01")
        profile.NUM_NODES = {"ERBS": 1}
        mock_retrieve.return_value = [profile]
        load_mgr.deallocate_all_exclusive_nodes([], service_to_be_used=True)
        mock_deallocate.assert_called_with(profile)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.load_mgr.ProfilePool.allocated_nodes', return_value=[])
    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    @patch('enmutils_int.lib.load_mgr.nodemanager_adaptor.deallocate_nodes')
    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_deallocate_all_exclusive_nodes__is_unsuccessful_if_service_is_used(self, mock_retrieve, mock_deallocate,
                                                                                mock_info, *_):
        profile = ExclusiveProfile(name="Test_01")
        profile.NUM_NODES = {"ERBS": 1}
        mock_retrieve.return_value = [profile]
        load_mgr.deallocate_all_exclusive_nodes([], service_to_be_used=True)
        self.assertFalse(mock_deallocate.called)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.load_mgr.ProfilePool.allocated_nodes', return_value=[1])
    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    @patch('enmutils_int.lib.load_mgr.get_all_active_profiles')
    @patch('enmutils_int.lib.load_mgr.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_deallocate_all_exclusive_nodes_ignores_ap01_if_running(self, mock_retrieve, mock_deallocate,
                                                                    mock_get_all_active_profiles, mock_info, *_):
        profile = ExclusiveProfile(name="AP_01")
        profile.NUM_NODES = {"ERBS": 1}
        mock_get_all_active_profiles.return_value = ["AP_01"]
        mock_retrieve.return_value = [profile]
        load_mgr.deallocate_all_exclusive_nodes([profile], stop_all=True)
        self.assertTrue(mock_deallocate.call_count is 1)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.InputData.get_profiles_values')
    @patch('enmutils_int.lib.load_mgr.InputData.get_all_exclusive_profiles', new_callable=PropertyMock)
    def test_retrieve_all_exclusive_profiles_removes_duplicates(self, mock_get_all_exclusive_profiles, *_):
        mock_get_all_exclusive_profiles.return_value = ["AP_01", "AP_01"]
        self.assertTrue(len(load_mgr._retrieve_all_exclusive_profiles()) is 1)

    @patch('enmutils_int.lib.load_mgr.profile.ExclusiveProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.load_mgr.InputData.get_profiles_values')
    @patch('enmutils_int.lib.load_mgr.InputData.get_all_exclusive_profiles', new_callable=PropertyMock)
    def test_retrieve_all_exclusive_profiles_excludes(self, mock_get_all_exclusive_profiles, mock_get_profiles_values,
                                                      _):
        mock_get_all_exclusive_profiles.return_value = ["AP_01", "CMIMPORT_02"]
        mock_get_profiles_values.return_value = {'SUPPORTED': True}
        self.assertTrue(len(load_mgr._retrieve_all_exclusive_profiles(exclude=["AP_01"])) is 1)

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', side_effect=EnvironError(""))
    def test_get_new_profiles_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, load_mgr.get_new_profiles)

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', return_value=("4.1.2", "4.1.1"))
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_get_new_profiles(self, mock_run_local_command, *_):
        mock_run_local_command.return_value = Mock(rc=0, stdout="ERICtorutilitiesinternal_CXP9030579-4.1.2.json")
        self.assertIn("CMIMPORT_11", load_mgr.get_new_profiles(previous_rpm='4.1.1'))

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', return_value=("4.1.2", "4.1.1"))
    @patch('enmutils_int.lib.load_mgr.filter_artifact_dict_for_profile_keys', return_value=["PROFILE"])
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version', side_effect=[20, 10, 20, 10])
    @patch('enmutils_int.lib.load_mgr.return_dict_from_json_artifact')
    def test_get_updated_profiles__success(self, mock_artifact_dict, mock_get_profile_update_version, mock_filter,
                                           mock_comparative_versions):
        self.assertIn("PROFILE", load_mgr.get_updated_profiles("4.1.1"))
        self.assertEqual(2, mock_get_profile_update_version.call_count)
        self.assertEqual(2, mock_artifact_dict.call_count)
        self.assertEqual(1, mock_filter.call_count)
        self.assertEqual(1, mock_comparative_versions.call_count)

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', return_value=("4.1.2", "4.1.1"))
    @patch('enmutils_int.lib.load_mgr.filter_artifact_dict_for_profile_keys', return_value=["PROFILE"])
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version')
    @patch('enmutils_int.lib.load_mgr.return_dict_from_json_artifact')
    def test_get_updated_profiles__fail_get_profile_update_version(self, mock_artifact_dict,
                                                                   mock_get_profile_update_version, mock_filter,
                                                                   mock_comparative_versions):
        load_mgr.get_updated_profiles("4.1.1")
        self.assertEqual(2, mock_get_profile_update_version.call_count)
        self.assertEqual(2, mock_artifact_dict.call_count)
        self.assertEqual(1, mock_filter.call_count)
        self.assertEqual(1, mock_comparative_versions.call_count)

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', return_value=("4.1.2", "4.1.1"))
    @patch('enmutils_int.lib.load_mgr.filter_artifact_dict_for_profile_keys', return_value=["PROFILE"])
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version')
    @patch('enmutils_int.lib.load_mgr.return_dict_from_json_artifact')
    def test_get_updated_profiles__no_previous_rpm_specified(self, mock_artifact_dict, mock_get_profile_update_version,
                                                             mock_filter, mock_comparative_versions):
        load_mgr.get_updated_profiles()
        self.assertEqual(2, mock_get_profile_update_version.call_count)
        self.assertEqual(2, mock_artifact_dict.call_count)
        self.assertEqual(1, mock_filter.call_count)
        self.assertEqual(1, mock_comparative_versions.call_count)

    @patch('enmutils_int.lib.load_mgr.get_comparative_versions', return_value=("4.1.2", "4.1.1"))
    def test_get_new_profiles__no_previous_rpm_specified(self, mock_comparative_versions):
        self.assertIn("CMIMPORT_11", load_mgr.get_new_profiles())
        self.assertEqual(1, mock_comparative_versions.call_count)

    @patch("enmutils_int.lib.load_mgr.download_mavendata_from_nexus")
    @patch("xml.etree.ElementTree.parse")
    @patch('enmutils_int.lib.load_mgr.get_installed_version', return_value="Unknown")
    def test_get_comparative_versions__raises_error_if_cant_get_installed_version(self, *_):
        self.assertRaises(EnvironError, load_mgr.get_comparative_versions)

    @patch("enmutils_int.lib.load_mgr.download_mavendata_from_nexus", return_value=False)
    @patch("xml.etree.ElementTree.parse")
    @patch('enmutils_int.lib.load_mgr.get_installed_version')
    def test_get_comparative_versions__raises_error_if_cant_download_xml(self, *_):
        self.assertRaises(EnvironError, load_mgr.get_comparative_versions)

    @patch("enmutils_int.lib.load_mgr.check_nexus_version")
    @patch("enmutils_int.lib.load_mgr.download_mavendata_from_nexus")
    @patch("enmutils_int.lib.load_mgr.get_previous_version", return_value="4.5.11")
    @patch('enmutils_int.lib.load_mgr.get_installed_version', return_value="4.54.12")
    @patch("xml.etree.ElementTree.parse")
    def test_get_comparative_versions__is_successful(self, mock_parse, *_):

        mock_parse.return_value.getroot.return_value.iter.return_value = [Mock(text="4.54.10"),
                                                                          Mock(text="4.54.11"),
                                                                          Mock(text="4.54.12")]

        self.assertEqual(("4.54.12", "4.5.11"), load_mgr.get_comparative_versions())

    @patch("enmutils_int.lib.load_mgr.check_nexus_version", return_value="")
    def test_get_previous_version__raises_error(self, _):
        installed = "4.54.11"
        all_rpm_versions = ["4.54.10", "4.54.11", "4.54.12"]
        self.assertRaises(EnvironError, load_mgr.get_previous_version, installed, all_rpm_versions)

    def test_get_previous_version__index_fails_while_loop(self):
        installed_version = '4.54.10'
        all_rpm_versions = '4.54.10'
        self.assertRaises(EnvironError, load_mgr.get_previous_version(installed_version, all_rpm_versions))

    @patch("enmutils_int.lib.load_mgr.check_nexus_version")
    def test_get_previous_version__is_successfull(self, mock_check_nexus_version):
        installed = "4.54.11"
        previous = "4.54.10"
        mock_check_nexus_version.return_value = previous

        all_rpm_versions = ["4.54.10", "4.54.11", "4.54.12"]
        self.assertEqual(previous, load_mgr.get_previous_version(installed, all_rpm_versions))

    def test_get_profile_update_version__raises_no_exception_on_missing_key(self):
        profile = "TEST_01"
        json_dict = {"basic": {'test': {'TEST_01': {'SUPPORTED': True}}}}
        self.assertEqual(None, load_mgr.get_profile_update_version(profile, json_dict))

    def test_get_profile_update_version__returns_none_restart_result(self):
        profile = "TEST_01"
        json_dict = {"basic": {'test': {'TEST_02': {'SUPPORTED': True}}}}
        self.assertEqual(99999, load_mgr.get_profile_update_version(profile, json_dict))

    @patch('enmutils_int.lib.load_mgr.get_installed_version')
    @patch('enmutils_int.lib.load_mgr.return_dict_from_json_artifact')
    def test_get_profile_update_version__no_json(self, mock_json, _):
        profile = "TEST_01"
        mock_json.return_value = {"basic": {'test': {'TEST_02': {'SUPPORTED': True}}}}
        self.assertEqual(99999, load_mgr.get_profile_update_version(profile))
        self.assertEqual(1, mock_json.call_count)

    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_allocate_exclusive_returns_false_if_no_profiles(self, mock_retrieve_all_exclusive_profiles):
        mock_retrieve_all_exclusive_profiles.return_value = []
        self.assertFalse(load_mgr.allocate_exclusive_nodes())

    @patch('enmutils_int.lib.load_mgr.check_if_required_allocated_node_count_reached', return_value=True)
    @patch('enmutils_int.lib.load_mgr.node_pool_mgr.Pool.allocated_nodes', return_value=[Mock() for _ in range(23)])
    @patch('enmutils_int.lib.load_mgr._retrieve_all_exclusive_profiles')
    def test_allocate_exclusive_nodes__returns_true_when_all_nodes_allocated(self, mock_retrieve_all_exclusive_profiles,
                                                                             *_):
        mock_retrieve_all_exclusive_profiles.return_value = [Mock()]
        self.assertTrue(load_mgr.allocate_exclusive_nodes())

    @patch('enmutils_int.lib.load_mgr.time.sleep', return_value=0)
    @patch('enmutils_int.lib.load_mgr._get_stopping_profiles')
    def test_wait_for_stopping_profiles(self, *_):
        load_mgr.wait_for_stopping_profiles({}, 0.00001)

    @patch('enmutils_int.lib.load_mgr.time.sleep', return_value=0)
    @patch('enmutils_int.lib.load_mgr._get_stopping_profiles', return_value=None)
    def test_wait_for_stopping_profiles_no_stopping(self, *_):
        load_mgr.wait_for_stopping_profiles({}, 0.00001)

    @patch('enmutils_int.lib.load_mgr.time.sleep', return_value=0)
    @patch('enmutils_int.lib.load_mgr._get_stopping_profiles', return_value={"Profile": "Profile"})
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    def test_wait_for_stopping_profiles__jenkins_false_raises_no_exception(self, mock_info, *_):
        load_mgr.wait_for_stopping_profiles({"Profile": Profile}, wait_time=0.000001, interim_time=0.0000001,
                                            time_interval=0.0000001)
        self.assertEqual(1, mock_info.call_count)

    @patch('enmutils_int.lib.load_mgr.time.sleep', return_value=0)
    @patch('enmutils_int.lib.load_mgr._get_stopping_profiles', return_value={"Profile": "Profile"})
    @patch('enmutils_int.lib.load_mgr.log.logger.info')
    def test_wait_for_stopping_profiles__raises_exception_if_jenkins(self, mock_info, *_):
        self.assertRaises(Exception, load_mgr.wait_for_stopping_profiles, {"Profile": Profile}, wait_time=0.000001,
                          jenkins=True, interim_time=0.0000001, time_interval=0.0000001)
        mock_info.assert_called_with("The following profiles are still stopping: ['Profile']")

    def test_detect_and_create_renamed_objects__renamed_profile(self):
        load_mgr.basic_network.RENAMED_PROFILES = {"TEST_00": "TEST_01"}
        updated_profiles = [Mock(NAME="TEST_00")]
        result = load_mgr.detect_and_create_renamed_objects(updated_profiles)
        self.assertEqual(2, len(result))

    def test_detect_and_create_renamed_objects__no_renamed_profile(self):
        load_mgr.basic_network.RENAMED_PROFILES = {"TEST_00": "TEST_01"}
        updated_profiles = [Mock(NAME="TEST_01")]
        result = load_mgr.detect_and_create_renamed_objects(updated_profiles)
        self.assertEqual(1, len(result))

    @patch('enmutils_int.lib.load_mgr.get_installed_version', return_value='4.98.6')
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version', return_value='1')
    @patch('enmutils_int.lib.load_mgr.version.parse', side_effect=(1, 1))
    @patch('enmutils_int.lib.load_mgr.detect_and_create_renamed_objects', return_value=[])
    @patch('enmutils_int.lib.load_mgr.log.logger.debug')
    @patch('enmutils_int.lib.load_mgr.get_persisted_profiles_by_name')
    def test_get_updated_active_profiles__not_updated(self, mock_get, mock_debug, *_):
        profile = Mock(version="4.98.5", update_version="0")
        profile.NAME = "TEST_00"
        mock_get.return_value = {"Profile": profile}
        load_mgr.get_updated_active_profiles()
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils_int.lib.load_mgr.get_installed_version', return_value='4.98.6')
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version', return_value='1')
    @patch('enmutils_int.lib.load_mgr.version.parse', side_effect=(0, 1))
    @patch('enmutils_int.lib.load_mgr.detect_and_create_renamed_objects', return_value=[])
    @patch('enmutils_int.lib.load_mgr.log.logger.debug')
    @patch('enmutils_int.lib.load_mgr.get_persisted_profiles_by_name')
    def test_get_updated_active_profiles__updated(self, mock_get, mock_debug, *_):
        profile = Mock(version="4.98.5", update_version="0")
        profile.NAME = "TEST_00"
        mock_get.return_value = {"Profile": profile}
        load_mgr.get_updated_active_profiles()
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils_int.lib.load_mgr.get_installed_version', return_value='4.98.6')
    @patch('enmutils_int.lib.load_mgr.get_profile_update_version', side_effect=EnvironError("Error"))
    @patch('enmutils_int.lib.load_mgr.version.parse', side_effect=(0, 1))
    @patch('enmutils_int.lib.load_mgr.detect_and_create_renamed_objects', return_value=[])
    @patch('enmutils_int.lib.load_mgr.get_profile_objects_from_profile_names')
    @patch('enmutils_int.lib.load_mgr.log.logger.debug')
    @patch('enmutils_int.lib.load_mgr.get_persisted_profiles_by_name')
    def test_get_updated_active_profiles__get_up_version_error(self, mock_get, mock_debug, mock_profile_objs, *_):
        profile = Mock(version="4.98.5", update_version="0")
        profile.NAME = "TEST_00"
        mock_get.return_value = {"Profile": profile}
        load_mgr.get_updated_active_profiles()
        self.assertEqual(1, mock_debug.call_count)
        self.assertEqual(1, mock_profile_objs.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
