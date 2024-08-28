#!/usr/bin/env python
import datetime
from functools import partial

import unittest2
from enmutils.lib.exceptions import NetsimError
from enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile import (
    PmBscRecordingsProfile, BscRecordingsSubscription, toggle_file_generation_on_node,
    toggle_file_generation_on_bsc_node)
from enmutils_int.lib.workload.pm_77 import PM_77
from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils


class PmBscRecordingsProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = PmBscRecordingsProfile()
        self.profile.USER = Mock()
        self.profile.NUM_NODES = {'RNC': 1}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "activate_deactivate_subscription_with_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    def test_execute_flow__is_successful_enabling_pm(
            self, mock_create_bsc_recording_subscription, mock_get_sub_file_action_enable_or_disable_command,
            mock_activate_deactivate_subscription_with_nodes, mock_get_schedule_times, *_):
        subscription = Mock()
        mock_create_bsc_recording_subscription.return_value = subscription
        mock_get_sub_file_action_enable_or_disable_command.return_value = "Enable"
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 0, 52)
        mock_get_schedule_times.return_value = [datetime.datetime(2019, 8, 22, 0, 52),
                                                datetime.datetime(2019, 8, 22, 2, 52),
                                                datetime.datetime(2019, 8, 22, 6, 52),
                                                datetime.datetime(2019, 8, 22, 8, 52),
                                                datetime.datetime(2019, 8, 22, 12, 52),
                                                datetime.datetime(2019, 8, 22, 14, 50),
                                                datetime.datetime(2019, 8, 22, 18, 52),
                                                datetime.datetime(2019, 8, 22, 20, 52)]
        self.profile.execute_flow()
        self.assertTrue(mock_activate_deactivate_subscription_with_nodes.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running",
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "activate_deactivate_subscription_with_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    def test_execute_flow__is_successful_disabling_pm(
            self, mock_create_bsc_recording_subscription, mock_get_sub_file_action_enable_or_disable_command,
            mock_activate_deactivate_subscription_with_nodes, mock_get_schedule_times, *_):
        subscription = Mock()
        mock_create_bsc_recording_subscription.return_value = subscription
        mock_get_sub_file_action_enable_or_disable_command.side_effect = ["Enable", "Disable"]
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 2, 52)
        mock_get_schedule_times.return_value = [datetime.datetime(2019, 8, 22, 0, 52),
                                                datetime.datetime(2019, 8, 22, 2, 52),
                                                datetime.datetime(2019, 8, 22, 6, 52),
                                                datetime.datetime(2019, 8, 22, 8, 52),
                                                datetime.datetime(2019, 8, 22, 12, 52),
                                                datetime.datetime(2019, 8, 22, 14, 50),
                                                datetime.datetime(2019, 8, 22, 18, 52),
                                                datetime.datetime(2019, 8, 22, 20, 52)]
        self.profile.execute_flow()
        self.assertTrue(mock_activate_deactivate_subscription_with_nodes.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.get_schedule_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "activate_deactivate_subscription_with_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile."
           "get_subscription_file_generation_action_enable_or_disable_command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    def test_execute_flow__is_unsuccessful_disabling_pm(
            self, mock_create_bsc_recording_subscription, mock_get_sub_file_action_enable_or_disable_command,
            mock_activate_deactivate_subscription_with_nodes, mock_get_schedule_times, *_):
        subscription = Mock()
        mock_create_bsc_recording_subscription.return_value = subscription
        mock_get_sub_file_action_enable_or_disable_command.return_value = "Disable"
        self.profile.next_run_time = datetime.datetime(2019, 8, 22, 2, 52)
        mock_get_schedule_times.return_value = [datetime.datetime(2019, 8, 22, 0, 52),
                                                datetime.datetime(2019, 8, 22, 2, 52),
                                                datetime.datetime(2019, 8, 22, 6, 52),
                                                datetime.datetime(2019, 8, 22, 8, 52),
                                                datetime.datetime(2019, 8, 22, 12, 52),
                                                datetime.datetime(2019, 8, 22, 14, 50),
                                                datetime.datetime(2019, 8, 22, 18, 52),
                                                datetime.datetime(2019, 8, 22, 20, 52)]
        self.profile.execute_flow()
        self.assertTrue(mock_activate_deactivate_subscription_with_nodes.called)
        self.assertEqual(mock_get_sub_file_action_enable_or_disable_command.return_value, "Disable")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.partial")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.picklable_boundmethod")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "toggle_file_generation_on_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running")
    def test_execute_flow__is_adds_error_if_subscription_cant_be_created(
            self, mock_keep_running, mock_create_bsc_recording_subscription, *_):
        mock_create_bsc_recording_subscription.side_effect = Exception
        self.profile.execute_flow()
        self.assertFalse(mock_keep_running.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "update_teardown_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "toggle_file_generation_on_nodes")
    def test_get_activate_subscription_with_nodes(self, mock_toggle_file_generation_on_nodes,
                                                  mock_update_teardown_list, *_):
        subscription = Mock()
        self.profile.activate_deactivate_subscription_with_nodes("Enable", "Disable", subscription)
        self.assertTrue(mock_toggle_file_generation_on_nodes.called)
        self.assertTrue(mock_update_teardown_list.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "update_teardown_list")
    def test_get_deactivate_subscription_with_nodes_failed(self, mock_update_teardown_list, *_):
        subscription = Mock()
        self.profile.activate_deactivate_subscription_with_nodes("Disable", "Disable", subscription)
        self.assertTrue(mock_update_teardown_list.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "update_teardown_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "toggle_file_generation_on_nodes")
    def test_get_deactivate_subscription_with_nodes(self, mock_toggle_file_generation_on_nodes,
                                                    mock_update_teardown_list, *_):
        subscription = Mock()
        self.profile.activate_deactivate_subscription_with_nodes("Disable", "Enable", subscription)
        self.assertTrue(mock_toggle_file_generation_on_nodes.called)
        self.assertTrue(mock_update_teardown_list.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.add_error_as_exception')
    def test_get_activate_subscription_with_nodes_failed(self, mock_exception, *_):
        subscription = Mock()
        self.profile.activate_deactivate_subscription_with_nodes("Enable", "Disable", subscription)
        subscription.activate.side_Effect = Exception
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "set_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription_object")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.BscRecordingsSubscription")
    def test_create_bsc_recording_subscription___is_successful(
            self, mock_bscrecordingssubscription, mock_create_bsc_recording_subscription_object,
            mock_set_teardown, *_):
        profile = PmBscRecordingsProfile()
        subscription = mock_create_bsc_recording_subscription_object.return_value
        subscription.name, subscription.id = "PM_XY", 999

        self.assertEqual(subscription, profile.create_bsc_recording_subscription())
        self.assertTrue(subscription.create.called)
        mock_set_teardown.assert_called_with(mock_bscrecordingssubscription, "PM_XY", 999)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.__init__",
           return_value=None)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "set_subscription_description", return_value="some_desc")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.identifier",
           new_callable=PropertyMock, return_value="profile_name")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.get_profile_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.BscRecordingsSubscription")
    def test_create_bsc_recording_subscription_object__is_successful(
            self, mock_bscrecordingssubscription, mock_get_profile_nodes, *_):
        profile = PmBscRecordingsProfile()
        profile.USER = "user1"
        nodes = [Mock()]

        mock_get_profile_nodes.return_value = nodes
        self.assertEqual(mock_bscrecordingssubscription.return_value,
                         profile.create_bsc_recording_subscription_object())
        mock_bscrecordingssubscription.assert_called_with(
            **{"name": "profile_name", "description": "some_desc", "user": "user1", "nodes": nodes})
        mock_get_profile_nodes.assert_called_with(node_attributes=["node_id", "poid", "primary_type",
                                                                   "node_name", "netsim", "simulation"])

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.toggle_file_generation_on_node")
    def test_toggle_file_generation_on_nodes__is_successful(
            self, mock_toggle_file_generation_on_node, mock_threadqueue):
        node1 = node2 = node3 = Mock()
        self.profile.NODE_THREAD_COUNT = 2
        self.profile.THREAD_TIMEOUT = 999
        subscription = Mock(nodes=[node1, node2, node3])
        self.profile.toggle_file_generation_on_nodes("Enable", subscription)
        mock_threadqueue.assert_called_with(subscription.nodes, num_workers=3,
                                            func_ref=mock_toggle_file_generation_on_node, args=["Enable", self.profile],
                                            task_wait_timeout=999)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "execute_netsim_command_on_netsim_node")
    def test_toggle_file_generation_on_bsc_node__returns_true_if_all_actions_successful(self,
                                                                                        mock_execute_netsim_command,
                                                                                        mock_debug_log, *_):
        node = Mock(node_id="Node1")
        self.profile.BSC_RECORDING_TYPES = ["Type1", "Type2"]
        self.assertTrue(toggle_file_generation_on_bsc_node(node, "Enable", self.profile))
        self.assertTrue(toggle_file_generation_on_bsc_node(node, "Disable", self.profile))
        self.assertTrue(mock_execute_netsim_command.called)
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "execute_netsim_command_on_netsim_node", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.log.logger.debug")
    def test_toggle_file_generation_on_bsc_node__returns_netsim_error_if_all_actions_not_successful(self,
                                                                                                    mock_debug_log, *_):
        node = Mock(node_id="Node1")
        self.profile.BSC_RECORDING_TYPES = ["Type1", "Type2"]
        self.assertRaises(NetsimError, toggle_file_generation_on_bsc_node, node, "Enable", self.profile)
        self.assertRaises(NetsimError, toggle_file_generation_on_bsc_node, node, "Disable", self.profile)
        self.assertFalse(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.toggle_file_generation_on_bsc_node")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.log.logger.debug")
    def test_toggle_file_generation_on_node__if_node_is_enable(self, mock_debug_log,
                                                               mock_toggle_file_generation_on_bsc_node):
        node = Mock(node_id="Node1")
        self.assertTrue(toggle_file_generation_on_node(node, "Enable", self.profile))
        self.assertTrue(mock_debug_log.called)
        mock_toggle_file_generation_on_bsc_node.assert_called_with(node, "Enable", self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.toggle_file_generation_on_bsc_node")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.log.logger.debug")
    def test_toggle_file_generation_on_node__if_node_is_disable(self, mock_debug_log,
                                                                mock_toggle_file_generation_on_bsc_node):
        node = Mock(node_id="Node1")
        self.assertTrue(toggle_file_generation_on_node(node, "Disable", self.profile))
        self.assertTrue(mock_debug_log.called)
        mock_toggle_file_generation_on_bsc_node.assert_called_with(node, "Disable", self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "toggle_file_generation_on_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.partial")
    def test_update_teardown_list__is_successful_when_called_with_enable(
            self, mock_partial, mock_toggle_file_generation_on_nodes, mock_picklable_boundmethod):
        node1 = Mock(node_id="Node1")
        node2 = Mock(node_id="Node2")
        user = self.profile.USER
        subscription = Mock(**{"name": "blah", "description": "blah", "nodes": [node1, node2]})
        self.profile.teardown_list = [user, subscription]

        mock_partial.return_value = Mock()
        self.profile.update_teardown_list("Enable", subscription)

        self.assertEqual(self.profile.teardown_list, [user, subscription, mock_partial.return_value])
        mock_picklable_boundmethod.assert_called_with(mock_toggle_file_generation_on_nodes)
        mock_partial.assert_called_with(mock_picklable_boundmethod.return_value, "Disable", subscription)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "toggle_file_generation_on_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.partial")
    def test_update_teardown_list__is_successful_when_called_with_disable(
            self, *_):
        node1 = Mock(node_id="Node1")
        node2 = Mock(node_id="Node2")
        user = self.profile.USER
        subscription = BscRecordingsSubscription(**{"name": "blah", "description": "blah", "nodes": [node1, node2]})

        mock_partial = partial(Mock(), "Disable", subscription)
        self.profile.teardown_list = [mock_partial, user, subscription]

        self.profile.update_teardown_list("Disable", subscription)
        self.assertEqual(self.profile.teardown_list, [user, subscription])

    @patch('enmutils_int.lib.workload.pm_77.PmBscRecordingsProfile.execute_flow')
    def test_run__in_pm_77_returns_none(self, *_):
        profile = PM_77()
        self.assertEqual(None, profile.run())

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_execute_flow__when_subscription_activation_failed_pm(self, mock_exception, *_):
        subscription = Mock()
        self.profile.execute_flow()
        subscription.activate.side_Effect = Exception
        self.assertTrue(mock_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile."
           "create_bsc_recording_subscription")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.state',
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile.PmSubscriptionProfile.execute_flow")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile.PmBscRecordingsProfile.sleep_until_time")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_execute_flow__when_subscription_deactivation_failed_pm(self, mock_exception, *_):
        subscription = Mock()
        self.profile.execute_flow()
        subscription.deactivate.side_Effect = Exception
        self.assertTrue(mock_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
