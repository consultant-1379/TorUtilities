#!/usr/bin/env python
from datetime import datetime

import unittest2
from mock import patch, Mock, MagicMock, call
from parameterizedtestcase import ParameterizedTestCase
from requests import HTTPError

from enmutils.lib.config import get_log_dir
from enmutils_int.lib import workload_ops
from testslib import unit_test_utils


class WorkloadOpsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False, '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()


class WorkloadInfoOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_workload_info__validate_raises_error(self):
        op = workload_ops.WorkloadInfoOperation()
        with self.assertRaises(NotImplementedError):
            op._validate()

    def test_execute_operation__in_workloadinfooperation_is_successful(self):
        op = workload_ops.WorkloadInfoOperation()
        self.assertRaises(NotImplementedError, op._execute_operation)

    @patch("enmutils_int.lib.workload_ops.nodemanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.workload_ops.profilemanager_helper_methods.get_all_profile_names")
    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation._update_total_node_count")
    def test_setup__in_workloadinfooperation_is_successful_if_service_can_be_used(
            self, mock_update_total_node_count, *_):
        op = workload_ops.WorkloadInfoOperation()
        op._setup()
        self.assertTrue(op.nodemanager_service_to_be_used)
        self.assertTrue(mock_update_total_node_count.called)

    @patch("enmutils_int.lib.workload_ops.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.workload_ops.profilemanager_helper_methods.get_all_profile_names")
    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation._update_total_node_count")
    def test_setup__in_workloadinfooperation_is_successful_if_service_not_used(
            self, mock_update_total_node_count, *_):
        op = workload_ops.WorkloadInfoOperation()
        op.operation_type = "start"
        op._setup()
        self.assertFalse(op.nodemanager_service_to_be_used)
        self.assertFalse(mock_update_total_node_count.called)

    @patch('enmutils_int.lib.workload_ops.nodemanager_helper_methods.update_total_node_count', return_value=10)
    def test_update_total_node_count__updates_total_nodes_if_service_not_used(self, mock_update_count):
        op = workload_ops.WorkloadInfoOperation()
        op._update_total_node_count(update=True)
        self.assertEqual(mock_update_count.call_count, 1)
        self.assertEqual(10, op.total_nodes)

    @patch('enmutils_int.lib.workload_ops.nodemanager_adaptor.list_nodes')
    @patch('enmutils_int.lib.workload_ops.nodemanager_helper_methods.update_total_node_count')
    def test_update_total_node_count__does_nothing_if_list_operation(self, mock_update_count, mock_list_nodes):
        args_dict = {"IDENTIFIER": "all", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.nodemanager_service_to_be_used = True
        op._update_total_node_count(update=True)
        self.assertFalse(mock_update_count.called)
        self.assertFalse(mock_list_nodes.called)
        self.assertEqual(0, op.total_nodes)

    @patch('enmutils_int.lib.workload_ops.nodemanager_adaptor.list_nodes', return_value=(10, 5, ["blah"]))
    def test_update_total_node_count__updates_total_nodes_if_service_used(self, mock_list_nodes):
        op = workload_ops.WorkloadInfoOperation()
        op.nodemanager_service_to_be_used = True
        op._update_total_node_count(update=True)
        self.assertEqual(mock_list_nodes.call_count, 1)
        self.assertEqual(10, op.total_nodes)

    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info__set_active_profiles_is_successful(self, mock_load_mgr):
        mock_load_mgr.get_persisted_profiles_by_name.return_value = {'TEST_PROFILE': self.mock_profile}
        op = workload_ops.WorkloadInfoOperation()
        op._set_active_profiles()
        self.assertEqual(op.active_profiles, {'TEST_PROFILE': self.mock_profile})

    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info__set_active_profiles_is_successful_with_specific_profiles(self, mock_load_mgr):
        mock_load_mgr.get_persisted_profiles_by_name.return_value = {'TEST_PROFILE': self.mock_profile,
                                                                     'TEST_PROFILE_2': self.mock_profile}
        op = workload_ops.WorkloadInfoOperation()
        op._set_active_profiles(specific_profiles=['TEST_PROFILE'])
        self.assertEqual(op.active_profiles, {'TEST_PROFILE': self.mock_profile})

    # _set_active_status test cases
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.'
           'filter_profiles_status_based_on_priority_and_json_response')
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info__set_active_status_is_successful(self, mock_load_mgr, *_):
        mock_load_mgr.get_persisted_profiles_status_by_name.return_value = ['TEST_PROFILE']
        op = workload_ops.WorkloadInfoOperation()
        self.assertEqual(op._set_active_status(), ['TEST_PROFILE'])

    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.'
           'filter_profiles_status_based_on_priority_and_json_response')
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info__set_active_status_is_successful_with_specific_profiles(self, mock_load_mgr, *_):
        mock_profile_obj = Mock()
        mock_profile_obj.NAME = 'TEST_PROFILE'
        mock_profile_obj_2 = Mock()
        mock_profile_obj_2.NAME = 'TEST_PROFILE_2'
        mock_load_mgr.get_persisted_profiles_status_by_name.return_value = [mock_profile_obj, mock_profile_obj_2]
        op = workload_ops.WorkloadInfoOperation()
        self.assertEqual(op._set_active_status(specific_profiles=[mock_profile_obj.NAME]), [mock_profile_obj])

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.'
           'filter_profiles_status_based_on_priority_and_json_response')
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.get_status')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info_set_active_status__uses_service(self, mock_load_mgr, mock_get_status,
                                                           mock_filter_profiles_status, _):
        status, status1 = Mock(), Mock()
        status.priority, status1.priority = 1, 2
        mock_get_status.return_value = [status, status1]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = "1"
        op._set_active_status()
        self.assertEqual(0, mock_load_mgr.call_count)
        self.assertEqual(1, mock_filter_profiles_status.call_count)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.'
           'filter_profiles_status_based_on_priority_and_json_response')
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.get_status')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info_set_active_status__if_json_response_is_true(self, mock_load_mgr, mock_get_status,
                                                                       mock_filter_profiles_status, _):
        mock_get_status.return_value = [{"status": "WARNING", "user_count": 2, "NAME": "NODESEC_15",
                                         "schedule": "Runs at the following times: 08:00 (last run: 15-Feb 18:01:25, "
                                                     "next run: 16-Feb 08:00:00)", "start_time": "10-Feb, 09:06:00",
                                         "pid": 1287, "last_run": "15-Feb, 18:01:25", "num_nodes": 41, "priority": 2,
                                         "state": "RUNNING"}]
        op = workload_ops.WorkloadInfoOperation()
        op._set_active_status(json_response=True)
        self.assertEqual(0, mock_load_mgr.call_count)
        mock_filter_profiles_status.assert_called_with(mock_get_status.return_value, True)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.'
           'filter_profiles_status_based_on_priority_and_json_response')
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.get_status')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_workload_info_set_active_status__if_json_response_is_true_with_priority(self, mock_load_mgr,
                                                                                     mock_get_status,
                                                                                     mock_filter_profiles_status, _):
        mock_get_status.return_value = [{"status": "WARNING", "user_count": 2, "NAME": "NODESEC_15",
                                         "schedule": "Runs at the following times: 08:00 (last run: 15-Feb 18:01:25, "
                                                     "next run: 16-Feb 08:00:00)", "start_time": "10-Feb, 09:06:00",
                                         "pid": 1287, "last_run": "15-Feb, 18:01:25", "num_nodes": 41, "priority": 1,
                                         "state": "RUNNING"}]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = 1
        op._set_active_status(json_response=True)
        self.assertEqual(0, mock_load_mgr.call_count)
        mock_filter_profiles_status.assert_called_with(mock_get_status.return_value, True)

    def test_filter_profiles_status_based_on_priority_and_json_response__if_json_response_required(self):
        status_profiles = [{"status": "WARNING", "user_count": 2, "NAME": "NODESEC_15",
                            "schedule": "Runs at the following times: 08:00 (last run: 15-Feb 18:01:25, "
                                        "next run: 16-Feb 08:00:00)", "start_time": "10-Feb, 09:06:00",
                            "pid": 1287, "last_run": "15-Feb, 18:01:25", "num_nodes": 41, "priority": 1,
                            "state": "RUNNING"}]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = 1
        op.filter_profiles_status_based_on_priority_and_json_response(status_profiles, True)
        self.assertEqual(status_profiles, op.status_profiles)

    def test_filter_profiles_status_based_on_priority_and_json_response__if_json_and_priority_is_None(self):
        status_profiles = [{"status": "WARNING", "user_count": 2, "NAME": "NODESEC_15",
                            "schedule": "Runs at the following times: 08:00 (last run: 15-Feb 18:01:25, "
                                        "next run: 16-Feb 08:00:00)", "start_time": "10-Feb, 09:06:00",
                            "pid": 1287, "last_run": "15-Feb, 18:01:25", "num_nodes": 41, "priority": 1,
                            "state": "RUNNING"}]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = None
        op.filter_profiles_status_based_on_priority_and_json_response(status_profiles, True)
        self.assertEqual(status_profiles, op.status_profiles)

    def test_filter_profiles_status_based_on_priority_and_json_response__is_success(self):
        status_profiles = [Mock(priority=1, NAME="NODESEC_15", state="RUNNING"),
                           Mock(priority=2, NAME="PM_26", state="SLEEPING")]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = None
        op.filter_profiles_status_based_on_priority_and_json_response(status_profiles, False)
        self.assertEqual(status_profiles, op.status_profiles)

    def test_filter_profiles_status_based_on_priority_and_json_response__if_priority_exist(self):
        status_profiles = [Mock(priority=1, NAME="NODESEC_15", state="RUNNING"),
                           Mock(priority=2, NAME="PM_26", state="SLEEPING")]
        op = workload_ops.WorkloadInfoOperation()
        op.priority = 2
        op.filter_profiles_status_based_on_priority_and_json_response(status_profiles, False)
        self.assertEqual(op.priority, op.status_profiles[0].priority)


class WorkloadOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._set_active_profiles')
    def test_setup__is_skipped_if_initial_install_teardown(self, mock_set_active_profiles, _):
        op = workload_ops.WorkloadOperation()
        op.initial_install_teardown = True
        op._setup()
        self.assertEqual(0, mock_set_active_profiles.call_count)

    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._validate')
    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._set_active_profiles')
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup')
    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.mutexer')
    def test_workload_operation_is_successful(self, mock_mutexer, mock_persistence, *_):
        mock_mutexer.mutex.return_value = MagicMock()
        mock_persistence.get.return_value = ['TEST_PROFILE_2']
        op = workload_ops.WorkloadOperation()
        op.restart = False
        op.active_profiles = {'TEST_PROFILE_2': self.mock_profile}
        op.profile_objects = {'TEST_PROFILE': self.mock_profile, 'TEST_PROFILE_2': None}
        with self.assertRaises(NotImplementedError):
            op.execute()

    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._validate')
    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._set_active_profiles')
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup')
    def test_workload_operation_is_successful_restart_true(self, *_):
        op = workload_ops.WorkloadOperation()
        op.restart = True
        with self.assertRaises(NotImplementedError):
            op.execute()

    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_workload_operation__remove_none_type_profiles_is_successful_no_profile_objects(self, mock_persistence):
        op = workload_ops.WorkloadOperation()
        op.profile_objects = {}
        op._remove_none_type_profiles()
        self.assertFalse(mock_persistence.called)

    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_workload_operation__remove_none_type_profiles_is_successful_no_none_type_profiles(self, mock_persistence):
        op = workload_ops.WorkloadOperation()
        op.profile_objects = {'TEST_PROFILE': self.mock_profile}
        op._remove_none_type_profiles()
        self.assertFalse(mock_persistence.called)

    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.mutexer')
    def test_workload_operation__remove_none_type_profiles_is_successful(self, mock_mutexer, mock_persistence):
        op = workload_ops.WorkloadOperation()
        op.profile_objects = {'TEST_PROFILE': self.mock_profile, 'TEST_PROFILE_2': None}
        mock_mutexer.mutex.return_value = MagicMock()
        mock_persistence.get.return_value = ['TEST_PROFILE']
        op.active_profiles = {'TEST_PROFILE': self.mock_profile}
        op._remove_none_type_profiles()
        self.assertTrue(mock_persistence.remove.called)
        self.assertTrue(mock_persistence.set.called)


class WorkloadHealthCheckOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.profilemanager_helper_methods.report_syncronised_level')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    def test_workload_health_check_execute_is_successful(
            self, mock_network_health_check, mock_report_syncronised_level, *_):
        op = workload_ops.WorkloadHealthCheckOperation()
        op.health_check = True
        op.no_network_size_check = True
        with self.assertRaises(NotImplementedError):
            op.execute()
            self.assertTrue(mock_network_health_check.called)
            self.assertTrue(mock_report_syncronised_level.called)

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    def test_workload_health_check_execute_is_successful_health_check_false(self, _):
        op = workload_ops.WorkloadHealthCheckOperation()
        with self.assertRaises(NotImplementedError):
            op.execute()

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    def test_workload_health_check__validate_pass(self, _):
        op = workload_ops.WorkloadHealthCheckOperation()
        op._validate()

    @patch('enmutils_int.lib.workload_ops.WorkloadHealthCheckOperation._execute_operation')
    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    @patch('enmutils_int.lib.workload_ops.profilemanager_helper_methods.report_syncronised_level',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.log')
    def test_workload_health_check_execute_exception(self, mock_log, *_):
        op = workload_ops.WorkloadHealthCheckOperation()
        op.health_check = True
        op.execute()
        self.assertTrue(mock_log.logger.error.called)

    @patch('enmutils_int.lib.workload_ops.WorkloadHealthCheckOperation._exclude_unsupported_exclusive_profiles',
           return_value=[])
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_allocate_exclusive_nodes__in_workloadhealthcheckoperation_is_successful(
            self, mock_persistence, mock_input_data, mock_load_mgr, *_):
        op = workload_ops.WorkloadHealthCheckOperation()
        op.no_exclusive = False
        mock_persistence.get_all_keys.return_value = []
        mock_input_data.return_value.get_all_exclusive_profiles = ['TEST_PROFILE_2']
        mock_load_mgr.allocate_exclusive_nodes.return_value = True
        op._allocate_exclusive_nodes(profile_list=['TEST_PROFILE', 'TEST_PROFILE_2'], service_to_be_used=False)
        mock_load_mgr.allocate_exclusive_nodes.assert_called_with(exclude=["TEST_PROFILE_2"],
                                                                  service_to_be_used=False)
        self.assertTrue(mock_persistence.set.called)

    @patch('enmutils_int.lib.workload_ops.WorkloadHealthCheckOperation._exclude_unsupported_exclusive_profiles',
           return_value=[])
    @patch('enmutils_int.lib.workload_ops.profile_properties_manager')
    @patch('enmutils_int.lib.workload_ops.cache')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_workload_health_check__allocate_exclusive_nodes_is_successful_soem_true(
            self, mock_persistence, mock_input_data, mock_load_mgr, mock_cache, mock_profile_properties_manager, _):
        op = workload_ops.WorkloadHealthCheckOperation()
        op.soem = True
        op.no_exclusive = False
        op.config_file = ''
        mock_persistence.get_all_keys.return_value = []
        mock_input_data.return_value.get_profiles_values.return_value = None
        mock_input_data.return_value.get_all_exclusive_profiles.return_value = ['TEST_PROFILE']
        mock_load_mgr.allocate_exclusive_nodes.return_value = False
        mock_cache.has_key.return_value = True
        mock_cache.get.return_value = ['True', 'False']
        mock_profile_obj = Mock()
        mock_profile_obj.SUPPORTED = True
        mock_profile_obj_2 = Mock()
        mock_profile_obj_2.SUPPORTED = 'INTRUSIVE'
        mock_profile_properties_manager.ProfilePropertiesManager.return_value.get_profile_objects.return_value = [
            mock_profile_obj, mock_profile_obj_2]
        op._allocate_exclusive_nodes(profile_list=['TEST_PROFILE', 'TEST_PROFILE_2'], service_to_be_used=False)

    @staticmethod
    def test_workload_health_check__allocate_exclusive_nodes_is_successful_no_exclusive_true():
        op = workload_ops.WorkloadHealthCheckOperation()
        op.soem = True
        op.no_exclusive = True
        op._allocate_exclusive_nodes(profile_list=['TEST_PROFILE', 'TEST_PROFILE_2'], service_to_be_used=False)

    @patch('enmutils_int.lib.workload_ops.cache.has_key', return_value=False)
    @patch('enmutils_int.lib.workload_ops.cache.get', return_value=[])
    @patch('enmutils_int.lib.workload_ops.profile_properties_manager.ProfilePropertiesManager.get_profile_objects')
    def test_exclude_unsupported_exclusive_profiles__success(self, mock_get_profiles, *_):
        profile, profile1 = Mock(SUPPORTED=True), Mock(SUPPORTED="INTRUSIVE")
        mock_get_profiles.return_value = [profile, profile1]
        op = workload_ops.WorkloadHealthCheckOperation()
        op.config_file = ""
        op._exclude_unsupported_exclusive_profiles([])


class DisplayProfilesOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None, '--exclusive': False}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._validate')
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup')
    @patch('enmutils_int.lib.workload_ops.profilemanager_helper_methods.get_all_profile_names')
    @patch('enmutils_int.lib.workload_ops.log')
    def test_display_profiles_execute__is_successful(self, mock_log, mock_get_all_profile_names, *_):
        op = workload_ops.DisplayProfilesOperation(argument_dict={"--exclusive": False})
        mock_get_all_profile_names.return_value = (['TEST_PROFILE', 'TEST_PROFILE_2'])
        op.execute()
        self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.DisplayProfilesOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.get_all_profiles_list')
    def test_execute_operation__uses_service(self, mock_get_all, *_):
        op = workload_ops.DisplayProfilesOperation(argument_dict={"--exclusive": False})
        op.exclusive = False
        op._execute_operation()
        self.assertEqual(1, mock_get_all.call_count)

    @patch('enmutils_int.lib.workload_ops.DisplayProfilesOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.InputData.get_all_exclusive_profiles')
    @patch('enmutils_int.lib.workload_ops.DisplayProfilesOperation._print_sorted_profile_names')
    def test_execute_operation__exclusive(self, mock_print, *_):
        op = workload_ops.DisplayProfilesOperation(argument_dict={"--exclusive": False})
        op.exclusive = True
        op._execute_operation()
        self.assertEqual(1, mock_print.call_count)

    @staticmethod
    def test_display_profiles__validate_pass():
        op = workload_ops.DisplayProfilesOperation(argument_dict={"--exclusive": False})
        op._validate()

    @staticmethod
    def test_display_profiles__print_exclusive():
        op = workload_ops.DisplayProfilesOperation(argument_dict={"--exclusive": False})
        op.exclusive = True
        op.exclusive_profiles = ['abc']
        op._print_sorted_profile_names()


class DisplayCategoriesOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._validate')
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup')
    @patch('enmutils_int.lib.workload_ops.profilemanager_helper_methods.get_categories')
    @patch('enmutils_int.lib.workload_ops.log')
    def test_display_categories_execute_is_successful(self, mock_log, mock_get_categories, *_):
        op = workload_ops.DisplayCategoriesOperation()
        mock_get_categories.return_value = (['TEST'])
        op.execute()
        self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.DisplayProfilesOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.get_categories_list')
    def test_display_categories_execute__uses_service(self, mock_get_all, *_):
        op = workload_ops.DisplayCategoriesOperation()
        op._execute_operation()
        self.assertEqual(1, mock_get_all.call_count)

    @staticmethod
    def test_display_categories__validate_pass():
        op = workload_ops.DisplayCategoriesOperation()
        op._validate()


class WorkloadDescriptionOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.profilemanager.build_describe_message_for_profiles')
    def test_workload_description_execute_operation__uses_legacy(self, mock_describe, _):
        op = workload_ops.WorkloadDescriptionOperation()
        op.profile_names = ['TEST_PROFILE', 'TEST_PROFILE_2']
        op._execute_operation()
        self.assertEqual(1, mock_describe.call_count)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.describe_profiles')
    def test_workload_description_execute_operation__uses_service(self, mock_describe, _):
        op = workload_ops.WorkloadDescriptionOperation()
        op.profile_names = ['TEST_PROFILE', 'TEST_PROFILE_2']
        op._execute_operation()
        self.assertEqual(1, mock_describe.call_count)

    @staticmethod
    def test_workload_description__validate_pass():
        op = workload_ops.WorkloadDescriptionOperation()
        op._validate()


class StatusOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': '', '--network-check': False,
                                 '--priority': None, '--json': False}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.StatusOperation.check_count_of_workload_admin_users')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._print_node_pool_summary')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.is_password_ageing_enabled')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._execute_operation')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._validate')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._setup')
    def test_status_operation_execute_is__successful(self, mock_setup, mock_validate, mock_execute_op,
                                                     mock_password_age, mock_print_node_pool_sum, mock_users_count):
        with patch('enmutils_int.lib.workload_ops.StatusOperation.'
                   'check_if_enm_accessible') as mock_check_if_enm_accessible:
            with patch('enmutils_int.lib.workload_ops.StatusOperation.'
                       'get_dependent_services_status') as mock_get_dependent_services:
                self.default_arg_dict['--error-type'] = 'ProfileError'
                self.default_arg_dict['--network-check'] = True
                op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
                op.execute()
                self.assertEqual(1, mock_setup.call_count)
                self.assertEqual(1, mock_validate.call_count)
                self.assertEqual(1, mock_execute_op.call_count)
                self.assertEqual(1, mock_password_age.call_count)
                self.assertEqual(1, mock_print_node_pool_sum.call_count)
                self.assertEqual(1, mock_users_count.call_count)
                self.assertEqual(1, mock_check_if_enm_accessible.call_count)
                self.assertEqual(1, mock_get_dependent_services.call_count)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.is_password_ageing_enabled')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.check_if_enm_accessible')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.check_count_of_workload_admin_users')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.get_dependent_services_status')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._validate')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._setup')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._execute_operation')
    @patch('enmutils_int.lib.workload_ops.log')
    def test_status_operation_execute__raises_type_error(self, mock_log, mock_execute_op, *_):
        self.default_arg_dict['--error-type'] = 'ProfileError'
        self.default_arg_dict['--network-check'] = True
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        mock_execute_op.side_effect = Exception
        with self.assertRaises(Exception):
            op.execute()
            self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.check_count_of_workload_admin_users')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._print_node_pool_summary')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.is_password_ageing_enabled')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._execute_operation')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._validate')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._setup')
    def test_status_operation_execute__when_json_response_is_true(self, mock_setup, mock_validate, mock_execute_op,
                                                                  mock_password_age, mock_print_node_pool_sum,
                                                                  mock_users_count):
        with patch('enmutils_int.lib.workload_ops.StatusOperation.'
                   'check_if_enm_accessible') as mock_check_if_enm_accessible:
            with patch('enmutils_int.lib.workload_ops.StatusOperation.'
                       'get_dependent_services_status') as mock_get_dependent_services:
                self.default_arg_dict['--error-type'] = 'ProfileError'
                self.default_arg_dict['--json'] = True
                op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
                op.execute()
                self.assertEqual(1, mock_setup.call_count)
                self.assertEqual(1, mock_validate.call_count)
                self.assertEqual(1, mock_execute_op.call_count)
                self.assertEqual(0, mock_password_age.call_count)
                self.assertEqual(0, mock_print_node_pool_sum.call_count)
                self.assertEqual(0, mock_users_count.call_count)
                self.assertEqual(0, mock_check_if_enm_accessible.call_count)
                self.assertEqual(0, mock_get_dependent_services.call_count)

    @patch('enmutils_int.lib.workload_ops.log')
    def test_status_operation__validate_is_successful_no_error_types(self, mock_log):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = None
        op._validate()
        self.assertFalse(mock_log.logger.info.called)

    @patch('enmutils_int.lib.workload_ops.log')
    def test_status_operation__validate_is_successful(self, mock_log):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = ['PROFILE']
        op._validate()
        self.assertFalse(mock_log.logger.info.called)
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = ['invalid_error']
        op._validate()
        self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_profile_sessions')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.print_duplicate_errors')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.print_log_file_path')
    @patch('enmutils_int.lib.workload_ops.datetime')
    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.ThreadQueue')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_is_successful(
            self, mock_set_active, mock_tq, mock_logger, mock_json, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = [self.mock_profile]
        op.profile_names = ['test_profile']
        mock_tq.return_value.exception_msgs = []
        op.sessions = {'test_profile': 1}
        errors = [['TIMESTAMP', 'Now', 'REASON', 'error', "DUPLICATES", []]]
        op.errors_info = {'TEST_PROFILE': errors}
        op._execute_operation()
        self.assertEqual(mock_logger.info.call_count, 4)
        self.assertEqual(mock_logger.error.call_count, 0)
        self.assertEqual(mock_json.dumps.call_count, 0)

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    @patch('enmutils_int.lib.workload_ops.log')
    def test_status_operation__execute_operation_raises_runtime_error_no_active_profiles(
            self, mock_log, mock_set_active, mock_input_data, mock_network_health_check, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_input_data.return_value.output_network_basic.side_effect = Exception
        mock_set_active.return_value = []
        op.profile_names = ['test_profile']
        with self.assertRaises(RuntimeError):
            op._execute_operation()
            self.assertTrue(mock_log.logger.debug.called)
            self.assertTrue(mock_log.logger.error.called)
            self.assertFalse(mock_network_health_check.called)

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_no_running_profiles(self, mock_set_active, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': None,
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = []
        op.profile_names = ['test_profile']
        with self.assertRaises(RuntimeError):
            op._execute_operation()

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_no_running_profiles_and_priority(
            self, mock_set_active, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = []
        op.profile_names = []
        with self.assertRaises(RuntimeError):
            op._execute_operation()

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.InputData')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_no_running_profiles_no_names(
            self, mock_set_active, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': None,
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = []
        op.profile_names = []
        with self.assertRaises(RuntimeError):
            op._execute_operation()

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.ThreadQueue')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_profile_sessions')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._sort_profiles')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_not_errors_only(self, mock_set_active, *_):
        arg_dict = {'--errors': False, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = [self.mock_profile]
        op.profile_names = ['test_profile']
        op.num_dead_profiles = 1
        with self.assertRaises(RuntimeError):
            op._execute_operation()

    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.ThreadQueue')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_profile_sessions')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._sort_profiles')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_errors_only(self, mock_set_active, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': None,
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = [self.mock_profile]
        op.profile_names = ['test_profile']
        op.num_errored_profiles = 1
        with self.assertRaises(RuntimeError):
            op._execute_operation()

    @patch('enmutils_int.lib.workload_ops.ThreadQueue')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_profile_sessions')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._sort_profiles')
    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_raises_runtime_error_when_profilemanager_stopped(
            self, mock_set_active, mock_logger, mock_json, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': None,
                    '--json': True}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = [self.mock_profile]
        op.profile_names = ['test_profile']
        op.num_errored_profiles = 1
        with self.assertRaises(RuntimeError):
            op._execute_operation()
        self.assertEqual(mock_logger.info.call_count, 0)
        self.assertEqual(mock_logger.error.call_count, 0)
        self.assertEqual(mock_json.dumps.call_count, 0)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.ThreadQueue')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_profile_sessions')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._sort_profiles')
    @patch('enmutils_int.lib.workload_ops.json')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._set_active_status')
    def test_status_operation__execute_operation_when_profilemanager_service_used_and_json_response_is_true(
            self, mock_set_active, mock_logger, mock_json, *_):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': False, '--priority': None,
                    '--json': True}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        mock_set_active.return_value = [{"status": "WARNING", "user_count": 2, "NAME": "NODESEC_15",
                                         "schedule": "Runs at the following times: 08:00 (last run: 15-Feb 18:01:25, "
                                                     "next run: 16-Feb 08:00:00)", "start_time": "10-Feb, 09:06:00",
                                         "pid": 1287, "last_run": "15-Feb, 18:01:25", "num_nodes": 41, "priority": 2,
                                         "state": "RUNNING"}]
        mock_json.dumps.return_value = mock_set_active.return_value
        op.profile_names = ['test_profile']
        op.json_response = True
        op.num_errored_profiles = 1
        op._execute_operation()
        self.assertEqual(mock_logger.info.call_count, 1)
        self.assertEqual(mock_logger.error.call_count, 0)
        self.assertEqual(mock_json.dumps.call_count, 1)

    @patch('enmutils_int.lib.workload_ops.log.logger')
    @patch('enmutils_int.lib.workload_ops.network_health_check')
    @patch('enmutils_int.lib.workload_ops.deployment_info_helper_methods.output_network_basic', side_effect=Exception())
    def test_perform_health_check__catches_exception(self, mock_network_basic, mock_network_health_check, mock_logger):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        op.profile_names = ['test_profile']
        op.perform_health_check()
        self.assertTrue(mock_network_basic.called)
        mock_logger.debug.assert_called_with('Exception raised for InputData: ')
        mock_logger.error.assert_called_with('Unable to get network status. ENM may be experiencing problems.')
        self.assertTrue(mock_network_health_check.called)

    def test_sort_profiles__when_not_sorted_by_runtime(self):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': False, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        profile1 = Mock(NAME="test_profile1")
        profile2 = Mock(NAME="test_profile2")
        op.profiles_to_print = [profile2, profile1]
        expected_sorted = [profile1, profile2]
        op._sort_profiles()
        self.assertEqual(expected_sorted, op.profiles_to_print)

    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_print_profile_info__successful(self, mock_logger_info):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        op._print_profile_info()
        mock_logger_info.assert_called_with(
            '\nNote: The "Nodes" column indicates the number of nodes currently reserved'
            ' by the profile in the workload pool.')

    @patch('enmutils_int.lib.workload_ops.tabulate', return_value="test table")
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._set_active_status', return_value=Mock())
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_print_profile_summary__successful(self, mock_logger, mock_set_active, _):
        arg_dict = {'--errors': True, '--warnings': True, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        op.profiles_to_print = mock_set_active
        op.sessions = {'logged_in': 1, 'total': 1}
        op._print_profile_summary()
        mock_logger.info.assert_called_with('test table')

    @patch('enmutils_int.lib.workload_ops.StatusOperation._print_profile_summary')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._print_profile_info')
    def test_print_status_output__errors_only_and_warnings_set_to_false(self, mock_print_profile_info,
                                                                        mock_print_profile_summary):
        arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                    '--lastrun': True, '--error-type': None, '--network-check': True, '--priority': '1',
                    '--json': False}
        op = workload_ops.StatusOperation(argument_dict=arg_dict)
        op.print_status_output()
        self.assertTrue(mock_print_profile_info.call_count, 1)
        self.assertTrue(mock_print_profile_summary.call_count, 1)

    @ParameterizedTestCase.parameterize(
        ('state', 'status', 'status_counter'),
        [
            ('RUNNING', 'OK', 'num_running_profiles'),
            ('STARTING', 'OK', 'num_starting_profiles'),
            ('COMPLETED', 'OK', 'num_completed_profiles'),
            ('COMPLETED', 'DEAD', 'num_dead_profiles'),
            ('RUNNING', 'ERROR', 'num_errored_profiles'),
            ('RUNNING', 'WARNING', 'num_warning_profiles')
        ]
    )
    def test_status_operation__update_status_counts_is_successful(self, state, status, status_counter):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        self.mock_profile.status = status
        self.mock_profile.state = state
        op._update_status_counts(self.mock_profile, profile_status=self.mock_profile.status)
        self.assertEqual(getattr(op, status_counter), 1)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.print_log_file_path')
    @patch('enmutils_int.lib.workload_ops.datetime')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.print_duplicate_errors')
    def test_status_operation__print_error_info_is_successful(self, mock_print_duplicate, mock_datetime, *_):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        mock_datetime.return_value = Mock()
        errors = [['Now', 'error', []], ['Now', 'error,\n error, error', []]]
        op.errors_info = {'TEST_PROFILE': errors}
        op._print_error_info()
        self.assertTrue(mock_print_duplicate.called)

    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_status_operation_print_log_file_path_is_successful(self, mock_log):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.print_log_file_path('CMIMPORT_TEST')
        self.assertEqual(mock_log.call_count, 2)
        op.print_log_file_path('TEST_PROFILE')
        self.assertEqual(mock_log.call_count, 3)
        op.print_log_file_path('APT_01')
        mock_log.assert_any_call("[Further information: https://eteamspace.internal.ericsson.com"
                                 "/display/ERSD/Starting+APT_01]")

    @patch('enmutils_int.lib.workload_ops.datetime')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_status_operation_print_duplicate_errors_is_successful(self, mock_log, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        error = ['time now', 'error', ['error', 'error']]
        text_wrapper = Mock()
        text_wrapper.wrap.side_effect = ['']
        op.print_duplicate_errors(error, text_wrapper)
        self.assertTrue(mock_log.called)

    @patch('enmutils_int.lib.workload_ops.datetime')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_status_operation_print_duplicate_errors_is_successful_if_no_duplicates(self, mock_log, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.print_duplicate_errors([], Mock())
        self.assertFalse(mock_log.called)

    def test_status_operation__get_errors_by_type(self):
        errors = [{'TIMESTAMP': '2017/02/23 14:30:54', 'REASON': '[\x1b[33mProfileError\x1b[0m] Failed to "GET"\n',
                   "DUPLICATES": ['2018/11/14 14:50:55']},
                  {'TIMESTAMP': '2017/02/23 14:50:55', 'REASON': '[\x1b[33mEnmApplicationError\x1b[0m] Failed to "GET"',
                   "DUPLICATES": ['2018/11/14 14:50:55']}]
        self.default_arg_dict['--error-type'] = 'ProfileError'
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        self.assertEqual([{'DUPLICATES': ['2018/11/14 14:50:55'],
                           'TIMESTAMP': '2017/02/23 14:30:54',
                           'REASON': '[\x1b[33mProfileError\x1b[0m] Failed to "GET"\n'}],
                         op._get_errors_by_type(errors))

    @patch('enmutils_int.lib.workload_ops.log.logger.debug')
    @patch('enmutils_int.lib.workload_ops.get_profile_sessions_info', return_value=({}, []))
    def test_status_operation__set_profile_sessions_success(self, mock_sessions_info, mock_debug):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op._set_profile_sessions([Mock()])
        mock_debug.assert_called_with('Top 10 Session hoarders: []')

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__warnings_only(self, mock_add_output, mock_get_errors, *_):
        profile = Mock(state="RUNNING", status="OK", pid="1234", num_nodes=0, user_count=0, priority=1, schedule="NOW")
        profile.start_time = datetime(2019, 11, 4, 11, 14, 48, 293520)
        profile.NAME = "TEST_00"
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = False
        op.errors_only = False
        op.warnings = True
        op.sessions = {"TEST_00": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        self.assertEqual(0, mock_get_errors.call_count)
        self.assertEqual(1, mock_add_output.call_count)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__errors_only(self, mock_add_output, mock_get_errors, *_):
        profile = Mock(state="RUNNING", status="OK", pid="1234", num_nodes=0, user_count=0, priority=1, schedule="NOW")
        profile.start_time = datetime(2019, 11, 4, 11, 14, 48, 293520)
        profile.NAME = "TEST_00"
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = ["ProfileError"]
        op.verbose = False
        op.errors_only = True
        op.warnings = False
        op.sessions = {"TEST_00": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        self.assertEqual(1, mock_get_errors.call_count)
        self.assertEqual(1, mock_add_output.call_count)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__verbose(self, mock_add_output, mock_get_errors, *_):
        profile = Mock(state="RUNNING", status="OK", pid="1234", num_nodes=0, user_count=0, priority=1, schedule="NOW")
        profile.start_time = datetime(2019, 11, 4, 11, 14, 48, 293520)
        profile.NAME = "TEST_00"
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = True
        op.errors_only = False
        op.warnings = False
        op.sessions = {"TEST_00": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        self.assertEqual(0, mock_get_errors.call_count)
        self.assertEqual(2, mock_add_output.call_count)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__schedule_shows_correct_info_for_completed_profiles(self, *_):
        profile = Mock(NAME="TEST_01", state="COMPLETED", status="OK", pid="1234", num_nodes=0, user_count=0,
                       priority=1, schedule="NOW", start_time=datetime(2020, 11, 10, 9, 8, 7, 654321))
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = False
        op.errors_only = False
        op.warnings = False
        op.sessions = {"TEST_01": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        profile_table_values = ['TEST_01', 'COMPLETED', '\x1b[92mOK\x1b[0m', '10-Nov 09:08:07', '1234', 0, 0, 1, 1,
                                'No further iterations of this profile will occur']
        self.assertEqual([profile_table_values], op.profiles_info_table_values)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__schedule_shows_correct_info_for_dead_profiles(self, *_):
        profile = Mock(NAME="TEST_01", state="STOPPING", status="DEAD", pid="1234", num_nodes=0, user_count=0,
                       priority=1, schedule="NOW", start_time=datetime(2020, 11, 10, 9, 8, 7, 654321))
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = False
        op.errors_only = False
        op.warnings = False
        op.sessions = {"TEST_01": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        profile_table_values = ['TEST_01', 'STOPPING', '\x1b[91mDEAD\x1b[0m', '10-Nov 09:08:07', '1234', 0, 0, 1, 1,
                                'No further iterations of this profile will occur']
        self.assertEqual([profile_table_values], op.profiles_info_table_values)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__schedule_shows_correct_info_for_non_completed_profiles(self, *_):
        profile = Mock(NAME="TEST_01", state="RUNNING", status="OK", pid="1234", num_nodes=0, user_count=0,
                       priority=1, schedule="NOW", start_time=datetime(2020, 11, 10, 9, 8, 7, 654321))
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = False
        op.errors_only = False
        op.warnings = False
        op.sessions = {"TEST_01": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        profile_table_values = ['TEST_01', 'RUNNING', '\x1b[92mOK\x1b[0m', '10-Nov 09:08:07', '1234', 0, 0, 1, 1,
                                'NOW']
        self.assertEqual([profile_table_values], op.profiles_info_table_values)

    @patch('enmutils_int.lib.workload_ops.StatusOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.StatusOperation._update_status_counts')
    @patch('enmutils_int.lib.workload_ops.mutexer.mutex')
    @patch('enmutils_int.lib.workload_ops.StatusOperation._get_errors_by_type')
    @patch('enmutils_int.lib.workload_ops.StatusOperation.add_output_of_errors_or_warnings')
    def test_task_set__schedule_shows_correct_info_for_warning_profiles(self, *_):
        profile = Mock(NAME="TEST_01", state="RUNNING", status="WARNING", pid="1234", num_nodes=0, user_count=0,
                       priority=1, schedule="NOW", start_time=datetime(2020, 11, 10, 9, 8, 7, 654321))
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.error_types = []
        op.verbose = False
        op.errors_only = False
        op.warnings = False
        op.sessions = {"TEST_01": 1}
        op.profiles_info_table_values = []
        op.taskset(profile, op)
        profile_table_values = ['TEST_01', 'RUNNING', '\033[33mWARNING\033[0m', '10-Nov 09:08:07', '1234', 0, 0, 1, 1,
                                'NOW']
        self.assertEqual([profile_table_values], op.profiles_info_table_values)

    @patch('enmutils_int.lib.common_utils.User.get_usernames',
           return_value=[u'LOGVIEWER_01_1113-10500859_u0', u'workload_admin_host', u'workload_admin_host2'])
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_count_of_workload_admin_users__success(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_count_of_workload_admin_users()
        mock_logger.debug.assert_any_call("Checking number of workload administrator users that exist on ENM")
        mock_logger.debug.assert_called_with("Number of workload admins found on ENM: 2\nAll usernames found: "
                                             "[u'workload_admin_host', u'workload_admin_host2']")
        mock_logger.info.assert_called_with("\x1b[91m2 Workload admins currently detected on ENM\x1b[0m")

    @patch('enmutils_int.lib.common_utils.User.get_usernames', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.workload_ops.log.logger.debug')
    def test_check_count_of_workload_admin_users__exception_logged(self, mock_debug, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_count_of_workload_admin_users()
        mock_debug.assert_any_call("Checking number of workload administrator users that exist on ENM")
        mock_debug.assert_called_with('Error occured trying to get all the usernames. Error: Error')

    @patch('enmutils_int.lib.common_utils.User.get_usernames',
           return_value=[u'LOGVIEWER_01_1113-10500859_u0', u'workload_admin_host'])
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_count_of_workload_admin_users__single_admin(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_count_of_workload_admin_users()
        mock_logger.debug.assert_called_with("Number of workload admins found on ENM: 1\nAll usernames found: "
                                             "[u'workload_admin_host']")

    @patch('enmutils_int.lib.workload_ops.check_enm_access', return_value=(False, 'no access'))
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_if_enm_accessible__adds_warning(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        mock_logger.warn.assert_called_once_with('no access')

    @patch('enmutils_int.lib.workload_ops.check_enm_access', return_value=(True, 'enm accessible'))
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_if_enm_accessible__logs_if_enm_accessible(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        self.assertFalse(mock_logger.warn.called)
        mock_logger.debug.assert_called_with('enm accessible')

    @patch('enmutils_int.lib.workload_ops.check_enm_access', return_value=None)
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_if_enm_accessible__does_not_log_if_response_not_tuple(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        self.assertFalse(mock_logger.warn.called)

    @patch('enmutils_int.lib.workload_ops.check_enm_access', side_effect=Exception('some error'))
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_check_if_enm_accessible__logs_exception(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        self.assertFalse(mock_logger.warn.called)
        mock_logger.debug.assert_called_with('Error occured while chekcking password-less access '
                                             'to enm. Error: some error')

    @patch('enmutils_int.lib.workload_ops.ThreadQueue.execute')
    @patch('enmutils_int.lib.workload_ops.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.tabulate')
    def test_get_dependent_services_status__success(self, mock_tabulate, *_):
        workload_ops.SERVICES_NOT_RUNNING = [('test', 'NOK')]
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        op.get_dependent_services_status()
        mock_tabulate.assert_called_with([('test', 'NOK')], headers=['Service Name', 'Service Status'])

    @patch('enmutils_int.lib.workload_ops.ThreadQueue.execute')
    @patch('enmutils_int.lib.workload_ops.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.tabulate')
    def test_get_dependent_services_status__does_not_log_if_all_services_ok(self, mock_tabulate, *_):
        workload_ops.SERVICES_NOT_RUNNING = []
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        op.get_dependent_services_status()
        self.assertFalse(mock_tabulate.called)

    @patch('enmutils_int.lib.workload_ops.commands.getstatusoutput')
    def test_check_service_status__success(self, mock_getoutput):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        not_running = []
        op.check_service_status('service', not_running)
        self.assertListEqual([('service', '\x1b[91mNOK\x1b[0m')], not_running)
        mock_getoutput.assert_called_with('/sbin/service service status')

    @patch('enmutils_int.lib.workload_ops.commands.getstatusoutput', return_value=[False])
    def test_check_service_status__does_not_add_in_not_running(self, mock_getoutput):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.check_if_enm_accessible()
        not_running = []
        op.check_service_status('service', not_running)
        self.assertListEqual([], not_running)
        mock_getoutput.assert_called_with('/sbin/service service status')

    @patch('enmutils_int.lib.workload_ops.check_password_ageing_policy_status', return_value='message')
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_is_password_ageing_enabled__success(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.is_password_ageing_enabled()
        mock_logger.debug.assert_called_once_with('Establishing if ENM Password Ageing Policy is enabled')
        mock_logger.warn.assert_called_once_with('message')

    @patch('enmutils_int.lib.workload_ops.check_password_ageing_policy_status', side_effect=Exception('some error'))
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_is_password_ageing_enabled__logs_exception_without_warning_to_user(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.is_password_ageing_enabled()
        mock_logger.debug.assert_called_with('Error occurred while checking ENM Password Ageing Policy. '
                                             'Error: some error')
        self.assertFalse(mock_logger.warn.called)

    @patch('enmutils_int.lib.workload_ops.check_password_ageing_policy_status', side_effect=HTTPError(
        'ENM is requesting a password change - disable password ageing'), response=Mock())
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_is_password_ageing_enabled__logs_exception_and_warns_user(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.is_password_ageing_enabled()
        mock_logger.debug.assert_called_with('Error occurred while checking ENM Password Ageing Policy. Error: ENM is '
                                             'requesting a password change - disable password ageing')
        mock_logger.warn.assert_called_once_with('ENM is requesting a password change - disable password ageing')

    @patch('enmutils_int.lib.workload_ops.check_password_ageing_policy_status', return_value=None)
    @patch('enmutils_int.lib.workload_ops.log.logger')
    def test_is_password_ageing_enabled__does_not_warn_when_service_can_not_be_used(self, mock_logger, _):
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.is_password_ageing_enabled()
        self.assertFalse(mock_logger.warn.called)

    def test_add_output_of_errors_or_warnings__success(self):
        profile = Mock()
        profile.NAME = "TEST_00"
        issues = [{'DUPLICATES': ['2019/10/24 19:15:50'], 'TIMESTAMP': 'time', 'REASON': "reason"},
                  {'TIMESTAMP': 'time1', 'REASON': "reason1"}]
        op = workload_ops.StatusOperation(argument_dict=self.default_arg_dict)
        op.total = 10
        op.add_output_of_errors_or_warnings(profile, issues)
        expected = [['time', 'reason', ['2019/10/24 19:15:50']], ['time1', 'reason1']]
        self.assertEqual(op.errors_info.get("TEST_00"), expected)


class ExportProfileOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.config')
    def test_export_operation__validate_is_successful(self, _):
        arg_dict = {'PROFILES': 'all', '--category': True}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op.active_profiles = {'test_01': Mock()}
        op.categories = ['test']
        op._validate()

    @patch('enmutils_int.lib.workload_ops.config')
    def test_export_operation__validate_is_successful_with_profile_names(self, _):
        arg_dict = {'PROFILES': 'all', '--category': False}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op.profile_names = ['test_01']
        op.active_profiles = {'test_01': Mock()}
        op._validate()

    @patch('enmutils_int.lib.workload_ops.config')
    def test_export_operation__validate_is_successful_no_match_categories(self, _):
        arg_dict = {'PROFILES': 'all', '--category': True}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op.active_profiles = {'test_01': Mock()}
        op.categories = ['cmimport']
        op._validate()

    @patch('enmutils_int.lib.workload_ops.config')
    def test_export_operation__validate_raises_runtime_error(self, _):
        arg_dict = {'PROFILES': 'test_01', '--category': False}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op.active_profiles = {'test_02': Mock()}
        op.profile_names = ['test_01']
        with self.assertRaises(RuntimeError):
            op._validate()

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.profilemanager.generate_export_file')
    def test_export_operation_execute_operation__uses_legacy(self, mock_export_file, _):
        arg_dict = {'PROFILES': 'test_01', '--category': False}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op._execute_operation()
        self.assertEqual(1, mock_export_file.call_count)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.export_profiles')
    @patch('enmutils_int.lib.workload_ops.profilemanager.generate_export_file')
    def test_export_operation_execute_operation__uses_service(self, mock_export_file, mock_adapator, _):
        arg_dict = {'PROFILES': 'test_01', '--category': False}
        op = workload_ops.ExportProfileOperation(arg_dict)
        op._execute_operation()
        self.assertEqual(0, mock_export_file.call_count)
        self.assertEqual(1, mock_adapator.call_count)


class RestartProfilesOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    @patch('enmutils_int.lib.workload_ops.StartOperation')
    @patch('enmutils_int.lib.workload_ops.load_mgr.wait_for_stopping_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation')
    def test_restart_operation_execute_is_successful(self, mock_stop_op, mock_wait, mock_start, _):
        arg_dict = {'--force-stop': False, '--supported': False, '--updated': False, '--jenkins': False}
        op = workload_ops.RestartProfilesOperation(arg_dict)
        op.execute()
        self.assertTrue(mock_stop_op.called)
        self.assertTrue(mock_wait.called)
        self.assertTrue(mock_start.called)

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    @patch('enmutils_int.lib.workload_ops.load_mgr.wait_for_stopping_profiles')
    @patch('enmutils_int.lib.workload_ops.StartOperation')
    @patch('enmutils_int.lib.workload_ops.load_mgr.get_updated_active_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation')
    def test_restart_operation_execute_is_successful_if_updated(self, mock_stop_op, mock_get_updated, mock_start, *_):
        arg_dict = {'--force-stop': False, '--supported': False, '--updated': True, '--jenkins': False}
        op = workload_ops.RestartProfilesOperation(arg_dict)
        mock_get_updated.return_value = [self.mock_profile]
        op.execute()
        self.assertTrue(mock_stop_op.called)
        self.assertTrue(mock_start.called)

    @patch('enmutils_int.lib.workload_ops.WorkloadOperation._setup')
    @patch('enmutils_int.lib.workload_ops.load_mgr.wait_for_stopping_profiles')
    @patch('enmutils_int.lib.workload_ops.StartOperation')
    @patch('enmutils_int.lib.workload_ops.StopOperation')
    def test_restart_operation_execute_is_successful_if_all_supported(self, mock_stop_op, mock_start, *_):
        arg_dict = {'--force-stop': False, '--supported': True, '--updated': False, '--release-exclusive-nodes': True,
                    '--jenkins': True}
        op = workload_ops.RestartProfilesOperation(arg_dict, profile_names=['test_01'])
        op.execute()
        self.assertTrue(mock_stop_op.called)
        self.assertTrue(mock_start.called)

    @patch('enmutils_int.lib.workload_ops.load_mgr.get_active_profile_names')
    def test_restart_operation__validate_is_successful(self, mock_get_active):
        arg_dict = {'--force-stop': False, '--supported': False, '--updated': False, '--jenkins': False}
        op = workload_ops.RestartProfilesOperation(arg_dict)
        op._validate()
        self.assertTrue(mock_get_active.called)
        op.profile_names = ['test_01', 'test_02']
        op.active_profiles = {'test_01': Mock(), 'test_02': Mock()}
        op._validate()
        self.assertTrue(mock_get_active.called)
        op.active_profiles = {}
        with self.assertRaises(RuntimeError):
            op._validate()
        self.assertTrue(mock_get_active.called)

    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    @patch('enmutils_int.lib.workload_ops.load_mgr.get_updated_active_profiles')
    def test_restart_operation__restart_updated_logs_no_profile_names(self, mock_get_updated, mock_log):
        arg_dict = {'--force-stop': False, '--supported': False, '--updated': False, '--jenkins': False}
        op = workload_ops.RestartProfilesOperation(arg_dict)
        mock_get_updated.return_value = []
        op._restart_updated()
        mock_log.assert_called_with('\x1b[33mNo profiles found to update.\x1b[0m')


class StopOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.StopOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.shell.Command')
    @patch('enmutils_int.lib.workload_ops.nodemanager_adaptor.update_nodes_cache_on_request')
    @patch('enmutils_int.lib.workload_ops.shell.run_local_cmd')
    @patch('enmutils_int.lib.workload_ops.common_utils.ensure_all_daemons_are_killed')
    def test_initial_install_teardown__removes_old_directory_and_persistence(self, mock_kill_all, mock_run_local,
                                                                             mock_update, *_):
        op = workload_ops.StopOperation({})
        op._initial_install_teardown()
        self.assertEqual(1, mock_kill_all.call_count)
        self.assertEqual(1, mock_update.call_count)
        self.assertEqual(2, mock_run_local.call_count)

    @patch('enmutils_int.lib.workload_ops.StopOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.log.yellow_text')
    @patch('enmutils_int.lib.workload_ops.load_mgr.get_active_foundation_profiles')
    def test_remove_foundation_profiles__removes_foundation_level_profiles(self, mock_get_active_foundation,
                                                                           mock_yellow, _):
        op = workload_ops.StopOperation({})
        setattr(op, 'valid_profiles', {"TEST_SETUP": "TEST_SETUP", "TEST_00": "TEST_00"})
        mock_get_active_foundation.return_value = ["TEST_SETUP"]
        op._remove_foundation_profiles()
        mock_yellow.assert_called_with('The following profiles are FOUNDATION profiles and will need to be stopped '
                                       'with --force-stop option. [TEST_SETUP]')

    @patch('enmutils_int.lib.workload_ops.StopOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.log.yellow_text')
    @patch('enmutils_int.lib.workload_ops.load_mgr.get_active_foundation_profiles')
    def test_remove_foundation_profiles__only_logs_if_foundation_removed(self, mock_get_active_foundation,
                                                                         mock_yellow, _):
        op = workload_ops.StopOperation({})
        setattr(op, 'valid_profiles', {"TEST_SETUP": "TEST_SETUP", "TEST_00": "TEST_00"})
        mock_get_active_foundation.return_value = []
        op._remove_foundation_profiles()
        self.assertEqual(0, mock_yellow.call_count)

    @patch('enmutils_int.lib.workload_ops.StopOperation.schedule_stop_by_group')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_execute_operation__is_successful(self, mock_load_mgr, mock_schedule):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": True, "--priority": '1', "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile = Mock()
        profile.NAME = 'TEST_02'
        op.valid_profiles = {'TEST_01': self.mock_profile, 'TEST_02': profile}
        op._execute_operation()

        mock_load_mgr.deallocate_all_exclusive_nodes.assert_called_with([], stop_all=False, service_to_be_used=False)
        self.assertEqual(1, mock_schedule.call_count)

    @patch('enmutils_int.lib.workload_ops.StopOperation._initial_install_teardown')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_stop_operation_execute_is_successful_with_initial_install(
            self, mock_load_mgr, mock_initial_install_teardown):
        args_dict = {"--schedule": None, "--force-stop": True, "--initial-install-teardown": True,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op._execute_operation()
        self.assertTrue(mock_initial_install_teardown.called)
        self.assertFalse(mock_load_mgr.deallocate_all_exclusive_nodes.called)

    @patch('enmutils_int.lib.workload_ops.StopOperation.group_profiles_by_category',
           return_value={"TEST": {"Test": Mock()}})
    @patch('enmutils_int.lib.workload_ops.workload_schedule.WorkloadSchedule.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.ThreadQueue.execute')
    def test_schedule_stop_by_group__creates_and_executes_threads(self, mock_execute, *_):
        args_dict = {"--schedule": None, "--force-stop": True, "--initial-install-teardown": True,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.schedule_stop_by_group()
        self.assertEqual(1, mock_execute.call_count)

    def test_stop_func__initiates_stop(self):
        args_dict = {"--schedule": None, "--force-stop": True, "--initial-install-teardown": True,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        scheduler = Mock()
        op = workload_ops.StopOperation(args_dict)
        op.stop_func(scheduler)
        self.assertEqual(1, scheduler.stop.call_count)

    def test_group_profiles_by_category__success(self):
        args_dict = {"--schedule": None, "--force-stop": True, "--initial-install-teardown": True,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_name, profile_name1, profile_name2 = "TEST_TEST_00", "TEST_01", "TEST_SETUP"
        profile = Mock()
        op.valid_profiles = {profile_name: profile, profile_name1: profile, profile_name2: profile}
        expected = {"TEST_TEST": {profile_name: profile}, "TEST": {profile_name1: profile, profile_name2: profile}}
        self.assertDictEqual(expected, op.group_profiles_by_category())

    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.StopOperation._remove_foundation_profiles')
    def test_stop_operation__validate_raises_runtime_error(self, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.active_profiles = {}
        with self.assertRaises(RuntimeError):
            op._validate()

    @patch('enmutils_int.lib.workload_ops.StopOperation._set_active_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation._remove_foundation_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation._workload_stop_checks',
           return_value=tuple((["TEST_01"], ["TEST_02"], [])))
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils.lib.log.logger.info')
    def test_stop_operation__alert_user_profiles_not_started(self, mock_logger_info, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.active_profiles = {'TEST_01': self.mock_profile}
        op.profile_names = ['TEST_01', 'TEST_02']
        op._validate()
        mock_logger_info.assert_called_with("The following profiles were not started: [TEST_02]")

    @patch('enmutils_int.lib.workload_ops.StopOperation._set_active_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation._remove_foundation_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation._workload_stop_checks',
           return_value=tuple((["TEST_01"], [], ["TEST_02"])))
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils.lib.log.logger.warn')
    def test_stop_operation__alert_user_profiles_were_killed(self, mock_logger_warn, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.active_profiles = {'TEST_01': self.mock_profile}
        op.profile_names = ['TEST_01', 'TEST_02']
        op._validate()
        mock_logger_warn.assert_called_with(
            "The following profiles were killed due to profile missing from persistence: [TEST_02]. "
            "For more information see debug logs and profile daemon logs.\n"
            "Logs directory: {0}".format(get_log_dir()))

    @patch('enmutils_int.lib.workload_ops.StopOperation._remove_foundation_profiles')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_stop_operation__validate_with_priority(self, mock_load_mgr, _):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": True, "--priority": '1', "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict, profile_names=['TEST_01'])
        mock_load_mgr.get_profiles_with_priority.return_value = ['TEST_01']
        mock_load_mgr.workload_stop_checks.return_value = tuple([['TEST_01'], [], []])
        op.ignored_profiles = ['TEST_01']
        op.active_profiles = {'TEST_01': self.mock_profile}
        op._validate()

    @patch('enmutils_int.lib.workload_ops.workload_schedule.WorkloadSchedule')
    def test_stop_operation__execute_operation_is_successful_no_valid_profiles(self, mock_schedule):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.valid_profiles = []
        op._execute_operation()
        self.assertFalse(mock_schedule.called)

    @patch('enmutils_int.lib.workload_ops.load_mgr.get_active_profile_names', return_value=["TEST_01", "TEST_02"])
    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid', return_value=["1234"])
    @patch('enmutils_int.lib.workload_ops.load_mgr.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.workload_ops.StopOperation._determine_stopping_action')
    def test_workload_stop_checks__profile_daemon_running(self, mock_stopping_action, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)

        profile_names = ["TEST_01", "TEST_02"]
        op._workload_stop_checks(profile_names)
        mock_stopping_action.assert_called_with('TEST_02', ([], [], []), True, True, True)

    @patch('enmutils_int.lib.workload_ops.load_mgr.get_active_profile_names', return_value=["TEST_01", "TEST_02"])
    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid', return_value=[])
    @patch('enmutils_int.lib.workload_ops.load_mgr.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.workload_ops.StopOperation._determine_stopping_action')
    def test_workload_stop_checks__no_profile_daemon_running(self, mock_stopping_action, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_names = ["TEST_01", "TEST_02"]
        op._workload_stop_checks(profile_names)
        mock_stopping_action.assert_called_with('TEST_02', ([], [], []), True, True, False)

    def test_determine_stopping_action__profile_in_ideal_state(self):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_state_lists = tuple([[], [], []])
        profile_persisted = True
        in_active_list = True
        profile_name = 'TEST_01'
        op._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list, True)
        self.assertEqual(['TEST_01'], profile_state_lists[0])

    def test_determine_stopping_action__profile_not_started(self):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_state_lists = tuple([[], [], []])
        profile_persisted = False
        in_active_list = False
        profile_name = 'TEST_01'
        op._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list, False)
        self.assertEqual(['TEST_01'], profile_state_lists[1])

    @patch('enmutils_int.lib.workload_ops.remove_profile_from_active_workload_profiles')
    @patch('enmutils_int.lib.workload_ops.load_mgr.kill_profile_daemon_process')
    def test_determine_stopping_action__profile_not_persisted_and_process_running_and_in_active_profiles(
            self, mock_kill_profile, mock_remove_profile_from_active):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_state_lists = tuple([[], [], []])
        profile_persisted = False
        in_active_list = True
        profile_name = 'TEST_01'
        op._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list, True)
        mock_kill_profile.assert_called()
        mock_remove_profile_from_active.assert_called()
        self.assertEqual(['TEST_01'], profile_state_lists[2])

    @patch('enmutils_int.lib.workload_ops.remove_profile_from_active_workload_profiles')
    @patch('enmutils_int.lib.workload_ops.load_mgr.kill_profile_daemon_process')
    def test_determine_stopping_action__profile_not_persisted_and_not_in_active_profiles_and_process_running(
            self, mock_kill_profile, mock_remove_profile_from_active):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_state_lists = tuple([[], [], []])
        profile_persisted = False
        in_active_list = False
        profile_name = 'TEST_01'
        op._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list, True)
        mock_kill_profile.assert_called()
        self.assertEqual(0, mock_remove_profile_from_active.call_count)
        self.assertEqual(['TEST_01'], profile_state_lists[2])

    @patch('enmutils_int.lib.workload_ops.add_profile_to_active_workload_profiles')
    def test_determine_stopping_action__profile_persited_but_not_in_active_list(
            self, mock_add_profile_to_active_profiles):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        profile_state_lists = tuple([[], [], []])
        profile_persisted = True
        in_active_list = False
        profile_name = 'TEST_01'
        op._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list, True)
        self.assertEqual(1, mock_add_profile_to_active_profiles.call_count)
        self.assertEqual(['TEST_01'], profile_state_lists[0])

    @patch('enmutils_int.lib.workload_ops.add_profile_to_active_workload_profiles')
    @patch('enmutils_int.lib.workload_ops.remove_profile_from_active_workload_profiles')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @ParameterizedTestCase.parameterize(
        ("profile_state", "profile_states_list"),
        [
            ([False, False, False], ([], ['TEST_01'], [])),
            ([False, False, True], ([], [], ['TEST_01'])),
            ([False, True, False], ([], ['TEST_01'], [])),
            ([False, True, True], ([], [], ['TEST_01'])),
            ([True, False, False], (['TEST_01'], [], [])),
            ([True, False, True], (['TEST_01'], [], [])),
            ([True, True, False], (['TEST_01'], [], [])),
            ([True, True, True], (['TEST_01'], [], []))
        ]
    )
    def test_determine_stopping_action__all_inputs(self, profile_state, profiles_states_list, *_):
        args_dict = {"--schedule": None, "--force-stop": False, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": False, "--priority": None, "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        starting_profile_states_list = tuple([[], [], []])
        op._determine_stopping_action('TEST_01', starting_profile_states_list, profile_state[0], profile_state[1],
                                      profile_state[2])
        self.assertEqual(profiles_states_list, starting_profile_states_list)

    @patch('enmutils_int.lib.workload_ops.persistence.get_all_keys', return_value=["EXCLUSIVE-ALLOCATED"])
    @patch('enmutils_int.lib.workload_ops.load_mgr.get_profiles_with_priority')
    @patch('enmutils_int.lib.workload_ops.StopOperation._workload_stop_checks', return_value=(["Valid"], [], []))
    @patch('enmutils_int.lib.workload_ops.StopOperation._set_active_profiles')
    @patch('enmutils_int.lib.workload_ops.StopOperation._remove_foundation_profiles')
    @patch('enmutils_int.lib.workload_ops.persistence.remove')
    def test_stop_operation_validate__force_stop_priority(self, mock_remove, *_):
        args_dict = {"--schedule": None, "--force-stop": True, "--initial-install-teardown": False,
                     "--release-exclusive-nodes": True, "--priority": "1", "PROFILES": ["all"]}
        op = workload_ops.StopOperation(args_dict)
        op.active_profiles = {}
        op._validate()
        self.assertEqual(1, mock_remove.call_count)


class StartOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid')
    @patch('enmutils_int.lib.workload_ops.StartOperation.check_if_profile_active_and_loadable_from_persistence')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_remove_already_started_profiles__profiles_already_running(self, mock_logger_info, mock_remove, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': True,
                     '--no-network-size-check': False}
        profile_obj = Mock()
        profile_obj.state = "COMPLETED"
        mock_remove.return_value = (True, profile_obj)
        op = workload_ops.StartOperation(args_dict, ['TEST_01', 'TEST_02'])
        op._remove_already_started_profiles()
        self.assertEqual(1, mock_logger_info.call_count)

    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid', return_value=[])
    @patch('enmutils_int.lib.workload_ops.StartOperation.check_if_profile_active_and_loadable_from_persistence')
    @patch('enmutils_int.lib.workload_ops.log.logger.warn')
    def test_remove_already_started_profiles__no_process_running_but_profile_persisted_without_completed_state(
            self, mock_logger_warn, mock_remove, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': True,
                     '--no-network-size-check': False}
        mock_profile = Mock()
        mock_profile.state = 'RUNNING'
        mock_remove.return_value = (True, mock_profile)

        op = workload_ops.StartOperation(args_dict, ['TEST_01', 'TEST_02'])
        op.ignored_profiles = ['TEST_02']
        op._remove_already_started_profiles()
        self.assertEqual(1, mock_logger_warn.call_count)

    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid', return_value=[])
    @patch('enmutils_int.lib.workload_ops.StartOperation.check_if_profile_active_and_loadable_from_persistence')
    @patch('enmutils_int.lib.workload_ops.log.logger.warn')
    def test_remove_already_started_profiles__no_process_running_but_profile_persisted_with_completed_state(
            self, mock_logger_warn, mock_remove, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': True,
                     '--no-network-size-check': False}
        mock_profile = Mock()
        mock_profile.state = 'COMPLETED'
        mock_remove.return_value = (True, mock_profile)

        op = workload_ops.StartOperation(args_dict, ['TEST_01', 'TEST_02'])
        op._remove_already_started_profiles()
        self.assertEqual(0, mock_logger_warn.call_count)

    @patch('enmutils_int.lib.workload_ops.process.get_profile_daemon_pid', return_value=[])
    @patch('enmutils_int.lib.workload_ops.StartOperation.check_if_profile_active_and_loadable_from_persistence',
           return_value=(False, None))
    @patch('enmutils_int.lib.workload_ops.log.logger.warn')
    def test_remove_already_started_profiles__profiles_not_running_and_not_in_persistence(self, mock_logger_warn, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': True,
                     '--no-network-size-check': False}

        op = workload_ops.StartOperation(args_dict, ['TEST_01', 'TEST_02'])
        op._remove_already_started_profiles()
        self.assertEqual(0, mock_logger_warn.call_count)

    @patch('enmutils_int.lib.workload_ops.StartOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.persistence.has_key', return_value=False)
    def test_check_if_profile_active_and_loadable_from_persistence__returns_none_type_if_not_found(self, *_):
        op = workload_ops.StartOperation({})
        op.active_profiles = ["TEST_01"]
        in_active, profile_obj = op.check_if_profile_active_and_loadable_from_persistence('TEST_00')
        self.assertIsNone(profile_obj)
        self.assertFalse(in_active)

    @patch('enmutils_int.lib.workload_ops.StartOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.workload_ops.persistence.get', return_value=None)
    @patch('enmutils_int.lib.workload_ops.profile_manager.ProfileManager')
    def test_check_if_profile_active_and_loadable_from_persistence__calls_remove_if_profile_none(self, mock_remove, *_):
        op = workload_ops.StartOperation({})
        op.active_profiles = ["TEST_01"]
        op.check_if_profile_active_and_loadable_from_persistence('TEST_00')
        self.assertEqual(1, mock_remove.return_value.remove_corrupted_profile_keys_and_update_active_list.call_count)

    @patch('enmutils_int.lib.workload_ops.StartOperation.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.workload_ops.persistence.get', return_value=Mock())
    @patch('enmutils_int.lib.workload_ops.profile_manager.ProfileManager')
    def test_check_if_profile_active_and_loadable_from_persistence__returns_profile_if_loadable(self, mock_remove, *_):
        op = workload_ops.StartOperation({})
        op.active_profiles = ["TEST_01"]
        in_active, profile_obj = op.check_if_profile_active_and_loadable_from_persistence('TEST_01')
        self.assertEqual(0, mock_remove.return_value.remove_corrupted_profile_keys_and_update_active_list.call_count)
        self.assertIsNotNone(profile_obj)
        self.assertTrue(in_active)

    @patch('enmutils_int.lib.workload_ops.RestartProfilesOperation')
    @patch('enmutils_int.lib.workload_ops.deployment_info_helper_methods.output_network_basic')
    @patch('enmutils_int.lib.workload_ops.config.set_prop')
    @patch('enmutils_int.lib.workload_ops.StartOperation._allocate_nodes_to_exclusive_profiles')
    @patch('enmutils_int.lib.workload_ops.workload_schedule.WorkloadSchedule')
    def test_execute_operation__in_startoperation_is_successful(
            self, mock_schedule, mock_allocate_nodes_to_exclusive_profiles, mock_set, *_):
        args_dict = {'--schedule': None, '--conf': 'path', '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profiles = ["TEST_PROFILE_01", "TEST_PROFILE_02"]
        op = workload_ops.StartOperation(args_dict, profile_names=profiles)
        op.dependent_profiles = ["NHM_03", "NHM_04"]
        op._execute_operation()
        self.assertEqual(1, mock_schedule.return_value.start.call_count)
        self.assertEqual(1, mock_allocate_nodes_to_exclusive_profiles.call_count)
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils_int.lib.workload_ops.deployment_info_helper_methods.output_network_basic')
    @patch('enmutils_int.lib.workload_ops.StartOperation._allocate_nodes_to_exclusive_profiles')
    @patch('enmutils_int.lib.workload_ops.workload_schedule.WorkloadSchedule')
    def test_execute_operation__in_startoperation_is_successful_if_no_exclusive_set(
            self, mock_schedule, mock_allocate_nodes_to_exclusive_profiles, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': True,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profiles = ["TEST_PROFILE_01", "TEST_PROFILE_02"]
        op = workload_ops.StartOperation(args_dict, profile_names=profiles)
        op._execute_operation()
        self.assertTrue(mock_schedule.return_value.start.called)
        self.assertFalse(mock_allocate_nodes_to_exclusive_profiles.called)

    @patch('enmutils_int.lib.workload_ops.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.workload_ops.node_pool_mgr.get_pool')
    @patch('enmutils_int.lib.workload_ops.StartOperation._allocate_exclusive_nodes')
    def test_allocate_nodes_to_exclusive_profiles__in_startoperation_is_successful_if_service_not_used(
            self, mock_allocate_exclusive_nodes, mock_get_pool, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profiles = ["TEST_PROFILE_01", "TEST_PROFILE_02"]
        op = workload_ops.StartOperation(args_dict, profile_names=profiles)
        op.nodemanager_service_to_be_used = False
        mock_get_pool.return_value.nodes = [Mock()]

        op._allocate_nodes_to_exclusive_profiles()

        mock_allocate_exclusive_nodes.assert_called_with(profile_list=profiles, service_to_be_used=False)

    @patch('enmutils_int.lib.workload_ops.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.workload_ops.nodemanager_adaptor.get_list_of_nodes_from_service', return_value=[Mock()])
    @patch('enmutils_int.lib.workload_ops.StartOperation._allocate_exclusive_nodes')
    def test_allocate_nodes_to_exclusive_profiles__in_startoperation_is_successful_if_service_is_used(
            self, mock_allocate_exclusive_nodes, mock_get_list_of_nodes_from_service, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profiles = ["TEST_PROFILE_01", "TEST_PROFILE_02"]
        op = workload_ops.StartOperation(args_dict, profile_names=profiles)
        op.nodemanager_service_to_be_used = True
        op.no_exclusive = False

        op._allocate_nodes_to_exclusive_profiles()

        mock_allocate_exclusive_nodes.assert_called_with(profile_list=profiles, service_to_be_used=True)
        mock_get_list_of_nodes_from_service.assert_called_with(node_attributes=["node_id", "profiles"])

    # _validate test cases
    def test_validate__in_startoperation_raises_runtime_error_new_only(self, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': True,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict)
        op.profile_names = []
        with self.assertRaises(RuntimeError):
            op._validate()

    def test_validate__in_startoperation_raises_runtime_error_updated(self, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': True,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict)
        with self.assertRaises(RuntimeError):
            op._validate()

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_validate__in_startoperation_is_successful(
            self, mock_persistence, mock_load_mgr, mock_categorize, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict)
        mock_persistence.get_all_keys.return_value = ['EXCLUSIVE-ALLOCATED']
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op.supported_profiles = profile_list
        op.ignored_profiles = ['TEST_03']
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        self.mock_profile.SUPPORTED = True
        mock_categorize.return_value = [], [], [], []
        op.valid_profiles = {'TEST_01': self.mock_profile, 'TEST_02': self.mock_profile, 'TEST_03': self.mock_profile}
        op._validate()
        self.assertTrue(mock_persistence.remove.called)

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_validate__in_startoperation_raises_runtime_error_no_supported_profile_names(
            self, mock_persistence, mock_load_mgr, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict)
        mock_persistence.get_all_keys.return_value = []
        op.supported_profiles = []
        with self.assertRaises(RuntimeError):
            op._validate()
            self.assertFalse(mock_load_mgr.called)

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_validate__in_startoperation_raises_runtime_error_cloud_unsupported(self, mock_persistence, mock_load_mgr,
                                                                                mock_categorize, mock_log, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profile_list = ['TEST_01', 'TEST_02']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        mock_persistence.get_all_keys.return_value = ['EXCLUSIVE-ALLOCATED']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        self.mock_profile.SUPPORTED = True
        self.mock_profile.CLOUD_SUPPORTED = False
        mock_categorize.return_value = [], [], [], []
        with self.assertRaises(RuntimeError):
            op._validate()
            mock_log.assert_called_with("Skipping unsupported profile(s) in cloud deployment "
                                        "The following profiles were not started:")

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.persistence')
    def test_validate__in_startoperation_raises_runtime_error_physical_unsupported(self, mock_persistence,
                                                                                   mock_load_mgr, mock_categorize,
                                                                                   mock_log, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        profile_list = ['TEST_01', 'TEST_02']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        mock_persistence.get_all_keys.return_value = ['EXCLUSIVE-ALLOCATED']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        self.mock_profile.SUPPORTED = True
        self.mock_profile.PHYSICAL_SUPPORTED = False
        mock_categorize.return_value = [], [], [], []
        with self.assertRaises(RuntimeError):
            op._validate()
            mock_log.assert_called_with("Skipping unsupported profile(s) in physical deployment "
                                        "The following profiles were not started:")

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_validate__in_startoperation_cloud_supported(self, mock_load_mgr, mock_categorize, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict, ignored_profiles=['TEST_02'])
        profile_list = ['TEST_01', 'TEST_02']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        profile_2 = Mock()
        profile_2.NAME = 'TEST_02'
        self.mock_profile.SUPPORTED = True
        self.mock_profile.CLOUD_SUPPORTED = True
        mock_categorize.return_value = [], [], [], []
        op.valid_profiles = {'TEST_01': self.mock_profile, 'TEST_02': self.mock_profile, 'TEST_03': self.mock_profile}
        op._validate()

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_validate__in_startoperation_physical_supported(self, mock_load_mgr, mock_categorize, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict, ignored_profiles=['TEST_02'])
        profile_list = ['TEST_01', 'TEST_02']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        profile_2 = Mock()
        profile_2.NAME = 'TEST_02'
        self.mock_profile.SUPPORTED = True
        self.mock_profile.CLOUD_SUPPORTED = False
        self.mock_profile.PHYSICAL_SUPPORTED = True
        mock_categorize.return_value = [], [], [], []
        op.valid_profiles = {'TEST_01': self.mock_profile, 'TEST_02': self.mock_profile, 'TEST_03': self.mock_profile}
        op._validate()

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_validate__in_startoperation_unsupported(self, mock_log, mock_load_mgr, mock_categorize, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict, ignored_profiles=['TEST_02'])
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        self.mock_profile.SUPPORTED = False
        mock_categorize.return_value = ['TEST_01'], ['TEST_01'], ['TEST_02'], ['TEST_03']
        op.valid_profiles = {}
        with self.assertRaises(RuntimeError):
            op._validate()
            mock_log.assert_called_with("Skipping unsupported profile(s) "
                                        "The following profiles were not started:")

    @patch('enmutils_int.lib.workload_ops.StartOperation._remove_already_started_profiles')
    @patch('enmutils_int.lib.workload_ops.persistence')
    @patch('enmutils_int.lib.workload_ops.StartOperation._get_profile_objects_and_categorize')
    @patch('enmutils_int.lib.workload_ops.load_mgr')
    def test_validate__in_startoperation_force_start(self, mock_load_mgr, mock_categorize, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': True, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': False, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': None, '--new-only': False,
                     '--no-network-size-check': False}
        op = workload_ops.StartOperation(args_dict)
        profile_list = ['TEST_01', 'TEST_02']
        op.supported_profiles = profile_list
        mock_load_mgr.get_profiles_with_priority.return_value = profile_list
        mock_categorize.return_value = [], [], [], []
        self.mock_profile.SUPPORTED = True
        mock_categorize.return_value = [], [], [], []
        op.valid_profiles = {'TEST_01': self.mock_profile, 'TEST_02': self.mock_profile, 'TEST_03': self.mock_profile}
        op._validate()

    # _get_profile_objects_and_categorize test cases
    @patch("enmutils_int.lib.workload_ops.cache.has_key")
    @patch("enmutils_int.lib.workload_ops.cache.get")
    @patch("enmutils_int.lib.workload_ops.profile_properties_manager.ProfilePropertiesManager.get_profile_objects")
    @patch('enmutils_int.lib.workload_ops.StartOperation._categorize_profiles')
    def test_get_profile_objects_and_categorize__in_startoperation_is_successful_when_force_is_false(self,
                                                                                                     mock_categorize_profiles,
                                                                                                     *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        mock_categorize_profiles.return_value = [], [], [], []
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        self.assertEqual(op._get_profile_objects_and_categorize([], [], [], []), ([], [], [], []))
        self.assertTrue(mock_categorize_profiles.called)

    @patch("enmutils_int.lib.workload_ops.cache.has_key")
    @patch("enmutils_int.lib.workload_ops.cache.get")
    @patch("enmutils_int.lib.workload_ops.profile_properties_manager.ProfilePropertiesManager.get_profile_objects")
    @patch('enmutils_int.lib.workload_ops.StartOperation._categorize_profiles')
    def test_get_profile_objects_and_categorize__in_startoperation_is_successful_when_force_is_true(self,
                                                                                                    mock_categorize_profiles,
                                                                                                    *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': True, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        mock_categorize_profiles.return_value = [], [], [], ["TEST_01"]
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        op._get_profile_objects_and_categorize([], [], [], [])
        self.assertEqual(op._get_profile_objects_and_categorize([], [], [], []), ([], [], [], []))
        self.assertFalse(mock_categorize_profiles.called)

    # _categorize_profiles test cases
    @patch("enmutils_int.lib.workload_ops.is_host_physical_deployment")
    @patch("enmutils_int.lib.workload_ops.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.workload_ops.cache.is_emp")
    @patch('enmutils_int.lib.workload_ops.StartOperation._categorize_profile')
    def test_categorize_profiles__in_start_operation_is_successful(self, mock_categorize_profile, *_):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        profile1 = Mock()
        profile2 = Mock()
        profile3 = self.mock_profile
        profile1.NAME = 'TEST_01'
        profile2.NAME = 'TEST_02'
        profile3.NAME = 'TEST_03'
        profile1.SUPPORTED = True
        profile2.SUPPORTED = False
        profile3.SUPPORTED = True
        profile_obs = [profile1, profile2, profile3]
        mock_categorize_profile.return_value = [], [], []
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list, ignored_profiles=['TEST_03'])
        self.assertEqual(op._categorize_profiles(profile_obs, [True], [], [], [], []), ([], [], [], ['TEST_02']))
        self.assertTrue(mock_categorize_profile.called)

    @patch("enmutils_int.lib.workload_ops.is_host_physical_deployment", return_value=False)
    @patch("enmutils_int.lib.workload_ops.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.workload_ops.cache.is_emp", return_value=True)
    def test_categorize_profile__in_start_operation_is_successful_when_a_profile_is_not_supported_in_cloud(
            self, mock_is_emp, mock_is_enm_on_cloud_native, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile1 = self.mock_profile
        profile1.NAME = 'TEST_01'
        profile1.SUPPORTED = True
        profile1.CLOUD_SUPPORTED = False
        mock_is_enm_on_cloud_native.return_value = False
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        self.assertEqual(op._categorize_profile(profile1, [], [], []), ([], ['TEST_01'], []))
        self.assertTrue(mock_is_emp.called)
        self.assertFalse(mock_is_enm_on_cloud_native.called)

    @patch("enmutils_int.lib.workload_ops.is_host_physical_deployment", return_value=False)
    @patch("enmutils_int.lib.workload_ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.workload_ops.cache.is_emp", return_value=False)
    def test_categorize_profile__in_start_operation_is_successful_when_a_profile_is_not_supported_in_cloud_native(
            self, mock_is_emp, mock_is_enm_on_cloud_native, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile2 = self.mock_profile
        profile2.NAME = 'TEST_02'
        profile2.SUPPORTED = True
        profile2.CLOUD_NATIVE_SUPPORTED = False
        mock_is_enm_on_cloud_native.return_value = True
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        self.assertEqual(op._categorize_profile(profile2, [], [], []), ([], [], ['TEST_02']))
        self.assertTrue(mock_is_emp.called)
        self.assertTrue(mock_is_enm_on_cloud_native.called)

    @patch("enmutils_int.lib.workload_ops.is_host_physical_deployment")
    @patch("enmutils_int.lib.workload_ops.is_enm_on_cloud_native")
    @patch("enmutils_int.lib.workload_ops.cache.is_emp")
    def test_categorize_profile__in_start_operation_is_successful(self, mock_is_emp,
                                                                  mock_is_enm_on_cloud_native, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile3 = self.mock_profile
        profile3.NAME = 'TEST_03'
        profile3.SUPPORTED = True
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        self.assertEqual(op._categorize_profile(profile3, [], [], []), ([], [], []))
        self.assertTrue(mock_is_emp.called)
        self.assertTrue(mock_is_enm_on_cloud_native.called)

    @patch("enmutils_int.lib.workload_ops.is_host_physical_deployment", return_value=True)
    @patch("enmutils_int.lib.workload_ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.workload_ops.cache.is_emp", return_value=False)
    def test_categorize_profile__in_start_operation_is_successful_when_a_profile_is_not_supported_in_physical(
            self, mock_is_emp, mock_is_enm_on_cloud_native, _):
        args_dict = {'--schedule': None, '--conf': None, '--force': False, '--include': None, '--updated': False,
                     '--release-exclusive-nodes': True, '--network-check': False, '--no-exclusive': False,
                     '--once-before-stability': False, '--priority': '1', '--new-only': False,
                     '--no-network-size-check': False}
        profile2 = self.mock_profile
        profile2.NAME = 'TEST_02'
        profile2.SUPPORTED = True
        profile2.PHYSICAL_SUPPORTED = False
        profile_list = ['TEST_01', 'TEST_02', 'TEST_03']
        op = workload_ops.StartOperation(args_dict, profile_names=profile_list)
        self.assertEqual(op._categorize_profile(profile2, [], [], []), (['TEST_02'], [], []))
        self.assertFalse(mock_is_emp.called)
        self.assertFalse(mock_is_enm_on_cloud_native.called)


class DiffOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.diff_profiles")
    def test_execute_operation__in_diff_operation_is_successful_if_service_is_used(self, mock_diff_profiles, *_):
        args_dict = {'--priority': 1, '--updated': True, '--rpm-version': "1.2.3", '--list-format': True,
                     '--no-ansi': False, '--nodes': False, '--node-poids': False}
        op = workload_ops.DiffOperation(args_dict)

        op._execute_operation()
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": [], "priority": 1, "no_ansi": False, "wl_enm_nodes_diff": False,
                      "wl_enm_poids_diff": False}
        mock_diff_profiles.assert_called_with(**parameters)

    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.workload_ops.profilemanager_helper_methods.diff_profiles")
    def test_execute_operation__in_diff_operation_is_successful_if_service_is_not_used(self, mock_diff_profiles, *_):
        args_dict = {'--priority': 1, '--updated': True, '--rpm-version': "1.2.3", '--list-format': True,
                     '--no-ansi': False, '--nodes': False, '--node-poids': False}
        op = workload_ops.DiffOperation(args_dict)

        op._execute_operation()
        parameters = {"updated": True, "list_format": True, "version": "1.2.3",
                      "profile_names": [], "priority": 1, "no_ansi": False, "wl_enm_nodes_diff": False,
                      "wl_enm_poids_diff": False}
        mock_diff_profiles.assert_called_with(**parameters)

    def test_validate__is_successful(self):
        args_dict = {'--priority': 1, '--updated': True, '--rpm-version': "1.2.3", '--list-format': True,
                     '--no-ansi': False, '--nodes': False, '--node-poids': False}
        op = workload_ops.DiffOperation(argument_dict=args_dict)
        self.assertFalse(op._validate())

    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.workload_ops.profilemanager_helper_methods.diff_profiles")
    def test_execute_operation__in_diff_operation_is_successful_if_nodes_diff_is_true(self, mock_diff_profiles, _):
        args_dict = {'--priority': 0, '--updated': False, '--rpm-version': "", '--list-format': False,
                     '--no-ansi': False, '--nodes': True, '--node-poids': False}
        op = workload_ops.DiffOperation(args_dict)

        op._execute_operation()
        parameters = {"updated": False, "list_format": False, "version": "",
                      "profile_names": [], "priority": 0, "no_ansi": False, "wl_enm_nodes_diff": True,
                      "wl_enm_poids_diff": False}
        mock_diff_profiles.assert_called_with(**parameters)


class CleanPIDUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.log.logger.debug')
    def test_clean_pid__validate(self, mock_debug):
        op = workload_ops.CleanPID()
        op._validate()
        mock_debug.assert_called_with('Skipping validation for clean pid')

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.profilemanager.delete_pid_files')
    def test_clean_pid_execute__is_successful(self, mock_delete_id, _):
        op = workload_ops.CleanPID()
        op.profile_names = ['TEST_01', 'TEST_02']
        op.execute()
        self.assertEqual(1, mock_delete_id.call_count)
        mock_delete_id.assert_called_with(op.profile_names)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.CleanPID.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files')
    @patch('enmutils_int.lib.workload_ops.log.logger.info')
    def test_clean_pid_execute_operation__uses_service(self, mock_info, mock_clear_profile_pid_files, *_):
        op = workload_ops.CleanPID()
        op.profile_names = ['TEST_01', 'TEST_02']
        op._execute_operation()
        self.assertEqual(0, mock_info.call_count)
        mock_clear_profile_pid_files.assert_called_with(op.profile_names)


class ClearErrorsUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False,
                                 '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup')
    @patch('enmutils_int.lib.workload_ops.load_mgr.clear_profile_errors')
    def test_clear_errors__is_successful(self, mock_clear_errors, *_):
        op = workload_ops.ClearErrors()
        op._validate()
        op._execute_operation()
        self.assertTrue(mock_clear_errors.called)

    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.workload_ops.ClearErrors.__init__', return_value=None)
    @patch('enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_exceptions')
    @patch('enmutils_int.lib.workload_ops.load_mgr.clear_profile_errors')
    def test_clear_errors__uses_service(self, mock_clear_errors, mock_clear, *_):
        op = workload_ops.ClearErrors()
        op.profile_names = None
        op._execute_operation()
        self.assertEqual(0, mock_clear_errors.call_count)
        self.assertEqual(1, mock_clear.call_count)

    @patch('enmutils_int.lib.workload_ops.StatusOperation')
    def test_get_workload_operations_is_succesful(self, mock_status):
        workload_ops.get_workload_operations('status', self.default_arg_dict)
        self.assertTrue(mock_status.called)


class WorkloadPoolSummaryOperationUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False, '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._validate")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._setup")
    @patch("enmutils_int.lib.workload_ops.log.logger.info")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._print_node_pool_summary")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._execute_operation")
    def test_execute__in_workloadpoolsummaryoperation_is_successful(
            self, mock_execute_operation, mock_print_node_pool_summary, mock_info, *_):
        op = workload_ops.WorkloadPoolSummaryOperation()
        op.execute()
        self.assertTrue(mock_execute_operation.called)
        self.assertTrue(mock_print_node_pool_summary.called)
        self.assertFalse(mock_info.called)

    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._validate")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._setup")
    @patch("enmutils_int.lib.workload_ops.log.logger.info")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._print_node_pool_summary")
    @patch("enmutils_int.lib.workload_ops.WorkloadPoolSummaryOperation._execute_operation",
           side_effect=Exception("blah"))
    def test_execute__in_workloadpoolsummaryoperation_is_unsuccessful(
            self, mock_execute_operation, mock_print_node_pool_summary, mock_info, *_):
        op = workload_ops.WorkloadPoolSummaryOperation()
        op.print_summary = False
        with self.assertRaises(Exception) as e:
            op.execute()
        self.assertEqual("", e.exception.message)
        self.assertTrue(mock_execute_operation.called)
        self.assertFalse(mock_print_node_pool_summary.called)
        self.assertTrue(mock_info.called)

    def test__execute_operation__raises_notimplementederror(self):
        op = workload_ops.WorkloadPoolSummaryOperation()
        with self.assertRaises(NotImplementedError):
            op._execute_operation()

    def test_validate__is_successful(self):
        op = workload_ops.WorkloadPoolSummaryOperation()
        self.assertFalse(op._validate())


class ListNodesOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.default_arg_dict = {'--errors': False, '--warnings': False, '--total': 0, '--verbose': False,
                                 '--lastrun': False, '--error-type': None, '--network-check': False, '--priority': None}

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.IMPORT_COUNT = 5
        mock_profile.TOTAL_NODES = 10
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.workload_ops.log")
    def test_list_nodes__execute_operation_is_successful_if_no_nodes_in_pool(self, mock_log):
        args_dict = {"IDENTIFIER": "all", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.total_nodes = 0
        op._execute_operation()
        mock_log.logger.warn.assert_called_with("No nodes found in the pool. Please add nodes to the pool.\n")

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_node_info_from_pool")
    @patch("enmutils_int.lib.workload_ops.log")
    def test_list_nodes__execute_operation_is_successful_if_no_service_specified(
            self, mock_log, mock_print_node_info_from_pool):
        args_dict = {"IDENTIFIER": "all", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.total_nodes = 1
        op._execute_operation()
        self.assertFalse(mock_log.logger.info.called)
        self.assertTrue(mock_print_node_info_from_pool.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    @patch("enmutils_int.lib.workload_ops.log")
    def test_list_nodes__execute_operation_is_successful_if_service_specified_and_query_results_in_nodes_found(
            self, mock_log, mock_print_list_of_nodes):
        args_dict = {"IDENTIFIER": "ERBS", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.total_nodes = 1
        op.nodemanager_service_to_be_used = True
        op.node_count_from_query = 1
        node1 = Mock()
        op.nodes_from_query = [node1]
        op._execute_operation()
        self.assertFalse(mock_log.logger.info.called)
        mock_print_list_of_nodes.assert_called_with([node1])

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    @patch("enmutils_int.lib.workload_ops.log")
    def test_list_nodes__execute_operation_is_successful_if_service_specified_and_json_format_specified(
            self, mock_log, mock_print_list_of_nodes):
        args_dict = {"IDENTIFIER": "ERBS", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.total_nodes = 1
        op.nodemanager_service_to_be_used = True
        op.node_count_from_query = 1
        op.nodes_from_query = {"blah": "blah1"}
        op._execute_operation()
        mock_log.logger.info.assert_called_with('{"blah": "blah1"}')
        self.assertFalse(mock_print_list_of_nodes.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_warning_when_no_matching_nodes_found")
    @patch("enmutils_int.lib.workload_ops.log")
    def test_list_nodes__execute_operation_is_successful_if_service_specified_and_query_results_in_no_nodes_found(
            self, mock_log, mock_print_warning_when_no_matching_nodes_found):
        args_dict = {"IDENTIFIER": "ERBS", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.total_nodes = 1
        op.nodemanager_service_to_be_used = True
        op.node_count_from_query = 0
        op._execute_operation()
        self.assertFalse(mock_log.logger.info.called)
        self.assertTrue(mock_print_warning_when_no_matching_nodes_found.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    def test__print_node_info_from_pool__is_successful_for_all_nodes(self, mock__print_list_of_nodes):
        args_dict = {"IDENTIFIER": "all", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        node1 = Mock()
        op.all_nodes = [node1]
        op._print_node_info_from_pool()
        self.assertTrue(mock__print_list_of_nodes.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    @patch("enmutils_int.lib.workload_ops.log")
    def test__print_node_info_from_pool__is_successful_for_all_nodes_if_json_specified(
            self, mock_log, mock__print_list_of_nodes):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        node1 = Mock()
        pool = Mock()
        op.all_nodes = [node1]
        op.pool = pool
        op._print_node_info_from_pool()
        self.assertFalse(mock__print_list_of_nodes.called)
        self.assertTrue(call(pool.jsonify.return_value) in mock_log.logger.info.mock_calls)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    def test__print_node_info_from_pool__is_successful_for_all_nodes_if_no_nodes_found(
            self, mock__print_list_of_nodes):
        args_dict = {"IDENTIFIER": "all", "--json": False, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.all_nodes = []
        op._print_node_info_from_pool()
        self.assertFalse(mock__print_list_of_nodes.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_list_of_nodes")
    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_available_node_names")
    def test__print_node_info_from_pool__is_successful_for_specified_pattern_of_nodes_if_no_nodes_found(
            self, mock_print_available_node_names, mock__print_list_of_nodes):
        args_dict = {"IDENTIFIER": "*ERBS*", "--json": False, "--errored-nodes": False, "--profiles": None}
        pool = Mock()
        pool.grep.return_value.values.return_value = []
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.pool = pool
        op._print_node_info_from_pool()
        self.assertFalse(mock__print_list_of_nodes.called)
        self.assertTrue(mock_print_available_node_names.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_node_information")
    def test_print_list_of_nodes__is_successful_for_nodes_that_match_profiles(self, mock_print_node_information):
        args_dict = {"IDENTIFIER": "ERBS", "--json": True, "--errored-nodes": False,
                     "--profiles": "Profile_01,Profile_03"}
        node1 = Mock(node_id="node1", profiles=["PROFILE_01", "PROFILE_03"])
        node2 = Mock(node_id="node2", profiles=["PROFILE_02", "PROFILE_04"])
        node3 = Mock(node_id="node2", profiles=["PROFILE_03"])

        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_list_of_nodes([node1, node2, node3])
        self.assertTrue(mock_print_node_information.called)

    @patch("enmutils_int.lib.workload_ops.ListNodesOperation._print_node_information")
    def test_print_list_of_nodes__is_successful_if_no_profiles_specified(self, mock_print_node_information):
        args_dict = {"IDENTIFIER": "ERBS", "--json": True, "--errored-nodes": False, "--profiles": None}
        node1 = Mock(node_id="node1", profiles=["PROFILE_01", "PROFILE_03"])
        node2 = Mock(node_id="node2", profiles=["PROFILE_02", "PROFILE_04"])
        node3 = Mock(node_id="node2", profiles=["PROFILE_03"])

        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_list_of_nodes([node1, node2, node3])
        mock_print_node_information.assert_called_with([node1, node2, node3])

    @patch("enmutils_int.lib.workload_ops.log")
    def test_print_available_node_names__is_successful_if_all_nodes_is_set(self, mock_log):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.all_nodes = [Mock(node_id="node1"), Mock(node_id="node2")]
        op._print_available_node_names()
        self.assertTrue(call("node1, node2") in mock_log.logger.info.mock_calls)

    @patch("enmutils_int.lib.workload_ops.log")
    def test_print_available_node_names__is_successful_if_all_nodes_is_not_set(self, mock_log):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.all_nodes = []
        op._print_available_node_names()
        self.assertFalse(mock_log.logger.info.called)

    def test_print_node_pool_summary__is_successful(self):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        self.assertFalse(op._print_node_pool_summary())

    @patch("enmutils_int.lib.workload_ops.log")
    def test_print_node_information__is_successful_if_node_allocated_to_a_profile(self, mock_log):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        node = Mock(node_id="node1", profiles=["PROFILE_01", "PROFILE_02"],
                    mim_version='456', simulation='netsim123')
        profiles = "PROFILE_01, PROFILE_02"
        mock_log.green_text.return_value = profiles
        mock_log.purple_text.return_value = 'node1'
        mock_log.blue_text.return_value = '1.1'
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_node_information([node])
        mock_log.green_text.assert_called_with(profiles)
        self.assertTrue(call(
            "node1 1.1 456 netsim123\n\tACTIVE PROFILES: PROFILE_01, PROFILE_02\n") in mock_log.logger.info.mock_calls)

    @patch("enmutils_int.lib.workload_ops.log")
    @patch("enmutils_int.lib.workload_ops", return_value=['hi', 'you'])
    def test_print_node_information__No_nodes(self, *_):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_node_information([], "Profile")

    @patch("enmutils_int.lib.workload_ops.log")
    @patch("enmutils_int.lib.workload_ops", return_value=['hi', 'you'])
    def test_print_node_information__with_nodes(self, *_):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        node = Mock(node_id="node1", profiles=["PROFILE_01", "PROFILE_02"],
                    mim_version='456', simulation='netsim123')
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_node_information([node], "Profile")

    @patch("enmutils_int.lib.workload_ops.log")
    def test_print_node_information__is_successful_if_node_not_allocated_to_a_profile(self, mock_log):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        node = Mock(node_id="node1", profiles=[], mim_version='456', simulation='netsim123')
        profiles = "NONE"
        mock_log.yellow_text.return_value = profiles
        mock_log.purple_text.return_value = 'node1'
        mock_log.blue_text.return_value = '1.1'
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op._print_node_information([node])
        mock_log.yellow_text.assert_called_with(profiles)
        self.assertTrue(call("node1 1.1 456 netsim123\n\tACTIVE PROFILES: NONE\n") in mock_log.logger.info.mock_calls)

    def test_validate__is_successful(self):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        self.assertFalse(op._validate())

    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation.__init__", return_value=None)
    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup")
    @patch("enmutils_int.lib.workload_ops.nodemanager_adaptor.list_nodes")
    def test_setup__is_successful_if_service_used(self, mock_list_nodes, *_):
        args_dict = {"IDENTIFIER": "*ERBS*", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.nodemanager_service_to_be_used = True
        mock_list_nodes.return_value = (3, 2, {"blah": "blah1"})
        op._setup()
        mock_list_nodes.assert_called_with(node_attributes=["node_id", "profiles", "node_ip", "mim_version",
                                                            "simulation"],
                                           match_patterns="*ERBS*", json_response=True)

    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation.__init__", return_value=None)
    @patch("enmutils_int.lib.workload_ops.WorkloadInfoOperation._setup")
    @patch("enmutils_int.lib.workload_ops.node_pool_mgr.get_pool")
    def test_setup__is_successful_if_service_not_used(self, mock_get_pool, *_):
        args_dict = {"IDENTIFIER": "all", "--json": True, "--errored-nodes": False, "--profiles": None}
        op = workload_ops.ListNodesOperation(argument_dict=args_dict)
        op.nodemanager_service_to_be_used = False
        op._setup()
        self.assertTrue(mock_get_pool.called)


class KillOperationUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

        mock_profile = Mock()
        mock_profile.NAME = 'TEST_01'
        mock_profile.PID = 123
        self.mock_profile = mock_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    def test__execute_operation_validate_raises_error(self, *_):
        op = workload_ops.KillOperation()
        with self.assertRaises(NotImplementedError):
            op._validate()

    @patch("enmutils_int.lib.workload_ops.persistence.get_all_keys",
           return_value={'HA_01': 0, 'SHM_01': 1, 'active_workload_profiles': ['py', 'msg', 'SHM_01']})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=['py', 'msg', 'SHM_01'])
    @patch("enmutils_int.lib.workload_ops.process.get_profile_daemon_pid")
    @patch("enmutils_int.lib.workload_ops.process.kill_process_id")
    @patch("enmutils_int.lib.workload_ops.profilemanager.delete_pid_files")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files")
    def test_execute_operation__success(self, *_):
        op = workload_ops.KillOperation(profile_names=['SHM_01'])
        op._execute_operation()

    @patch("enmutils_int.lib.workload_ops.persistence.get_all_keys", return_value=[])
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=[])
    @patch("enmutils_int.lib.workload_ops.process.get_profile_daemon_pid", return_value=[])
    @patch("enmutils_int.lib.workload_ops.process.kill_process_id", return_value=[])
    @patch("enmutils_int.lib.workload_ops.profilemanager.delete_pid_files", )
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files", return_value=[])
    @patch('enmutils_int.lib.workload_ops.log')
    def test_execute_operation__if_emptylist(self, mock_log, *_):
        op = workload_ops.KillOperation()
        op._execute_operation()
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.workload_ops.persistence.get_all_keys",
           return_value={'HA_01': 0, 'SHM_01': 1, 'active_workload_profiles': ['py', 'msg', 'SHM_01']})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=['py', 'msg', 'SHM_01'])
    @patch("enmutils_int.lib.workload_ops.process.get_profile_daemon_pid", return_value=[123, 456])
    @patch("enmutils_int.lib.workload_ops.process.kill_process_id")
    @patch("enmutils_int.lib.workload_ops.profilemanager.delete_pid_files")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files")
    def test_execute_operation_profile_pid_false(self, mock_profile_pid, *_):
        op = workload_ops.KillOperation(profile_names=['SHM_01'])
        op._execute_operation()
        self.assertFalse(op._execute_operation())
        self.assertTrue(mock_profile_pid)

    @patch("enmutils_int.lib.workload_ops.persistence.get_all_keys",
           return_value={'HA_01': 0, 'SHM_01': 1, 'active_workload_profiles': ['py', 'msg', 'SHM_01']})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=['py', 'msg', 'SHM_01'])
    @patch("enmutils_int.lib.workload_ops.process.get_profile_daemon_pid", return_value=[])
    @patch("enmutils_int.lib.workload_ops.process.kill_process_id")
    @patch("enmutils_int.lib.workload_ops.profilemanager.delete_pid_files")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files")
    def test_execute_operation_profile_pid_True(self, mock_profile_pid, *_):
        op = workload_ops.KillOperation(profile_names=['SHM_01'])
        op._execute_operation()
        self.assertFalse(op._execute_operation())
        self.assertTrue(mock_profile_pid)

    @patch("enmutils_int.lib.workload_ops.persistence.get_all_keys",
           return_value={'HA_01': 0, 'SHM_01': 1, 'active_workload_profiles': ['py', 'msg', 'SHM_01']})
    @patch('enmutils_int.lib.node_pool_mgr.persistence.get', return_value=['py', 'msg', 'SHM_01'])
    @patch("enmutils_int.lib.workload_ops.process.get_profile_daemon_pid")
    @patch("enmutils_int.lib.workload_ops.process.kill_process_id")
    @patch("enmutils_int.lib.workload_ops.profilemanager.delete_pid_files")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.can_service_be_used")
    @patch("enmutils_int.lib.workload_ops.profilemanager_adaptor.clear_profile_pid_files")
    def test_execute_operation__fail(self, *_):
        op = workload_ops.KillOperation(profile_names=['HA_01'])
        op._execute_operation()


if __name__ == '__main__':
    unittest2.main(verbosity=2)
