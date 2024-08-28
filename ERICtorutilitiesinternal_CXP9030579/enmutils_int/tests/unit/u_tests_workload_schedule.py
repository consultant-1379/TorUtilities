#!/usr/bin/env python
from collections import OrderedDict

import unittest2
from mock import Mock, patch

from enmutils.lib.exceptions import NoNodesAvailable
from enmutils_int.lib import workload_schedule
from testslib import unit_test_utils


class WorkloadScheduleUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.log.logger.info')
    def test_finished(self, mock_info, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule._finished("stop")
        self.assertEqual(mock_info.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.time.sleep', return_value=0)
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.log.logger.info')
    def test_sleep_ignored_if_initial_install_teardown(self, mock_info, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}},
                                                      initial_install_teardown=True)
        schedule._sleep(0, "TEST_01")
        self.assertEqual(mock_info.call_count, 0)

    @patch('enmutils_int.lib.workload_schedule.time.sleep', return_value=0)
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.log.logger.info')
    def test_sleep(self, mock_info, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule._sleep(0, "TEST_01")
        self.assertEqual(mock_info.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_get_profiles_from_schedule(self, mock_parse_schedule_file):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        test_schedule = [OrderedDict([('TEST', OrderedDict([('TEST_01', (0, 0))]))])]
        mock_parse_schedule_file.return_value = {"TEST": {"TEST_01": (0, 0)}}
        schedule.schedule = test_schedule
        profiles = schedule.get_profiles_from_schedule("TEST_01")
        self.assertDictEqual(profiles, {"TEST_01": (0, 0)})

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_get_profiles_from_schedule_returns_only_matches(self, mock_parse_schedule_file):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        test_schedule = [OrderedDict([('TEST', OrderedDict([('TEST_01', (0, 0))]))])]
        mock_parse_schedule_file.return_value = {"TEST": {"TEST_01": (0, 0)}}
        schedule.schedule = test_schedule
        profiles = schedule.get_profiles_from_schedule("TEST_02")
        self.assertDictEqual(profiles, {})

    @patch('enmutils_int.lib.workload_schedule.os.path.join', return_value="/test_schedule.py")
    @patch('enmutils_int.lib.workload_schedule.os.path.basename', return_value="test_schedule")
    @patch('enmutils_int.lib.workload_schedule.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.log.logger.info')
    @patch('enmutils_int.lib.workload_schedule.imp.load_source')
    def test_parse_schedule_file(self, mock_load_source, *_):
        test_schedule = Mock()
        test_schedule.WORKLOAD = "test_schedule"
        mock_load_source.return_value = test_schedule
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        parsed_schedule = schedule.parse_schedule_file("test_file")
        self.assertEqual(parsed_schedule, "test_schedule")

    @patch('enmutils_int.lib.workload_schedule.os.path.join', return_value="/test_schedule.py")
    @patch('enmutils_int.lib.workload_schedule.os.path.basename', return_value="test_schedule")
    @patch('enmutils_int.lib.workload_schedule.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.log.logger.info')
    @patch('enmutils_int.lib.workload_schedule.imp.load_source', side_effect=Exception("Exception"))
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    def test_parse_schedule_file_logs_load_exception(self, mock_error, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.parse_schedule_file("test_file")
        self.assertEqual(mock_error.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.os.path.join', return_value="/test_schedule.py")
    @patch('enmutils_int.lib.workload_schedule.os.path.basename', return_value="test_schedule")
    @patch('enmutils_int.lib.workload_schedule.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    def test_parse_schedule_file_logs_file_not_found(self, mock_error, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        parsed_schedule = schedule.parse_schedule_file("test_file")
        self.assertEqual(None, parsed_schedule)
        self.assertEqual(mock_error.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.start')
    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.stop')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._sleep')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_execute__start_index_mismatch(self, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        profile = Mock()
        profile.NAME = "TEST_01"
        schedule.profile_dict = {"TEST_01": profile}
        index = schedule._execute(0, "TEST_01", ["TEST_01", "TEST_02"], [0, 0])
        self.assertEqual(1, index)

    @patch('enmutils_int.lib.workload_schedule.config.has_prop', return_value=False)
    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.start')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._sleep')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_execute_start(self, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        profile = Mock()
        profile.NAME = "TEST_01"
        schedule.profile_dict = {"TEST_01": profile}
        index = schedule._execute(0, "TEST_01", ["TEST_01"], [0, 0])
        self.assertEqual(1, index)

    @patch('enmutils_int.lib.workload_schedule.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.start', side_effect=NoNodesAvailable(""))
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._sleep')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_execute_start_processes_exceptio(self, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        profile = Mock()
        profile.NAME = "TEST_01"
        schedule.profile_dict = {"TEST_01": profile}
        index = schedule._execute(0, "TEST_01", ["TEST_01", "TEST_02"], [0, 0])
        self.assertEqual(1, index)

    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.start', side_effect=Exception(""))
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._sleep')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_execute_start_no_nodes(self, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        profile = Mock()
        profile.NAME = "TEST_01"
        schedule.profile_dict = {"TEST_01": profile}
        index = schedule._execute(0, "TEST_01", ["TEST_01"], [0, 0])
        self.assertEqual(1, index)

    @patch('enmutils_int.lib.workload_schedule.config.get_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.config.has_prop', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.profile_manager.ProfileManager.stop')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._sleep')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    def test_execute_stop(self, *_):
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        profile = Mock()
        profile.NAME = "TEST_01"
        schedule.profile_dict = {"TEST_01": profile}
        index = schedule._execute(0, "TEST_01", ["TEST_01"], [0, 0], action="stopping")
        self.assertEqual(1, index)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._finished')
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.get_profiles_from_schedule')
    def test_workload_schedule_start_logs_no_profiles_to_start(self, mock_get_profiles, mock_error, mock_finished,
                                                               mock_parse_schedule_file):
        mock_get_profiles.return_value = OrderedDict()
        mock_parse_schedule_file.return_value = {"APP": {"APP_01": (0, 0)}}
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.start()
        self.assertEqual(mock_error.call_count, 1)
        self.assertEqual(mock_finished.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.check_for_existing_process', return_value=False)
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._execute')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._finished')
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.get_profiles_from_schedule')
    def test_workload_schedule_start(self, mock_get_profiles, mock_error, mock_finished, mock_parse_schedule_file,
                                     mock_execute, *_):
        mock_get_profiles.return_value = {"TEST_01": (0, 0)}
        mock_parse_schedule_file.return_value = {"TEST": {"TEST_01": (0, 0)}}
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.start()
        self.assertEqual(mock_error.call_count, 0)
        self.assertEqual(mock_finished.call_count, 1)
        self.assertEqual(mock_execute.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.check_for_existing_process', return_value=True)
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._execute')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._finished')
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.get_profiles_from_schedule')
    def test_workload_schedule_start_skips_existing_profile(self, mock_get_profiles, mock_error, mock_finished,
                                                            mock_parse_schedule_file, mock_execute, *_):
        mock_get_profiles.return_value = {"TEST_01": (0, 0)}
        mock_parse_schedule_file.return_value = {"TEST": {"TEST_01": (0, 0)}}
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.start()
        self.assertEqual(mock_error.call_count, 0)
        self.assertEqual(mock_finished.call_count, 1)
        self.assertEqual(mock_execute.call_count, 0)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._finished')
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.get_profiles_from_schedule')
    def test_workload_schedule_stop__logs_no_profiles_to_stop(self, mock_get_profiles, mock_error, mock_finished,
                                                              mock_parse_schedule_file):
        mock_get_profiles.return_value = OrderedDict()
        mock_parse_schedule_file.return_value = {"APP": {"APP_01": (0, 0)}}
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.stop()
        self.assertEqual(mock_error.call_count, 1)
        self.assertEqual(mock_finished.call_count, 0)

    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._execute')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.parse_schedule_file')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule._finished')
    @patch('enmutils_int.lib.workload_schedule.log.logger.error')
    @patch('enmutils_int.lib.workload_schedule.WorkloadSchedule.get_profiles_from_schedule')
    def test_workload_schedule_stop__success(self, mock_get_profiles, mock_error, mock_finished,
                                             mock_parse_schedule_file, mock_execute):
        mock_get_profiles.return_value = {"TEST_01": (0, 0)}
        mock_parse_schedule_file.return_value = {"TEST": {"TEST_01": (0, 0)}}
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        schedule.stop()
        self.assertEqual(mock_error.call_count, 0)
        self.assertEqual(mock_finished.call_count, 0)
        self.assertEqual(mock_execute.call_count, 1)

    @patch('enmutils_int.lib.workload_schedule.persistence.get', return_value=set(["TEST_01", "TEST_03"]))
    @patch('enmutils_int.lib.workload_schedule.mutexer')
    @patch('enmutils_int.lib.workload_schedule.log.logger.debug')
    @patch('enmutils_int.lib.workload_schedule.shell.run_local_cmd')
    def test_check_for_existing_process(self, mock_local_cmd, mock_debug, *_):
        profiles = ["TEST_01", "TEST_02", "TEST_03"]
        response, response1, response2 = Mock(), Mock(), Mock()
        response.ok, response1.ok, response2.ok = True, False, True
        response.stdout = "pid"
        mock_local_cmd.side_effect = [response, response1, response2]
        schedule = workload_schedule.WorkloadSchedule(profile_dict={"TEST": {"TEST_01": (0, 0)}})
        for _ in profiles:
            schedule.check_for_existing_process(_)
        self.assertEqual(4, mock_debug.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
