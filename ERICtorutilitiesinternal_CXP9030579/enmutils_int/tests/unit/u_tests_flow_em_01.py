# !/usr/bin/env python
import unittest2
from mock import Mock, patch, PropertyMock
from enmutils_int.lib.workload.em_01 import EM_01
from enmutils_int.lib.profile_flows.em_flows.em_01_flow import (
    EM01Flow, ValidationError, EnmApplicationError
)
from testslib import unit_test_utils


class EMFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username='EM_01_user')
        self.flow = EM01Flow()
        self.flow.NUM_USERS = 1
        self.flow.TOTAL_NODES_NON_RACK = 1
        self.flow.NUM_USERS_RACK = 1
        self.flow.USER_ROLES = ["SomeRole"]
        self.flow.PARALLEL_SESSIONS_LAUNCH = 2
        self.radionodes = unit_test_utils.setup_test_node_objects(2, primary_type="RadioNode")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.execute_flow")
    def test_sev_profile_em_01_execute_flow__successful(self, mock_flow):
        EM_01().run()
        self.assertTrue(mock_flow.called)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_configured_nodes', return_value=["Node1", "Node2"])
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch("enmutils.lib.enm_user_2.User.remove_session", side_effect=[Exception, 0, 0])
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.validate_sessions', side_effect=[0, Exception])
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.update_profile_persistence_nodes_list")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_users')
    def test_001_em_execute_flow_is_successful(self, mock_create_user, mock_keep_running, mock_sleep,
                                               mock_configure_assigned, mock_poids, mock_nodes_list, *_):
        mock_nodes_list.return_value = self.radionodes[:]
        user1 = self.user
        user2 = Mock(username="EM_user")
        user2.remove_session.side_effect = Exception
        mock_create_user.return_value = [user1, user2]
        mock_configure_assigned.side_effect = [True, True]
        mock_poids.return_value = (["181477779763364", "181477779763360"], [self.radionodes])
        mock_keep_running.side_effect = [True, True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep.called)
        self.assertRaises(Exception, self.flow.execute_flow)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_configured_nodes',
           return_value=["Node1", "Node2"])
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch("enmutils.lib.enm_user_2.User.remove_session", side_effect=[Exception, 0, 0])
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.validate_sessions', side_effect=[0, Exception])
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.update_profile_persistence_nodes_list")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_values_from_global_properties', return_value='Extra_Large_ENM_On_Rack_Servers')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_users')
    def test_016_em_execute_flow_on_rack_is_successful(self, mock_create_user, mock_keep_running, mock_sleep,
                                                       mock_configure_assigned, mock_poids, mock_nodes_list, *_):
        mock_nodes_list.return_value = self.radionodes[:]
        user1 = self.user
        user2 = Mock(username="EM_user")
        user2.remove_session.side_effect = Exception
        mock_create_user.return_value = [user1, user2]
        mock_configure_assigned.side_effect = [True, True]
        mock_poids.return_value = (["181477779763364", "181477779763360"], [self.radionodes])
        mock_keep_running.side_effect = [True, True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep.called)
        self.assertRaises(Exception, self.flow.execute_flow)

    @patch('enmutils_int.lib.profile.Profile.nodes_list', new_callable=PropertyMock)
    @patch("enmutils.lib.enm_user_2.User.get")
    @patch("enmutils.lib.enm_user_2.User.remove_session")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep")
    def test_002_em_taskset(self, mock_sleep, *_):
        poid = "181477779763365"
        user_nodes = (self.user, poid)
        self.flow.task_set(user_nodes, self.flow)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.add_error_as_exception')
    def test_003_em_taskset_raises_exception(self, mock_add_error, *_):
        poid = "181477779763365"
        user_nodes = (self.user, poid)
        self.user.get.side_effect = Exception
        self.flow.task_set(user_nodes, self.flow)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_004_em_retrieve_poid(self, mock_debug, mock_sleep, mock_poids, *_):
        self.flow.SUCCESSFUL_NODES = []
        poid = ["181477779763365"]
        mock_poids.side_effect = [([], [self.radionodes[0]]), (poid, [self.radionodes[1]])]
        self.flow.retrieve_poids(self.radionodes)
        self.assertEquals(1, mock_debug.call_count)
        self.assertEquals(1, mock_sleep.call_count)

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    def test_005_em_configure_nodes_successful(self, mock_pull_config_tarball, *_):
        mock_pull_config_tarball.return_value = "abc"
        expected_configured_nodes = self.radionodes[:]
        response = self.flow.configure_nodes(self.radionodes)
        self.assertEqual(response, (expected_configured_nodes, []))

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.add_error_as_exception')
    def test_006_em_configure_nodes__pull_config_tarball_raises_validation_error(self, mock_add_error,
                                                                                 mock_pull_config_tarball, *_):
        mock_pull_config_tarball.side_effect = ValidationError
        response = self.flow.configure_nodes(self.radionodes)
        self.assertTrue(mock_add_error.called)
        self.assertEqual(response, ([], self.radionodes))

    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.add_error_as_exception')
    def test_007_em_configure_nodes__pull_config_tarball_raises_exception(self, mock_add_error, mock_pull_config_tarball, *_):
        mock_pull_config_tarball.side_effect = Exception
        response = self.flow.configure_nodes(self.radionodes)
        self.assertTrue(mock_add_error.called)
        self.assertEqual(response, ([], self.radionodes))

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_008_em_configure_nodes_configure_assigned_nodes_raises_exception(self, mock_debug, mock_add_error,
                                                                              mock_configure_assigned, *_):
        mock_configure_assigned.side_effect = Exception
        response = self.flow.configure_nodes(self.radionodes)
        self.assertTrue(mock_add_error.called)
        self.assertTrue(mock_debug.called)
        self.assertEqual(response, ([], self.radionodes))

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_configured_nodes', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.validate_sessions')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.update_profile_persistence_nodes_list")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_users')
    def test_009_em_execute_flow_has_unconfigured_nodes(self, mock_create_user, mock_keep_running, mock_sleep,
                                                        mock_configure_assigned, mock_poids, mock_nodes_list, *_):
        mock_nodes_list.return_value = self.radionodes[:]
        mock_create_user.return_value = [self.user] * 2
        mock_configure_assigned.side_effect = [True, Exception, True]
        mock_poids.return_value = (["181477779763364", "181477779763360"], [self.radionodes])
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.validate_sessions')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.update_profile_persistence_nodes_list")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_users')
    def test_010_em_execute_flow_has_more_users(self, mock_create_user, mock_keep_running, mock_sleep,
                                                mock_configure_assigned, mock_nodes_list, mock_poids, *_):
        mock_nodes_list.return_value = self.radionodes[:]
        self.flow.PARALLEL_SESSIONS_LAUNCH = 1
        mock_create_user.return_value = [self.user] * 4
        mock_configure_assigned.side_effect = [True, Exception, True]
        mock_poids.return_value = (["181477779763364", "181477779763360", "181477779765364", "181477779765334"],
                                   [self.radionodes])
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.validate_sessions')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.pull_config_files_tarball")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.get_poids")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.update_profile_persistence_nodes_list")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.configure_assigned_nodes")
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.sleep_until_time")
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.create_users')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_011_em_execute_flow_has_unconfigured_nodes(self, mock_debug, mock_create_user, mock_keep_running,
                                                        mock_sleep, mock_configure_assigned, mock_nodes_list, *_):
        mock_nodes_list.return_value = self.radionodes * 3
        mock_create_user.return_value = []
        mock_configure_assigned.side_effect = [True, True, Exception]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_012_em_execute_flow_validate_sessions__is_successful(
            self, mock_logger_debug):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.url = "url"
        response.json.return_value = [{"userId": "EM_01_user"}]
        self.user.get.return_value = response
        self.flow.validate_sessions([self.user])
        self.assertEqual(mock_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_013_em_01_validate_sessions__raises_EnmApplicationError(self, mock_logger_debug):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.url = "url"
        response.json.return_value = []
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.validate_sessions, [self.user])
        self.assertEqual(mock_logger_debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    def test_014_em_01_validate_sessions__raises_EnmApplicationError_2(self, mock_logger_debug):
        response = Mock()
        response.ok = True
        response.status_code = 403
        response.url = "url"
        response.text = '[]'
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.flow.validate_sessions, [self.user])
        self.assertEqual(mock_logger_debug.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.configure_nodes")
    def test_015_em_01_get_configured_nodes(self, mock_nodes, mock_log):
        configured_nodes, unconfigured_nodes = self.radionodes, []
        mock_nodes.return_value = configured_nodes, unconfigured_nodes
        nodes = self.radionodes * 2
        users = [self.user] * 3
        configured_nodes = self.flow.get_configured_nodes(users, nodes)
        self.assertFalse(mock_log.called)
        self.assertEqual(len(configured_nodes), 4)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.configure_nodes")
    def test_017_em_01_get_configured_nodes(self, mock_nodes, mock_log):
        configured_nodes, unconfigured_nodes = self.radionodes[:1], []
        mock_nodes.return_value = configured_nodes, unconfigured_nodes
        nodes = self.radionodes * 1
        users = [self.user] * 3
        configured_nodes = self.flow.get_configured_nodes(users, nodes)
        self.assertFalse(mock_log.called)
        self.assertEqual(len(configured_nodes), 2)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.configure_nodes")
    def test_017_em_01_get_configured_nodes_fail(self, mock_nodes, mock_log):
        configured_nodes, unconfigured_nodes = self.radionodes[:1], self.radionodes
        mock_nodes.return_value = configured_nodes, unconfigured_nodes
        nodes = self.radionodes * 1
        users = [self.user] * 3
        configured_nodes = self.flow.get_configured_nodes(users, nodes)
        self.assertTrue(mock_log.called)
        self.assertEqual(len(configured_nodes), 2)

    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.em_flows.em_01_flow.EM01Flow.get_nodes_list_by_attribute')
    def test_018_get_profile_nodes_users__raises_exception(self, mock_nodes_list, mock_add_error, *_):
        mock_nodes_list.return_value = Exception
        self.flow.get_profile_users_nodes()
        self.assertTrue(mock_add_error.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
