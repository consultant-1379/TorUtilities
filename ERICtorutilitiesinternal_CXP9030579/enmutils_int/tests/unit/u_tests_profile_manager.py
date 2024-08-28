#!/usr/bin/env python

import unittest2
from enmutils.lib import filesystem, persistence
from enmutils.lib.exceptions import ProfileAlreadyRunning, NoNodesAvailable
from enmutils_int.lib import profile_manager
from enmutils_int.lib.profile import CMImportProfile, Profile
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class ProfileManagerUnitTests(unittest2.TestCase):

    Profile.NAME = "TEST"

    def setUp(self):
        unit_test_utils.setup()
        self.profile_with_nodes = self._get_profiles(num_profiles=1, num_nodes=10)["TEST_00"]
        self.profile_without_nodes = self._get_profiles(num_profiles=2)["TEST_01"]
        self.import_profile = self._get_profiles(num_profiles=3, num_nodes=10, import_profile=True)["TEST_02"]
        self.import_profile_exclusive = self._get_profiles(num_profiles=4, num_nodes=10, exclusive=True, import_profile=True)["TEST_03"]
        self.profile_manager = profile_manager.ProfileManager(Mock())
        profile = Mock()
        profile.NAME = "CMSYNC_01"
        self.profile_mgr = profile_manager.ProfileManager(profile, release_nodes=False)

    def tearDown(self):
        unit_test_utils.tear_down()
        for pid_file in ["/var/tmp/enmutils/daemon/TEST_00.pid", "/var/tmp/enmutils/daemon/TEST_00_stop.pid",
                         "/var/tmp/enmutils/daemon/TEST_01.pid", "/var/tmp/enmutils/daemon/TEST_01_stop.pid",
                         "/var/tmp/enmutils/daemon/TEST_02.pid", "/var/tmp/enmutils/daemon/TEST_02_stop.pid",
                         "/var/tmp/enmutils/daemon/TEST_03.pid", "/var/tmp/enmutils/daemon/TEST_03_stop.pid"]:
            if filesystem.does_file_exist(pid_file):
                filesystem.delete_file(pid_file)

    def _get_profiles(self, num_profiles, num_nodes=None, exclusive=None, import_profile=None):
        profiles = {}
        for i in range(num_profiles):

            profile = Profile()
            if import_profile:
                profile = CMImportProfile()
            # If exclusive = None, alternate whether exclusivity is True or False
            if exclusive is None:
                if i % 2 == 0:
                    profile.EXCLUSIVE = True
            else:
                profile.EXCLUSIVE = exclusive
            profile.NAME = "TEST_0{}".format(i)
            if num_nodes:
                profile.NUM_NODES = {"ERBS": num_nodes}
            profiles[profile.NAME] = profile
        return profiles

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr")
    @patch("enmutils_int.lib.profile_manager.log")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._start")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile")
    def test_start__is_successful_if_services_not_used(
            self, mock_allocate_nodes_to_profile, mock_start, mock_log, mock_node_pool_mgr, *_):
        self.profile_manager.nodes_mgr = mock_node_pool_mgr
        self.profile_manager.start()
        self.assertTrue(mock_start.called)
        self.assertTrue(mock_allocate_nodes_to_profile.called)
        mock_log.logger.debug.assert_called_with("Using legacy architecture for node allocation")

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor")
    @patch("enmutils_int.lib.profile_manager.log")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._start")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile")
    def test_start__is_successful_if_services_used(
            self, mock_allocate_nodes_to_profile, mock_start, mock_log, mock_nodemanager_adaptor, *_):
        self.profile_manager.nodes_mgr = mock_nodemanager_adaptor
        self.profile_manager.start()
        self.assertTrue(mock_start.called)
        self.assertTrue(mock_allocate_nodes_to_profile.called)
        mock_log.logger.debug.assert_called_with("Using services architecture for node allocation")

    @patch("enmutils_int.lib.profile_manager.ProfileManager.checks_profile_is_stopping")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping", return_value=False)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._stop")
    def test_profile_manager_stop_profile__is_successful_if_nodemanager_service_not_used(
            self, mock_stop, mock_node_pool_pgr, *_):
        profile_mgr = profile_manager.ProfileManager(self.profile_with_nodes)
        profile_mgr.stop()
        self.assertEqual(mock_stop.call_count, 1)
        self.assertFalse(profile_mgr.nodemanager_service_can_be_used)
        self.assertEqual(profile_mgr.nodes_mgr, mock_node_pool_pgr)

    @patch("enmutils_int.lib.profile_manager.ProfileManager.checks_profile_is_stopping")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping", return_value=False)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor")
    @patch("enmutils_int.lib.profile_manager.ProfileManager._stop")
    def test_profile_manager_stop_profile__is_successful_if_nodemanager_service_is_used(
            self, mock_stop, mock_nodemanager_adaptor, *_):
        profile_mgr = profile_manager.ProfileManager(self.profile_with_nodes)
        profile_mgr.stop()
        self.assertEqual(mock_stop.call_count, 1)
        self.assertTrue(profile_mgr.nodemanager_service_can_be_used)
        self.assertEqual(profile_mgr.nodes_mgr, mock_nodemanager_adaptor)

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping", return_value=True)
    def test_profile_manager_stop_profile__raises_profilealreadyrunning_error_if_is_already_stopping(self, *_):
        self.assertRaises(ProfileAlreadyRunning, profile_manager.ProfileManager(self.profile_with_nodes).stop)

    @patch('enmutils_int.lib.profile_manager.log.logger.info')
    @patch("enmutils_int.lib.profile_manager.multitasking.UtilitiesDaemon")
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes")
    def test_stop__profile_deallocates_nodes_if_exclusive(self, mock_deallocate_nodes, mock_utilitiesdaemon, mock_info):
        self.profile_with_nodes.EXCLUSIVE = True
        profile_mgr = profile_manager.ProfileManager(self.profile_with_nodes)
        self.assertTrue(profile_mgr._stop())
        self.assertTrue(mock_deallocate_nodes.called)
        mock_utilitiesdaemon.assert_called_with("TEST_00_stop", self.profile_with_nodes, log_identifier="TEST_00",
                                                args=[True])
        self.assertEqual(2, mock_info.call_count)

    @patch("enmutils_int.lib.profile_manager.process.kill_spawned_process")
    @patch('enmutils_int.lib.profile.Profile.running', new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_manager.multitasking.UtilitiesDaemon")
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.profile_manager.process.kill_process_id")
    def test_stop__sends_kill_signal_if_profile_is_running(
            self, mock_kill, mock_deallocate_nodes, mock_utilitiesdaemon, *_):
        profile = Mock(EXCLUSIVE=False)
        profile_manager.ProfileManager(profile)._stop()
        self.assertFalse(mock_deallocate_nodes.called)
        self.assertTrue(mock_kill.called)
        self.assertFalse(mock_utilitiesdaemon.called)

    @patch("enmutils_int.lib.profile_manager.multitasking.UtilitiesDaemon.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_manager.ProfileManager.checks_profile_is_stopping")
    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping', return_value=False)
    @patch("enmutils_int.lib.profile_manager.multitasking.UtilitiesDaemon.start")
    @patch('enmutils_int.lib.profile_manager.persistence.remove')
    def test_profile_manager_stop__removes_cmimport_mo_key_exclusive_and_release_nodes(
            self, mock_remove, mock_start, *_):
        mgr = profile_manager.ProfileManager(self.import_profile_exclusive)
        mgr.nodes_mgr = Mock()
        mgr._stop()
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mgr.nodes_mgr.deallocate_nodes.call_count)
        self.assertEqual(1, mock_start.call_count)

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_manager.ProfileManager.checks_profile_is_stopping")
    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping', return_value=False)
    def test_stop__in_profile_manager_does_not_remove_cmimport_mo_key_if_exclusive_and_not_release_nodes(self, *_):
        persistence.set(self.import_profile_exclusive.NAME + "-mos", self.import_profile_exclusive, -1)
        profile_manager.ProfileManager(self.import_profile_exclusive, release_nodes=False).stop()
        self.assertTrue(persistence.has_key(self.import_profile_exclusive.NAME + "-mos"))

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_manager.ProfileManager.checks_profile_is_stopping")
    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_is_stopping', return_value=False)
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.profile_manager.multitasking.UtilitiesDaemon.start")
    def test_stop__profile_persists_lock(self, *_):
        profile = self._get_profiles(num_profiles=1, num_nodes=10)["TEST_00"]
        profile.NAME = "TEST_LOCK_PROFILE"
        profile_manager.ProfileManager(profile).stop()
        self.assertTrue(persistence.has_key("stop_TEST_LOCK_PROFILE_lock"))
        self.assertRaises(ProfileAlreadyRunning, profile_manager.ProfileManager(profile).stop)

    @patch('enmutils_int.lib.profile_manager.persistence.get')
    @patch("enmutils_int.lib.profile_manager.process.kill_pid")
    @patch("enmutils_int.lib.profile_manager.time.sleep", return_value=0)
    def test_checks_profile_is_stopping__is_successful_if_profile_state_is_stopping(self, mock_sleep, mock_kill_pid,
                                                                                    mock_get):
        profile = Mock(state="STOPPING")
        mock_get.return_value = profile
        profile_mgr = profile_manager.ProfileManager(profile)
        profile_mgr.checks_profile_is_stopping()
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(mock_kill_pid.call_count, 0)

    @patch('enmutils_int.lib.profile_manager.persistence.get', return_value=None)
    @patch("enmutils_int.lib.profile_manager.process.kill_pid")
    @patch("enmutils_int.lib.profile_manager.time.sleep", return_value=0)
    def test_checks_profile_is_stopping__is_successful_if_profile_is_removed(self, mock_sleep, mock_kill_pid, _):
        profile = Mock(state="STOPPING")
        profile_mgr = profile_manager.ProfileManager(profile)
        profile_mgr.checks_profile_is_stopping()
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(mock_kill_pid.call_count, 0)

    @patch('enmutils_int.lib.profile_manager.persistence.get')
    @patch("enmutils_int.lib.profile_manager.process.kill_pid")
    @patch("enmutils_int.lib.profile_manager.time.sleep", return_value=0)
    def test_checks_profile_is_stopping__is_successful_if_profile_state_is_hanging(self, mock_sleep, mock_kill_pid,
                                                                                   mock_get):
        profile = Mock(state="RUNNING")
        mock_get.return_value = profile
        profile_mgr = profile_manager.ProfileManager(profile)
        profile_mgr.checks_profile_is_stopping()
        self.assertEqual(mock_sleep.call_count, 300)
        self.assertEqual(mock_kill_pid.call_count, 1)

    @patch('enmutils_int.lib.profile_manager.persistence.has_key', return_value=False)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch('enmutils_int.lib.profile_manager.ProfileManager.remove_from_active_profiles_list')
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes")
    @patch('enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._start')
    def test_start__deallocates_when_exception_encountered_not_already_running(
            self, mock_start, mock_deallocate_nodes, *_):
        mock_start.side_effect = ValueError("Some exception")
        try:
            self.profile_manager.start()
        except Exception as e:
            self.assertIsInstance(e, ValueError)
        self.assertEqual(mock_deallocate_nodes.call_count, 1)

    @patch('enmutils_int.lib.profile_manager.ProfileDaemon')
    def test_start__is_successful(self, *_):
        profile_manager.ProfileManager(self.profile_with_nodes)._start()

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch('enmutils_int.lib.profile_manager.ProfileManager.remove_from_active_profiles_list')
    @patch("enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes")
    @patch('enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._start')
    @patch('enmutils_int.lib.profile_manager.persistence')
    def test_start__persists_lock(self, mock_persistence, *_):
        mock_persistence.has_key.return_value = False
        self.profile_manager.profile.NAME = "TEST_LOCK_PROFILE"
        self.profile_manager.start()
        mock_persistence.has_key.assert_called_with("start_TEST_LOCK_PROFILE_lock")
        mock_persistence.set.assert_called_with("start_TEST_LOCK_PROFILE_lock", "", 5)

    @patch('enmutils_int.lib.profile_manager.log.logger.info')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._exclusive_profile_nodes_allocated')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_no_more_nodes_allocated_to_profile__if_profile_is_exclusive_and_already_has_nodes(self, mock_allocate,
                                                                                               mock_deallocate,
                                                                                               mock_nodes_allocated,
                                                                                               mock_info):
        self.profile_manager.release_nodes = False
        self.profile_manager.profile = Mock()
        self.profile_manager.profile.get_nodes_list_by_attribute.return_value = ["", ""]
        mock_nodes_allocated.return_value = True
        self.profile_manager._retain_or_release_nodes()
        self.assertFalse(mock_allocate.called)
        self.assertFalse(mock_deallocate.called)
        self.assertTrue(mock_info.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._exclusive_profile_nodes_allocated')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_retain_or_release_nodes_release(self, mock_allocate, mock_deallocate, mock_nodes_allocated):
        self.profile_manager._retain_or_release_nodes()
        self.assertTrue(mock_allocate.called)
        self.assertTrue(mock_deallocate.called)
        self.assertFalse(mock_nodes_allocated.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._exclusive_profile_nodes_allocated', return_value=False)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_retain_or_release_nodes_release_flag_false(self, mock_allocate, mock_deallocate, mock_nodes_allocated):
        self.profile_manager.release_nodes = False
        self.profile_manager._retain_or_release_nodes()
        self.assertTrue(mock_allocate.called)
        self.assertFalse(mock_deallocate.called)
        self.assertTrue(mock_nodes_allocated.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._exclusive_profile_nodes_allocated', return_value=True)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    @patch('enmutils_int.lib.profile_manager.log.logger.info')
    def test_retain_or_release_nodes__release_logs_if_nodes_filled(self, mock_info, *_):
        self.profile_manager.release_nodes = False
        self.profile_manager.profile.NAME = "TEST"
        self.profile_manager.profile.get_nodes_list_by_attribute.return_value = []
        self.profile_manager._retain_or_release_nodes()
        self.assertTrue(mock_info.called)

    def test_profile_requires_nodes(self):
        # Mock objects will return True for any hasattr, even if not explicitly assigned
        delattr(self.profile_manager.profile, "NUM_NODES")
        delattr(self.profile_manager.profile, "SUPPORTED_NODE_TYPES")
        self.assertFalse(self.profile_manager._profile_requires_nodes())
        self.profile_manager.profile.NUM_NODES = {"ERBS": 1}
        self.assertTrue(self.profile_manager._profile_requires_nodes())

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=True)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._retain_or_release_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_allocate_nodes_to_profile__is_successful_for_non_exclusive_profiles_if_services_not_used(
            self, mock_allocate, mock_retain_or_release_nodes, *_):
        self.profile_manager.profile.EXCLUSIVE = False
        self.profile_manager.profile.nodes_list = [Mock()]
        self.profile_manager._allocate_nodes_to_profile()
        self.assertTrue(mock_allocate.called)
        self.assertFalse(mock_retain_or_release_nodes.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=True)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._retain_or_release_nodes')
    @patch('enmutils_int.lib.profile_manager.nodemanager_adaptor')
    def test_allocate_nodes_to_profile__is_successful_for_non_exclusive_profiles_if_services_used(
            self, mock_nodemanager_adaptor, mock_retain_or_release_nodes, *_):
        self.profile_manager.nodes_mgr = mock_nodemanager_adaptor
        self.profile_manager.profile.EXCLUSIVE = False
        self.profile_manager.profile.nodes_list = [Mock()]
        self.profile_manager._allocate_nodes_to_profile()
        self.assertTrue(mock_nodemanager_adaptor.allocate_nodes.called)
        self.assertFalse(mock_retain_or_release_nodes.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=True)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._retain_or_release_nodes')
    def test_allocate_nodes_to_profile__is_successful_for_exclusive_profiles(
            self, mock_retain_or_release_nodes, *_):
        self.profile_manager.profile.EXCLUSIVE = True
        self.profile_manager.profile.nodes_list = [Mock()]
        self.profile_manager._allocate_nodes_to_profile()
        self.assertTrue(mock_retain_or_release_nodes.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=False)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._retain_or_release_nodes')
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_allocate_nodes_does_nothing_if_no_nodes_required(self, mock_allocate, mock_retain_or_release_nodes, *_):
        self.profile_manager._allocate_nodes_to_profile()
        self.assertFalse(mock_allocate.called)
        self.assertFalse(mock_retain_or_release_nodes.called)

    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._calculate_required_nodes', return_value=1)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.get_pool')
    def test_exclusive_profile_nodes_allocated__returns_true_if_service_not_used_and_all_nodes_allocated(
            self, mock_get_pool, *_):
        mock_get_pool.return_value.allocated_nodes.return_value = [Mock()]
        self.assertTrue(self.profile_manager._exclusive_profile_nodes_allocated())

    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._calculate_required_nodes', return_value=2)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.get_pool')
    def test_exclusive_profile_nodes_allocated__returns_false_if_service_not_used_and_not_all_nodes_allocated(
            self, mock_get_pool, *_):
        mock_get_pool.return_value.allocated_nodes.return_value = [Mock()]
        self.assertFalse(self.profile_manager._exclusive_profile_nodes_allocated())

    @patch("enmutils_int.lib.profile_manager.ProfileManager._calculate_required_nodes", return_value=1)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.list_nodes")
    def test_exclusive_profile_nodes_allocated__returns_true_if_service_used_and_all_nodes_allocated(
            self, mock_list_nodes, *_):
        self.profile_manager.nodemanager_service_can_be_used = True
        self.profile_manager.profile.NAME = "TEST_PROFILE_01"
        mock_list_nodes.return_value = (_, _, [Mock(profiles="TEST_PROFILE_01"), Mock(profiles="TEST_PROFILE_02")])
        self.assertTrue(self.profile_manager._exclusive_profile_nodes_allocated())
        mock_list_nodes.assert_called_with(node_attributes=["profiles"])

    @patch("enmutils_int.lib.profile_manager.ProfileManager._calculate_required_nodes", return_value=2)
    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.list_nodes")
    def test_exclusive_profile_nodes_allocated__returns_false_if_service_used_and_not_all_nodes_allocated(
            self, mock_list_nodes, *_):
        self.profile_manager.nodemanager_service_can_be_used = True
        self.profile_manager.profile.NAME = "TEST_PROFILE_01"
        mock_list_nodes.return_value = (_, _, [Mock(profiles="TEST_PROFILE_01"), Mock(profiles="TEST_PROFILE_02")])
        self.assertFalse(self.profile_manager._exclusive_profile_nodes_allocated())

    def test_calculate_required_nodes__is_successful_if_total_nodes_specified_in_profile(self):
        self.profile_manager.profile.TOTAL_NODES = 2
        self.assertEqual(2, self.profile_manager._calculate_required_nodes([[Mock()] * 10]))

    def test_calculate_required_nodes__is_successful_if_num_nodes_specified_in_profile(self, *_):
        self.profile_manager.profile = Mock()
        self.profile_manager.profile.NUM_NODES = {"ERBS": 1}
        delattr(self.profile_manager.profile, "TOTAL_NODES")
        nodes = [Mock(primary_type="ERBS")] * 5 + [Mock(primary_type="RadioNode")] * 5
        self.assertEqual(1, self.profile_manager._calculate_required_nodes(nodes))

    def test_calculate_required_nodes__is_successful_if_num_nodes_specified_in_profile_is_all_nodes_of_a_type(self, *_):
        self.profile_manager.profile = Mock()
        self.profile_manager.profile.NUM_NODES = {"ERBS": 1, "RadioNode": -1}
        delattr(self.profile_manager.profile, "TOTAL_NODES")
        nodes = [Mock(primary_type="ERBS")] * 5 + [Mock(primary_type="RadioNode")] * 5
        self.assertEqual(6, self.profile_manager._calculate_required_nodes(nodes))

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=True)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_allocate_erbs_nodes_to_profile(self, mock_allocate, *_):
        self.profile_mgr.profile.EXCLUSIVE = False
        self.profile_mgr.profile.NUM_NODES = {"ERBS": 1}
        self.profile_mgr.profile.nodes_list = [Mock()]
        self.profile_mgr._allocate_nodes_to_profile()
        self.assertTrue(mock_allocate.called)

    @patch('enmutils_int.lib.profile_manager.ProfileManager._profile_requires_nodes', return_value=True)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.Pool.allocated_nodes', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.allocate_nodes')
    def test_allocate_nodes_to_profile__exclusive(self, *_):
        self.profile_mgr.profile.EXCLUSIVE = True
        self.profile_mgr.profile.TOTAL_NODES = 1
        del self.profile_mgr.profile.NUM_NODES
        self.profile_mgr.profile.get_nodes_list_by_attribute.return_value = [Mock(), Mock()]
        self.profile_mgr.release_nodes = False
        self.profile_mgr._allocate_nodes_to_profile()

    @patch('enmutils_int.lib.profile_manager.persistence.get', return_value=["TEST_01"])
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.profile_manager.persistence.set')
    def test_remove_from_active_profiles_list(self, mock_set, *_):
        test, test1 = Mock(), Mock()
        test.NAME, test1.NAME = "TEST", "TEST_01"
        for _ in [test, test1]:
            self.profile_mgr.profile = _
            self.profile_mgr.remove_from_active_profiles_list()
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils_int.lib.profile_manager.ProfileManager.remove_from_active_profiles_list')
    @patch('enmutils_int.lib.profile_manager.persistence.remove')
    def test_remove_corrupted_profile_keys_and_update_active_list__removes_from_persistence_and_active_list(
            self, mock_remove, mock_active_list):
        self.profile_mgr.remove_corrupted_profile_keys_and_update_active_list("TEST_00")
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(1, mock_active_list.call_count)

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch('enmutils_int.lib.profile_manager.node_pool_mgr.deallocate_nodes')
    @patch('enmutils_int.lib.profile_manager.ProfileManager.remove_from_active_profiles_list')
    @patch('enmutils_int.lib.profile_manager.ProfileManager._start', side_effect=NoNodesAvailable)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile', side_effect=NoNodesAvailable)
    @patch('enmutils_int.lib.profile_manager.log.logger.error')
    def test_start__raises_nonodesavailable(self, mock_error, *_):
        self.profile_mgr.profile = Mock()
        self.profile_mgr.profile.NUM_NODES = {"ERBS": 1}
        self.assertRaises(NoNodesAvailable, self.profile_mgr.start)
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(False, self.profile_mgr.profile.run_profile)

    @patch("enmutils_int.lib.profile_manager.nodemanager_adaptor.can_service_be_used", return_value=False)
    @patch('enmutils_int.lib.profile_manager.ProfileManager._start', side_effect=ProfileAlreadyRunning("", 1234))
    @patch('enmutils_int.lib.profile_manager.ProfileManager._allocate_nodes_to_profile')
    def test_start_raises_profile_already_running(self, *_):
        self.assertRaises(ProfileAlreadyRunning, self.profile_mgr.start)

    @patch('enmutils_int.lib.profile_manager.process.kill_process_id')
    def test_initial_install_teardown(self, mock_os_kill):
        self.profile_mgr.initial_install_teardown()
        self.assertEqual(1, mock_os_kill.call_count)

    @patch('enmutils_int.lib.profile_manager.process.kill_process_id')
    @patch('enmutils_int.lib.profile_manager.log.logger.debug')
    def test_initial_install_teardown_logs_exception(self, mock_debug, mock_os_kill):
        mock_os_kill.side_effect = Exception("Error")
        self.profile_mgr.initial_install_teardown()
        mock_debug.assert_called_with("Failed to kill pid, may have already been killed, continuing teardown: Error")

    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    def test_profile_daemon_catches_existing_process(self, mock_run_local, *_):
        profile = Mock()
        profile_name = "TEST_01"
        response = Mock(stdout="root 12345 TEST_01 test_01")
        response.ok = 1
        mock_run_local.return_value = response
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        self.assertRaises(ProfileAlreadyRunning, daemon.check_for_existing_process, profile_name)

    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    def test_profile_daemon(self, mock_run_local, *_):
        profile = Mock()
        profile_name = "TEST_01"
        response = Mock(stdout="root 12345 TEST_01 test_01")
        response.ok = 0
        mock_run_local.return_value = response
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        daemon.check_for_existing_process(profile_name)

    @patch('enmutils_int.lib.profile_manager.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.get_pid')
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.check_for_existing_process')
    @patch('enmutils_int.lib.profile_manager.cache.is_host_ms', return_value=True)
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    def test_profile_daemon_raise_if_running_raises_workload_vm_exception(self, mock_run_local, *_):
        profile = Mock()
        profile_name = "TEST_01"
        profile.NAME = profile_name
        response = Mock(stdout="WORKLOAD_VM")
        response.ok = 0
        mock_run_local.return_value = response
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        self.assertRaises(profile_manager.WorkloadVMDetected, daemon._raise_if_running)

    @patch('enmutils_int.lib.profile_manager.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.get_pid')
    @patch('enmutils_int.lib.profile_manager.process.is_pid_running', return_value=True)
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.check_for_existing_process')
    @patch('enmutils_int.lib.profile_manager.cache.is_host_ms', return_value=False)
    @patch('enmutils_int.lib.profile_manager.cache.get_apache_url', return_value="localhost")
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.does_file_exist', return_value=True)
    def test_profile_daemon_raise_if_running_raises_already_running_exception(self, *_):
        profile = Mock()
        profile_name = "TEST_01"
        profile.NAME = profile_name
        profile.pid = "1234"
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        self.assertRaises(ProfileAlreadyRunning, daemon._raise_if_running)

    @patch('enmutils_int.lib.profile_manager.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.get_pid')
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.check_for_existing_process')
    @patch('enmutils_int.lib.profile_manager.cache.is_host_ms', return_value=False)
    @patch('enmutils_int.lib.profile_manager.cache.get_apache_url', return_value="localhost")
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.does_file_exist', return_value=False)
    def test_profile_daemon_raise_if_running(self, *_):
        profile = Mock()
        profile_name = "TEST_01"
        profile.NAME = profile_name
        profile.pid = "1234"
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        daemon._raise_if_running()

    @patch('enmutils_int.lib.profile_manager.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.get_pid')
    @patch('enmutils_int.lib.profile_manager.process.is_pid_running', return_value=True)
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.check_for_existing_process')
    @patch('enmutils_int.lib.profile_manager.shell.Command')
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    @patch('enmutils_int.lib.profile_manager.filesystem.does_file_exist', return_value=True)
    def test_raise_if_running__detects_completed_or_none_type_status(self, *_):
        profile = Mock()
        profile.state = None
        profile_name = "TEST_01"
        profile.ident_file_path = "file"
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        daemon._raise_if_running()
        profile.state = "COMPLETED"
        daemon._raise_if_running()
        profile.state = "STARTING"
        self.assertRaises(ProfileAlreadyRunning, daemon._raise_if_running)

    @patch('enmutils_int.lib.profile_manager.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.get_pid')
    @patch('enmutils_int.lib.profile_manager.process.is_pid_running', return_value=False)
    @patch('enmutils_int.lib.profile_manager.ProfileDaemon.check_for_existing_process')
    @patch('enmutils_int.lib.profile_manager.shell.Command')
    @patch('enmutils_int.lib.profile_manager.shell.run_local_cmd')
    @patch('enmutils_int.lib.profile_manager.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.profile_manager.shell.filesystem.delete_file')
    def test_raise_if_running__detects_non_running_process_for_existing_pid_file(self, mock_delete_file, *_):
        profile = Mock()
        profile.state = None
        profile_name = "TEST_01"
        profile.ident_file_path = "file"
        daemon = profile_manager.ProfileDaemon(profile_name, profile)
        daemon._raise_if_running()
        self.assertTrue(mock_delete_file.called)

    def test_profile_is_stopping__returns_true_if_profile_is_stopping(self):
        profile = Mock(state="STOPPING", running=True)
        profile_mgr = profile_manager.ProfileManager(profile)
        self.assertTrue(profile_mgr._profile_is_stopping())

    def test_profile_is_stopping__returns_false_if_profile_is_running(self):
        profile = Mock(state="RUNNING", running=True)
        profile_mgr = profile_manager.ProfileManager(profile)
        self.assertFalse(profile_mgr._profile_is_stopping())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
